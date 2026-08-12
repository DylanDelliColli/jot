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

Jot does not:

- write or refactor product source code;
- replace `br` as the work tracker;
- orchestrate agents or execute their product work; or
- become a general-purpose knowledge database.

## Kill criteria

Stop or pivot rather than add machinery if real use shows that:

- `jot-review` is not being used;
- Jot's captured output becomes another markdown-soup backlog; or
- agents routinely ignore the documentation structure enforced by docs-doctor.

These are product-level failures to address from observed evidence, not
invitations to build speculative safeguards.
