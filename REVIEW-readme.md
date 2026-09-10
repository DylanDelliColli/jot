```doc-meta
role: working
lifecycle: active
```

# Human-facing README review

Task: `jot-f7f`. Baseline: `7abdd5800f113260b9daa0fa2e2f97ab90ba4f4a`.
Reviewed README SHA-256: `349ba9b252ae0dac1be0a4499dc5e1672b372877522be4db493970980071188b`.

First-ready preview: 2026-09-10T20:09:50.462700Z (original passing preview's
filesystem timestamp). Repaired installation smoke: 2026-09-10T20:12:39.067235+00:00.
Independent acceptance observed: 2026-09-10T20:14:47Z. No code was changed.

## Scope and review identity

The operator requested a README that lets a human quickly understand Jot's
value and install it, with styling common to GitHub OSS projects. The README
now has a centered introduction, factual badges, section navigation, a capture
example, install steps, a command table, optional agent-review setup, local
storage details and contribution links. Internal task/spec history has left
the reader path. No tagging feature, installer or licensing change was added.

The required metadata is preserved inside an opening HTML comment, with a
narrow README exception in AGENTS.md. The previous bytes of every changed
governed document were verified against HEAD and their archive coordinates
recorded before editing.

The former named Claude pane is absent. A fresh Claude reviewer ran in Herdr
`w84:pA`, named `jot-readme-review`, session
`a3b35608-73d0-4276-90a6-c935fda082de`. Its tools were Read, Glob and Grep;
it made no edits or shell calls. No model or effort override was passed.

## Findings and repair

| Finding or evidence request | Resolution |
| --- | --- |
| A Claude skills directory that already points to the shared directory makes plain ln -s create a nested link in the checkout. | Reproduced using real temporary directories and symlinks. The docs now use ln -sn, say to inspect existing destinations, and skip redundant Claude setup. The repaired command refuses the existing symlink without modifying its target. |
| The word issues could be read as GitHub issues. | The README identifies the local br tracker and defines its issues as beads. |
| Python 3 alone understates the API floor. | Prerequisite and badge say 3.7 or newer; the source uses subprocess capture_output/text and parses with the 3.7 grammar. |
| PATH setup can select a different system jot. | The README specifies PATH precedence and includes command -v jot before the help check. |
| Executable mode must hold in a fresh clone. | The public HTTPS-clone smoke executed the linked command successfully and checked its executable bit. |

Tracker prerequisites now precede the first review prompt; discards are listed
so the reader can rescue them. The reviewer re-read the repaired README and
accepted it, confirming all five first-pass items were resolved with no new
factual or installation problems. Its remaining wording suggestion (bead versus
issue after the definition) was optional and does not warrant another round.

## Validation

- Executed the documented install from a fresh public HTTPS clone, with only
  home paths redirected to task-owned files. Actual HOME, user installation,
  shell startup files and Git configuration were unchanged.
- Installed both shared and Claude skill links. Ran all three capture examples,
  listing and queue-location commands in a separate real Git repository;
  verified note fields and that the queue belonged to that project. Repeated
  after the link-command repair. Final scratch root: `/tmp/jot-f7f-install-o9fq0y0c`.
- Initialized the sample tracker using the installed pinned br 0.1.45. No live
  curation was run. Existing Jot suite passed 25/25.
- GitHub's Markdown API rendered the final source: metadata is hidden, tables
  and the disclosure render, and all relative document links exist. The API
  omits page-level heading anchors; the local preview supplies heading slugs
  to check navigation, rather than changing the README for the test harness.
- Inspected desktop and final mobile screenshots using a named agent-browser
  session. At width 390, document width remained 390. The Install navigation
  landed on its heading, the disclosure opened, and all badge images loaded.
- Public repository and br release links returned HTTP 200. A direct Python
  request to shields.io returned HTTP 403; the actual GitHub-camo images loaded
  successfully in the browser. npm's available-version notice was not acted on.

This was documentation-only work. The actual install/capture path and rendering
were tested; no tests matching prose were added. The reviewer independently
checked content, while command and browser evidence came from the chief.
Screenshots use GitHub-rendered HTML with local preview CSS, not a claim of
pixel-identical GitHub chrome. Execution checks ran on this Linux host.

The skill's conflicting wording about deleting versus moving processed notes
was captured with jot for later operator-directed curation; it was not changed.
The completed review is committed before retirement and remains recoverable
through docs/history/INDEX.md.
