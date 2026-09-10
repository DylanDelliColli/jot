```doc-meta
role: working
lifecycle: active
```

# Archive pointer index

Archived working records live as immutable Git objects in commits reachable
from `refs/heads/main`. Recover a row with `git show <commit>:<path>`. Rows are
unique by `(path, commit)`, and `source_blob` is the exact blob stored at that
coordinate. This index is intentionally the only file under `docs/history/`.

| path | commit | source_blob | claim |
|---|---|---|---|
| SHIFT-REPORT-2026-08-13-CLAUDE.md | e5a00cebe1ddc36e83688285ad52b31b320835d2 | f0614dc93024b28562bfc14ea51e6354cbba757b | Claude-lane shift report for the `jot-met.7.1` capture landing. Carries the read-first authority map, decisions D1-D4, hazards H1-H6, the incoming boot sequence, and the verification ledger current at the 2026-08-13 handoff. Its section 9 records two post-landing defects: the dead docs-doctor path corrected by `jot-d9m`, and the `jot-met.3` rename impact. Retired from the tree once its handoff was consumed. |
| AGENTS.md | acbd673d6b7f51919434e08171d71e6b296cfcda | a37591987d417eb12b9a810e8f40d14c0b66c911 | State before docs-doctor removal in jot-310. |
| README.md | acbd673d6b7f51919434e08171d71e6b296cfcda | 6c077a5c4dd7e3e3562da173dc7958431feb191e | State before docs-doctor removal in jot-310. |
| NORTH-STAR.md | acbd673d6b7f51919434e08171d71e6b296cfcda | b243e3f28b6bb9e889a26464b8360ffd63dc268b | State before docs-doctor removal in jot-310. |
| docs/INDEX.md | acbd673d6b7f51919434e08171d71e6b296cfcda | 10726baf429feaed9e72506e6bb3f40c348e32ff | State before docs-doctor removal in jot-310. |
| docs/history/INDEX.md | acbd673d6b7f51919434e08171d71e6b296cfcda | 119afdc3407effe629c831d3d23d8580ba00396b | State before docs-doctor removal in jot-310. |
| skills/jot-review/SKILL.md | acbd673d6b7f51919434e08171d71e6b296cfcda | a7625aad6155fe453178e4394d9eeb3a4f630e19 | State before docs-doctor removal in jot-310. |
| docs-corpus.json | acbd673d6b7f51919434e08171d71e6b296cfcda | e6634cf7e022d58d31e94245fcfe5b2c3ccea22f | State before docs-doctor removal in jot-310. |
