```doc-meta
role: working
lifecycle: active
```

# docs-doctor removal review

Task: `jot-310`. Baseline: `acbd673d6b7f51919434e08171d71e6b296cfcda`.
First-ready candidate recorded at 2026-09-10T13:53Z. Review result observed
at 2026-09-10T13:59:29+00:00. No runtime product repair was required.

## Scope and review identity

The operator asked to remove docs-doctor from this repository and then discuss
new Jot features. The candidate removes the implementation, fixtures, manifest,
setup instructions, workflow gate and review-skill dependency. Capture and
operator-gated curation remain the product. Consumer checkouts and shared host
launchers are outside this change.

The August named pane `w1H:p2` no longer exists. The chief disclosed this and
used a fresh Claude reviewer, `jot-removal-review`, in Herdr `w98:p2`, session
`607bc0c1-70a0-4ccb-bd87-4a712febf154`. No model or effort override was passed.
The reviewer had read-only tools and made no file or tracker edits.

## Independent result

Claude accepted the removal with two mechanical items before commit:

1. The reviewer questioned archive rows for documents that remain in the tree,
   suggesting retaining only the deleted manifest row unless the literal
   transition-guard interpretation was confirmed.
2. The review file already named in the documentation index must exist with
   a `doc-meta` block when committed.

The reviewer independently ran the Jot suite: 25 passed, 0 failed. It found no
executable or active workflow dependency on docs-doctor in the retained tools,
skill or contracts. It verified the seven added archive coordinates and mainline
reachability, the installed skill aliases, the tracker retirements and backup
ignore. The DOC step now follows the receiving repository's instructions.

## Chief adjudication

Item 1 is rejected. The existing contract explicitly applies the transition
guard to **every overwrite or deletion** of a governed document or working
record, and requires a pointer row when overwriting or deleting. Each original
file was tracked, byte-identical to HEAD, and already committed on main before
editing. Historical omissions do not override that instruction. All rows stay.

Item 2 is satisfied by this record and its index entry. The completed review
will be committed, then archived and removed in a later commit with its exact
commit and blob coordinate. The archive/index checks will be rerun afterward.

Optional terminology refinements in the documentation index and NORTH-STAR are
not needed for removal. The stale named review pane was captured with `jot` for
later operator-directed handling.

The reviewer confirmed the adjudication: "no removal defect remains" and
"accepted for commit as integrated." Acceptance observed at
2026-09-10T13:59:55Z. No product change or additional test run followed.

## Validation and limitations

Before removal, the real repository's docs-doctor result was clean and its
fixture suite passed 116 checks. The first sandboxed fixture run failed because
Unix-socket binding was denied; it passed after the operator enabled full access.
The chief's retained Jot suite passed all 25 checks before and after removal.
Skill-creator quick validation passed. The installed `jot` captured a real
tracker diagnostic and listed it alongside the existing queue; no live curation
was invoked. No wording-match or deleted-file tests were introduced for this
removal-only change.

The reviewer could not run `br --version` under its allowed-tool policy; the
chief directly verified the installed pinned binary as `br 0.1.45`. The default
host binary expects schema 17 and cannot open this schema-5 tracker. The pinned
binary restored access; its repair preserved all 20 original issues. Ordinary
writes cause its stale-cache diagnostic to return, so that behavior was captured
instead of repeatedly rebuilding the database. Recovery backups remain local
under `.beads/.br_recovery/`, ignored by Git. See `jot-udf`.

The host symlink `~/.local/bin/docs-doctor` still points to the removed source
and is now dangling. This consequence was disclosed and captured; no consumer
checkout or shared installation was changed. The installed `jot-review` skill
resolves to this checkout and therefore already uses the revised DOC step.

The original tracker descriptions and dated compatibility evidence remain
intact. `jot-waa` and `jot-m3h` were closed as retired; independent citation and
documentation-coordination work was left alone.
