```doc-meta
role: working
lifecycle: active
```

# Jot v1.1.0 review

Task: jot-6ab; study skill: jot-6ab.1. Codex owns CLI, tests and integration;
Claude owns the study skill. Both independently assess the other's work.
The operator authorized the implementation on 2026-09-14 after publishing
v1.0.0 (release tag `prod`) at `47693ce8eff9e74cee72439b9bf3be2bee601230`.

## Required outcome

Add optional scoped JSON memory while preserving discovery capture and the
operator-directed jot-review flow. Rough capture, autonomous study, cleaned-only
recall, revision and deletion work with or without agent identity. No Markdown
memory, model service or consumer-specific dependency.

## Evidence so far

- Baseline: original 25 real filesystem/Git checks passed. Installed capture,
  list and dir exercised in a scratch repository.
- Test-first: new CLI tests failed on the original product's missing memory
  operations; after implementation all 10 memory scenarios passed.
- Study skill review by Codex at Claude's `5ec8f67`: explicit --agent selection
  could be lost when subsequent bare commands fell back to JOT_AGENT. Requested
  carrying scope on every operation. Also corrected treating rough notes as
  necessarily true and an unadopted whole-bank size requirement. Repair pending.

## Status

Integrated CLI review and independent study dogfood are pending. This is a
current development record; it is not release acceptance or a published release.

## First ready candidate, 2026-09-14 14:38 UTC

The CLI and skill are integrated through `c36974e`. The repaired skill carries
explicit scope through subsequent commands, treats rough notes as claims, and
leaves context-loading size open. Twelve memory tests (record units and real
CLI journeys) pass. Claude exercised all documented CLI operations in a scratch
repo before integration; no CLI findings in that preliminary pass. Formal
independent review and Codex's study dogfood follow this candidate.
