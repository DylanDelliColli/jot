```doc-meta
role: contract
lifecycle: active
```

# Jot

Jot is the home of reusable documentation governance and durable observation
capture. It is being extracted from its incubation in abacus so that abacus
and other repositories can consume the machinery without owning it.

The repository contains its foundation contract, the `jot` capture command,
and docs-doctor. Subsequent tracked work builds the `jot-review` curation
skill. Do not infer that a listed product surface is available until its bead
has landed.

The approved funnel specification is a design of record, not a build order.
`jot-met.7` governs the capture MVP: parity with the working sable tools plus
its named cheap improvements, accepted through dogfooding. Richer crash-safety
machinery remains unbuilt unless observed evidence justifies later work.

## Product surfaces

- **docs-doctor** enforces the documentation structure a repository declares
  in `docs-corpus.json` — the enforcement is real, the declaration is the
  repository's. Landed in `jot-met.3`; `tools/docs_doctor.py` is stdlib-only.
  See [Setting up docs-doctor](#setting-up-docs-doctor-in-a-repository) below.

  Four checks ship: docs-structure (every file matches exactly one declared
  class), metadata (`doc-meta` blocks agree with their class), index-symmetry
  (`docs/INDEX.md` lists exactly the managed corpus), and inflight-residency
  (one review file per cycle, one shift report per lane). Seven further
  checks — supersession, probes, bead-citations, historical-bytes,
  archive-index, reverse-citations, evidence-index — and the probe executor
  they need are deferred, not rejected. They remain in the frozen `abacus-v1`
  tree and return only by being ported here against an observed need.

- **jot** durably captures ownerless observations as one JSON file per note in
  an on-disk queue. Landed in `jot-met.7.1`; `tools/jot.py` is stdlib-only and
  runs from anywhere on PATH. The queue lives at `<git-common-dir>/jot/pending`
  so notes stay with the repository they concern and survive worktree teardown.

  ```sh
  ln -s "$PWD/tools/jot.py" ~/.local/bin/jot   # install
  jot "<observation>" [--file P] [--symptom S] [--repro R] [--why W]
  jot list                                     # pending notes
  jot dir                                      # queue path
  ```

- **jot-review** provides operator-gated curation into tracker or documentation
  outcomes and runs docs-doctor after documentation changes. Not yet built;
  tracked by `jot-met.7`.

The implementation and its fixture suites are product artifacts. Repository
consumers supply their own corpus membership and conventions.

## Setting up docs-doctor in a repository

Point it at a repository that already has some documentation. It reads what
is there and writes a configuration matching it — you are not expected to
author `docs-corpus.json` from a blank file.

```sh
ln -s /path/to/jot/tools/docs_doctor.py ~/.local/bin/docs-doctor   # install

cd /your/repo
docs-doctor --repo . --init   # 1. write docs-corpus.json + a starter index
docs-doctor --repo .          # 2. see what is left to do
docs-doctor --classes         # 3. what else may be declared, and where
```

**Step 1** writes a working configuration for any repository, new or old. The
`classes` array it writes is **the whitelist of document locations this
repository admits**, and it starts complete — every location the tool ships,
one per line:

```json
 "classes": [
   "docs/adr",
   "docs/prd",
   "docs/compatibility",
   "docs/compatibility/INDEX.md",
   "docs/INDEX.md",
   "docs/architecture.md",
   "docs/history/INDEX.md"
 ],
```

**That array is where you filter.** Delete the lines you do not want. A
location you do not list is *forbidden*, not merely unchecked — documents
there are reported as unknown, which is what makes adding a genre later a
deliberate edit rather than a drift. Step 1 also refuses to overwrite an
existing `docs-corpus.json` without `--force`, and scaffolds `docs/INDEX.md`
when absent, with a row per document it found and a `TODO` claim in each.

Documents that belong under `docs/` but fit none of those locations go in
`standing_files`, listed individually.

**Step 2** reports what remains, and it is normally two things: each document
needs a `doc-meta` block, and each row of `docs/INDEX.md` needs a real claim
in place of the `TODO`. A document's block looks like this, before any other
content in the file:

````markdown
```doc-meta
role: contract
lifecycle: active
```
````

`role` is one of `contract`, `evidence`, `working`, and must agree with the
class the document belongs to — `--classes` shows which classes fix a role.
`lifecycle` is one of `active`, `partially-superseded`, `superseded`,
`withdrawn`, `parked`, `historical`. Root contracts such as `AGENTS.md` may
run without a block, on their index row as a temporary sidecar; that reports
`degraded` rather than `failed`.

**Step 3** reprints that whitelist with a description of each location, for
when you are narrowing it later and the file alone is not enough. Everything
else in `docs-corpus.json` names files rather than locations: `managed_files`
(root documents), `managed_globs` (e.g. `mod-*/README.md`), `alias_symlinks`,
`historical_files`, and `inflight_globs` (root working records such as
`PROPOSAL-*.md`).

Then wire it into whatever gates your changes:

```sh
docs-doctor --repo . --json  # exit 0 clean or degraded, 1 failed, 2 exec error
```

`failed` and `execution_error` should block a landing. `degraded` is allowed
only when every finding is accounted for, and is never reported as clean.

## Start here

1. Read `AGENTS.md`; `CLAUDE.md` resolves to the same contract.
2. Run `br ready`, then `br show <id>` and claim only ready work. Jot tracker
   IDs use the `jot-` prefix.
3. Read `docs/INDEX.md` for the authoritative corpus map and
   `docs/history/INDEX.md` for archived-record coordinates.
4. Run the docs-doctor command in `AGENTS.md` before landing a change.
