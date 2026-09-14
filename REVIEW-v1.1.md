```doc-meta
role: working
lifecycle: active
```

# Jot v1.1.0 review

Task: jot-6ab; study skill: jot-6ab.1. Codex owns CLI, tests, documentation and
integration. Claude owns the study skill and independently reviewed the CLI.
Codex independently reviewed and used the skill.

The operator authorized implementation on 2026-09-14 after publishing v1.0.0
(tag `prod`) at `47693ce8eff9e74cee72439b9bf3be2bee601230`. Delivery is a reviewed
development branch/PR. Acceptance below is engineering acceptance, not permission
to merge main, publish a release, or change consumer installations.

## Outcome and candidate

Claude accepted integrated candidate
`d105072e8ccdcded7c1373470cca0d3b52ae66e9` with two nonblocking concerns, disposed
of below. CLI and skill bytes are unchanged by subsequent documentation and
tracker delivery commits. Runtime source is `tools/jot.py`; study instructions
are `skills/jot-study/SKILL.md` from Claude's `428643c` (integrated as `c36974e`).

The candidate adds optional scoped JSON memory alongside discovery capture:
rough capture; study using the running agent; cleaned-only recall; revision and
deletion. Identity is optional. Existing discovery capture/list/dir and
operator-directed jot-review keep their behavior, with newly reserved command
words and an explicit literal-capture escape documented below. No memory
Markdown, model service, indexing, or consumer-specific dependency.

## Verification

- Test-first: new CLI tests failed against v1.0.0's missing memory operations.
- Both authors independently ran the original 25 real filesystem/Git checks;
  all passed. Both ran the 12 memory tests; all passed. The memory suite covers
  record units, actual CLI processes, scope defaults/overrides/general reads,
  cleaned-only recall, save/rewrite/delete, malformed input and linked worktrees.
- Claude independently exercised a symlinked installation, full study commands
  while launched as A and explicitly studying B, general/all-agent reads, clear
  failure paths, discovery compatibility, and memory surviving worktree removal.
- Codex used the actual study skill through a symlinked CLI in a separate scratch
  repository: grounded three rough claims in settings.json, revised an obsolete
  cache-path memory, saved a qualified recovery lesson, and deleted the consumed
  notes. Agent A's bank and the discovery queue were unchanged; only B was
  studied. Unsupported Redis speculation never entered cleaned recall.
- Both skills pass skill-creator quick_validate. Changed docs are indexed,
  doc-meta is present, local links resolve, and archived source blobs recover.
  The v1.0.0 archive sources are reachable from main; development snapshots are
  reachable on dev/v1.1-memory and join main when the feature is merged.

## Findings and dispositions

**Study scope loss, fixed before first ready.** Codex found that selecting B
under JOT_AGENT=a could be lost on subsequent bare commands. Claude's repair
carries --agent through every operation. Both independent scoped study exercises
passed on the repaired candidate. The skill also treats rough notes as claims
or hypotheses and leaves context-loading size open.

**Command-word collisions, documented.** Claude reproduced `jot remember to
update the docs` becoming a query and `jot memory leak in parser` becoming rough
memory capture. v1.0.0 captured those as discoveries. New command words are
intentional; literal capture is available with `jot -- "<observation>"`. The
README now puts this beside capture usage and in copyable agent instructions,
with evidence flags before the separator. No parser heuristics were added.

**Corrupt-record recovery, documented.** Claude placed invalid JSON in bank and
confirmed that reads in every scope fail with the file path; CLI delete also
refuses because it cannot validate identity and scope. Exact-file repair or
removal restores reads. The README explains this behavior and its difference
from discovery's unreadable-note placeholder. No force-delete command or new
recovery machinery was added.

## Timing and limits

First ready: 2026-09-14 14:38 UTC. Independent acceptance received:
2026-09-14 14:45 UTC. Study-skill repairs preceded first ready; final concern
dispositions change documentation only. These are wall-clock milestones, not
engineering-time, token, or cost measurements.

Validation ran on Linux on this host, with sequential writers. Concurrent
same-record edits, other operating systems, and Python 3.7 runtime execution
were not exercised (syntax was checked against 3.7 and the stdlib API minimum
was preserved). Memory remains local to the clone and is not backed up by Git.
No consumer installation, main merge, release publication, or prod-tag change.

This record remains current for the unmerged release candidate. Once its final
commit is reachable from main and the release integration is complete, archive
its exact commit/blob and remove it under AGENTS.md's transition guard.
