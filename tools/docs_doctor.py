#!/usr/bin/env python3
"""docs-doctor — structural checks for a declared documentation corpus.

A repository declares its corpus in `docs-corpus.json`; this tool enforces
that declaration against the working tree. It does not impose a canonical
structure — the enforcement is real, the declaration is the repository's.

Four checks ship here:

  docs-structure    every file under docs/ matches exactly one declared
                    class, every root markdown matches a root class, and
                    no corpus path escapes the repository via a symlink
  metadata          every managed document carries a well-formed doc-meta
                    block whose role agrees with the class it belongs to
  index-symmetry    docs/README.md lists exactly the managed corpus, with
                    well-formed managed, historical, and alias rows
                    (the index/doc-meta agreement pass reports here too)
  inflight-residency  one review file per cycle, one shift report per lane

Aggregate: clean | degraded | failed | execution_error. Exit 0 = clean or
degraded, 1 = failed, 2 = execution error. A degraded result is never
clean: every finding must trace to an open bead or a recorded decision.

Ported from the eleven-check implementation incubated in abacus, narrowed
by jot-met.3 to the checks that serve the declared-structure scope. Seven
checks — supersession, probes, bead-citations, historical-bytes,
archive-index, reverse-citations, evidence-index — and the probe executor
they need are DEFERRED, not rejected: they remain in the frozen abacus-v1
parts bin and are revived by porting them here against an observed need.

Two manifest keys are therefore validated but not yet consumed:
`protected_mainline_ref` (archive-index) and a class's `indexes_class`
(evidence-index). They are kept so a repository's manifest survives the
narrowing unchanged and a later revival needs code, not a new schema.

Stdlib only, matching the other tools in this repository.
"""
import argparse
import datetime
import fnmatch
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import PurePath

HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
ROLES = ("contract", "evidence", "working")
LIFECYCLES = ("active", "partially-superseded", "superseded", "withdrawn",
              "parked", "historical")
META_KEYS = ("role", "lifecycle", "superseded-by", "surviving-clauses",
             "review-when", "expires-when")

FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)$")


def scan_fences(text):
    """One delimiter-aware fence scanner for every 'outside fenced blocks'
    contract. Yields (line, state, info): state is None outside,
    'opener'/'content'/'closer' inside; info is the opener's info string.
    A close requires the same character, at least the opener's length, and
    nothing else on the line; openers inside an open fence are content.
    Returns (rows, unterminated_info) — unterminated_info is the open
    block's info string when EOF arrives inside a fence, else None."""
    rows = []
    open_char, open_len, info = None, 0, None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if open_char is None:
            # a backtick opener's info string may not contain a backtick
            # (CommonMark); such a line is ordinary content
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                seq = m.group(1)
                open_char, open_len = seq[0], len(seq)
                info = m.group(2).strip()
                rows.append((line, "opener", info))
            else:
                rows.append((line, None, None))
        else:
            if m and m.group(1)[0] == open_char \
                    and len(m.group(1)) >= open_len \
                    and not m.group(2).strip():
                rows.append((line, "closer", info))
                open_char, info = None, None
            else:
                rows.append((line, "content", info))
    return rows, info if open_char is not None else None


def strip_fences(text):
    """Lines of text with fenced code-block lines blanked."""
    rows, _ = scan_fences(text)
    return [line if state is None else "" for line, state, _info in rows]


def repo_relative(p):
    """One OS-usable repo-relative path predicate for manifest fields and
    index cells alike."""
    segs = p.split("/") if isinstance(p, str) else []
    return isinstance(p, str) and p and not p.startswith("/") \
        and not any(s in ("", ".", "..") for s in segs) \
        and not any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in p)


def parse_doc_meta(text):
    """(meta dict | None, [error strings]). The block must open the file
    (leading blank lines tolerated) and must be closed."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or lines[i].strip() != "```doc-meta":
        return None, []
    meta, errors = {}, []
    closed = False
    i += 1
    while i < len(lines):
        if lines[i].strip() == "```":
            closed = True
            break
        line = lines[i]
        i += 1
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"unparseable line: {line.strip()[:60]}")
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key not in META_KEYS:
            errors.append(f"unknown key: {key}")
            continue
        if key in meta:
            errors.append(f"duplicate key: {key}")
            continue
        if not value:
            errors.append(f"empty value: {key}")
            continue
        meta[key] = value
    for req in ("role", "lifecycle"):
        if req not in meta:
            errors.append(f"missing key: {req}")
    if meta.get("role") not in ROLES and "role" in meta:
        errors.append(f"invalid role: {meta['role']}")
    if meta.get("lifecycle") not in LIFECYCLES and "lifecycle" in meta:
        errors.append(f"invalid lifecycle: {meta['lifecycle']}")
    lc = meta.get("lifecycle")
    if not closed:
        errors.append("unterminated doc-meta block")
    if lc == "superseded" and "superseded-by" not in meta:
        errors.append("superseded requires superseded-by")
    if lc == "partially-superseded":
        if "superseded-by" not in meta:
            errors.append("partially-superseded requires superseded-by")
        if "surviving-clauses" not in meta:
            errors.append("partially-superseded requires surviving-clauses")
    if lc not in ("superseded", "partially-superseded") \
            and "superseded-by" in meta:
        errors.append(f"superseded-by forbidden for lifecycle {lc}")
    if lc != "partially-superseded" and "surviving-clauses" in meta:
        errors.append(f"surviving-clauses forbidden for lifecycle {lc}")
    return meta, errors


def parse_table_rows(text):
    """All markdown table data rows outside fences, as cell lists."""
    rows = []
    for line in strip_fences(text):
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|") and len(s) > 1):
            continue
        cells = [c.strip() for c in s[1:-1].split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(cells)
    return rows


class Doctor:
    def __init__(self, repo):
        self.repo = os.path.realpath(repo)
        self.findings = []
        self.meta = {}          # path -> doc-meta dict (or None)
        self.index_rows = {}    # path -> managed row cells
        self.manifest = None
        self.docs_files = {}    # relpath -> class name (docs tree)
        self.managed = []       # all managed doc relpaths needing metadata
        self.modules = []       # managed_globs matches
        self.root_contracts = []
        self.tracked = None     # single git discovery observation
        self.unreadable = set()  # read-failed paths, one finding each
        self.docs_observed = True  # walk enumerated fully
        self.unobservable = set()  # stat-failed paths

    def find(self, check, path, locator, result, reason):
        self.findings.append({"check": check, "path": path,
                              "locator": locator, "result": result,
                              "reason": reason})

    def _git(self, *args, stdin=None):
        """Failure-safe git seam: a spawn or decode failure is an
        observation with the sentinel rc -255, which every caller must
        classify as execution_error, never as row data."""
        try:
            return subprocess.run(["git", *args], cwd=self.repo, input=stdin,
                                  capture_output=True, text=True)
        except (OSError, ValueError) as exc:
            return subprocess.CompletedProcess(
                ["git", *args], returncode=-255, stdout="",
                stderr=f"git unavailable: {exc}")

    def _confined(self, rel):
        """Realpath repo confinement through the nearest existing ancestor:
        lexical repo-relativity is insufficient when an intermediate
        component is a symlink."""
        probe = os.path.join(self.repo, rel)
        while not os.path.lexists(probe):
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        rp = os.path.realpath(probe)
        return rp == self.repo or rp.startswith(self.repo + os.sep)

    def _read(self, rel):
        """Text of a managed file, or None after emitting one structured
        execution_error — a filesystem failure must never escape the
        result algebra as a traceback."""
        if rel in self.unreadable or rel in self.unobservable:
            return None
        try:
            with open(os.path.join(self.repo, rel), encoding="utf-8",
                      errors="replace") as fh:
                return fh.read()
        except OSError as exc:
            self.unreadable.add(rel)
            self.find("execution", rel, "-", "execution_error",
                      f"unreadable managed file: {exc}")
            return None

    def _stat_state(self, rel):
        """Type-aware tri-state observation: 'regular' | 'symlink' |
        'other' | 'absent' | 'error'. EACCES is never absence — it emits
        one execution_error per path and callers must suppress every
        absence- or type-derived conclusion. Only a successfully observed
        regular file can satisfy current-file resolution; a directory,
        FIFO, or undeclared symlink cannot."""
        try:
            st = os.lstat(os.path.join(self.repo, rel))
        except (FileNotFoundError, NotADirectoryError):
            return "absent"
        except (OSError, ValueError) as exc:
            # ValueError covers an embedded NUL reaching a syscall: a
            # no-traceback backstop for authored input
            if rel not in self.unobservable:
                self.unobservable.add(rel)
                self.find("execution", rel, "-", "execution_error",
                          f"path unobservable: {exc}")
            return "error"
        if stat.S_ISLNK(st.st_mode):
            return "symlink"
        if stat.S_ISREG(st.st_mode):
            return "regular"
        return "other"

    def _exists(self, rel):
        return self._stat_state(rel) == "regular"

    # -- manifest -----------------------------------------------------------
    def load_manifest(self):
        """Fail-closed manifest gate: the complete schema is validated
        before any consumer runs; one structured execution_error per
        violation, never a traceback or a silent policy change."""
        path = os.path.join(self.repo, "docs-corpus.json")
        if not os.path.isfile(path):
            self.find("execution", "docs-corpus.json", "-", "execution_error",
                      "manifest missing")
            return False
        try:
            with open(path, encoding="utf-8") as fh:
                mf = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            self.find("execution", "docs-corpus.json", "-", "execution_error",
                      f"manifest unreadable or unparseable: {exc}")
            return False
        errs = self._validate_manifest(mf)
        ref = mf.get("protected_mainline_ref")
        if isinstance(ref, str) and ref.startswith("refs/"):
            # Git's own ref-name grammar, not a regex approximation:
            # refs/heads/main@old is legal, refs/heads/main~1 is not
            r = self._git("check-ref-format", ref)
            if r.returncode == -255:
                errs.append(f"cannot validate protected_mainline_ref: "
                            f"{r.stderr.strip()[:80]}")
            elif r.returncode != 0:
                errs.append("protected_mainline_ref is not a valid full "
                            "ref name (git check-ref-format); revision "
                            "expressions are not roots")
        if errs:
            for e in errs[:20]:
                self.find("execution", "docs-corpus.json", "-",
                          "execution_error", f"manifest invalid: {e}")
            return False
        self.manifest = mf
        return True

    TOP_KEYS = {"docs_classes", "managed_globs", "managed_files",
                "alias_symlinks", "historical_files", "inflight_globs",
                "protected_mainline_ref", "discovery", "regex_semantics",
                "glob_semantics"}
    CLASS_KEYS = {"dir": {"name", "dir", "basename_regex", "unique_by",
                          "calendar_date_group", "role"},
                  "file": {"name", "file", "role", "indexes_class",
                           "exactly_one_file_in_dir"},
                  "files": {"name", "files", "role"}}
    # the implementation hardcodes these semantics; a manifest declaring
    # anything else would silently lie about what runs
    FROZEN_LITERALS = {
        ("discovery", "docs"): "filesystem walk of docs/, no ignore filtering",
        ("discovery", "root_and_modules"):
            "git ls-files --cached --others --exclude-standard -z",
        ("regex_semantics",): "python re.fullmatch over the basename, "
                              "after the class directory matches exactly",
        ("glob_semantics",): "python pathlib PurePath.full_match; "
                             "** crosses separators"}

    @classmethod
    def _validate_manifest(cls, mf):
        errs = []
        if not isinstance(mf, dict):
            return ["top level must be an object"]
        for key in sorted(set(mf) - cls.TOP_KEYS):
            errs.append(f"unknown key: {key}")
        for key in sorted(cls.TOP_KEYS - set(mf)):
            errs.append(f"missing key: {key}")

        repo_rel = repo_relative

        def path_list(key):
            v = mf.get(key)
            if not isinstance(v, list) or not all(repo_rel(s) for s in v):
                errs.append(f"{key} must be a list of repo-relative paths")
                return []
            return v

        seen_paths = {}
        for key in ("managed_files", "alias_symlinks", "historical_files"):
            for p in path_list(key):
                if p in seen_paths:
                    errs.append(f"{p} in both {seen_paths[p]} and {key}")
                seen_paths[p] = key
        for key in ("managed_globs", "inflight_globs"):
            path_list(key)
        ref = mf.get("protected_mainline_ref")
        if not isinstance(ref, str) or not ref.startswith("refs/"):
            errs.append("protected_mainline_ref must be an exact full ref "
                        "name (refs/...); HEAD, short names, and revision "
                        "expressions are not roots")
        disc = mf.get("discovery")
        if not isinstance(disc, dict) or set(disc) != {"docs",
                                                       "root_and_modules"}:
            # exactly the two frozen policies — an extra key would claim a
            # discovery no consumer executes
            errs.append("discovery must declare exactly docs and "
                        "root_and_modules")
        for keys, want in cls.FROZEN_LITERALS.items():
            node = mf
            for k in keys:
                node = node.get(k) if isinstance(node, dict) else None
            if node != want:
                errs.append(f"{'.'.join(keys)} must be the frozen literal "
                            f"{want!r}")
        classes = mf.get("docs_classes")
        if not isinstance(classes, list) or not classes:
            errs.append("docs_classes must be a nonempty list")
            return errs
        names = set()
        for c in classes:
            if not isinstance(c, dict) or not isinstance(c.get("name"), str):
                errs.append("every class needs a string name")
                continue
            n = c["name"]
            if n in names:
                errs.append(f"duplicate class name {n}")
            names.add(n)
            kinds = [k for k in ("dir", "file", "files") if k in c]
            if len(kinds) != 1:
                errs.append(f"class {n} needs exactly one of dir/file/files")
                continue
            kind = kinds[0]
            for key in sorted(set(c) - cls.CLASS_KEYS[kind]):
                errs.append(f"class {n}: key {key} not applicable to a "
                            f"{kind} class")
            if kind == "dir":
                if not repo_rel(c["dir"]):
                    errs.append(f"class {n}: dir must be repo-relative")
                rx = c.get("basename_regex")
                if not isinstance(rx, str):
                    errs.append(f"class {n}: dir class needs basename_regex")
                    continue
                try:
                    compiled = re.compile(rx)
                except re.error as exc:
                    errs.append(f"class {n}: basename_regex invalid: {exc}")
                    continue
                for gkey in ("unique_by", "calendar_date_group"):
                    g = c.get(gkey)
                    if g is not None and (not isinstance(g, str)
                                          or g not in compiled.groupindex):
                        errs.append(f"class {n}: {gkey} must name a capture "
                                    "group")
            elif kind == "file":
                if not repo_rel(c["file"]):
                    errs.append(f"class {n}: file must be repo-relative")
                elif c["file"] in seen_paths:
                    errs.append(f"class {n}: {c['file']} already claimed by "
                                f"{seen_paths[c['file']]}")
                else:
                    seen_paths[c["file"]] = f"class {n}"
                if not isinstance(c.get("exactly_one_file_in_dir", False),
                                  bool):
                    errs.append(f"class {n}: exactly_one_file_in_dir must "
                                "be boolean")
            else:
                if not isinstance(c["files"], list) or not all(
                        repo_rel(s) for s in c["files"]):
                    errs.append(f"class {n}: files must be repo-relative")
                else:
                    for p in c["files"]:
                        if p in seen_paths:
                            errs.append(f"class {n}: {p} already claimed by "
                                        f"{seen_paths[p]}")
                        seen_paths[p] = f"class {n}"
            role = c.get("role")
            if role is not None and role not in ROLES:
                errs.append(f"class {n}: role {role} not in {ROLES}")
        for c in classes:
            if not isinstance(c, dict):
                continue
            tgt = c.get("indexes_class")
            if tgt is None:
                continue
            # type before membership: an unhashable value must be a
            # structured error, never a lookup crash
            if not isinstance(tgt, str) or tgt not in names or not any(
                    isinstance(o, dict) and o.get("name") == tgt
                    and "dir" in o for o in classes):
                errs.append(f"indexes_class {tgt!r} must name a dir class")
        return errs

    # -- discovery + docs structure ----------------------------------------
    def classify_docs(self):
        classes = self.manifest["docs_classes"]
        docs_root = os.path.join(self.repo, "docs")
        if os.path.islink(docs_root):
            self.find("docs-structure", "docs", "-", "failed",
                      "docs/ itself is a symlink")
            return
        if not os.path.isdir(docs_root):
            return
        if not os.path.realpath(docs_root).startswith(self.repo + os.sep):
            self.find("execution", "docs", "-", "execution_error",
                      "docs/ escapes the repository")
            return
        # the closed world includes directories: every directory under
        # docs/ must be a class directory
        known_dirs = {"docs"}
        for c in classes:
            if "dir" in c:
                known_dirs.add(c["dir"])
            for f in [c.get("file")] + list(c.get("files", [])):
                if f:
                    known_dirs.add(os.path.dirname(f))
        entries = []

        def _walk_error(exc):
            # a tree that cannot be enumerated is inoperable, not empty:
            # absence must never be derived from it
            self.docs_observed = False
            self.find("execution", os.path.relpath(
                getattr(exc, "filename", docs_root) or docs_root, self.repo),
                "-", "execution_error",
                f"docs walk failed: {exc}")

        for base, dirs, files in os.walk(docs_root, onerror=_walk_error):
            for name in list(dirs):
                full = os.path.join(base, name)
                rel = os.path.relpath(full, self.repo)
                if os.path.islink(full):
                    self.find("docs-structure", rel, "-", "failed",
                              "symlink under docs/")
                    dirs.remove(name)
                    continue
                if rel not in known_dirs:
                    self.find("docs-structure", rel, "-", "failed",
                              "unknown subdirectory under docs/")
                    dirs.remove(name)
            for name in files:
                full = os.path.join(base, name)
                rel = os.path.relpath(full, self.repo)
                # the discovery domain is regular files and symlinks:
                # sockets, FIFOs, and devices are rejected unopened, from
                # one observation
                fstate = self._stat_state(rel)
                if fstate == "error":
                    self.docs_observed = False
                    continue
                if fstate == "symlink":
                    self.find("docs-structure", rel, "-", "failed",
                              "symlink under docs/")
                    continue
                if fstate != "regular":
                    self.find("docs-structure", rel, "-", "failed",
                              "not a regular file")
                    continue
                entries.append(rel)
        by_class = {c["name"]: [] for c in classes}
        for rel in sorted(entries):
            matches = []
            base = os.path.basename(rel)
            parent = os.path.dirname(rel)
            for c in classes:
                if "dir" in c:
                    if parent == c["dir"] \
                            and re.fullmatch(c["basename_regex"], base):
                        matches.append(c)
                elif "file" in c:
                    if rel == c["file"]:
                        matches.append(c)
                elif "files" in c:
                    if rel in c["files"]:
                        matches.append(c)
            if len(matches) != 1:
                self.find("docs-structure", rel, "-", "failed",
                          "matches no class" if not matches
                          else f"matches {len(matches)} classes")
                continue
            cls = matches[0]
            m = re.fullmatch(cls.get("basename_regex", ""), base) \
                if "dir" in cls else None
            group = cls.get("calendar_date_group")
            if m and group:
                try:
                    datetime.date.fromisoformat(m.group(group))
                except ValueError:
                    self.find("docs-structure", rel, group, "failed",
                              f"invalid calendar date {m.group(group)}")
                    continue
            self.docs_files[rel] = cls["name"]
            by_class[cls["name"]].append((rel, m))
        for c in classes:
            key = c.get("unique_by")
            if key:
                seen = {}
                for rel, m in by_class[c["name"]]:
                    seen.setdefault(m.group(key), []).append(rel)
                for val, rels in seen.items():
                    if len(rels) > 1:
                        for rel in rels:
                            self.find("docs-structure", rel, key, "failed",
                                      f"duplicate {key} {val} in class "
                                      f"{c['name']}")
            if c.get("exactly_one_file_in_dir"):
                d = os.path.dirname(c["file"])
                others = [r for r in entries
                          if os.path.dirname(r) == d and r != c["file"]]
                for rel in others:
                    self.find("docs-structure", rel, "-", "failed",
                              f"{d} admits only {c['file']}")

    def discover_tracked(self):
        """One git discovery observation, captured and reused: a second
        call could fail or race into a hybrid corpus snapshot."""
        r = self._git("ls-files", "--cached", "--others",
                      "--exclude-standard", "-z")
        if r.returncode != 0:
            self.find("execution", ".", "-", "execution_error",
                      f"git ls-files failed: {r.stderr.strip()[:120]}")
            self.tracked = None
            return
        self.tracked = [p for p in r.stdout.split("\0") if p]

    def classify_root_and_modules(self):
        mf = self.manifest
        if self.tracked is None:
            return
        lanes = {}
        for rel in self.tracked:
            full = os.path.join(self.repo, rel)
            is_md = rel.endswith(".md")
            if is_md and os.path.islink(full) \
                    and rel not in mf["alias_symlinks"]:
                self.find("docs-structure", rel, "-", "failed",
                          "symlinked markdown outside the alias list")
                continue
            if "/" not in rel and is_md:
                if rel in mf["managed_files"] or rel in mf["alias_symlinks"] \
                        or rel in mf["historical_files"]:
                    continue
                if any(fnmatch.fnmatch(rel, g) for g in mf["inflight_globs"]):
                    low = rel.lower()
                    if fnmatch.fnmatch(low, "*-review-r*.md"):
                        self.find("inflight-residency", rel, "-", "failed",
                                  "round-suffixed review filename")
                    m = re.fullmatch(
                        r"SHIFT-REPORT-\d{4}-\d{2}-\d{2}-([A-Za-z0-9]+)\.md",
                        rel)
                    lane = m.group(1) if m else ("unattributed"
                          if rel.startswith("SHIFT-REPORT-") else None)
                    if lane is not None:
                        lanes.setdefault(lane, []).append(rel)
                    continue
                self.find("docs-structure", rel, "-", "failed",
                          "root markdown matches no root class")
        for lane, rels in lanes.items():
            if len(rels) > 1:
                for rel in rels:
                    self.find("inflight-residency", rel, lane, "failed",
                              f"two shift reports for lane {lane}")

    def collect_managed(self):
        mf = self.manifest
        self.managed = list(self.docs_files)
        modules = []
        for rel in (self.tracked or []):
            if any(PurePath(rel).full_match(g) for g in mf["managed_globs"]):
                modules.append(rel)
        self.modules = sorted(set(modules))
        self.managed += self.modules
        self.root_contracts = [p for p in mf["managed_files"]
                               if self._exists(p)]
        self.managed += self.root_contracts
        # realpath confinement for every manifest-defined corpus path
        # before any read: managed, historical, and alias alike — a
        # symlinked intermediate directory can carry a lexically
        # repo-relative path outside the repository
        for rel in list(self.managed):
            if not self._confined(rel):
                self.find("docs-structure", rel, "-", "failed",
                          "path escapes the repository via symlink")
                self.managed.remove(rel)
        for rel in mf["historical_files"] + mf["alias_symlinks"]:
            if self._stat_state(rel) not in ("absent", "error") \
                    and not self._confined(rel):
                self.find("docs-structure", rel, "-", "failed",
                          "path escapes the repository via symlink")

    # -- metadata ------------------------------------------------------------
    def check_metadata(self):
        for rel in self.managed:
            text = self._read(rel)
            if text is None:
                self.meta[rel] = None
                continue
            meta, errors = parse_doc_meta(text)
            self.meta[rel] = meta
            if meta is None:
                if rel in self.root_contracts:
                    if rel in self.index_rows:
                        self.find("metadata", rel, "-", "degraded",
                                  "root contract without doc-meta; index row "
                                  "is the temporary sidecar")
                    else:
                        self.find("metadata", rel, "-", "failed",
                                  "no doc-meta and no sidecar index row")
                else:
                    self.find("metadata", rel, "-", "failed",
                              "missing doc-meta block")
                continue
            for err in errors:
                self.find("metadata", rel, "-", "failed",
                          f"invalid_metadata: {err}")
            cls = self.docs_files.get(rel)
            fixed = None
            if cls:
                spec = next(c for c in self.manifest["docs_classes"]
                            if c["name"] == cls)
                fixed = spec.get("role")
            elif rel in self.modules:
                fixed = "contract"
            if fixed and meta.get("role") and meta["role"] != fixed:
                self.find("docs-structure", rel, "role", "failed",
                          f"class fixes role {fixed}, doc-meta says "
                          f"{meta['role']}")
            for k in ("review-when", "expires-when"):
                if k in meta:
                    self.find("metadata", rel, k, "info",
                              f"{k}: {meta[k]} (human trigger, not evaluated)")

    # -- corpus index ---------------------------------------------------------
    def check_corpus_index(self):
        rel = "docs/README.md"
        listed = {}
        if not self._exists(rel):
            for path in self.managed:
                if path != rel:
                    self.find("index-symmetry", path, "-", "failed",
                              "corpus index docs/README.md absent")
            return
        index_text = self._read(rel)
        if index_text is None:
            return
        rows = parse_table_rows(index_text)
        mf = self.manifest
        historical = set(mf["historical_files"])
        aliases = set(mf["alias_symlinks"])
        headers = (["path", "claim", "role", "lifecycle", "superseded-by"],
                   ["path", "claim", "role", "lifecycle", "superseded-by",
                    "source_blob", "current_homes"],
                   ["path", "alias-of"])
        for cells in rows:
            if not cells or cells in headers:
                continue
            path = cells[0]
            if path in listed:
                self.find("index-symmetry", rel, path, "failed",
                          "duplicate path row")
                continue
            listed[path] = cells
        repo_rel = repo_relative

        for path, cells in listed.items():
            # rows are dispatched by the path's declared identity, never by
            # cell count alone
            if path in aliases:
                if len(cells) != 2 or not all(cells):
                    self.find("index-symmetry", rel, path, "failed",
                              "alias row needs | path | alias-of |")
                    continue
                target = cells[1]
                if not repo_rel(target) or target not in self.managed:
                    self.find("index-symmetry", rel, path, "failed",
                              f"alias target not a managed regular file: "
                              f"{target}")
                    continue
                tstate = self._stat_state(target)
                if tstate == "error":
                    continue  # observation unavailable, not wrong
                if tstate != "regular":
                    self.find("index-symmetry", rel, path, "failed",
                              f"alias target not a managed regular file: "
                              f"{target}")
                    continue
                afull = os.path.join(self.repo, path)
                astate = self._stat_state(path)
                if astate == "error":
                    continue
                if astate != "symlink":
                    self.find("index-symmetry", path, "-", "failed",
                              "declared alias is not a symlink on disk")
                    continue
                actual = os.path.normpath(os.path.join(
                    os.path.dirname(path), os.readlink(afull)))
                if actual != target:
                    self.find("index-symmetry", path, "-", "failed",
                              f"alias points at {actual}, row says {target}")
                    continue
                # lexical agreement is not resolution: the alias must
                # actually resolve, repo-confined, to the declared regular
                # file (missing/../AGENTS.md normalizes but dangles; the
                # resolved object must stay under the repo)
                try:
                    st = os.stat(afull)  # follows the link
                    resolves = stat.S_ISREG(st.st_mode)
                except (FileNotFoundError, NotADirectoryError):
                    resolves = False
                except (OSError, ValueError) as exc:
                    self.find("execution", path, "-", "execution_error",
                              f"alias unobservable: {exc}")
                    continue
                resolved = os.path.realpath(afull)
                if not resolves or resolved \
                        != os.path.realpath(os.path.join(self.repo, target)):
                    self.find("index-symmetry", path, "-", "failed",
                              "alias does not resolve to its declared target")
                    continue
                if not (resolved == self.repo
                        or resolved.startswith(self.repo + os.sep)):
                    self.find("index-symmetry", path, "-", "failed",
                              "alias resolves outside the repository")
                continue
            if path in historical:
                if len(cells) != 7:
                    self.find("index-symmetry", rel, path, "failed",
                              "historical row needs 7 cells incl. "
                              "source_blob, current_homes")
                    continue
                _, claim, role, lc, sup, blob, homes = cells
                bad = []
                if not claim:
                    bad.append("empty claim")
                if role not in ROLES:
                    bad.append(f"role {role}")
                if lc != "historical":
                    bad.append(f"historical row must say historical, not {lc}")
                if sup != "-":
                    bad.append("historical rows forbid superseded-by "
                               "(must be -)")
                if not HEX40_RE.fullmatch(blob):
                    bad.append("source_blob must be full 40-hex")
                if homes != "-" and not all(
                        repo_rel(h) for h in homes.split(",")):
                    bad.append(f"current_homes invalid: {homes}")
                for b in bad:
                    self.find("index-symmetry", rel, path, "failed",
                              f"historical row: {b}")
                continue
            if len(cells) != 5:
                self.find("index-symmetry", rel, path, "failed",
                          "managed row needs | path | claim | role | "
                          "lifecycle | superseded-by |")
                continue
            _, claim, role, lc, sup = cells
            if path not in self.managed:
                self.find("index-symmetry", rel, path, "failed",
                          "managed row for a file outside the managed corpus")
                continue
            bad = []
            if not claim:
                bad.append("empty claim")
            if role not in ROLES:
                bad.append(f"role {role} not in {ROLES}")
            if lc not in LIFECYCLES:
                bad.append(f"lifecycle {lc} not in vocabulary")
            if sup != "-" and not repo_rel(sup.partition("#")[0]):
                bad.append(f"superseded-by not repo-relative: {sup}")
            # row-level conditional coherence: the sidecar path must obey
            # the same lifecycle/field rules as doc-meta
            if lc in ("superseded", "partially-superseded"):
                if sup == "-":
                    bad.append(f"lifecycle {lc} requires a superseded-by "
                               "target")
            elif lc in LIFECYCLES and sup != "-":
                bad.append(f"superseded-by forbidden for lifecycle {lc}")
            for b in bad:
                self.find("index-symmetry", rel, path, "failed",
                          f"managed row: {b}")
            if not bad:
                self.index_rows[path] = {"claim": claim, "role": role,
                                         "lifecycle": lc,
                                         "superseded-by": sup}
        for path in self.managed:
            if path not in listed:
                self.find("index-symmetry", path, "-", "failed",
                          "orphan: on disk but not in the corpus index")
        for path in sorted(historical):
            if self._exists(path) and path not in listed:
                self.find("index-symmetry", path, "-", "failed",
                          "historical file without a sidecar row")
        for path in sorted(aliases):
            astate = self._stat_state(path)
            if astate == "error":
                continue  # unknown, never absence
            if path not in listed and astate != "absent":
                self.find("index-symmetry", path, "-", "failed",
                          "declared alias without an index row")
            if astate == "absent":
                self.find("index-symmetry", path, "-", "failed",
                          "declared alias absent on disk")
        for path in listed:
            if path in aliases:
                continue
            if self._stat_state(path) == "absent":
                self.find("index-symmetry", rel, path, "failed",
                          "ghost: listed but absent on disk")

    def check_corpus_index_agreement(self):
        for path, row in self.index_rows.items():
            meta = self.meta.get(path)
            if meta is None and row["lifecycle"] == "partially-superseded":
                # the five-cell row has no surviving-clauses cell, so a
                # metadata-less sidecar cannot substantiate this lifecycle;
                # it becomes legal once the in-file block exists
                self.find("index-symmetry", path, "lifecycle", "failed",
                          "sidecar rows cannot carry partially-superseded "
                          "(no surviving-clauses cell)")
                continue
            if meta:
                for key in ("role", "lifecycle"):
                    if meta.get(key) and row[key] != meta[key]:
                        self.find("index-symmetry", path, key, "failed",
                                  f"index says {row[key]}, doc-meta says "
                                  f"{meta[key]}")
                doc_sup = meta.get("superseded-by", "-")
                if (row["superseded-by"] or "-") != (doc_sup or "-"):
                    self.find("index-symmetry", path, "superseded-by",
                              "failed",
                              "index/header disagreement on superseded-by")

    def run(self):
        if self.load_manifest():
            self.classify_docs()
            self.discover_tracked()
            # both observations must succeed before any check whose
            # subject set depends on them: a missing set is inoperability,
            # never absence
            if self.tracked is not None and self.docs_observed:
                self.classify_root_and_modules()
                self.collect_managed()
                self.check_corpus_index()
                self.check_metadata()
                self.check_corpus_index_agreement()
        order = {"info": 0, "degraded": 1, "failed": 2, "execution_error": 3}
        worst = max((order[f["result"]] for f in self.findings), default=0)
        aggregate = ["clean", "degraded", "failed", "execution_error"][worst]
        counts = {}
        for f in self.findings:
            counts[f["result"]] = counts.get(f["result"], 0) + 1
        return {"aggregate": aggregate, "counts": counts,
                "findings": self.findings}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    doctor = Doctor(args.repo)
    report = doctor.run()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for f in report["findings"]:
            loc = f["locator"]
            if not isinstance(loc, str):
                loc = json.dumps(loc, sort_keys=True)
            print(f"{f['result']:16} {f['check']:20} {f['path']} "
                  f"[{loc}] {f['reason']}")
        print(f"aggregate: {report['aggregate']} "
              f"(degraded is never called clean)")
    agg = report["aggregate"]
    return {"clean": 0, "degraded": 0, "failed": 1, "execution_error": 2}[agg]


if __name__ == "__main__":
    sys.exit(main())
