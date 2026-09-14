```doc-meta
role: contract
lifecycle: active
```

# Jot - agent instructions

Instructions for every Claude or Codex session working in this repository.
`AGENTS.md` is authoritative; `CLAUDE.md` is only its alias.

## What this repository is

Jot owns the durable capture and review funnel first proven in abacus.
Its products are the `jot` command, the operator-directed `jot-review`
curation skill, and autonomous `jot-study` for repository memory.

Abacus and Alleyoop are consumers of Jot, not Jot's owners. Keep product code and fixtures
consumer-neutral. Consumer-specific conventions belong in that consumer's
configuration, not in Jot's implementation.

## MVP first, fix as we use

Build the smallest usable replacement, put it into real use, and fix failures
that dogfooding actually exposes. Do not build contingencies for failure modes
that have not occurred merely because an approved design describes them.
Complexity earns admission through observed evidence or an explicit current
requirement, not through plausibility.

The product being replaced is the first seam to verify. Before drafting or
implementing a replacement, open, read, and use the working product; record
what it actually does and the observed inadequacy the replacement addresses.
Only then inspect code, provider, and storage seams. "Verify the seam before
you draft" is defective when it verifies implementation interfaces but never
examines the product whose behavior defines parity.

An approved proposal can be a **design of record without being a build
order**. It preserves decisions and possible future machinery. The active `br`
bead's stated scope and acceptance criteria are authoritative for what gets
built now. When a design document is broader, implement only the bead and do
not infer the remainder as required work.

For v1.1.0, `jot-6ab` is the authorized memory scope: JSON rough notes,
autonomous study into cleaned memories, cleaned-only recall, revision and
deletion. Agent identity is optional; memory defaults to an explicit `--agent`,
then `JOT_AGENT`, otherwise repository-general. Existing capture/list/dir and
operator-directed discovery review remain compatible. No memory service,
indexing, cross-machine sync, Markdown memory, or automatic discovery review.
Memory curation uses the running agent through `jot-study`; it needs no
operator approval and never creates work or edits documentation.

For the original capture funnel, `jot-met.7` was the implementation authority: MVP scope
is sable-note and sable-review parity plus only the cheap improvements named in
that bead. The v20 funnel design's event fold, publish protocol,
two-observation gate, patch artifacts, attempt state machine, reconciliation,
and crash-injection matrix are explicitly not part of that MVP. They remain
design of record until an observed failure supports a new bead.

MVP acceptance is dogfooding: install and use the product for real capture and
curation in Jot and its consumers, with only the smallest smoke check needed to
show the path works. Turn failures found in use into `jot-` beads carrying the
observed reproduction and evidence. Do not substitute a speculative fixture
matrix for opening and using the product.

## Work tracking and legacy machinery

- Use `br` for every work item in this repository. IDs use the lowercase
  `jot-` prefix. Start with `br ready`, inspect the bead, and claim it before
  changing the tree. This checkout uses `br` 0.1.45. On this host, invoke
  `~/.local/bin/br-0.1.45` while the default `br` requires a newer database
  schema; do not migrate the tracker as a side effect of product work.
- Never use `bd` or `sable-note` here. Do not invoke other legacy SABLE
  workflow machinery for Jot work.
- Capture what you notice but are not acting on with `jot "<observation>"`,
  with `--file`, `--symptom`, `--repro` and `--why` where you have them.
  Curate discoveries with `jot-review`, which is **operator-invoked only** — never on a
  schedule, a hook, or at session close. A blocking defect is the carve-out:
  bead it immediately rather than capturing it.
  Both lineages invoke it as `/jot-review`. It installs once, into the
  shared `~/.agents/skills/`, which Codex reads directly and which
  `~/.claude/skills/` symlinks into — so a skill placed only under
  `~/.claude/skills/` is invisible to Codex. Its `allowed-tools` front
  matter is a Claude construct and constrains nothing under Codex, where
  the sandbox does.
- Honor bead dependencies and operator lane boundaries. Do not begin blocked
  work merely because its prerequisites look approachable.
- A consumer checkout is read-only unless an operator explicitly coordinates
  a migration that names mutations in that checkout. In particular, never
  fold an uncoordinated abacus edit into a Jot change.

## Git rules

- The only remote is
  `git@github-personal:DylanDelliColli/jot.git`. The `github-personal` SSH
  alias is required; the machine's default GitHub key has no write access.
  Never replace the remote with a plain `github.com` URL or add another
  remote.
- Repository-local commit identity is already configured. Do not change it.
- Keep commits coherent and reviewable, and push landed commits.
- Legacy tree-claim hooks may fire on Git operations. If a stage or commit is
  blocked, inspect `sable-claim status`, release only this lane's claim
  promptly after the commit batch, and use
  `git -c core.hooksPath=/dev/null commit -F <message-file>` only when hook
  interference has corrupted the normal operation. Do not change global
  hooks or Git configuration.

## Documentation and tree residency

The working tree holds current state; reachable Git history is the archive. A
document or working record earns tree residency only when a fresh agent needs
it now. Closed review rounds, dead proposals, superseded shift reports, and
handoffs leave the tree instead of remaining as searchable misinformation.

Apply this transition guard to every overwrite or deletion of a governed
document or working record:

1. Refuse the transition if the path is untracked or its bytes differ from
   `HEAD:<path>`.
2. Commit the completed record first, so the exact bytes exist in a commit.
3. Record the full last-containing commit and its exact blob ID.
4. Only in a later commit, overwrite or delete the path and add its pointer row
   to `docs/history/INDEX.md`.
5. Verify the recorded commit is reachable from the protected mainline
   `refs/heads/main`. Never rewrite an archive-bearing mainline commit.

The archive pointer index is the only file stored under `docs/history/`. Its
rows are `| path | commit | source_blob | claim |`, use full object IDs, are
unique by `(path, commit)`, and keep `|` out of cell text. A row must recover
with `git show <commit>:<path>`, and that blob must equal `source_blob`.

An active design or review cycle has exactly one review file at the repository
root. Overwrite that same file between rounds under the transition guard;
round-suffixed review files are forbidden. On alignment, archive the
last-containing coordinate and delete the review file under the same guard.
Each lane likewise keeps at most one current root-level shift report and
overwrites it at handoff under the guard.

Root contracts, review and shift reports, and documents under `docs/` start
with `doc-meta` and appear exactly once in `docs/INDEX.md`. Skill files use
their own front matter. Consumers choose their own documentation structure
and checks. `README.md` may wrap its opening `doc-meta` block in an HTML
comment so GitHub renders the reader-facing introduction first.

`docs/INDEX.md` is a table of contents — `| path | claim |`. Role and
lifecycle live in each document's own block and are never copied into it.

## Verification

Run the capture suite before pushing changes to Jot's capture or review
workflow:

```sh
python3 tools/test_jot.py
python3 tools/test_memory.py
```

It exercises real filesystems and Git repositories, including linked
worktrees. Check review-skill edits against the capture format and the
receiving repository's instructions. Record validation on the bead being
landed. Expensive observations from real use belong in a checked-in record.

## Cross-lineage review lane

**v1.1.0 arrangement (operator, 2026-09-14):** Codex in Herdr `w9X:p2`
and Claude in `w9X:p1` are authorized to build and cross-review the memory
extension. Each writer uses its own checkout. This pairing supersedes the
older pane reference below for `jot-6ab`. Inspect live identities before
using any saved pane reference.

**Confirmed arrangement (operator, 2026-08-12):** the Codex build lane in this
repository pairs with the Claude adversarial-review lane in tmux pane
`w1H:p2`, whose working directory is `/home/ddc/dev-environment/jot`. This is
the active named cross-review lane; do not silently substitute a self-review.

Under this arrangement, the two lineages build and adversarially review each
other's work. They do not edit the same file concurrently. Cross-review is
mandatory for product seam changes and phase gates. Review the MVP against the
working product it replaces, the active bead, and evidence from dogfooding. Do
not expand review into the crash-safety machinery excluded by `jot-met.7`
unless a later evidence-backed bead brings that machinery into scope. Findings
and adjudications live in the cycle's single root review file; an aligned
review is archived through the transition guard above.

Review ceremony is bounded at two levels. Within an accepted scope, judge a
round by defects found and decisions resolved; two consecutive rounds that
produce only refinements end the cycle. Before and during the cycle, also test
the scope itself against the working baseline and the smallest usable product.
A review can catch real defects simply because the artifact under review is
oversized. Defects caught prove that the round was productive; they do not
prove that the artifact should have been that large.
