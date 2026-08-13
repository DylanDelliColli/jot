#!/usr/bin/env python3
"""Contract tests for tools.jot.

Run from the repo root: python3 tools/test_jot.py

Real filesystem and real git repositories throughout — no mocks. The queue
location is derived from git, so a mocked git would test nothing that matters.

The load-bearing cases are worktree.resolves_to_common_dir (a note captured in
a linked worktree must outlive that worktree) and id.same_second_no_collision
(same pid, same second — the random suffix is the only thing preventing loss).
"""
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.jot import main, queue_dir  # noqa: E402

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"check": name, "pass": bool(ok), "detail": str(detail)[:160]})


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, capture_output=True, text=True, check=True)


def make_repo(path):
    """An initialised repo with one commit, so HEAD resolves."""
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    Path(path, "seed.txt").write_text("seed\n", encoding="utf-8")
    git(path, "add", "seed.txt")
    git(path, "commit", "-q", "-m", "seed")
    return path


def run(argv, cwd):
    """Invoke jot, returning (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = main(argv=argv, cwd=cwd, stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def notes_in(repo):
    queue = queue_dir(repo)
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(queue.glob("*.json"))]


def test_capture_writes_every_automatic_field(root):
    repo = make_repo(os.path.join(root, "auto"))
    code, out, _ = run(["docs-doctor exits 0 on a degraded corpus"], repo)
    written = notes_in(repo)
    note = written[0] if written else {}
    check("capture.exit_zero", code == 0, f"code={code} out={out!r}")
    check("capture.one_file_per_note", len(written) == 1, f"count={len(written)}")
    check("capture.text_verbatim",
          note.get("text") == "docs-doctor exits 0 on a degraded corpus", note.get("text"))
    check("capture.has_automatic_fields",
          all(note.get(f) for f in ("id", "created_at", "cwd", "branch", "rev")),
          {f: note.get(f) for f in ("id", "created_at", "cwd", "branch", "rev")})
    check("capture.branch_is_real", note.get("branch") == "main", note.get("branch"))
    check("capture.created_at_is_utc",
          str(note.get("created_at", "")).endswith("Z"), note.get("created_at"))


def test_optional_fields_only_when_passed(root):
    repo = make_repo(os.path.join(root, "optional"))
    run(["bare note"], repo)
    bare = notes_in(repo)[0]
    check("optional.absent_when_unused",
          not any(f in bare for f in ("file", "symptom", "repro", "why")), sorted(bare))

    repo2 = make_repo(os.path.join(root, "optional2"))
    run(["flagged", "--file", "tools/jot.py", "--symptom", "exits 2",
         "--repro", "run outside a repo", "--why", "capture must not fail silently"], repo2)
    full = notes_in(repo2)[0]
    check("optional.present_when_passed",
          full.get("file") == "tools/jot.py" and full.get("symptom") == "exits 2"
          and full.get("repro") == "run outside a repo" and full.get("why"),
          {k: full.get(k) for k in ("file", "symptom", "repro", "why")})


def test_same_second_no_collision(root):
    repo = make_repo(os.path.join(root, "collide"))
    for i in range(12):
        run([f"note {i}"], repo)
    written = notes_in(repo)
    ids = {n["id"] for n in written}
    check("id.same_second_no_collision",
          len(written) == 12 and len(ids) == 12, f"files={len(written)} ids={len(ids)}")


def test_queue_from_subdirectory(root):
    repo = make_repo(os.path.join(root, "subdir"))
    nested = os.path.join(repo, "a", "b")
    os.makedirs(nested)
    code, _, _ = run(["from a subdirectory"], nested)
    written = notes_in(repo)
    check("subdir.writes_to_repo_queue",
          code == 0 and len(written) == 1, f"code={code} count={len(written)}")
    check("subdir.cwd_is_repo_relative",
          written and written[0].get("cwd") == os.path.join("a", "b"),
          written[0].get("cwd") if written else "none")


def test_worktree_resolves_to_common_dir(root):
    repo = make_repo(os.path.join(root, "wt-main"))
    tree = os.path.join(root, "wt-linked")
    git(repo, "worktree", "add", "-q", "-b", "side", tree)
    code, _, _ = run(["captured inside a linked worktree"], tree)
    check("worktree.resolves_to_common_dir",
          code == 0 and len(notes_in(repo)) == 1,
          f"code={code} main_queue={len(notes_in(repo))}")
    check("worktree.queue_not_inside_worktree",
          not Path(tree, ".git", "jot").exists(), "queue leaked into the worktree gitdir")

    git(repo, "worktree", "remove", "--force", tree)
    check("worktree.note_survives_teardown",
          not os.path.exists(tree) and len(notes_in(repo)) == 1,
          f"after teardown={len(notes_in(repo))}")


def test_list(root):
    repo = make_repo(os.path.join(root, "listing"))
    code, out, _ = run(["list"], repo)
    check("list.empty_safe", code == 0 and "no pending" in out, f"code={code} out={out!r}")

    run(["first observation"], repo)
    run(["second observation", "--file", "AGENTS.md"], repo)
    code, out, _ = run(["list"], repo)
    check("list.shows_pending",
          code == 0 and "first observation" in out and "second observation" in out
          and "2 pending" in out, f"code={code} out={out!r}")
    check("list.shows_optional_fields", "file=AGENTS.md" in out, out)


def test_outside_repo(root):
    outside = os.path.join(root, "not-a-repo")
    os.makedirs(outside)
    code, _, err = run(["should not be captured"], outside)
    check("outside_repo.exits_nonzero", code == 2, f"code={code}")
    check("outside_repo.message_is_actionable",
          "not inside a git repository" in err and "Traceback" not in err, err.strip())

    code, _, err = run(["list"], outside)
    check("outside_repo.list_also_fails", code == 2 and "jot:" in err, f"code={code} err={err!r}")


def test_dir_subcommand(root):
    repo = make_repo(os.path.join(root, "dir-cmd"))
    code, out, _ = run(["dir"], repo)
    expected = str(Path(repo, ".git", "jot", "pending"))
    check("dir.prints_queue_path",
          code == 0 and out.strip() == expected, f"got={out.strip()!r} want={expected!r}")


def test_empty_observation(root):
    repo = make_repo(os.path.join(root, "empty"))
    code, _, err = run([], repo)
    check("empty.rejected", code == 2 and "observation is required" in err, f"code={code} err={err!r}")


def test_nudge_prompts_but_never_blocks(root):
    """At the threshold capture must still succeed — a gate here would make
    capture cost something, which is the one thing it may never do."""
    from tools.jot import NUDGE_AT
    repo = make_repo(os.path.join(root, "nudge"))
    for i in range(NUDGE_AT - 2):
        run([f"note {i}"], repo)
    code, out, _ = run(["the one below the threshold"], repo)
    # not the bare word "pending" — the queue path contains it
    check("nudge.silent_below_threshold",
          code == 0 and "jot-review" not in out, f"code={code} out={out!r}")

    code, out, _ = run(["the one that reaches it"], repo)
    check("nudge.prompts_at_threshold",
          code == 0 and f"{NUDGE_AT} notes are pending" in out
          and "jot-review" in out, f"code={code} out={out!r}")

    code, _, _ = run(["and capture still works past it"], repo)
    check("nudge.never_blocks_capture",
          code == 0 and len(notes_in(repo)) == NUDGE_AT + 1,
          f"code={code} count={len(notes_in(repo))}")


def main_():
    with tempfile.TemporaryDirectory() as root:
        for case in (
            test_capture_writes_every_automatic_field,
            test_optional_fields_only_when_passed,
            test_same_second_no_collision,
            test_queue_from_subdirectory,
            test_worktree_resolves_to_common_dir,
            test_list,
            test_outside_repo,
            test_dir_subcommand,
            test_empty_observation,
            test_nudge_prompts_but_never_blocks,
        ):
            try:
                case(root)
            except Exception as exc:  # a crashing case is a failing case, not a lost run
                check(f"{case.__name__}.raised", False, f"{type(exc).__name__}: {exc}")

    passed = sum(1 for c in CHECKS if c["pass"])
    failed = len(CHECKS) - passed
    print(json.dumps({"checks": CHECKS, "passed": passed, "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main_())
