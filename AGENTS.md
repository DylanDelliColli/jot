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
change. Run docs-doctor before a push, at phase gates, and at session close.
Until the tool migrates here, use:

```sh
python3 /home/ddc/dev-environment/abacus/tools/docs_doctor.py \
  --repo /home/ddc/dev-environment/jot --json
```

After migration, the equivalent repository-local command is authoritative.
`failed` and `execution_error` block landing. A `degraded` result is allowed
only when every finding is named in the validation ledger; never call it
clean.

## Cross-lineage review lane

**Proposed named arrangement - pending operator confirmation:** the Codex build
lane in this repository pairs with the Claude adversarial-review lane in tmux
pane `w1H:p2`, whose working directory is
`/home/ddc/dev-environment/jot`. The operator must confirm or replace this
assignment before it is treated as active; do not silently substitute a
self-review.

Once confirmed, the two lineages build and adversarially review each other's
work. They do not edit the same file concurrently. Cross-review is mandatory
for product seam changes, phase gates, and especially the stateful on-disk
queue, crash-safety, reconciliation, and concurrent-drain work in `jot` and
`jot-review`. Findings and adjudications live in the cycle's single root review
file; an aligned review is archived through the transition guard above.

Review ceremony is bounded by defects found and decisions resolved. Two
consecutive rounds that produce only refinements end the review cycle and send
the nearest real deliverable forward.
