---
name: jot-review
description: |
  Curate the pending notes captured by `jot` into beads, documentation
  changes, or nothing. Reads one-JSON-file-per-note from the queue at
  `jot dir`, proposes a disposition for each, and after operator decisions
  files beads via `br create`, applies documentation edits,
  and archives what it processed.
  Use when asked to "review my notes", "/jot-review", "process the jot
  queue", "curate captured notes", or when `jot` says a review is due.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - AskUserQuestion
---

# /jot-review

Curate raw observations captured by `jot` into things that deserve to exist.

## The two rules that shape everything else

**Discard is the default disposition.** A note earns promotion; it does not
earn deletion. For each note the question is "does this deserve to become a
bead or a documentation change?" — and if the answer is not clearly yes, it is
discarded. Capture is cheap so nothing is lost; curation is strict so the
backlog stays a plan instead of a landfill. **A review pass that promotes most
of what it sees has failed.**

**Agents may discard. Only the operator may promote.** You can clear noise on
your own judgement. Nothing becomes a bead or a landed document without the
operator's explicit decision, one note at a time. The asymmetry is deliberate:
the risk being managed is unbounded growth, so the gate belongs on creation,
not on deletion.

## Steps

### 1. Read the queue

```bash
jot dir      # the queue path
jot list     # human-readable listing
```

Read the `*.json` files in that directory directly — one object per file, so
they parse without heuristics. Fields: `id`, `created_at`, `text`, `cwd`,
`branch`, `rev`, and optionally `file`, `symptom`, `repro`, `why`.

Skip any `processed/` subdirectory. If the queue is empty or absent, say so
and stop — do not invent work.

### 2. Ground each note before judging it

A note is a claim made at some past moment. Before proposing anything, check
whether it is still true:

- Does the `file` it names still exist, and does the `symptom` still
  reproduce? A note about code that has since changed is usually a discard.
- Is it already tracked? Check `br list` for an existing bead covering it.
- Was it already fixed? `git log` since `created_at` on the named file.

Say what you checked. A disposition proposed without grounding is a guess.

### 3. Propose a disposition per note

| Disposition | When | What you produce |
|---|---|---|
| **DISCARD** | The default. Stale, already fixed, already tracked, too vague to act on, or simply not worth a bead | One line: which of those, and the evidence |
| **BEAD** | A real defect or a real piece of work, specific enough to act on | A draft bead: title, type, priority, and a description that passes the Fresh Agent Test |
| **DOC** | The corpus is wrong or missing something, and the fix is a documented change rather than work | The exact edit, as old/new text |
| **DISCUSS** | You genuinely cannot tell | The observation, your read, and the question for the operator |

Group the report by disposition, discards first and briefly — they should be
the bulk of it. For each note show its id and `created_at` so the operator can
trace it back.

### 4. Get decisions

Present the report and ask. Use `AskUserQuestion` when there are more than
about five to decide; otherwise ask in one message. **Every BEAD and every DOC
needs an explicit yes.** Discards need no approval, but list them so the
operator can rescue any you got wrong.

### 5. Apply what was approved

**BEAD** — file it:

```bash
br create --title "<title>" --type <type> --priority <n> \
          --description "<text>"
```

`br create` is the one tracker operation Jot wraps, pinned in the jot
repository's `docs/compatibility/` records. If `br` is missing or fails, stop
and tell the operator — do not fall back to writing the bead somewhere else.

**Do not carry the note id onto the bead.** It is tempting — `br create`
takes `--external-ref` and it looks like provenance — but the note is deleted
at the end of this pass, so the reference dangles by construction, and
north-star non-goal 8 forbids retaining notes for later reference at all. The
bead must stand on its own: if it cannot be acted on without its note, the
bead is not finished. Promotion **is** the durability mechanism, which is why
a note can be thrown away the moment its bead exists.

**DOC** — apply the edit, then **run docs-doctor and report the result**:

```bash
docs-doctor --repo . --json
```

If the repository has no `docs-corpus.json`, docs-doctor is not set up there —
say so rather than running `--init` as a side effect of curating a note.

A documentation change that has not been checked is not finished. `failed` or
`execution_error` must be resolved before the pass ends; `degraded` is
acceptable only if every finding is accounted for.

**DISCARD** — no action beyond archiving.

### 6. Archive what you processed

Move every processed note into a `processed/` subdirectory of the queue.
Pending notes are not durable history — they live in the git common dir, are
never pushed, and are expected to clear in bulk at review. Anything that must
survive was promoted in step 5; **that promotion is the durability
mechanism.**

### 7. Report

How many notes reviewed, how many discarded, which beads were filed with their
ids, which documents changed, and the docs-doctor result if any document
changed.

## Honesty rules

- Never promote without an explicit decision. Not "this seems worth filing" —
  an actual yes.
- Never soften a discard into a bead to look productive. A large discard pile
  is the system working.
- If two notes describe the same thing, say so and propose one bead, not two.
- If a note names a file, function, or flag, verify it still exists before
  proposing anything. A bead built on a hallucinated reference wastes a full
  agent cycle.
- If you cannot ground a note, put it in DISCUSS rather than guessing.

## When NOT to use this skill

- **Not for capture.** That is `jot`, and it is meant to be a three-second
  action. Do not review notes one at a time as they arrive.
- **Not automatically.** This runs when the operator invokes it. Nothing
  should trigger it on a schedule, on a hook, or at session end.
