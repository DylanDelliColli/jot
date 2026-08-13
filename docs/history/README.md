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
