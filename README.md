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
  (`docs/README.md` lists exactly the managed corpus), and inflight-residency
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

**Step 1** declares only the classes your repository already has documents
for — it does not pre-authorise genres you are not using, because the point
of the check is that adding a genre later is a deliberate edit. It refuses to
overwrite an existing `docs-corpus.json` without `--force`. If `docs/README.md`
is absent it scaffolds one, with a row per document it found and a `TODO`
claim in each.

**Step 2** reports what remains, and it is normally two things: each document
needs a `doc-meta` block, and each row of `docs/README.md` needs a real claim
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

**Step 3** lists the shipped classes. Declaring one admits its location;
omitting it forbids that location entirely. Everything else in
`docs-corpus.json` is membership — root documents, aliases, module globs, and
which root working-record genres such as `PROPOSAL-*.md` your repository uses.

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
3. Read `docs/README.md` for the authoritative corpus map and
   `docs/history/README.md` for archived-record coordinates.
4. Run the docs-doctor command in `AGENTS.md` before landing a change.
