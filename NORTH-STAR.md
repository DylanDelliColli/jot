```doc-meta
role: contract
lifecycle: active
```

# Jot North Star

## Thesis

Jot makes repository intelligence clean and efficient. It gives the operator
and agents a disciplined path to capture issues arising during execution,
transform them into actionable tasks and evidence, and maintain structured
documentation instead of accumulating markdown soup.

## Beneficiaries

The operator and their agents use Jot while building and maintaining
repositories. They need accurate, current context with strong coverage so they
can orient quickly and act on trustworthy repository knowledge.

## Success condition

Jot is succeeding when its consuming repositories:

- avoid ad hoc markdown-soup folders;
- update governed documentation as the product evolves;
- capture issues quickly through `jot`;
- regularly curate captured issues through `jot-review`; and
- consistently honor the structure enforced by docs-doctor.

Implementation scope and working rules remain governed by
[AGENTS.md](AGENTS.md) and active `br` beads.

## Non-goals

Scoped to this thesis. Each may be revisited through revise mode once the success condition is met; none is admissible as "future-facing" work before then.

Category boundaries — Jot is not a different product:

1. Writing or refactoring product source code.
2. Replacing `br` as the work tracker.
3. Orchestrating agents or executing their product work.
4. Becoming a general-purpose knowledge database.

Scope boundaries — things Jot could plausibly grow into and will not:

5. **Autonomous promotion.** `jot-review` never mints a bead or lands a document without operator approval. Agents may discard a note; only the operator promotes one. A funnel that can create work by itself is the boundless backlog growth this thesis exists to prevent.

6. **Durability machinery beyond one file per note.** No event identifiers, canonical digests, create-exclusive publish protocols, event folds, two-observation gates, attempt state machines, or crash reconciliation. A pending note lost to a crash costs one re-observation; that is cheaper than the machinery preventing it, and discard is already the default disposition at review.

7. **Cross-machine or cross-checkout synchronisation.** Pending notes live in one repository's git common dir on one machine. They are never pushed and never shared between hosts or people.

8. **A query or index layer over pending notes.** Notes are read at review, then promoted or deleted. Nothing searches, ranks, links, or retains them for later reference.

9. **A canonical documentation structure that repositories must adopt.** docs-doctor enforces the structure a repository *declares* — the enforcement is real, the declaration is the repository's. The shipped default is the maximum; reducing it is commenting lines out of a list.

## Kill criteria

Stop or pivot rather than add machinery if real use shows that:

- `jot-review` is not being used;
- Jot's captured output becomes another markdown-soup backlog; or
- agents routinely ignore the documentation structure enforced by docs-doctor.

These are product-level failures to address from observed evidence, not
invitations to build speculative safeguards.
