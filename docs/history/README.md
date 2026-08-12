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
