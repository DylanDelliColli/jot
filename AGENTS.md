```doc-meta
role: contract
lifecycle: active
```

# Jot - agent instructions

Instructions for every Claude or Codex session working in this repository.
`AGENTS.md` is authoritative; `CLAUDE.md` is only its alias.

## What this repository is

Jot owns the general-purpose documentation and capture machinery first proven
in abacus. Its tools are the product, not incidental repository scripts:

- `docs-doctor` governs a declared documentation corpus and its provenance;
- the probe executor runs typed, bounded verification probes; and
- `jot` and `jot-review` will provide the durable capture and review funnel.

Abacus is a consumer of Jot, not Jot's owner. Keep product code and fixtures
consumer-neutral. Consumer-specific membership and conventions belong in that
consumer's configuration, not in Jot's implementation.

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

For the capture funnel, `jot-met.7` is the implementation authority: MVP scope
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
  changing the tree.
- Never use `bd` or `sable-note` here. Do not invoke other legacy SABLE
  workflow machinery for Jot work.
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
   to `docs/history/README.md`.
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

Every managed document starts with `doc-meta`, appears exactly once in
`docs/README.md`, and obeys `docs-corpus.json`. The `docs/` tree is closed:
adding a genre, standing file, or subdirectory requires a reviewed manifest
change.

`docs-corpus.json` declares MEMBERSHIP only. Its `classes` array is the
whitelist of document locations this repository admits, named by those
locations; the class definitions themselves ship inside
`tools/docs_doctor.py` and are the maximum, never a structure to adopt.
`docs-doctor --repo . --init` writes the whole whitelist and narrowing is
deleting lines from it — a location not listed is forbidden, not merely
unchecked, which is what makes admitting a new genre a reviewed edit. Do not
put a class definition back into `docs-corpus.json`; the membership validator
rejects keys no consumer reads. `conforms_to` names the class-library version
the file was written against and is refused if this tool does not implement
it.

Run docs-doctor before a push, at phase gates, and at session close, from
this repository's root:

```sh
python3 tools/docs_doctor.py --repo . --json
python3 tools/test_docs_doctor.py    # the fixture suite, before touching the tool
```

The tool enforces the structure this repository *declares*: four checks —
docs-structure, metadata, index-symmetry, and inflight-residency — plus the
manifest gate and path confinement they need. Seven further checks and the
probe executor are deferred, not rejected; they remain in the frozen
`abacus-v1` parts bin and return only by being ported here against an
observed need. Do not reach into that tree to run a check jot has not
adopted.

`failed` and `execution_error` block landing. A `degraded` result is allowed
only when every finding is accounted for — traceable to an open bead or to a
recorded decision; never call it clean. Never edit a record to silence a
finding. The deferred `reverse-citations` check made the cost visible: it
flags any mention of a filename, including a closed bead explaining why that
file will never exist here, and twice the resolution taken was to reword the
tracker rather than the tree. A record edited to quiet a tool is a record
corrupted to flatter it, and that holds for whichever check is running.

Record the run on the bead you are landing, not in a table. This check is
instant and deterministic, so current state is obtained by running it — a
maintained copy of its output is a cache of a cheap computation, and unlike
the tool the cache can be wrong. Expensive, non-reproducible observations
such as a live provider capture or a concurrency pilot are the opposite
case and do belong in a checked-in record.

## Cross-lineage review lane

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
