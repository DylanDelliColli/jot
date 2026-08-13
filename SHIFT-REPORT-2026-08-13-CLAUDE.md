# Shift report — 2026-08-13 (Claude lane)

## 1. Identity and snapshot boundary

Repository `jot`, branch `main`. Outgoing: the Claude session that compared the
repository against `NORTH-STAR.md`, then split the capture half out of
`jot-met.7` and built it. Incoming: the next agent working this repository —
see section 6, the lane identity is a genuine open question, not a formality.

**Pre-report base: `3182825`** — the capture landing, the last commit before
this document. Current HEAD is deliberately not written here; committing this
report changes it. Resolve this report's own object after intake with
`git log --oneline -1 -- SHIFT-REPORT-2026-08-13-CLAUDE.md`.

Observation time for every probe below: 2026-08-13 authoring pass. Work
described as landed was committed 2026-08-12.

This is the first shift report in this repository. It supersedes nothing, and
nothing was archived under the transition guard to create it.

## 2. Read-first authority map

- **Agent operating contract:** `AGENTS.md`. `CLAUDE.md` is only its alias.
- **Product thesis, success conditions, kill criteria:** `NORTH-STAR.md`.
- **Work items:** `br`, `jot-` prefix. `jot-met.7` is the authority on capture
  funnel MVP scope, including the explicit not-built list.
- **Capture implementation:** `tools/jot.py` at `3182825`. The code is the
  authority on behavior; this report is not.
- **Corpus membership:** `docs-corpus.json`; the map is `docs/README.md`.
- **Validation evidence:** the ledger table in `README.md`.
- **Design of record, explicitly NOT a build order:**
  `PROPOSAL-funnel-and-docs-doctor.md`. It lives in the abacus checkout and has
  not been migrated (`jot-met.2`). Its absence here is intentional and is the
  source of the two standing docs-doctor findings.

**No authority inversion is active.** Code, tracker, and documentation are
believed to agree. Any disagreement found is a defect to investigate, not
licence to prefer one source generally.

## 3. Objective and success condition

The session had two objectives. The first — compare the repository against the
north star — was analysis and produced no durable artifact beyond the notes in
section 5. The second was to build the capture command, and that landed.

Completion for the wider arc is defined by `NORTH-STAR.md`: consuming
repositories capture through `jot`, curate through `jot-review`, and honor the
structure docs-doctor enforces. Capture is now the only one of those three that
exists.

Expressly outside the current task: `jot-review` (`jot-met.7`), the tool and
spec migrations (`jot-met.3`, `jot-met.2`), and the entire crash-safety
machinery, which is parked — see section 5.

## 4. Direction changes and settled decisions

**D1 — Language for capture: Python. APPLY, do not relitigate.**
Prior direction: open; Rust was weighed because the primary consumer, abacus,
is a 46,094-line Rust workspace. Replacement: stdlib-only Python. Evidence: the
4,178 lines migrating in `jot-met.3` are stdlib-only Python with zero
third-party dependencies; a build artifact is not smaller than a script, which
`AGENTS.md` MVP-first rule disfavors. Durable object: `jot-met.7.1` description
and the `3182825` commit message.
**Bounded:** this settles capture only. The repository-wide language question is
open and belongs to `jot-met.3`, where 4,178 lines are decided — not here,
where 165 were.

**D2 — `jot-met.7` split; capture landed independently. APPLY.**
Prior: one bead covering `jot` and `jot-review`, blocked by `jot-met.4`, `.5`,
and `.6`. Replacement: `jot-met.7.1` carries capture, reparented under the epic
`jot-met`, and is closed. `jot-met.7` retains `jot-review` and its original
blockers. Evidence: capture touches neither `docs-corpus.json` (`.4`), nor
abacus identifiers (`.5`), nor `br` (`.6`). Durable objects: `jot-met.7.1`
(closed), `jot-met.7` (open).

**D3 — Two gaps `jot-met.7` left open are now pinned. APPLY.**
Note ids are `timestamp-pid-6hex`, because ULIDs are excluded by `jot-met.7`
and same-second writes are ordinary at the ten-worker target. `--why` ships as
`jot-met.7` specifies it. Durable object: `jot-met.7.1` description and
`tools/jot.py`.

**D4 — `jot dir` was added beyond the bead. NOT RATIFIED.**
A third subcommand printing the queue path, so `jot-review` can locate the
queue without duplicating git-common-dir resolution in markdown. The operator
was told; no bead records it. Treat as provisional scope.

**Unresolved product choices — do not settle these silently:**

- Whether the probe executor belongs in the product at all. It is a first-class
  surface in `README.md` and `AGENTS.md` and appears nowhere in
  `NORTH-STAR.md`. Captured as a pending note, deliberately not beaded.
- Whether `--why` survives; it is the one field the global capture rule does
  not ask for.
- Repository-wide language, at `jot-met.3`.
- Whether `jot-met.4`, `.5`, and `.6` are real blockers for `jot-review`. Only
  its docs-doctor step plainly needs `jot-met.3`. Not investigated.

## 5. Durable work state

**Landed** — committed and pushed, contained in `origin/main`:

- `3182825` "jot-met.7.1: build the jot capture command" — adds `tools/jot.py`,
  `tools/test_jot.py`, `tools/__init__.py`; updates `README.md` product surface
  and ledger; updates `.beads/issues.jsonl`. Remote containment verified, not
  assumed (section 9).

**In flight:** nothing. No bead is claimed. No agent or worker is running for
this repository from this lane.

**Uncommitted / external — the part the branch cannot prove:**

- **Three pending notes** at `.git/jot/pending/*.json`, captured by dogfooding:
  the probe-executor/north-star gap, the tracked `.beads` runtime lock files,
  and the absolute-path docs-doctor invocation in `AGENTS.md`. They live inside
  `.git`, so they are **not versioned, not pushed, and absent from any fresh
  clone**. They are the only dogfooding evidence produced so far, and
  `NORTH-STAR.md` names dogfooding as what its kill criteria depend on. Owner:
  this lane, handed to the incoming agent. See hazard H1.
- **`~/.local/bin/jot`** → symlink to `tools/jot.py`. Machine state, not
  repository state. Another machine or checkout has no `jot` on PATH until it
  runs the install line in `README.md`.

**Planned — not implemented, do not describe in present tense:**

- `jot-review` curation skill (`jot-met.7`).
- Tool migration (`jot-met.3`) and spec migration (`jot-met.2`), both ready.

**Parked / held:**

- The crash-safety machinery — seven-event fold, ULIDs and canonical-JSON
  digests, publish protocol, drain flock, two-observation gate, patch artifacts,
  attempt state machine, reconciliation, the 28-entry error vocabulary, and the
  experiment-5 crash matrix. Design of record only, per the operator ruling of
  2026-08-12 recorded on `jot-met.7`. Release condition: an observed failure
  that supports a new bead. Decision owner: operator.

**Pre-existing dirty files:** none. The tree was clean before this report
(`git status --porcelain` returned zero lines). The abacus checkout was also
clean; this lane issued no write to it.

## 6. Ownership and boundaries

**Lane identity is unresolved and matters.** `AGENTS.md` records that the Codex
build lane pairs with the Claude adversarial-review lane in tmux pane `w1H:p2`.
**This session did build work as Claude.** From inside the session I cannot
verify whether this is pane `w1H:p2`. Either the arrangement has changed, or
this build was performed outside the named build lane. Do not paper over it —
the operator should confirm which lane owns building before more product code
lands.

**Cross-review is owed.** `AGENTS.md` makes cross-review mandatory for product
seam changes. `tools/jot.py` is a product seam change and **has not been
cross-reviewed**. This is an open obligation, not a closed step.

The abacus checkout is read-only from this lane and stayed that way: files were
read for line counts, dependency surface, and shift-report convention only.

No live messages are pending delivery. No coordination is outstanding beyond
the two items above.

## 7. Hazards, holds, and negative instructions

- **H1 — Do not destroy the pending notes.** Scope: `.git/jot/pending/`. No
  `git clean -xdf`, no deleting `.git/jot`, and do not assume a fresh clone has
  parity. Release: when `jot-review` curates them, or they are transcribed into
  beads.
- **H2 — Treat `tools/jot.py` as provisional.** Scope: the product seam only,
  not the tracker or docs. Release: cross-review adjudicated per `AGENTS.md`.
- **H3 — docs-doctor runs by absolute path into another repository.** If the
  abacus checkout moves or is removed, validation silently breaks. Scope: the
  command in `AGENTS.md` and `README.md`. Release: `jot-met.3`.
- **H4 — Do not build the parked crash-safety machinery.** Scope: the list in
  section 5. Release: an observed failure plus a new bead. Owner: operator.
- **H5 — Never use `bd` or `sable-note` in this repository.** Use `br` and
  `jot`. The global instruction file says `sable-note`; `AGENTS.md` overrides it
  here. No release condition — this is standing.
- **H6 — `br dep add` defaults to `blocks`, and a child of a blocked parent
  cannot be claimed.** Use `--type=parent-child` explicitly. Learned by failure
  during this session; see section 9.

## 8. Incoming boot sequence

1. `br ready`
2. `git status --porcelain` then `git rev-parse HEAD origin/main`
3. `python3 tools/test_jot.py`
4. `jot list` — confirms the pending notes survived; if `jot` is not on PATH,
   install per `README.md` first
5. `python3 /home/ddc/dev-environment/abacus/tools/docs_doctor.py --repo /home/ddc/dev-environment/jot --json`

**First consequential act:** claim `jot-met.3` and migrate the tools. It is
ready, it unblocks `.4`, `.5`, and `.6`, and it retires H3. Do this before
`jot-met.2`, whose output is what the two standing docs-doctor findings are
waiting on and which changes nothing executable.

Route the section 6 items to the operator in parallel; neither is yours to
settle alone.

## 9. Verification ledger and known defects

| Claim | Evidence or probe | Observed result and time | Incoming action |
|---|---|---|---|
| Branch `main`, upstream equal | `git rev-parse HEAD` vs `origin/main` | both `3182825c2ec73c64f17d52b5ed17d5e48995d1ff`, equal — 2026-08-13 | Rerun; report commit will have advanced HEAD |
| Capture commit is on the remote, not just local | `git branch -r --contains 3182825` | `origin/main` — 2026-08-13 | Trust as durable |
| Working tree clean | `git status --porcelain` | 0 lines — 2026-08-13 | Rerun before any edit |
| Capture suite green | `python3 tools/test_jot.py` | 22 passed, 0 failed — 2026-08-13 | Rerun; treat any failure as blocking |
| docs-doctor unchanged | `docs_doctor.py --repo ... --json` | `degraded`, 2 findings, both `reverse-citations` on `jot-met` and `jot-met.2` citing `PROPOSAL-funnel-and-docs-doctor.md` — 2026-08-13 | Rerun; new finding classes must not be called clean |
| Three notes pending | `ls $(jot dir)/*.json` | 3 files — 2026-08-13 | Rerun; a count below 3 means loss, escalate |
| Notes are not versioned | `git ls-files \| grep -c jot/pending` = 0, positive control `grep -c tools/jot.py` = 1 | 0 with control 1, so the probe can see tracked files — 2026-08-13 | Trust as structural |
| `jot` on PATH | `ls -la ~/.local/bin/jot` | symlink → `tools/jot.py` — 2026-08-13 | Rerun; machine-local, absent on other machines |
| No tree claim held | `sable-claim status` | `no claim` — 2026-08-13 | Rerun before staging |
| abacus unmutated by this lane | `git -C ../abacus status --porcelain` | 0 lines — 2026-08-13 | Rerun; other lanes may dirty it legitimately |
| `jot-met.7.1` closed | `br show jot-met.7.1` | CLOSED with reason — 2026-08-13 | Trust as durable |
| Ready work | `br ready` | `jot-met.2`, `jot-met.3` — 2026-08-13 | Rerun |

**Known defects and corrections:**

- **Bead parenting failure.** `jot-met.7.1` was first created with
  `--parent=jot-met.7`, which made it unclaimable: `br` refused with
  `cannot claim blocked issue: jot-met.7`, because a child inherits a blocked
  parent's state. Reparenting under the epic `jot-met` fixed it, but
  `br dep add` silently defaults to `blocks`, so the first repair attempt made
  the bead blocked by the epic instead. Correct form:
  `br dep add <child> <parent> --type=parent-child`. Lesson recorded as H6.
- **An analysis claim in conversation was corrected mid-session** — that 93% of
  the migrating code traces to the north star. It was a name-check, not a
  weight check, and understated the imbalance. No durable artifact carried the
  wrong figure; it is noted here only so the incoming agent does not rediscover
  the corrected reasoning as if it were new.
- No defect has been found in this report after landing. If one is, append it
  here rather than editing the failed claim away.

## 10. Closeout pointer

This report is the index; `AGENTS.md`, `NORTH-STAR.md`, `br`, and `3182825` are
the cargo. The outgoing session ends after this document is committed and
pushed and its own commit object is resolved. Do not treat the outgoing session
as a live source of truth once that is done.
