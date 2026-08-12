#!/usr/bin/env python3
"""jot — durable capture of ownerless observations.

Writes ONE FILE PER NOTE as JSON into <git-common-dir>/jot/pending/ so notes
stay with the repository they concern and survive worktree teardown. One file
per note is the whole concurrency story at the ten-worker target: writers never
share a file, so they never contend.

Capture is a three-second action. Everything expensive — judging whether an
observation deserves a bead, a doc edit, or nothing — belongs to jot-review,
which is operator-invoked and human-gated.

Usage:
  jot "<observation>" [--file P] [--symptom S] [--repro R] [--why W]
  jot list                 Print pending notes
  jot dir                  Print the queue directory (jot-review locates it here)

Stdlib only, matching the other tools in this repository.
"""
import argparse
import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

QUEUE_PARTS = ("jot", "pending")
OPTIONAL_FIELDS = ("file", "symptom", "repro", "why")


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
        description="Capture an observation into this repository's note queue.")
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
    path = write_note(queue_dir(cwd), note)
    print(f"noted → {path}", file=stdout)
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


def main(argv=None, cwd=None, stdout=None, stderr=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cwd = cwd or os.getcwd()
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    try:
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
