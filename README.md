<!--
```doc-meta
role: contract
lifecycle: active
```
-->

<h1 align="center">jot</h1>

<p align="center">
  <strong>From agent findings to actionable tasks.</strong><br>
  Structured capture, review, and reusable memory for development.
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
  <a href="#memory">Memory</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

Jot lets agents quickly record structured findings while executing tasks or
having conversations with the operator. Later, the agent uses `jot-review` to
parse those notes, check the evidence, and turn relevant findings into actionable
tasks for the operator to approve. The optional memory flow captures lessons
separately, lets an agent study them without operator input, and retrieves
only the cleaned results.

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

The first words `list`, `dir`, `memory`, `study`, and `remember` select commands.
For generated or unquoted discovery text, use `jot -- "<observation>"` so a
finding such as "remember to update the docs" is captured literally. Put any
evidence flags before `--`, for example:

```sh
jot --file README.md -- "remember to update the docs before release"
```

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
Use jot -- "<observation>" to capture findings for later follow-up during execution and our conversations.
Include --file, --symptom, --repro, and --why before the -- separator when useful.
Write notes with enough context to become actionable tasks during review.
Only run jot-review when I ask. Get my approval before creating tasks or editing docs.
```

The agent needs `jot` on its PATH and permission to write to the repository's
Git directory.

</details>

## Memory

Memory is optional and works without a tracker, agent name, or orchestration
framework. Use the existing discovery queue for findings that may become work;
use memory for knowledge worth carrying into a future session.

```sh
jot memory "Restoring saved state did not refresh the next recommendation"
jot study
jot remember "restoring"
```

`jot study` prints the bundled study instructions and the current rough notes
and cleaned bank. The agent running the command then performs the study: it
checks useful claims, saves or revises lessons, and deletes notes it has
consumed. Jot itself does not launch a model. A human running the command sees
the same material and can use the record operations directly.

`remember` returns **only cleaned memories**, never rough notes. With no query,
it lists the selected bank; with a query, it performs a case-insensitive text
search. Notes do not become memories just because they were captured.

| Command | What it does |
| --- | --- |
| `jot memory "rough observation"` | Capture a rough memory note (`--add` is optional) |
| `jot memory --list` | Read rough notes |
| `jot study` | Start an agent-directed study using the bundled instructions |
| `jot study --json` | Read scoped rough notes and cleaned memories as JSON |
| `jot study --save "useful lesson"` | Save a cleaned memory after studying |
| `jot study --save "revised lesson" --id ID` | Replace an existing memory's text |
| `jot memory --delete ID` | Delete a rough note |
| `jot study --delete ID` | Delete a cleaned memory |
| `jot remember "search text"` | Retrieve matching cleaned memories |

Memory commands support `--json` and `--help`. Records include IDs, timestamps,
text, and repository context. Save operations return the resulting record or
its ID. Revision preserves the ID and creation time and updates the text,
repository context, and `updated_at`. Delete acts on one record in the selected
scope; there is no memory archive or undo command. Save useful lessons before
deleting the rough notes they replace.

### Optional agent scopes

Memory selects `--agent NAME` first, otherwise `JOT_AGENT`, otherwise the
repository-general collection. An agent scope selects exactly that agent's
records. Identity affects memory only; ordinary `jot "finding"`, `list`, `dir`,
and operator-directed `jot-review` keep their existing behavior.

```sh
JOT_AGENT=a jot memory "A lesson to study later"
JOT_AGENT=a jot study
JOT_AGENT=a jot remember "lesson"
jot remember --agent b "lesson"
jot remember --agent ""          # repository-general, even with JOT_AGENT set
jot remember --all-agents        # every scope in this repository
```

Set `JOT_AGENT` in an agent's launch environment to omit the flag during normal
work. `--agent ""` also selects general scope for writes. `--all-agents` is a
read option for `remember`, `memory --list`, and `study`; writes and deletes
always select one scope. Attribution is a convention, not an access-control
boundary. Each repository has its own records, shared by its linked worktrees.

The bundled `skills/jot-study/SKILL.md` is the sole source of study instructions.
`jot study` loads it directly from the Jot checkout; no additional skill install
is required for that entrypoint. For discovery as `/jot-study` in your agent,
optionally link `skills/jot-study` using the same installation pattern as
`jot-review` above. Study maintains memories autonomously. It does not run
`jot-review`, create tasks, or edit documentation.

## Where notes live

Notes are plain JSON files under `<git-common-dir>/jot/pending/` — usually
`.git/jot/pending/`. They're stored locally, outside the tracked source tree,
and aren't included in Git pushes.

Worktrees of the same clone share a queue. Separate clones and machines have
separate queues. Use `jot dir` to find yours.

Memory is stored alongside the queue in `<git-common-dir>/jot/memory/rough/`
and `bank/`, one JSON file per record. Memory survives agent resets and linked
worktree teardown. It remains local to the clone: Git pushes do not back it up,
and deleting the clone also deletes its memory.

If a memory JSON record is malformed, reads of that collection stop and name
the damaged file, including reads of other agent scopes in that collection.
Inspect the exact file reported and repair its JSON, or remove that file if it
is no longer useful. CLI deletion also validates a record's identity and scope,
so it cannot delete an unreadable record for you. This differs from discovery
listing, which continues with an unreadable-note placeholder.

## Contributing

Found a problem? [Open an issue](https://github.com/DylanDelliColli/jot/issues)
with what happened, what you expected, and how to reproduce it.

For development, start with [AGENTS.md](AGENTS.md). Run the capture suite from
the checkout root:

```sh
python3 tools/test_jot.py
python3 tools/test_memory.py
```

The suite uses real filesystems and Git repositories, including linked worktrees.
