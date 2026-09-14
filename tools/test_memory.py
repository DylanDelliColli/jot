#!/usr/bin/env python3
"""Memory acceptance tests using the real CLI, files, and linked worktrees."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().with_name("jot.py")
sys.path.insert(0, str(CLI.parent.parent))
from tools.jot import JotError, memory_by_id, read_memory, write_memory  # noqa: E402


class MemoryRecords(unittest.TestCase):
    def test_rewrite_keeps_complete_json_and_no_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = {"id": "record", "text": "first", "agent": "a"}
            write_memory(root, note)
            note["text"] = "Café\nRevised evidence"
            write_memory(root, note)
            self.assertEqual(read_memory(root / "record.json"), note)
            self.assertEqual([p.name for p in root.iterdir()], ["record.json"])

    def test_record_lookup_rejects_paths_and_other_scopes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_memory(root, {"id": "record", "text": "keep", "agent": "a"})
            for record_id in ("", ".", "..", "../record", "sub/record"):
                with self.assertRaises(JotError):
                    memory_by_id(root, record_id, "a")
            with self.assertRaises(JotError):
                memory_by_id(root, "record", "b")
            self.assertEqual(memory_by_id(root, "record", "a")[1]["text"], "keep")


class MemoryCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="jot-memory-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "seed").write_text("seed\n")
        self.git(self.repo, "add", "seed")
        self.git(self.repo, "commit", "-qm", "seed")
        self.env = dict(os.environ)
        self.env.pop("JOT_AGENT", None)

    def git(self, cwd, *args):
        return subprocess.run(
            ["git", "-c", "user.name=Jot test", "-c", "user.email=test@example.invalid", *args],
            cwd=cwd, text=True, capture_output=True, check=True)

    def jot(self, *args, cwd=None, agent=None, code=0):
        env = dict(self.env)
        if agent is not None:
            env["JOT_AGENT"] = agent
        result = subprocess.run([sys.executable, str(CLI), *args],
                                cwd=cwd or self.repo, env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def records(self, kind):
        directory = self.repo / ".git" / "jot" / "memory" / kind
        return [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]

    def save(self, text, **kwargs):
        return json.loads(self.jot("study", "--save", text, "--json", **kwargs).stdout)

    def test_capture_and_recall_are_separate(self):
        self.jot("memory", "An unverified restart theory", agent="a")
        rough = self.records("rough")
        self.assertEqual(len(rough), 1)
        self.assertEqual(rough[0]["agent"], "a")
        self.assertEqual(rough[0]["branch"], "main")
        self.assertTrue(rough[0]["rev"])
        recalled = json.loads(self.jot("remember", "--json", agent="a").stdout)
        self.assertEqual(recalled, [])
        listed = json.loads(self.jot("memory", "--list", "--json", agent="a").stdout)
        self.assertEqual(listed, rough)
        self.assertFalse((self.repo / ".git/jot/pending").exists())

    def test_study_reads_both_kinds_then_updates_and_deletes(self):
        self.jot("memory", "Restart must refresh the first recommendation")
        rough_id = self.records("rough")[0]["id"]
        saved = self.save("Check the first action after restoring saved state")
        self.assertEqual(len(self.records("rough")), 1)
        study = json.loads(self.jot("study", "--json").stdout)
        self.assertEqual(study["rough"][0]["id"], rough_id)
        self.assertEqual(study["bank"][0]["id"], saved["id"])
        revised = json.loads(self.jot("study", "--save", "Check both restored state and the next action",
                                      "--id", saved["id"], "--json").stdout)
        self.assertEqual(revised["id"], saved["id"])
        self.assertEqual(revised["created_at"], saved["created_at"])
        self.assertGreaterEqual(revised["updated_at"], saved["updated_at"])
        self.assertEqual(len(self.records("bank")), 1)
        self.jot("memory", "--delete", rough_id)
        self.jot("study", "--delete", saved["id"])
        self.assertEqual(self.records("rough"), [])
        self.assertEqual(self.records("bank"), [])
        self.assertEqual(json.loads(self.jot("remember", "--json").stdout), [])

    def test_scope_defaults_overrides_and_shared_reads(self):
        self.save("General repository lesson")
        a = self.save("Agent A lesson", agent="a")
        self.save("Agent B lesson", agent="b")
        self.assertEqual([r["text"] for r in json.loads(self.jot("remember", "--json").stdout)],
                         ["General repository lesson"])
        self.assertEqual(json.loads(self.jot("remember", "--json", agent="a").stdout)[0]["id"], a["id"])
        b = json.loads(self.jot("remember", "--agent", "b", "--json", agent="a").stdout)
        self.assertEqual([r["text"] for r in b], ["Agent B lesson"])
        general = json.loads(self.jot("remember", "--agent", "", "--json", agent="a").stdout)
        self.assertEqual(general[0]["text"], "General repository lesson")
        self.assertEqual(len(json.loads(self.jot("remember", "--all-agents", "--json", agent="a").stdout)), 3)
        self.jot("study", "--delete", a["id"], agent="b", code=2)
        self.assertEqual(len(self.records("bank")), 3)
        self.jot("study", "--delete", a["id"], "--agent", "a", agent="b")
        self.assertEqual(len(self.records("bank")), 2)

    def test_scope_is_also_applied_to_capture_and_study(self):
        self.jot("memory", "A rough", agent="a")
        self.jot("memory", "B rough", "--agent", "b", agent="a")
        self.save("B cleaned", agent="b")
        study = json.loads(self.jot("study", "--json", agent="a").stdout)
        self.assertEqual([r["text"] for r in study["rough"]], ["A rough"])
        self.assertEqual(study["bank"], [])
        self.assertEqual(len(json.loads(self.jot("memory", "--list", "--all-agents", "--json").stdout)), 2)

    def test_query_preserves_complete_unicode_multiline_lesson(self):
        text = "Café recovery\nCheck state AND the first action.\n" + "Evidence matters. " * 30
        self.save(text)
        self.save("Unrelated networking lesson")
        matches = json.loads(self.jot("remember", "CAFÉ", "--json").stdout)
        self.assertEqual([r["text"] for r in matches], [text])
        self.assertIn(text, self.jot("remember", "recovery").stdout)
        self.assertEqual(json.loads(self.jot("remember", "absent", "--json").stdout), [])

    def test_discovery_behavior_does_not_depend_on_identity(self):
        self.jot("Ordinary discovery", "--file", "seed", agent="a")
        self.save("A memory", agent="a")
        listed = self.jot("list", agent="b").stdout
        self.assertIn("Ordinary discovery", listed)
        self.assertNotIn("A memory", listed)
        pending = self.repo / ".git/jot/pending"
        self.assertEqual(Path(self.jot("dir", agent="a").stdout.strip()), pending)
        discovery = json.loads(next(pending.glob("*.json")).read_text())
        self.assertNotIn("agent", discovery)
        self.assertEqual(discovery["file"], "seed")
        self.jot("--", "memory", agent="a")
        self.assertEqual(len(list(pending.glob("*.json"))), 2)

    def test_memory_survives_worktree_teardown_and_is_repo_local(self):
        linked = self.root / "linked"
        self.git(self.repo, "worktree", "add", "-qb", "side", str(linked))
        self.jot("memory", "From the linked checkout", cwd=linked, agent="a")
        saved = self.save("Shared across this repo's worktrees", cwd=linked, agent="a")
        self.git(self.repo, "worktree", "remove", str(linked))
        self.assertEqual(len(self.records("rough")), 1)
        self.assertEqual(json.loads(self.jot("remember", "--json", agent="a").stdout)[0]["id"], saved["id"])
        other = self.root / "other"
        other.mkdir()
        self.git(other, "init", "-q")
        self.assertEqual(json.loads(self.jot("remember", "--json", cwd=other, agent="a").stdout), [])

    def test_invalid_mutations_do_not_change_records(self):
        original = self.save("Keep this lesson")
        rough = self.jot("memory", "Still rough", "--json")
        rough_id = json.loads(rough.stdout)["id"]
        for args in [("study", "--save", " "),
                     ("study", "--save", "Changed", "--id", ""),
                     ("study", "--save", "Changed", "--id", "missing"),
                     ("study", "--delete", "../pending/victim"),
                     ("study", "--delete", rough_id),
                     ("memory", "--delete", original["id"]),
                     ("study", "--id", original["id"]),
                     ("memory", "--list", "unexpected text"),
                     ("memory", "--all-agents", "ambiguous author")]:
            self.jot(*args, code=2)
        self.assertEqual(self.records("bank"), [original])
        self.assertEqual(len(self.records("rough")), 1)

    def test_bad_record_is_reported_instead_of_becoming_a_lesson(self):
        self.save("Sound memory")
        bad = self.repo / ".git/jot/memory/bank/bad.json"
        bad.write_text("{broken")
        result = self.jot("remember", code=2)
        self.assertIn("bad.json", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        bad.write_text(json.dumps({"id": "bad", "text": ["not text"]}))
        self.jot("remember", code=2)

    def test_memory_commands_outside_a_repository_fail_cleanly(self):
        for args in [("memory", "A note"), ("study",), ("remember",)]:
            result = self.jot(*args, cwd=self.root, code=2)
            self.assertIn("not inside a git repository", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
