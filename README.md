```doc-meta
role: contract
lifecycle: active
```

# Jot

Jot is the home of reusable documentation governance and durable observation
capture. It is being extracted from its incubation in abacus so that abacus
and other repositories can consume the machinery without owning it.

The repository contains its foundation contract and the `jot` capture command.
Subsequent tracked work will migrate the operator-approved funnel
specification, docs-doctor, probe executor, and their fixtures, and build the
`jot-review` curation skill. Do not infer that a listed product surface is
available until its bead has landed.

The approved funnel specification is a design of record, not a build order.
`jot-met.7` governs the capture MVP: parity with the working sable tools plus
its named cheap improvements, accepted through dogfooding. Richer crash-safety
machinery remains unbuilt unless observed evidence justifies later work.

## Product surfaces

- **docs-doctor** validates document structure, metadata, indexes,
  supersession, probes, tracker citations, and archive reachability.
- **Probe executor** runs the small typed probe DSL through bounded,
  repository-confined operations.
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

## Start here

1. Read `AGENTS.md`; `CLAUDE.md` resolves to the same contract.
2. Run `br ready`, then `br show <id>` and claim only ready work. Jot tracker
   IDs use the `jot-` prefix.
3. Read `docs/README.md` for the authoritative corpus map and
   `docs/history/README.md` for archived-record coordinates.
4. Run the docs-doctor command in `AGENTS.md` before landing a change.
