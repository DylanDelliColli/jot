#!/usr/bin/env python3
"""Broken-corpus fixture suite for tools/docs_doctor.py.

Run from the repo root: python3 tools/test_docs_doctor.py

Builds one hermetic baseline corpus in a temp git repo (which must run
clean), then applies one mutation per case and asserts finding kind,
aggregate, and exit mapping.

The fixture MEMBERSHIP is defined HERE, not copied from this repository's
docs-corpus.json: a suite that borrowed the host's membership would drift
with it and would leave the features this repository happens not to use —
module globs, historical files, standing documents — untested. The CLASSES
come from the shipped library, because after the class-library split the
grammar is part of the product rather than part of a consumer, and the
fixture should exercise what actually ships.

Scope note: this suite covers the four checks jot carries (docs-structure,
metadata, index-symmetry, inflight-residency) and the manifest gate,
discovery, and path-confinement machinery they need. Cases for the seven
deferred checks stayed with them in the frozen abacus-v1 tree; see
tools/docs_doctor.py for what was deferred and why.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import docs_doctor  # noqa: E402
from tools.docs_doctor import Doctor  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXIT = {"clean": 0, "degraded": 0, "failed": 1, "execution_error": 2}
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append({"case": name, "pass": bool(ok), "detail": str(detail)[:200]})


def sh(cwd, *args):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{args}: {r.stderr}")
    return r.stdout.strip()


def blob_id(data):
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def meta_block(meta):
    lines = ["```doc-meta"]
    for k, v in meta.items():
        lines.append(f"{k}: {v}")
    lines.append("```")
    return "\n".join(lines)


def write(root, rel, text):
    full = os.path.join(root, rel)
    os.makedirs(os.path.dirname(full) or root, exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


def append(root, rel, text):
    with open(os.path.join(root, rel), "a", encoding="utf-8") as fh:
        fh.write(text)


def replace(root, rel, old, new):
    """Substitute inside a fixture file, failing loudly when the anchor has
    drifted — a silent no-op would make the case assert nothing."""
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if old not in text:
        raise RuntimeError(f"anchor not found in {rel}: {old!r}")
    write(root, rel, text.replace(old, new, 1))


# ---------------------------------------------------------------- baseline --
FIXTURE_MEMBERSHIP = {
    "conforms_to": docs_doctor.CLASS_LIBRARY_VERSION,
    "classes": ["prd", "adr", "evidence", "evidence-index", "corpus-index",
                "architecture", "archive-index", "standing"],
    "standing_files": ["docs/migration.md", "docs/notes.md"],
    "managed_globs": ["mod-*/README.md"],
    "managed_files": ["AGENTS.md", "CONTEXT.md", "README.md"],
    "alias_symlinks": ["CLAUDE.md"],
    "historical_files": ["NOTES.md"],
    "inflight_globs": ["PROPOSAL-*.md", "SHIFT-REPORT-*.md"],
    "protected_mainline_ref": "refs/heads/main",
}

CORPUS = {
    "docs/adr/0001-first-decision.md":
        dict(role="contract", lifecycle="active",
             body="# Decision\n\nFirst decision.\n"),
    "docs/adr/0002-second-decision.md":
        dict(role="contract", lifecycle="active",
             body="# Second\n\nAnother decision.\n"),
    "docs/compatibility/2026-01-02-sample-record.md":
        dict(role="evidence", lifecycle="active",
             body="# Record\n\nObserved things.\n"),
    "docs/compatibility/README.md":
        dict(role="working", lifecycle="active",
             body="# Records\n\n- [`2026-01-02-sample-record.md`]"
                  "(2026-01-02-sample-record.md)\n"),
    "docs/architecture.md":
        dict(role="contract", lifecycle="active",
             body="# Architecture\n\nCurrent topology.\n"),
    "docs/migration.md":
        dict(role="working", lifecycle="active", body="# Migration\n\nPlan.\n"),
    "docs/notes.md":
        dict(role="working", lifecycle="active", body="# Notes\n"),
    "docs/README.md":
        dict(role="working", lifecycle="active", body=None),  # generated
    "docs/history/README.md":
        dict(role="working", lifecycle="active",
             body="# Archive pointer index\n\nNo retired records yet.\n"),
    "mod-core/README.md":
        dict(role="contract", lifecycle="active", body="# Core\n\nSeam.\n"),
    "AGENTS.md": dict(role="contract", lifecycle="active", body="# Agents\n"),
    "CONTEXT.md": dict(role="contract", lifecycle="active",
                       body="# Context\n"),
    "README.md": dict(role="contract", lifecycle="active", body="# Readme\n"),
}

NOTES_BYTES = b"legacy notes residue\n"


def corpus_index_text(corpus, sup=None):
    sup = sup or {}
    rows = ["| path | claim | role | lifecycle | superseded-by |",
            "|---|---|---|---|---|"]
    for path, spec in sorted(corpus.items()):
        rows.append(f"| {path} | fixture doc | {spec['role']} | "
                    f"{spec['lifecycle']} | {sup.get(path, '-')} |")
    hist = ["", "| path | claim | role | lifecycle | superseded-by | "
            "source_blob | current_homes |",
            "|---|---|---|---|---|---|---|",
            f"| NOTES.md | legacy notes | working | historical | - | "
            f"{blob_id(NOTES_BYTES)} | - |"]
    alias = ["", "| path | alias-of |", "|---|---|",
             "| CLAUDE.md | AGENTS.md |"]
    return "\n".join(rows + hist + alias) + "\n"


def render(root, corpus, sup=None):
    """(Re)write every managed document plus the generated corpus index."""
    for path, spec in corpus.items():
        if path == "docs/README.md":
            body = "# Corpus index\n\n" + corpus_index_text(corpus, sup)
        else:
            body = spec["body"]
        meta = {"role": spec["role"], "lifecycle": spec["lifecycle"]}
        if sup and path in sup and sup[path] != "-":
            meta["superseded-by"] = sup[path]
        if spec.get("surviving"):
            meta["surviving-clauses"] = spec["surviving"]
        write(root, path, meta_block(meta) + "\n\n" + body)


def build_baseline(root):
    sh(root, "git", "init", "-q", "-b", "main")
    sh(root, "git", "config", "user.email", "fixture@example.com")
    sh(root, "git", "config", "user.name", "Fixture")
    os.makedirs(os.path.join(root, "fixture-bin"))
    render(root, CORPUS)
    with open(os.path.join(root, "NOTES.md"), "wb") as fh:
        fh.write(NOTES_BYTES)
    write(root, "docs-corpus.json", json.dumps(FIXTURE_MEMBERSHIP, indent=1))
    os.symlink("AGENTS.md", os.path.join(root, "CLAUDE.md"))
    write(root, "PROPOSAL-sample.md", "# Working proposal\n")
    write(root, "SHIFT-REPORT-2026-01-01-CLAUDE.md", "# Handoff\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-qm", "baseline corpus")
    write(root, "fixture-info.json",
          json.dumps({"head": sh(root, "git", "rev-parse", "HEAD")}))


def run_doctor(root):
    doctor = Doctor(root)
    report = doctor.run()
    report["exit"] = EXIT[report["aggregate"]]
    return report


def expect(name, report, aggregate, *needles, absent=(), counts=None):
    """Assert aggregate, exit mapping, needle presence/absence, and — where
    given — the exact occurrence count of a needle."""
    ok = report["aggregate"] == aggregate and report["exit"] == EXIT[aggregate]
    blob = json.dumps(report["findings"])
    missing = [n for n in needles if n not in blob]
    present = [n for n in absent if n in blob]
    badcount = {n: (blob.count(n), want) for n, want in (counts or {}).items()
                if blob.count(n) != want}
    if missing or present or badcount or not ok:
        check(name, False,
              f"aggregate={report['aggregate']} missing={missing} "
              f"unexpected={present} badcount={badcount} "
              f"findings={blob[:600]}")
    else:
        check(name, True)


def expect_findings(name, report, aggregate, specs, absent=()):
    """specs: (result, reason_substring, exact_count) tuples, or dicts
    binding the full contract tuple {result, reason, count, check?, path?}."""
    ok = report["aggregate"] == aggregate and report["exit"] == EXIT[aggregate]
    problems = []
    if not ok:
        problems.append(f"aggregate={report['aggregate']}")
    for spec in specs:
        if not isinstance(spec, dict):
            spec = {"result": spec[0], "reason": spec[1], "count": spec[2]}

        def match(f, spec=spec):
            if f["result"] != spec["result"]:
                return False
            if spec.get("reason", "") not in f["reason"]:
                return False
            if spec.get("check") is not None and f["check"] != spec["check"]:
                return False
            if spec.get("path") is not None and f["path"] != spec["path"]:
                return False
            return True

        got = sum(1 for f in report["findings"] if match(f))
        if got != spec["count"]:
            problems.append(f"{spec} got {got}")
    blob = json.dumps(report["findings"])
    problems += [f"unexpected {n!r}" for n in absent if n in blob]
    check(name, not problems, "; ".join(str(p) for p in problems)
          + " | " + blob[:400] if problems else "")


# ---------------------------------------------------------------- helpers --
def mutate_manifest(root, fn):
    path = os.path.join(root, "docs-corpus.json")
    with open(path, encoding="utf-8") as fh:
        mf = json.load(fh)
    fn(mf)
    write(root, "docs-corpus.json", json.dumps(mf))


def with_library(fn):
    """Run the doctor against a mutated copy of the SHIPPED class library.

    The library is code, not a per-repo file, so the only way to author a
    bad one is to edit the constant. These cases prove the composed-manifest
    validator still fails closed on a library the tool ships itself — the
    failure mode the old per-repo frozen-literal check used to cover."""
    original = docs_doctor.CLASS_LIBRARY
    mutated = json.loads(json.dumps(original))
    fn(mutated)

    def run(root):
        docs_doctor.CLASS_LIBRARY = mutated
        try:
            return run_doctor(root)
        finally:
            docs_doctor.CLASS_LIBRARY = original
    return run


def library_class(lib, name):
    return next(c for c in lib["classes"] if c["name"] == name)


def rewrite(root, sup=None, corpus_mut=None):
    corpus = {k: dict(v) for k, v in CORPUS.items()}
    if corpus_mut:
        corpus_mut(corpus)
    render(root, corpus, sup)


def stub_git(root, script_body):
    """A git shim on PATH that delegates everything it does not intercept."""
    real_git = shutil.which("git")
    write(root, "fixture-bin/git",
          "#!/bin/sh\n" + script_body + f'exec {real_git} "$@"\n')
    os.chmod(os.path.join(root, "fixture-bin/git"), 0o755)


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


# ------------------------------------------------------------- structure --
@case("baseline_clean")
def _(root):
    expect("baseline_clean", run_doctor(root), "clean")


@case("misnamed_docs_file")
def _(root):
    write(root, "docs/adr/BADNAME.md", meta_block(
        {"role": "contract", "lifecycle": "active"}) + "\n# X\n")
    expect("misnamed_docs_file", run_doctor(root), "failed",
           "matches no class")


@case("unknown_subdirectory")
def _(root):
    write(root, "docs/plans/plan.md", "# plan\n")
    expect("unknown_subdirectory", run_doctor(root), "failed",
           "unknown subdirectory under docs/")


@case("empty_unknown_docs_directory")
def _(root):
    os.makedirs(os.path.join(root, "docs/unrecognized"))
    expect("empty_unknown_docs_directory", run_doctor(root), "failed",
           "unknown subdirectory under docs/")


@case("non_markdown_residue")
def _(root):
    write(root, "docs/residue.txt", "junk\n")
    expect("non_markdown_residue", run_doctor(root), "failed",
           "matches no class")


@case("ignored_docs_path_still_seen")
def _(root):
    write(root, ".gitignore", "docs/tmp-*.md\n")
    write(root, "docs/tmp-scratch.md", "# scratch\n")
    expect("ignored_docs_path_still_seen", run_doctor(root), "failed",
           "matches no class")


@case("symlink_under_docs")
def _(root):
    os.symlink("../AGENTS.md", os.path.join(root, "docs/link.md"))
    expect("symlink_under_docs", run_doctor(root), "failed",
           "symlink under docs/")


@case("symlinked_subdirectory_under_docs")
def _(root):
    os.makedirs(os.path.join(root, "elsewhere"))
    os.symlink("../elsewhere", os.path.join(root, "docs/aliased"))
    expect("symlinked_subdirectory_under_docs", run_doctor(root), "failed",
           "symlink under docs/")


@case("duplicate_adr_number")
def _(root):
    write(root, "docs/adr/0001-duplicate.md", meta_block(
        {"role": "contract", "lifecycle": "active"}) + "\n# Dup\n")
    expect("duplicate_adr_number", run_doctor(root), "failed",
           "duplicate number 0001 in class adr")


@case("prd_valid_clean")
def _(root):
    def mut(corpus):
        corpus["docs/prd/0001-first-product.md"] = dict(
            role="contract", lifecycle="active", body="# Product\n")
    rewrite(root, corpus_mut=mut)
    expect("prd_valid_clean", run_doctor(root), "clean")


@case("prd_duplicate_number")
def _(root):
    def mut(corpus):
        corpus["docs/prd/0001-first-product.md"] = dict(
            role="contract", lifecycle="active", body="# Product\n")
        corpus["docs/prd/0001-second-product.md"] = dict(
            role="contract", lifecycle="active", body="# Product two\n")
    rewrite(root, corpus_mut=mut)
    expect("prd_duplicate_number", run_doctor(root), "failed",
           "duplicate number 0001 in class prd")


@case("invalid_calendar_date")
def _(root):
    write(root, "docs/compatibility/2026-99-99-impossible.md", meta_block(
        {"role": "evidence", "lifecycle": "active"}) + "\n# X\n")
    expect("invalid_calendar_date", run_doctor(root), "failed",
           "invalid calendar date")


@case("uppercase_slug")
def _(root):
    write(root, "docs/adr/0003-BadSlug.md", "# x\n")
    expect("uppercase_slug", run_doctor(root), "failed", "matches no class")


@case("empty_slug_component")
def _(root):
    write(root, "docs/adr/0004-.md", "# x\n")
    expect("empty_slug_component", run_doctor(root), "failed",
           "matches no class")


@case("second_file_in_history_dir")
def _(root):
    write(root, "docs/history/extra.md", "# extra\n")
    expect("second_file_in_history_dir", run_doctor(root), "failed",
           "admits only docs/history/README.md")


@case("absent_standing_file_tolerated")
def _(root):
    def mut(corpus):
        del corpus["docs/notes.md"]
    rewrite(root, corpus_mut=mut)
    os.unlink(os.path.join(root, "docs/notes.md"))
    expect("absent_standing_file_tolerated", run_doctor(root), "clean")


@case("root_unmatched_markdown")
def _(root):
    write(root, "ROGUE.md", "# rogue\n")
    expect("root_unmatched_markdown", run_doctor(root), "failed",
           "root markdown matches no root class")


@case("root_symlink_outside_aliases")
def _(root):
    os.symlink("AGENTS.md", os.path.join(root, "LINKED.md"))
    expect("root_symlink_outside_aliases", run_doctor(root), "failed",
           "symlinked markdown outside the alias list")


@case("round_suffixed_review_file")
def _(root):
    write(root, "PROPOSAL-sample-review-r2.md", "# round\n")
    expect("round_suffixed_review_file", run_doctor(root), "failed",
           "round-suffixed review filename")


@case("duplicate_lane_reports")
def _(root):
    write(root, "SHIFT-REPORT-2026-01-02-CLAUDE.md", "# second\n")
    expect("duplicate_lane_reports", run_doctor(root), "failed",
           "two shift reports for lane CLAUDE")


@case("socket_under_docs_rejected")
def _(root):
    import socket as socketlib
    s = socketlib.socket(socketlib.AF_UNIX)
    try:
        s.bind(os.path.join(root, "docs/adr/0003-socket.md"))
    except OSError as exc:
        check("socket_under_docs_rejected", False, f"bind failed: {exc}")
        return
    try:
        expect("socket_under_docs_rejected", run_doctor(root), "failed",
               "not a regular file")
    finally:
        s.close()


@case("unreadable_docs_directory")
def _(root):
    adr = os.path.join(root, "docs/adr")
    os.chmod(adr, 0)
    try:
        r = run_doctor(root)
    finally:
        os.chmod(adr, 0o755)
    blob = json.dumps(r["findings"])
    check("unreadable_docs_directory",
          r["aggregate"] == "execution_error" and r["exit"] == 2
          and "docs walk failed" in blob
          and "ghost" not in blob and "orphan" not in blob
          and "outside the managed corpus" not in blob,
          f"aggregate={r['aggregate']} {blob[:300]}")


@case("symlinked_dir_escape_fails")
def _(root):
    outside = os.path.join(os.path.dirname(root),
                           root.split(os.sep)[-1] + "-outside")
    os.makedirs(outside, exist_ok=True)
    write(outside, "OUT.md", meta_block(
        {"role": "contract", "lifecycle": "active"}) + "\n# Out\n")
    os.symlink(outside, os.path.join(root, "escape"))
    mutate_manifest(root, lambda mf: mf.update(
        managed_files=mf["managed_files"] + ["escape/OUT.md"]))
    expect_findings("symlinked_dir_escape_fails", run_doctor(root), "failed",
                    [("failed", "escapes the repository via symlink", 1)])


@case("escaping_historical_path")
def _(root):
    outside = os.path.join(os.path.dirname(root),
                           root.split(os.sep)[-1] + "-hist-outside")
    os.makedirs(outside, exist_ok=True)
    data = b"external historical bytes\n"
    with open(os.path.join(outside, "OUT.md"), "wb") as fh:
        fh.write(data)
    os.symlink(outside, os.path.join(root, "hist-escape"))
    mutate_manifest(root, lambda mf: mf.update(
        historical_files=mf["historical_files"] + ["hist-escape/OUT.md"]))
    append(root, "docs/README.md",
           f"| hist-escape/OUT.md | external | working | historical | - "
           f"| {blob_id(data)} | - |\n")
    expect_findings("escaping_historical_path", run_doctor(root), "failed",
                    [("failed", "escapes the repository via symlink", 1)])


@case("module_dir_unreadable_not_absent")
def _(root):
    mod = os.path.join(root, "mod-core")
    os.chmod(mod, 0)
    try:
        r = run_doctor(root)
    finally:
        os.chmod(mod, 0o755)
    blob = json.dumps(r["findings"])
    unobs = sum(1 for f in r["findings"]
                if f["result"] == "execution_error"
                and "mod-core/README.md" in f["path"])
    check("module_dir_unreadable_not_absent",
          r["aggregate"] == "execution_error" and r["exit"] == 2
          # exactly one observation error per path, and no absence- or
          # type-derived conclusion drawn from an unobservable path
          and unobs == 1
          and "ghost" not in blob and "orphan" not in blob,
          f"aggregate={r['aggregate']} unobs={unobs} {blob[:300]}")


@case("real_corpus_paths_classify")
def _(root):
    """This repository's shipped manifest must still classify this
    repository's own layout: real manifest, real paths, stub bytes."""
    shape = os.path.join(os.path.dirname(root),
                         root.split(os.sep)[-1] + "-shape")
    os.makedirs(shape)
    sh(shape, "git", "init", "-q", "-b", "main")
    sh(shape, "git", "config", "user.email", "f@example.com")
    sh(shape, "git", "config", "user.name", "F")
    shutil.copy(os.path.join(REPO_ROOT, "docs-corpus.json"),
                os.path.join(shape, "docs-corpus.json"))
    with open(os.path.join(shape, "docs-corpus.json"), encoding="utf-8") as fh:
        mf = json.load(fh)
    real = []
    for base, _dirs, files in os.walk(os.path.join(REPO_ROOT, "docs")):
        real += [os.path.relpath(os.path.join(base, n), REPO_ROOT)
                 for n in files]
    real += mf["managed_files"]
    for path in sorted(set(real)):
        write(shape, path, "# stub\n")
    for alias in mf["alias_symlinks"]:
        os.symlink(os.path.basename(mf["managed_files"][0]),
                   os.path.join(shape, alias))
    sh(shape, "git", "add", "-A")
    sh(shape, "git", "commit", "-qm", "real shape")
    report = run_doctor(shape)
    structure = [f for f in report["findings"]
                 if f["check"] in ("docs-structure", "execution")]
    check("real_corpus_paths_classify", not structure,
          json.dumps(structure)[:400])


# -------------------------------------------------------------- discovery --
@case("first_ls_files_failure_no_hybrid")
def _(root):
    stub_git(root, 'if [ "$1" = "ls-files" ]; then\n'
                   "  echo forced-ls-files-failure >&2\n  exit 70\nfi\n")
    expect_findings("first_ls_files_failure_no_hybrid", run_doctor(root),
                    "execution_error",
                    [("execution_error", "git ls-files failed", 1)],
                    absent=("outside the managed corpus", "ghost", "orphan"))


@case("second_ls_files_failure")
def _(root):
    counter = os.path.join(root, "fixture-bin", "lsfiles-count")
    stub_git(root,
             'case " $* " in *" --others "*)\n'
             f"  n=$(cat {counter} 2>/dev/null || echo 0)\n"
             f"  echo $((n+1)) > {counter}\n"
             '  if [ "$n" -ge 1 ]; then\n'
             "    echo forced-second-ls-files-failure >&2\n    exit 70\n"
             "  fi\n"
             ";; esac\n")
    r = run_doctor(root)
    calls = open(counter).read().strip() if os.path.exists(counter) else "0"
    blob = json.dumps(r["findings"])
    # one discovery observation, captured and reused: a second call could
    # race into a hybrid corpus snapshot
    check("second_ls_files_failure",
          calls == "1" and r["aggregate"] == "clean"
          and "outside the managed corpus" not in blob,
          f"calls={calls} aggregate={r['aggregate']} {blob[:300]}")


@case("missing_git_is_execution_error")
def _(root):
    old = os.environ["PATH"]
    os.environ["PATH"] = os.path.join(root, "fixture-bin")
    try:
        r = run_doctor(root)
    finally:
        os.environ["PATH"] = old
    check("missing_git_is_execution_error",
          r["aggregate"] == "execution_error" and r["exit"] == 2,
          f"aggregate={r['aggregate']} {json.dumps(r['findings'])[:300]}")


@case("unreadable_managed_file")
def _(root):
    os.chmod(os.path.join(root, "docs/migration.md"), 0)
    try:
        r = run_doctor(root)
    finally:
        os.chmod(os.path.join(root, "docs/migration.md"), 0o644)
    check("unreadable_managed_file",
          r["aggregate"] == "execution_error" and r["exit"] == 2
          and any("unreadable managed file" in f["reason"]
                  for f in r["findings"]),
          f"aggregate={r['aggregate']}")


# --------------------------------------------------------------- metadata --
@case("missing_metadata_docs_file")
def _(root):
    write(root, "docs/migration.md", "# Migration\n\nno meta\n")
    expect("missing_metadata_docs_file", run_doctor(root), "failed",
           "missing doc-meta block")


@case("root_contract_sidecar_degraded")
def _(root):
    write(root, "AGENTS.md", "# Agents\n\nno meta yet\n")
    expect("root_contract_sidecar_degraded", run_doctor(root), "degraded",
           "temporary sidecar")


@case("root_contract_without_sidecar_fails")
def _(root):
    write(root, "AGENTS.md", "# Agents\n\nno meta yet\n")
    replace(root, "docs/README.md",
            "| AGENTS.md | fixture doc | contract | active | - |\n", "")
    expect("root_contract_without_sidecar_fails", run_doctor(root), "failed",
           "no doc-meta and no sidecar index row")


@case("unknown_metadata_key")
def _(root):
    write(root, "docs/migration.md", meta_block(
        {"role": "working", "lifecycle": "active", "banana": "yes"})
        + "\n# Migration\n")
    expect("unknown_metadata_key", run_doctor(root), "failed",
           "unknown key: banana")


@case("empty_metadata_value")
def _(root):
    write(root, "docs/migration.md",
          "```doc-meta\nrole:\nlifecycle: active\n```\n# Migration\n")
    expect("empty_metadata_value", run_doctor(root), "failed",
           "empty value: role")


@case("duplicate_metadata_key")
def _(root):
    write(root, "docs/migration.md",
          "```doc-meta\nrole: working\nrole: working\nlifecycle: active\n"
          "```\n# Migration\n")
    expect_findings("duplicate_metadata_key", run_doctor(root), "failed",
                    [("failed", "duplicate key: role", 1)])


@case("unparseable_metadata_line")
def _(root):
    write(root, "docs/migration.md",
          "```doc-meta\nrole: working\nlifecycle: active\nnonsense\n"
          "```\n# Migration\n")
    expect("unparseable_metadata_line", run_doctor(root), "failed",
           "unparseable line: nonsense")


@case("missing_required_metadata_key")
def _(root):
    write(root, "docs/migration.md",
          "```doc-meta\nrole: working\n```\n# Migration\n")
    expect("missing_required_metadata_key", run_doctor(root), "failed",
           "missing key: lifecycle")


@case("invalid_metadata_vocabulary")
def _(root):
    write(root, "docs/migration.md",
          "```doc-meta\nrole: banana\nlifecycle: someday\n```\n# Migration\n")
    expect("invalid_metadata_vocabulary", run_doctor(root), "failed",
           "invalid role: banana", "invalid lifecycle: someday")


@case("unterminated_doc_meta_block")
def _(root):
    write(root, "docs/migration.md",
          "```doc-meta\nrole: working\nlifecycle: active\n")
    expect("unterminated_doc_meta_block", run_doctor(root), "failed",
           "unterminated doc-meta block")


@case("superseded_without_target")
def _(root):
    write(root, "docs/migration.md", meta_block(
        {"role": "working", "lifecycle": "superseded"}) + "\n# Migration\n")
    expect("superseded_without_target", run_doctor(root), "failed",
           "superseded requires superseded-by")


@case("forbidden_supersession_fields")
def _(root):
    write(root, "docs/migration.md", meta_block(
        {"role": "working", "lifecycle": "active",
         "superseded-by": "docs/architecture.md"}) + "\n# Migration\n")
    expect("forbidden_supersession_fields", run_doctor(root), "failed",
           "superseded-by forbidden for lifecycle active")


@case("surviving_clauses_on_full_supersession")
def _(root):
    write(root, "docs/adr/0002-second-decision.md",
          "```doc-meta\nrole: contract\nlifecycle: superseded\n"
          "superseded-by: docs/adr/0001-first-decision.md\n"
          "surviving-clauses: none really\n```\n# Second\n")
    expect("surviving_clauses_on_full_supersession", run_doctor(root),
           "failed", "surviving-clauses forbidden for lifecycle superseded")


@case("class_role_mismatch")
def _(root):
    def mut(corpus):
        corpus["docs/adr/0001-first-decision.md"]["role"] = "working"
    rewrite(root, corpus_mut=mut)
    expect("class_role_mismatch", run_doctor(root), "failed",
           "class fixes role contract, doc-meta says working")


@case("module_role_mismatch")
def _(root):
    def mut(corpus):
        corpus["mod-core/README.md"]["role"] = "working"
    rewrite(root, corpus_mut=mut)
    expect("module_role_mismatch", run_doctor(root), "failed",
           "class fixes role contract, doc-meta says working")


@case("human_trigger_key_is_info_only")
def _(root):
    write(root, "docs/migration.md", meta_block(
        {"role": "working", "lifecycle": "active",
         "review-when": "the port lands"}) + "\n# Migration\n")
    expect("human_trigger_key_is_info_only", run_doctor(root), "clean",
           "human trigger, not evaluated")


# ------------------------------------------------------------------ index --
@case("orphan_unlisted_doc")
def _(root):
    write(root, "docs/adr/0005-unlisted.md", meta_block(
        {"role": "contract", "lifecycle": "active"}) + "\n# New\n")
    expect("orphan_unlisted_doc", run_doctor(root), "failed", "orphan")


@case("ghost_listed_absent")
def _(root):
    append(root, "docs/README.md",
           "| docs/adr/0009-ghost.md | gone | contract | active | - |\n")
    expect("ghost_listed_absent", run_doctor(root), "failed", "ghost")


@case("absent_corpus_index_fails")
def _(root):
    os.unlink(os.path.join(root, "docs/README.md"))
    expect("absent_corpus_index_fails", run_doctor(root), "failed",
           "corpus index docs/README.md absent")


@case("duplicate_index_rows")
def _(root):
    append(root, "docs/README.md",
           "| docs/migration.md | again | working | active | - |\n")
    expect("duplicate_index_rows", run_doctor(root), "failed",
           "duplicate path row")


@case("corpus_blank_claim_cell")
def _(root):
    replace(root, "docs/README.md",
            "| docs/architecture.md | fixture doc |",
            "| docs/architecture.md |  |")
    expect("corpus_blank_claim_cell", run_doctor(root), "failed",
           "managed row: empty claim")


@case("corpus_row_bad_vocabulary")
def _(root):
    replace(root, "docs/README.md",
            "| docs/notes.md | fixture doc | working | active | - |",
            "| docs/notes.md | fixture doc | scribe | someday | - |")
    expect("corpus_row_bad_vocabulary", run_doctor(root), "failed",
           "role scribe not in", "lifecycle someday not in vocabulary")


@case("managed_row_wrong_cell_count")
def _(root):
    replace(root, "docs/README.md",
            "| docs/notes.md | fixture doc | working | active | - |",
            "| docs/notes.md | fixture doc | working |")
    expect_findings("managed_row_wrong_cell_count", run_doctor(root), "failed",
                    [("failed", "managed row needs", 1)])


@case("unmanaged_index_row")
def _(root):
    write(root, "UNMANAGED.txt", "not a corpus file\n")
    append(root, "docs/README.md",
           "| UNMANAGED.txt | rogue | working | active | - |\n")
    expect("unmanaged_index_row", run_doctor(root), "failed",
           "outside the managed corpus")


@case("index_header_disagreement")
def _(root):
    replace(root, "docs/migration.md", "lifecycle: active",
            "lifecycle: parked")
    expect("index_header_disagreement", run_doctor(root), "failed",
           "index says active, doc-meta says parked")


@case("index_superseded_by_disagreement")
def _(root):
    def mut(corpus):
        corpus["docs/adr/0002-second-decision.md"]["lifecycle"] = "superseded"
    rewrite(root, sup={"docs/adr/0002-second-decision.md":
                       "docs/adr/0001-first-decision.md"}, corpus_mut=mut)
    replace(root, "docs/README.md",
            "| docs/adr/0002-second-decision.md | fixture doc | contract "
            "| superseded | docs/adr/0001-first-decision.md |",
            "| docs/adr/0002-second-decision.md | fixture doc | contract "
            "| superseded | docs/adr/0001-first-decision.md#Decision |")
    expect("index_superseded_by_disagreement", run_doctor(root), "failed",
           "index/header disagreement on superseded-by")


@case("sidecar_conditional_lifecycle_invalid")
def _(root):
    write(root, "AGENTS.md", "# Agents\n\nno meta\n")
    replace(root, "docs/README.md",
            "| AGENTS.md | fixture doc | contract | active | - |",
            "| AGENTS.md | fixture doc | contract | superseded | - |")
    expect("sidecar_conditional_lifecycle_invalid", run_doctor(root),
           "failed", "requires a superseded-by target")


@case("sidecar_partial_supersession_rejected")
def _(root):
    write(root, "AGENTS.md", "# Agents\n\nno meta\n")
    replace(root, "docs/README.md",
            "| AGENTS.md | fixture doc | contract | active | - |",
            "| AGENTS.md | fixture doc | contract | partially-superseded "
            "| docs/architecture.md |")
    expect("sidecar_partial_supersession_rejected", run_doctor(root),
           "failed", "sidecar rows cannot carry partially-superseded")


@case("historical_row_wrong_lifecycle")
def _(root):
    replace(root, "docs/README.md",
            "| NOTES.md | legacy notes | working | historical |",
            "| NOTES.md | legacy notes | working | active |")
    expect("historical_row_wrong_lifecycle", run_doctor(root), "failed",
           "historical row must say historical")


@case("historical_row_nondash_superseded")
def _(root):
    replace(root, "docs/README.md",
            "| NOTES.md | legacy notes | working | historical | - |",
            "| NOTES.md | legacy notes | working | historical "
            "| docs/migration.md |")
    expect("historical_row_nondash_superseded", run_doctor(root), "failed",
           "historical rows forbid superseded-by")


@case("historical_row_short_blob")
def _(root):
    replace(root, "docs/README.md", blob_id(NOTES_BYTES),
            blob_id(NOTES_BYTES)[:12])
    expect("historical_row_short_blob", run_doctor(root), "failed",
           "source_blob must be full 40-hex")


@case("historical_row_bad_current_homes")
def _(root):
    replace(root, "docs/README.md", f"{blob_id(NOTES_BYTES)} | - |",
            f"{blob_id(NOTES_BYTES)} | /absolute,,bad |")
    expect("historical_row_bad_current_homes", run_doctor(root), "failed",
           "current_homes invalid")


@case("historical_file_without_row")
def _(root):
    replace(root, "docs/README.md",
            f"| NOTES.md | legacy notes | working | historical | - "
            f"| {blob_id(NOTES_BYTES)} | - |\n", "")
    expect("historical_file_without_row", run_doctor(root), "failed",
           "historical file without a sidecar row")


@case("alias_target_invalid")
def _(root):
    replace(root, "docs/README.md", "| CLAUDE.md | AGENTS.md |",
            "| CLAUDE.md | NOPE.md |")
    expect("alias_target_invalid", run_doctor(root), "failed",
           "alias target not a managed regular file")


@case("alias_row_deleted")
def _(root):
    replace(root, "docs/README.md", "| CLAUDE.md | AGENTS.md |\n", "")
    expect("alias_row_deleted", run_doctor(root), "failed",
           "declared alias without an index row")


@case("alias_file_deleted")
def _(root):
    os.unlink(os.path.join(root, "CLAUDE.md"))
    expect("alias_file_deleted", run_doctor(root), "failed",
           "declared alias absent on disk")


@case("alias_regular_file")
def _(root):
    os.unlink(os.path.join(root, "CLAUDE.md"))
    write(root, "CLAUDE.md", "# not a symlink\n")
    expect("alias_regular_file", run_doctor(root), "failed",
           "declared alias is not a symlink on disk")


@case("alias_retargeted")
def _(root):
    os.unlink(os.path.join(root, "CLAUDE.md"))
    os.symlink("CONTEXT.md", os.path.join(root, "CLAUDE.md"))
    expect("alias_retargeted", run_doctor(root), "failed",
           "alias points at CONTEXT.md, row says AGENTS.md")


@case("alias_dangling_but_lexically_normal")
def _(root):
    os.unlink(os.path.join(root, "CLAUDE.md"))
    os.symlink("missing/../AGENTS.md", os.path.join(root, "CLAUDE.md"))
    expect("alias_dangling_but_lexically_normal", run_doctor(root), "failed",
           "alias does not resolve to its declared target")


@case("alias_indirect_but_resolving_clean")
def _(root):
    os.makedirs(os.path.join(root, "via"))
    os.unlink(os.path.join(root, "CLAUDE.md"))
    os.symlink("via/../AGENTS.md", os.path.join(root, "CLAUDE.md"))
    expect("alias_indirect_but_resolving_clean", run_doctor(root), "clean")


@case("alias_parent_unreadable_not_absent")
def _(root):
    os.makedirs(os.path.join(root, "blocked"))
    os.symlink("../AGENTS.md", os.path.join(root, "blocked/CLAUDE.md"))
    mutate_manifest(root, lambda mf: mf.update(
        alias_symlinks=mf["alias_symlinks"] + ["blocked/CLAUDE.md"]))
    append(root, "docs/README.md", "| blocked/CLAUDE.md | AGENTS.md |\n")
    os.chmod(os.path.join(root, "blocked"), 0)
    try:
        r = run_doctor(root)
    finally:
        os.chmod(os.path.join(root, "blocked"), 0o755)
    blob = json.dumps(r["findings"])
    check("alias_parent_unreadable_not_absent",
          any(f["result"] == "execution_error" for f in r["findings"])
          and "declared alias is not a symlink" not in blob
          and "declared alias absent on disk" not in blob,
          f"aggregate={r['aggregate']} {blob[:300]}")


# --------------------------------------------------------- fence contract --
@case("fenced_table_row_inert")
def _(root):
    append(root, "docs/README.md",
           "\n```text\n"
           "| docs/adr/0009-ghost.md | example | contract | active | - |\n"
           "```\n")
    expect("fenced_table_row_inert", run_doctor(root), "clean")


@case("backtick_info_string_not_a_fence")
def _(root):
    # a backtick opener whose info string contains a backtick is ordinary
    # content, so the row below it is a real index row
    append(root, "docs/README.md",
           "\n```not`a-valid-info-string\n"
           "| docs/adr/0009-ghost.md | example | contract | active | - |\n"
           "```\n")
    expect("backtick_info_string_not_a_fence", run_doctor(root), "failed",
           "ghost")


@case("tilde_info_string_is_a_fence")
def _(root):
    append(root, "docs/README.md",
           "\n~~~not`a-valid-info-string\n"
           "| docs/adr/0009-ghost.md | example | contract | active | - |\n"
           "~~~\n")
    expect("tilde_info_string_is_a_fence", run_doctor(root), "clean")


@case("nested_fence_content_inert")
def _(root):
    append(root, "docs/README.md",
           "\n````text\nexample only:\n```\n"
           "| docs/adr/0009-ghost.md | example | contract | active | - |\n"
           "```\n````\n")
    expect("nested_fence_content_inert", run_doctor(root), "clean")


# ------------------------------------------------------------------ manifest --
@case("manifest_missing_names_its_remedy")
def _(root):
    # the cold start is the first thing anyone adopting the tool sees; a
    # bare "manifest missing" is a dead end
    os.unlink(os.path.join(root, "docs-corpus.json"))
    expect("manifest_missing_names_its_remedy", run_doctor(root),
           "execution_error", "manifest missing", "--init", "--classes")


# ------------------------------------------------------------- cold start --
def fresh_repo(root, name, files, links=()):
    """A git repo with documents and NO manifest — an adoption candidate."""
    repo = os.path.join(root, name)
    os.makedirs(repo)
    sh(repo, "git", "init", "-q", "-b", "main")
    sh(repo, "git", "config", "user.email", "f@example.com")
    sh(repo, "git", "config", "user.name", "F")
    for rel, text in files.items():
        write(repo, rel, text)
    for link, target in links:
        os.symlink(target, os.path.join(repo, link))
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-qm", "documents, no manifest")
    return repo


def init(repo, force=False):
    """cmd_init with its operator-facing narration captured, not printed."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        rc = docs_doctor.cmd_init(repo, force)
    return rc, out.getvalue()


COLD_START = {"README.md": "# my project\n",
              "AGENTS.md": "# agent contract\n",
              "docs/adr/0001-pick-a-db.md": "# pick a db\n",
              "docs/architecture.md": "# how it fits together\n"}


@case("init_reaches_an_actionable_state")
def _(root):
    """Setup must end somewhere the author can act, not at another wall:
    after init the only findings left are per-document ones they own."""
    repo = fresh_repo(root, "cold", COLD_START, links=[("CLAUDE.md",
                                                        "AGENTS.md")])
    rc, _ = init(repo)
    r = run_doctor(repo)
    unactionable = [f for f in r["findings"]
                    if "doc-meta" not in f["reason"]]
    check("init_reaches_an_actionable_state",
          rc == 0 and not unactionable
          and any(f["reason"] == "missing doc-meta block"
                  for f in r["findings"]),
          f"rc={rc} unactionable={json.dumps(unactionable)[:300]}")


@case("init_output_survives_the_author_finishing_it")
def _(root):
    """The scaffold must not plant a failure that fires later. Adding the
    doc-meta blocks init asked for has to reach a passing run."""
    repo = fresh_repo(root, "finish", COLD_START, links=[("CLAUDE.md",
                                                          "AGENTS.md")])
    init(repo)
    for rel in ("docs/adr/0001-pick-a-db.md", "docs/architecture.md"):
        with open(os.path.join(repo, rel), encoding="utf-8") as fh:
            body = fh.read()
        write(repo, rel, meta_block({"role": "contract",
                                     "lifecycle": "active"}) + "\n\n" + body)
    r = run_doctor(repo)
    check("init_output_survives_the_author_finishing_it",
          r["exit"] == 0 and not [f for f in r["findings"]
                                  if f["result"] not in ("degraded", "info")],
          f"aggregate={r['aggregate']} {json.dumps(r['findings'])[:300]}")


@case("init_declares_only_present_classes")
def _(root):
    """Honest opening declaration: setup must not pre-authorise genres the
    repository does not have, or the closed-world rule starts life defeated."""
    repo = fresh_repo(root, "narrow", COLD_START)
    init(repo)
    with open(os.path.join(repo, "docs-corpus.json"), encoding="utf-8") as fh:
        mem = json.load(fh)
    absent = [n for n in ("prd", "evidence", "evidence-index",
                          "archive-index", "standing")
              if n in mem["classes"]]
    write(repo, "docs/prd/0001-a-product.md", "# p\n")
    check("init_declares_only_present_classes",
          not absent and mem["classes"] == ["adr", "corpus-index",
                                            "architecture"]
          and any(f["reason"] == "unknown subdirectory under docs/"
                  for f in run_doctor(repo)["findings"]),
          f"declared={mem['classes']} unexpected={absent}")


@case("init_refuses_to_overwrite")
def _(root):
    repo = fresh_repo(root, "existing", COLD_START)
    init(repo)
    write(repo, "docs-corpus.json", '{"hand": "written"}')
    rc, message = init(repo)
    with open(os.path.join(repo, "docs-corpus.json"), encoding="utf-8") as fh:
        kept = fh.read()
    rc_forced, _ = init(repo, force=True)
    with open(os.path.join(repo, "docs-corpus.json"), encoding="utf-8") as fh:
        replaced = fh.read()
    check("init_refuses_to_overwrite",
          rc == 2 and '"hand"' in kept and "--force" in message
          and rc_forced == 0 and "conforms_to" in replaced,
          f"rc={rc} rc_forced={rc_forced} kept={kept[:60]}")


@case("init_output_is_conformant_membership")
def _(root):
    """Whatever init writes must pass the same validator a hand-written
    file faces — including the version gate it just stamped."""
    repo = fresh_repo(root, "conformant", COLD_START,
                      links=[("CLAUDE.md", "AGENTS.md")])
    init(repo)
    with open(os.path.join(repo, "docs-corpus.json"), encoding="utf-8") as fh:
        mem = json.load(fh)
    errs = Doctor._validate_membership(mem)
    composed = Doctor._compose(mem)
    check("init_output_is_conformant_membership",
          not errs and not Doctor._validate_manifest(composed)
          and mem["conforms_to"] == docs_doctor.CLASS_LIBRARY_VERSION,
          f"membership={errs} composed="
          f"{Doctor._validate_manifest(composed)}")


@case("manifest_missing_classes_key")
def _(root):
    mutate_manifest(root, lambda mf: mf.pop("classes"))
    expect("manifest_missing_classes_key", run_doctor(root),
           "execution_error", "missing key: classes")


@case("manifest_empty_classes_list")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(classes=[]))
    expect("manifest_empty_classes_list", run_doctor(root),
           "execution_error", "classes must be a nonempty list")


@case("manifest_unknown_class_name")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        classes=mf["classes"] + ["runbook"]))
    expect("manifest_unknown_class_name", run_doctor(root),
           "execution_error", "the shipped library does not define")


@case("manifest_duplicate_class_name")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        classes=mf["classes"] + ["adr"]))
    expect("manifest_duplicate_class_name", run_doctor(root),
           "execution_error", "more than once")


@case("manifest_standing_files_without_class")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        classes=[c for c in mf["classes"] if c != "standing"]))
    expect("manifest_standing_files_without_class", run_doctor(root),
           "execution_error", "nothing would classify those documents")


@case("manifest_unknown_key")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(surprise=1))
    expect("manifest_unknown_key", run_doctor(root), "execution_error",
           "unknown key: surprise")


@case("manifest_inline_class_grammar_rejected")
def _(root):
    # the grammar ships with the tool; a repo that tries to redeclare it is
    # writing something no consumer reads
    mutate_manifest(root, lambda mf: mf.update(docs_classes=[]))
    expect("manifest_inline_class_grammar_rejected", run_doctor(root),
           "execution_error", "unknown key: docs_classes")


@case("library_bad_regex")
def _(root):
    run = with_library(lambda lib: library_class(lib, "adr").update(
        basename_regex="(unclosed"))
    expect("library_bad_regex", run(root), "execution_error",
           "basename_regex invalid")


@case("library_unique_by_wrong_type")
def _(root):
    run = with_library(lambda lib: library_class(lib, "adr").update(
        unique_by=[]))
    expect("library_unique_by_wrong_type", run(root), "execution_error",
           "must name a capture group")


@case("library_option_misapplied")
def _(root):
    run = with_library(lambda lib: library_class(lib, "adr").update(
        exactly_one_file_in_dir=True))
    expect("library_option_misapplied", run(root), "execution_error",
           "not applicable to a dir class")


@case("library_indexes_class_on_dir")
def _(root):
    run = with_library(lambda lib: library_class(lib, "adr").update(
        indexes_class="evidence"))
    expect("library_indexes_class_on_dir", run(root), "execution_error",
           "not applicable to a dir class")


@case("library_indexes_class_wrong_type")
def _(root):
    run = with_library(lambda lib: library_class(lib, "evidence-index").update(
        indexes_class=[]))
    expect("library_indexes_class_wrong_type", run(root), "execution_error",
           "must name a dir class")


@case("library_class_without_summary")
def _(root):
    """Every class must say where its documents live: the membership file
    names classes and nothing else, so an unsummarised class would be
    undiscoverable to the person writing that file."""
    def drop(lib):
        library_class(lib, "adr").pop("summary")
    expect("library_class_without_summary", with_library(drop)(root),
           "execution_error", "needs a nonempty summary")


@case("class_listing_names_every_class")
def _(root):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = docs_doctor.print_class_library()
    text = out.getvalue()
    missing = [c["name"] for c in docs_doctor.CLASS_LIBRARY["classes"]
               if c["name"] not in text or c["summary"] not in text]
    check("class_listing_names_every_class",
          rc == 0 and not missing
          and docs_doctor.CLASS_LIBRARY_VERSION in text,
          f"rc={rc} missing={missing}")


@case("library_wrong_frozen_literal")
def _(root):
    run = with_library(lambda lib: lib["discovery"].update(
        docs="honor git ignores"))
    expect("library_wrong_frozen_literal", run(root),
           "execution_error", "must be the frozen literal")


@case("library_unknown_nested_discovery_key")
def _(root):
    run = with_library(lambda lib: lib["discovery"].update(
        archive="scan some other source"))
    expect("library_unknown_nested_discovery_key", run(root),
           "execution_error", "exactly docs and root_and_modules")


@case("manifest_invalid_utf8")
def _(root):
    with open(os.path.join(root, "docs-corpus.json"), "wb") as fh:
        fh.write(b"\xff\xfe{}")
    expect("manifest_invalid_utf8", run_doctor(root), "execution_error",
           "unreadable or unparseable")


@case("manifest_absolute_managed_path")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        managed_files=["/etc/passwd", "AGENTS.md"]))
    expect("manifest_absolute_managed_path", run_doctor(root),
           "execution_error", "repo-relative")


@case("manifest_nul_byte_path")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        managed_files=["AGENTS.md", "BAD\x00.md", "CONTEXT.md", "README.md"]))
    expect("manifest_nul_byte_path", run_doctor(root), "execution_error",
           "repo-relative")


@case("manifest_dot_segment_dual_identity")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        historical_files=mf["historical_files"] + ["./AGENTS.md"]))
    expect("manifest_dot_segment_dual_identity", run_doctor(root),
           "execution_error", "repo-relative")


@case("manifest_mid_path_dot_segment")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        managed_globs=["mod-core/./README.md"]))
    expect("manifest_mid_path_dot_segment", run_doctor(root),
           "execution_error", "repo-relative")


@case("manifest_path_claimed_twice")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        managed_files=mf["managed_files"] + ["NOTES.md"]))
    expect("manifest_path_claimed_twice", run_doctor(root), "execution_error",
           "NOTES.md in both managed_files and historical_files")


@case("manifest_file_class_path_claimed")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        managed_files=mf["managed_files"] + ["docs/architecture.md"]))
    expect("manifest_file_class_path_claimed", run_doctor(root),
           "execution_error", "already claimed by managed_files")


@case("manifest_missing_protected_ref_field")
def _(root):
    mutate_manifest(root, lambda mf: mf.pop("protected_mainline_ref"))
    expect("manifest_missing_protected_ref_field", run_doctor(root),
           "execution_error", "missing key: protected_mainline_ref")


@case("manifest_head_as_protected_ref_rejected")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(protected_mainline_ref="HEAD"))
    expect("manifest_head_as_protected_ref_rejected", run_doctor(root),
           "execution_error", "exact full ref")


@case("manifest_short_name_protected_ref_rejected")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(protected_mainline_ref="main"))
    expect("manifest_short_name_protected_ref_rejected", run_doctor(root),
           "execution_error", "exact full ref")


@case("manifest_revision_expression_ref")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(
        protected_mainline_ref="refs/heads/main~1"))
    expect("manifest_revision_expression_ref", run_doctor(root),
           "execution_error", "not a valid full ref name")


# ------------------------------------------------------- conforms_to gate --
@case("conforms_to_unknown_version_refused")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(conforms_to="99"))
    expect_findings("conforms_to_unknown_version_refused", run_doctor(root),
                    "execution_error",
                    [("execution_error", "is not implemented by this "
                                         "docs-doctor", 1)])


@case("conforms_to_missing_refused")
def _(root):
    mutate_manifest(root, lambda mf: mf.pop("conforms_to"))
    expect("conforms_to_missing_refused", run_doctor(root),
           "execution_error", "is not implemented by this docs-doctor")


@case("conforms_to_wrong_type_refused")
def _(root):
    mutate_manifest(root, lambda mf: mf.update(conforms_to=1))
    expect("conforms_to_wrong_type_refused", run_doctor(root),
           "execution_error", "is not implemented by this docs-doctor")


@case("conforms_to_refusal_precedes_every_other_reading")
def _(root):
    """A file written for another library version must not be interpreted
    under this one, so the version refusal is the ONLY finding — even when
    the file is also full of errors this tool would otherwise report."""
    def fn(mf):
        mf["conforms_to"] = "99"
        mf["surprise"] = 1
        mf.pop("managed_files")
        mf["classes"] = ["runbook"]
    mutate_manifest(root, fn)
    r = run_doctor(root)
    expect_findings("conforms_to_refusal_precedes_every_other_reading", r,
                    "execution_error",
                    [("execution_error", "is not implemented by this "
                                         "docs-doctor", 1)],
                    absent=("unknown key: surprise",
                            "missing key: managed_files",
                            "the shipped library does not define"))


# ---------------------------------------------------- membership reduction --
@case("reducing_classes_closes_the_genre")
def _(root):
    """The shipped library is the maximum, not a structure to adopt: a repo
    that stops declaring a class stops admitting that genre."""
    clean = run_doctor(root)
    mutate_manifest(root, lambda mf: mf.update(
        classes=[c for c in mf["classes"] if c not in ("prd", "adr")]))
    reduced = run_doctor(root)
    check("reducing_classes_closes_the_genre",
          clean["aggregate"] == "clean"
          and reduced["aggregate"] == "failed"
          and all(f["reason"] in ("matches no class",
                                  "unknown subdirectory under docs/")
                  for f in reduced["findings"]
                  if f["check"] == "docs-structure"),
          f"clean={clean['aggregate']} reduced={reduced['aggregate']} "
          f"{json.dumps(reduced['findings'])[:300]}")


@case("standing_files_are_membership_not_library")
def _(root):
    """The standing class ships empty; its members come from the repo."""
    mutate_manifest(root, lambda mf: mf.update(
        standing_files=[p for p in mf["standing_files"]
                        if p != "docs/notes.md"]))
    expect("standing_files_are_membership_not_library", run_doctor(root),
           "failed", "matches no class")


@case("inflight_globs_stay_per_repo")
def _(root):
    """Live consumers disagree about root working-record genres, so this
    stayed in membership; a repo that declares one gets it honoured."""
    write(root, "SKILL-REVIEW-topic.md", "# review\n")
    unadmitted = run_doctor(root)
    mutate_manifest(root, lambda mf: mf.update(
        inflight_globs=mf["inflight_globs"] + ["SKILL-REVIEW-*.md"]))
    admitted = run_doctor(root)
    check("inflight_globs_stay_per_repo",
          unadmitted["aggregate"] == "failed"
          and any("matches no root class" in f["reason"]
                  for f in unadmitted["findings"])
          and admitted["aggregate"] == "clean",
          f"unadmitted={unadmitted['aggregate']} "
          f"admitted={admitted['aggregate']}")


@case("manifest_legal_at_sign_ref_accepted")
def _(root):
    with open(os.path.join(root, "fixture-info.json"), encoding="utf-8") as fh:
        head = json.load(fh)["head"]
    sh(root, "git", "update-ref", "refs/heads/main@old", head)
    mutate_manifest(root, lambda mf: mf.update(
        protected_mainline_ref="refs/heads/main@old"))
    expect("manifest_legal_at_sign_ref_accepted", run_doctor(root), "clean")


def main():
    os.environ["GIT_CONFIG_GLOBAL"] = "/dev/null"
    os.environ["GIT_CONFIG_SYSTEM"] = "/dev/null"
    with tempfile.TemporaryDirectory() as work:
        baseline = os.path.join(work, "baseline")
        os.makedirs(baseline)
        build_baseline(baseline)
        orig_path = os.environ["PATH"]
        for name, fn in CASES:
            root = os.path.join(work, name)
            shutil.copytree(baseline, root, symlinks=True)
            os.environ["PATH"] = \
                os.path.join(root, "fixture-bin") + ":" + orig_path
            try:
                fn(root)
            except Exception as exc:  # a crashing case is a failing case
                check(name, False, f"exception: {exc!r}")
            finally:
                os.environ["PATH"] = orig_path
    passed = sum(1 for c in CHECKS if c["pass"])
    failed = len(CHECKS) - passed
    print(json.dumps({"cases": [c for c in CHECKS if not c["pass"]],
                      "passed": passed, "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
