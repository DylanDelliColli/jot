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
4. Run the validation command recorded below before landing a change.

## Validation ledger

This table records the validation evidence for the current repository state.
A degraded result is never described as clean; its finding classes must remain
visible until their owning beads land.

| date | scope | command | result | evidence |
|---|---|---|---|---|
| 2026-08-12 | repository foundation | `python3 /home/ddc/dev-environment/abacus/tools/docs_doctor.py --repo /home/ddc/dev-environment/jot --json` | degraded - 2 planned-output references, 0 failed, 0 execution errors | `PROPOSAL-funnel-and-docs-doctor.md` is intentionally absent until `jot-met.2`; findings are on `jot-met` and `jot-met.2` |
| 2026-08-12 | jot capture (`jot-met.7.1`) | `python3 tools/test_jot.py` | 22 passed, 0 failed | real git repos and real filesystem, no mocks; covers linked-worktree resolution and same-second id collision |
| 2026-08-12 | jot capture (`jot-met.7.1`) | `python3 /home/ddc/dev-environment/abacus/tools/docs_doctor.py --repo /home/ddc/dev-environment/jot --json` | degraded - same 2 planned-output references, 0 failed, 0 execution errors | adding `tools/` introduced no new findings; the two degraded rows are unchanged and still owned by `jot-met` and `jot-met.2` |
| 2026-08-13 | stale path correction (`jot-d9m`) | `python3 /home/ddc/dev-environment/abacus-v1/tools/docs_doctor.py --repo /home/ddc/dev-environment/jot --json` | degraded - same 2 planned-output references, 0 failed, 0 execution errors | first run from the corrected path; reproduces the 2026-08-12 baseline exactly, so the rename moved the tool without changing the result |
| 2026-08-13 | north-star non-goals revision (`jot-gtz`) | `python3 /home/ddc/dev-environment/abacus-v1/tools/docs_doctor.py --repo /home/ddc/dev-environment/jot --json` | degraded - same 2 planned-output references, 0 failed, 0 execution errors | the revised `NORTH-STAR.md` introduces no findings of its own; an interim run showed 4 because the tracking bead quoted the unmigrated spec's filename twice, and the reverse-citations check emits one finding per occurrence - the bead was reworded, since the two standing findings owned by `jot-met` and `jot-met.2` are the intended signal that the spec has not migrated |

The two 2026-08-12 rows above name `abacus/tools/docs_doctor.py`. That path no
longer exists: the repository was renamed `abacus-v1` on 2026-08-13. Those rows
are left as written because they record commands actually run on their stated
date, and rewriting a command that was executed would falsify the evidence.
Run the tool at the `abacus-v1` path until `jot-met.3` migrates it here.
