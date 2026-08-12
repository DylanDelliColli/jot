```doc-meta
role: contract
lifecycle: active
```

# Jot

Jot is the home of reusable documentation governance and durable observation
capture. It is being extracted from its incubation in abacus so that abacus
and other repositories can consume the machinery without owning it.

The repository currently contains its foundation contract. Subsequent tracked
work will migrate the operator-approved funnel specification, docs-doctor,
probe executor, and their fixtures before building the still-unimplemented
`jot` and `jot-review` capture funnel. Do not infer that a listed product
surface is available until its bead has landed.

The approved funnel specification is a design of record, not a build order.
`jot-met.7` governs the capture MVP: parity with the working sable tools plus
its named cheap improvements, accepted through dogfooding. Richer crash-safety
machinery remains unbuilt unless observed evidence justifies later work.

## Product surfaces

- **docs-doctor** validates document structure, metadata, indexes,
  supersession, probes, tracker citations, and archive reachability.
- **Probe executor** runs the small typed probe DSL through bounded,
  repository-confined operations.
- **jot** durably captures ownerless observations in an on-disk event queue.
- **jot-review** provides operator-gated curation into tracker or documentation
  outcomes and runs docs-doctor after documentation changes.

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
