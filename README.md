```doc-meta
role: contract
lifecycle: active
```

# Jot

Jot captures observations during repository work and helps the operator
curate them into actionable tasks, documentation changes, or nothing. It
serves abacus and other repositories without depending on their conventions.

The repository contains both halves of the capture funnel: the `jot`
command and the `jot-review` curation skill.

The approved funnel specification is a design of record, not a build order.
`jot-met.7` governs the capture MVP: parity with the working sable tools plus
its named cheap improvements, accepted through dogfooding. Richer crash-safety
machinery remains unbuilt unless observed evidence justifies later work.

## Product surfaces

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

- **jot-review** curates pending notes into beads, documentation changes, or
  nothing. Documentation edits follow the receiving repository's instructions.
  Landed in `jot-met.7`. Discard is the default disposition and only the
  operator may promote — a pass that promotes most of what it sees has failed.

  ```sh
  ln -s "$PWD/skills/jot-review" ~/.agents/skills/jot-review        # install
  ln -s ../../.agents/skills/jot-review ~/.claude/skills/jot-review
  /jot-review
  ```

  Install into the shared `~/.agents/skills/`, not `~/.claude/skills/`.
  Codex reads the shared directory directly and Claude symlinks into it; a
  skill placed only under `~/.claude/skills/` is invisible to Codex. The
  `allowed-tools` front matter is a Claude construct and constrains nothing
  under Codex, where the sandbox does.

## Verification

Run the capture suite from the repository root:

```sh
python3 tools/test_jot.py
```

The suite uses real filesystems and Git repositories, including linked
worktrees. The review skill is exercised through operator-invoked curation.

## Start here

1. Read `AGENTS.md`; `CLAUDE.md` resolves to the same contract.
2. Run `br ready`, then `br show <id>` and claim only ready work. Jot tracker
   IDs use the `jot-` prefix.
3. Read `docs/INDEX.md` for the documentation map and
   `docs/history/INDEX.md` for archived-record coordinates.
4. Follow the verification requirements in `AGENTS.md` before landing a change.
