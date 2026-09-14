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
| REVIEW-docs-doctor-removal.md | 0a7d48154b5c0e47981c6683ac77b36d2a9ef220 | 31e4f9a2954ec36ca4db53616fca2bf6852341cc | Accepted Claude cross-lineage review of jot-310; no removal defect remained. |
| docs/INDEX.md | 0a7d48154b5c0e47981c6683ac77b36d2a9ef220 | ffdf3ee25890602fccaca9580e1dd363a004de77 | Index state before archiving the accepted jot-310 review. |
| docs/history/INDEX.md | 0a7d48154b5c0e47981c6683ac77b36d2a9ef220 | d4e7eaad68da3fb871e8b9cf6376bbed1c88034c | Index state before archiving the accepted jot-310 review. |
| README.md | 7abdd5800f113260b9daa0fa2e2f97ab90ba4f4a | 66449b2af4f5739d949ac64a3a14f132f6b59141 | State before the human-facing README rewrite in jot-f7f. |
| AGENTS.md | 7abdd5800f113260b9daa0fa2e2f97ab90ba4f4a | dab28cb972dc0565d800b288f21d8aa5edd28a0c | State before the human-facing README rewrite in jot-f7f. |
| docs/INDEX.md | 7abdd5800f113260b9daa0fa2e2f97ab90ba4f4a | 40c26c788e4f877c85c7db1f527a8fc841255cee | State before the human-facing README rewrite in jot-f7f. |
| docs/history/INDEX.md | 7abdd5800f113260b9daa0fa2e2f97ab90ba4f4a | 90286a0165b2fbbc47785c1e03481ddf0b787f81 | State before the human-facing README rewrite in jot-f7f. |
| REVIEW-readme.md | 8dae673a1a35b81713da43991c8e634f550155dd | 68023305910cd0518cf0ea942d321317a134fa2c | Accepted Claude review of the GitHub README, with installation and rendering evidence for jot-f7f. |
| docs/INDEX.md | 8dae673a1a35b81713da43991c8e634f550155dd | 8297ce5018060449bca21dd199f74c9f344e21cb | Index state before archiving the accepted jot-f7f review. |
| docs/history/INDEX.md | 8dae673a1a35b81713da43991c8e634f550155dd | c00496287bedc935e8a9552d72eaebfb8dd63f11 | Index state before archiving the accepted jot-f7f review. |
| README.md | 339772812a83ff40d656f85b085d1916a0526bc6 | b88db219703d62637b2c101fba77df178997e0df | State before the operator-corrected agentic-development framing in jot-f7f. |
| docs/history/INDEX.md | 339772812a83ff40d656f85b085d1916a0526bc6 | 118942de9da282194a79cbcff6404c557b5b8f4a | State before the operator-corrected agentic-development framing in jot-f7f. |
| AGENTS.md | 47693ce8eff9e74cee72439b9bf3be2bee601230 | 7c4bef6faee253f1cf7e59a30a4d72577a76460e | State before the authorized v1.1.0 memory extension in jot-6ab. |
| NORTH-STAR.md | 47693ce8eff9e74cee72439b9bf3be2bee601230 | d9461941376cdf089b764521be7172176034a5d1 | State before the authorized v1.1.0 memory extension in jot-6ab. |
| README.md | 47693ce8eff9e74cee72439b9bf3be2bee601230 | e9dd6ae875bd0f16cb0b0383503cba94e2e586a2 | State before the authorized v1.1.0 memory extension in jot-6ab. |
| docs/INDEX.md | 47693ce8eff9e74cee72439b9bf3be2bee601230 | 40c26c788e4f877c85c7db1f527a8fc841255cee | State before the authorized v1.1.0 memory extension in jot-6ab. |
| docs/history/INDEX.md | 47693ce8eff9e74cee72439b9bf3be2bee601230 | 0209261a8f8628a12d1de2edda33e71492a1f56a | State before the authorized v1.1.0 memory extension in jot-6ab. |
| README.md | d105072e8ccdcded7c1373470cca0d3b52ae66e9 | fe2608fda203d0cc1bfa1b77b18a656185d23dd6 | Development candidate before final v1.1 review dispositions in jot-6ab; joins main on feature merge. |
| REVIEW-v1.1.md | d105072e8ccdcded7c1373470cca0d3b52ae66e9 | 7b7547539a8e97adc5731f86d94718c30c8dc987 | Development candidate before final v1.1 review dispositions in jot-6ab; joins main on feature merge. |
| docs/history/INDEX.md | d105072e8ccdcded7c1373470cca0d3b52ae66e9 | e8bcf95a648ac3e36347714f32a53ab9a5e24084 | Development candidate before final v1.1 review dispositions in jot-6ab; joins main on feature merge. |
