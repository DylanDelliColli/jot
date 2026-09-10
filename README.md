<!--
```doc-meta
role: contract
lifecycle: active
```
-->

<h1 align="center">jot</h1>

<p align="center">
  <strong>From agent findings to actionable tasks.</strong><br>
  Structured capture and review for agentic development.
</p>

<p align="center">
  <a href="#install"><img src="https://img.shields.io/badge/Python-3.7%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.7 or newer"></a>
  <a href="#install"><img src="https://img.shields.io/badge/dependencies-standard_library-486B53" alt="Standard library only"></a>
  <a href="#where-notes-live"><img src="https://img.shields.io/badge/Git-worktree_aware-F05032?logo=git&amp;logoColor=white" alt="Git worktree aware"></a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#review-with-your-agent">Agent review</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

Jot lets agents quickly record structured findings while executing tasks or
having conversations with the operator. Later, the agent uses `jot-review` to
parse those notes, check the evidence, and turn relevant findings into actionable
tasks for the operator to approve.

An agent can capture a finding in one command:

```sh
jot "The setup guide references a removed command" --file README.md
```

**Agent findings → structured Jot notes → review → actionable tasks.**

- **Structured for agents to parse.** Each note is a JSON record. Jot captures
  the time, branch, commit, and working directory automatically.
- **Evidence stays with the finding.** The agent can include the affected file,
  symptom, reproduction steps, and why the finding matters.
- **Tasks another agent can act on.** During review, the agent checks findings
  and drafts tasks with the context needed to pick them up later. The operator
  approves what becomes work.

## Install

You'll need **Python 3.7 or newer**, **Git**, and a shell on Linux, macOS, or WSL.
The capture command uses only the Python standard library. Install it below,
then [set up the review skill](#review-with-your-agent) for your agent.

```sh
git clone https://github.com/DylanDelliColli/jot.git
cd jot

mkdir -p "$HOME/.local/bin"
ln -sn "$PWD/tools/jot.py" "$HOME/.local/bin/jot"
export PATH="$HOME/.local/bin:$PATH"

command -v jot
jot --help
```

Add the `export PATH` line to your shell's startup file, such as `~/.zshrc` or
`~/.bashrc`. Keep `~/.local/bin` ahead of system directories on PATH;
`command -v jot` should show the link you just installed. Keep the Jot
checkout in place: the installed command links to its files.

These steps are for a first install. If a destination already exists, inspect
it before replacing it. To update an existing installation, run
`git pull --ff-only` from your Jot checkout.

## Usage

Agents run `jot` from the Git repository they are working in. During execution,
a quick finding can be captured as:

```sh
jot "The setup guide references a removed command"
```

For a finding that needs more context, the agent can record supporting evidence:

```sh
jot "The setup guide references a removed command" \
  --file README.md \
  --symptom "The documented setup command is not found" \
  --repro "Follow the Quick start section from a fresh clone" \
  --why "New contributors cannot finish setup"
```

Findings from conversations with the operator use the same format:

```sh
jot "The operator needs exports to include archived projects" \
  --why "Monthly reporting must account for completed work"
```

| Command | What it does |
| --- | --- |
| `jot "a finding to follow up"` | Save a structured finding in this repository |
| `jot list` | Show pending notes, oldest first |
| `jot dir` | Print the queue's filesystem path |
| `jot --help` | Show capture options |

All four context flags are optional. At 20 pending notes, Jot suggests a review;
capture keeps working and no review starts automatically.

## Review with your agent

`jot-review` is the review stage of the workflow, provided as a skill for
**Codex** and **Claude Code**. When the operator requests a review, the agent
reads the structured notes, checks each finding against the current repository,
and develops the findings worth pursuing into actionable tasks.

### Install the skill

From your Jot checkout, link the skill into the shared skills directory.
If a `jot-review` destination already exists, inspect it before replacing it:

```sh
mkdir -p "$HOME/.agents/skills"
ln -sn "$PWD/skills/jot-review" "$HOME/.agents/skills/jot-review"
```

Codex reads that directory directly. For Claude Code, also add its discovery
link. Skip this step if `~/.claude/skills` already points to `~/.agents/skills`.

```sh
mkdir -p "$HOME/.claude/skills"
ln -sn "$HOME/.agents/skills/jot-review" "$HOME/.claude/skills/jot-review"
```

The skill checks existing work and creates approved issues in your project's
local [Beads Rust (`br`)](https://github.com/Dicklesworthstone/beads_rust)
tracker. These issues are called **beads**. Install and initialize `br` in the
repository you plan to review. Jot's recorded compatible version is
[0.1.45](https://github.com/Dicklesworthstone/beads_rust/releases/tag/v0.1.45);
see the [compatibility record](docs/compatibility/2026-08-13-br-pin.md).
For a project that does not yet use `br`, run `br init` there after installing it.
Capture and listing work without `br`.

Start a new agent session in the repository whose notes you want to review
and ask it to use the `jot-review` skill:

```text
Use jot-review to turn the pending findings into actionable tasks for me to approve.
```

### What a review does

1. **Checks the evidence.** Is the observation still true? Is it already fixed
   or tracked?
2. **Drafts actionable tasks.** Findings that warrant work become proposed
   beads with enough context for another agent to act on. The agent can also
   propose a documentation edit, discard stale notes, or discuss an open question.
3. **Applies your decisions.** New beads and documentation edits require your
   approval. The agent may discard noise on its own and lists its discards
   so you can rescue anything worth keeping.
4. **Clears the pending queue.** Processed notes move into a `processed/`
   subdirectory. The useful context now lives in the approved task or document.

Review runs when you ask. The default is to discard observations that no longer
justify action, so capturing freely doesn't commit you to an ever-growing backlog.

<details>
<summary><strong>Give your agent capture instructions</strong></summary>

Add a short instruction to your project's `AGENTS.md` or `CLAUDE.md`:

```text
Use jot to capture findings for later follow-up during execution and our conversations.
Include --file, --symptom, --repro, and --why when useful.
Write notes with enough context to become actionable tasks during review.
Only run jot-review when I ask. Get my approval before creating tasks or editing docs.
```

The agent needs `jot` on its PATH and permission to write to the repository's
Git directory.

</details>

## Where notes live

Notes are plain JSON files under `<git-common-dir>/jot/pending/` — usually
`.git/jot/pending/`. They're stored locally, outside the tracked source tree,
and aren't included in Git pushes.

Worktrees of the same clone share a queue. Separate clones and machines have
separate queues. Use `jot dir` to find yours.

## Contributing

Found a problem? [Open an issue](https://github.com/DylanDelliColli/jot/issues)
with what happened, what you expected, and how to reproduce it.

For development, start with [AGENTS.md](AGENTS.md). Run the capture suite from
the checkout root:

```sh
python3 tools/test_jot.py
```

The suite uses real filesystems and Git repositories, including linked worktrees.
