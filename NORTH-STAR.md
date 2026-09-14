```doc-meta
role: contract
lifecycle: active
```

# Jot North Star

## Thesis

Jot makes repository intelligence clean and efficient. It gives the operator
and agents a disciplined path to capture issues arising during execution,
transform them into actionable tasks and evidence, and maintain structured
documentation instead of accumulating markdown soup. Its optional memory
flow turns rough observations into useful JSON lessons that agents can
maintain and recall across sessions, with or without named agent identities.

## Beneficiaries

The operator and their agents use Jot while building and maintaining
repositories. They need accurate, current context with strong coverage so they
can orient quickly and act on trustworthy repository knowledge.

## Success condition

Jot is succeeding when its consuming repositories:

- avoid ad hoc markdown-soup folders;
- update governed documentation as the product evolves;
- capture issues quickly through `jot`; and
- regularly curate captured issues through `jot-review`; and
- retain useful lessons through `jot-study` and retrieve only cleaned
  memories through `jot remember`, without changing discovery review.

Implementation scope and working rules remain governed by
[AGENTS.md](AGENTS.md) and active `br` beads.

## Non-goals

Scoped to this thesis. Each may be revisited through revise mode once the success condition is met; none is admissible as "future-facing" work before then.

Category boundaries — Jot is not a different product:

1. Writing or refactoring product source code.
2. Replacing `br` as the work tracker.
3. Orchestrating agents or executing their product work.
4. Becoming a general-purpose knowledge database unrelated to repository work.

Scope boundaries — things Jot could plausibly grow into and will not:

5. **Autonomous discovery promotion.** `jot-review` never mints a bead or lands a document without operator approval. Agents may discard a note; only the operator promotes one. A funnel that can create work by itself is the boundless backlog growth this thesis exists to prevent. The operator-authorized v1.1.0 memory flow is separate: `jot-study` may save, revise, consolidate, or delete memories without operator input; this never promotes discoveries into tasks or documents.

6. **Durability machinery beyond one file per note.** No event identifiers, canonical digests, create-exclusive publish protocols, event folds, two-observation gates, attempt state machines, or crash reconciliation. A pending note lost to a crash costs one re-observation; that is cheaper than the machinery preventing it, and discard is already the default disposition at review.

7. **Cross-machine or cross-checkout synchronisation.** Discovery notes and memory records live in one repository's git common dir on one machine. They are never pushed and never shared between hosts or people.

8. **A query or index layer over pending discovery notes.** Discoveries are read at review, then promoted or deleted. Memory has separate rough and cleaned collections. `remember` searches only cleaned records; memory deletion applies to either collection. No indexing or ranking is required for v1.1.0.

9. **Enforcing a documentation schema.** Consuming repositories own their documentation structure and validation conventions.

## Kill criteria

Stop or pivot rather than add machinery if real use shows that:

- `jot-review` is not being used; or
- Jot's captured output becomes another markdown-soup backlog.

These are product-level failures to address from observed evidence, not
invitations to build speculative safeguards.
