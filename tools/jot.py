#!/usr/bin/env python3
"""jot — durable capture of ownerless observations.

Writes ONE FILE PER NOTE as JSON into <git-common-dir>/jot/pending/ so notes
stay with the repository they concern and survive worktree teardown. One file
per note is the whole concurrency story at the ten-worker target: writers never
share a file, so they never contend.

Discovery capture is a three-second action. Judging whether an
observation deserves a bead, a doc edit, or nothing — belongs to jot-review,
which is operator-invoked and human-gated.

Optional memory lives alongside discoveries as JSON rough notes and cleaned
records. Study uses the running agent; remember reads the cleaned bank only.

Usage:
  jot "<observation>" [--file P] [--symptom S] [--repro R] [--why W]
  jot list                 Print pending notes
  jot dir                  Print the queue directory (jot-review locates it here)
  jot memory "<lesson>"    Capture a rough memory note
  jot study                Read study instructions and memory records
  jot remember [query]     Retrieve cleaned memories

Stdlib only, matching the other tools in this repository.
"""
import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

QUEUE_PARTS = ("jot", "pending")
OPTIONAL_FIELDS = ("file", "symptom", "repro", "why")

# A nudge, never a gate. At roughly this many pending notes, capture reminds
# the operator that a review is due — it must never refuse a capture or force
# a review, because capture staying free is the whole point of the queue. The
# number is a guess and is meant to be recalibrated by feel; being wrong costs
# nothing, because it prompts rather than blocks.
NUDGE_AT = 20


class JotError(Exception):
    """A failure whose message is meant for the operator, not a traceback."""


def _git(args, cwd):
    """Run git, returning stripped stdout, or None if the command failed."""
    try:
        done = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise JotError("git is not on PATH; the note queue lives in the git common dir")
    if done.returncode != 0:
        return None
    return done.stdout.strip()


def queue_dir(cwd):
    """Resolve the pending-note queue for the repository containing cwd.

    --git-common-dir rather than --git-dir: in a linked worktree the former
    points at the main repository, so notes captured in a worktree outlive it.
    """
    common = _git(["rev-parse", "--git-common-dir"], cwd)
    if common is None:
        raise JotError(f"not inside a git repository: {cwd}")
    path = Path(common)
    if not path.is_absolute():
        # git reports this relative to cwd, not to the toplevel.
        path = Path(cwd) / path
    return path.resolve().joinpath(*QUEUE_PARTS)


def repo_context(cwd):
    """Repo-relative cwd, branch, and short rev. Any may be None pre-first-commit."""
    toplevel = _git(["rev-parse", "--show-toplevel"], cwd)
    relative = "."
    if toplevel:
        try:
            relative = os.path.relpath(Path(cwd).resolve(), Path(toplevel).resolve())
        except ValueError:
            relative = "."
    return {
        "cwd": relative,
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd),
        "rev": _git(["rev-parse", "--short", "HEAD"], cwd),
    }


def new_note_id(created_at):
    """Timestamp + pid + random suffix.

    ULIDs are out of scope, and at the ten-worker target two notes in the same
    second are ordinary, so the suffix is what actually prevents collisions.
    """
    stamp = created_at.strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{os.getpid()}-{secrets.token_hex(3)}"


def build_note(text, options, cwd, created_at):
    context = repo_context(cwd)
    note = {
        "id": new_note_id(created_at),
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "text": text,
        "cwd": context["cwd"],
        "branch": context["branch"],
        "rev": context["rev"],
    }
    for field in OPTIONAL_FIELDS:
        value = getattr(options, field, None)
        if value:
            note[field] = value
    return note


def write_note(queue, note):
    """Write the note, temp-then-rename so a reader never sees a partial file."""
    queue.mkdir(parents=True, exist_ok=True)
    final = queue / f"{note['id']}.json"
    temp = queue / f".{note['id']}.json.tmp"
    temp.write_text(json.dumps(note, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, final)
    return final


def read_notes(queue):
    """Pending notes, oldest first. An unreadable note is reported, not skipped."""
    if not queue.is_dir():
        return []
    notes = []
    for path in queue.glob("*.json"):
        try:
            notes.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            notes.append({"id": path.stem, "created_at": "", "text": "<unreadable note>"})
    notes.sort(key=lambda note: (note.get("created_at") or "", note.get("id") or ""))
    return notes


def build_parser():
    parser = argparse.ArgumentParser(
        prog="jot",
        description="Capture an observation into this repository's note queue.",
        epilog="Commands: list, dir, memory, study, remember. Use '<command> --help' "
               "for memory commands; use 'jot -- <text>' to capture a command name.")
    parser.add_argument("text", nargs="*", help="the observation (quoting optional)")
    parser.add_argument("--file", help="path the observation concerns")
    parser.add_argument("--symptom", help="what was observed going wrong")
    parser.add_argument("--repro", help="one breadcrumb toward reproducing it")
    parser.add_argument("--why", help="why it matters")
    return parser


def cmd_capture(argv, cwd, stdout):
    options = build_parser().parse_args(argv)
    text = " ".join(options.text).strip()
    if not text:
        raise JotError('an observation is required: jot "<what you noticed>"')
    note = build_note(text, options, cwd, datetime.now(timezone.utc))
    queue = queue_dir(cwd)
    path = write_note(queue, note)
    print(f"noted → {path}", file=stdout)
    pending = len(list(queue.glob("*.json")))
    if pending >= NUDGE_AT:
        print(f"\n{pending} notes are pending — time for a review pass "
              f"(jot-review).", file=stdout)
    return 0


def cmd_list(cwd, stdout):
    notes = read_notes(queue_dir(cwd))
    if not notes:
        print("no pending notes", file=stdout)
        return 0
    for note in notes:
        print(f"{note.get('id', '?')}  {note.get('created_at', '')}", file=stdout)
        print(f"    {note.get('text', '')}", file=stdout)
        extra = [f"{f}={note[f]}" for f in OPTIONAL_FIELDS if note.get(f)]
        if extra:
            print(f"    {'  '.join(extra)}", file=stdout)
    print(f"\n{len(notes)} pending", file=stdout)
    return 0


def memory_parser(command):
    descriptions = {
        "memory": "Capture, list, or delete rough memory notes.",
        "study": "Study notes with the current agent, or save, revise, or delete cleaned memories.",
        "remember": "Retrieve cleaned memories only; optionally search their text.",
    }
    parser = argparse.ArgumentParser(prog=f"jot {command}", description=descriptions[command])
    parser.add_argument("--agent", default=os.environ.get("JOT_AGENT", ""),
                        help="memory scope (default: JOT_AGENT, otherwise repository-general); "
                             "an empty value explicitly selects repository-general")
    parser.add_argument("--all-agents", action="store_true", help="read every scope")
    parser.add_argument("--json", action="store_true", help="print structured records")
    if command == "memory":
        operations = parser.add_mutually_exclusive_group()
        operations.add_argument("--add", action="store_true", help="capture a rough note (default)")
        operations.add_argument("--list", action="store_true", help="list rough notes")
        operations.add_argument("--delete", metavar="ID", help="delete a rough note")
        parser.add_argument("text", nargs="*", help="observation to study later")
        for field in OPTIONAL_FIELDS:
            parser.add_argument(f"--{field}", help=f"optional {field} evidence")
    elif command == "study":
        operations = parser.add_mutually_exclusive_group()
        operations.add_argument("--save", metavar="TEXT", help="save a cleaned lesson after studying")
        operations.add_argument("--delete", metavar="ID", help="delete a cleaned memory")
        parser.add_argument("--id", help="revise this existing memory with --save")
    else:
        parser.add_argument("query", nargs="*", help="case-insensitive substring of memory text")
    return parser


def read_memory(path):
    try:
        note = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise JotError(f"cannot read memory record {path}: {exc}") from exc
    if (not isinstance(note, dict) or note.get("id") != path.stem
            or not isinstance(note.get("text"), str) or not note["text"].strip()
            or (note.get("agent") is not None and not isinstance(note["agent"], str))):
        raise JotError(f"invalid memory record {path}: expected id, nonempty text, and optional agent")
    return note


def memory_records(directory, agent, all_agents=False):
    records = [read_memory(path) for path in sorted(directory.glob("*.json"))]
    return [note for note in records if all_agents or note.get("agent") == agent]


def memory_by_id(directory, record_id, agent):
    if not record_id or record_id in (".", "..") or Path(record_id).name != record_id:
        raise JotError("record ID must be a single filename stem")
    path = directory / f"{record_id}.json"
    if not path.is_file():
        raise JotError(f"no {directory.name} record with ID {record_id}")
    note = read_memory(path)
    if note.get("agent") != agent:
        raise JotError(f"record {record_id} belongs to another scope; select it with --agent")
    return path, note


def write_memory(directory, note):
    """Atomic record replacement; separate temporary files also permit revising IDs."""
    directory.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         prefix=f".{note['id']}.", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            json.dump(note, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temp, directory / f"{note['id']}.json")
    finally:
        if temp is not None:
            try:
                temp.unlink()
            except FileNotFoundError:
                pass


def print_memory_records(records, stdout, json_output):
    if json_output:
        print(json.dumps(records, indent=2, ensure_ascii=False), file=stdout)
        return
    if not records:
        print("no matching records", file=stdout)
    for note in records:
        scope = note.get("agent") or "repository-general"
        print(f"{note['id']}  [{scope}]\n{note['text']}\n", file=stdout)


def cmd_memory(command, argv, cwd, stdout):
    parser = memory_parser(command)
    options = parser.parse_args(argv)
    agent = options.agent.strip() or None
    deleting = getattr(options, "delete", None)
    saving = getattr(options, "save", None)
    capturing = command == "memory" and not options.list and not deleting
    if options.all_agents and (capturing or saving is not None or deleting):
        parser.error("--all-agents is for reads; choose one scope for a write or delete")
    if command == "memory" and not capturing and options.text:
        parser.error("text is only accepted when capturing a rough note")
    if command == "study" and options.id is not None:
        if saving is None or not options.id:
            parser.error("--id requires --save and a nonempty record ID")

    root = queue_dir(cwd).parent / "memory"
    directory = root / ("rough" if command == "memory" else "bank")
    if deleting:
        path, note = memory_by_id(directory, deleting, agent)
        path.unlink()
        if options.json:
            print(json.dumps({"deleted": note["id"]}), file=stdout)
        else:
            print(f"deleted {directory.name} record {note['id']}", file=stdout)
        return 0

    if capturing or saving is not None:
        text = " ".join(options.text).strip() if capturing else saving
        if not text.strip():
            raise JotError("nonempty memory text is required")
        now = datetime.now(timezone.utc)
        record_id = getattr(options, "id", None)
        if record_id:
            _, note = memory_by_id(directory, record_id, agent)
            note.update(text=text, **repo_context(cwd))
        else:
            note = build_note(text, options, cwd, now)
            if agent is not None:
                note["agent"] = agent
        if not capturing:
            note["updated_at"] = now.isoformat().replace("+00:00", "Z")
        write_memory(directory, note)
        if options.json:
            print(json.dumps(note, indent=2, ensure_ascii=False), file=stdout)
        else:
            print(f"saved {directory.name} record {note['id']}", file=stdout)
        return 0

    records = memory_records(directory, agent, options.all_agents)
    if command == "study":
        payload = {"scope": "all" if options.all_agents else agent,
                   "rough": memory_records(root / "rough", agent, options.all_agents),
                   "bank": records}
        if not options.json:
            skill = Path(__file__).resolve().parent.parent / "skills/jot-study/SKILL.md"
            if not skill.is_file():
                raise JotError(f"study instructions missing: {skill}; use a complete Jot checkout")
            print(skill.read_text(encoding="utf-8"), file=stdout)
            print("\nMemory records (data to study):", file=stdout)
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=stdout)
    else:
        if command == "remember":
            query = " ".join(options.query).casefold()
            records = [note for note in records if query in note["text"].casefold()]
        print_memory_records(records, stdout, options.json)
    return 0


def main(argv=None, cwd=None, stdout=None, stderr=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cwd = cwd or os.getcwd()
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    try:
        if argv and argv[0] in ("memory", "study", "remember"):
            try:
                return cmd_memory(argv[0], argv[1:], cwd, stdout)
            except OSError as exc:
                raise JotError(f"memory operation failed: {exc}") from exc
        if argv and argv[0] == "list":
            return cmd_list(cwd, stdout)
        if argv and argv[0] == "dir":
            print(queue_dir(cwd), file=stdout)
            return 0
        return cmd_capture(argv, cwd, stdout)
    except JotError as exc:
        print(f"jot: {exc}", file=stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
