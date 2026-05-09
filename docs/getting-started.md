# Getting started

Five short steps to get from "no Overleaf integration" to "synced".

## 1. Install

The recommended way uses [pipx](https://pipx.pypa.io/) so the tool gets its own isolated environment:

```bash
pipx install claude-to-overleaf
```

Or with regular pip:

```bash
pip install --user claude-to-overleaf
```

Either way, you should now have a `claude-to-overleaf` command on your `PATH`:

```bash
claude-to-overleaf --help
```

??? note "For development"
    Clone the repo and `pip install -e .` from inside it. Tests run with `python -m unittest discover -s tests`.

## 1a. Install the Claude Code skill (optional, recommended)

If you use Claude Code, run this once:

```bash
claude-to-overleaf install-skill
```

It drops a skill file at `~/.claude/skills/claude-to-overleaf/SKILL.md`. Restart Claude Code and from then on, Claude knows to use this tool whenever you say things like *"sync to overleaf"* or *"push my latex to overleaf"* — including the right way to handle "Overleaf has commits ahead" warnings (cherry-pick first, never `--force` without asking).

[:octicons-arrow-right-24: More on the Claude Code integration](using-with-claude-code.md)

## 2. Grab your Overleaf credentials

Two things from Overleaf:

| What | Where to find it |
|---|---|
| **Project ID** | Open your project → Menu (top left) → Sync → Git. URL looks like `https://git.overleaf.com/<long-hex-id>`. The hex string is the project id. |
| **Access token** | Account Settings → Git Integration → "Generate token". Starts with `olp_`. **Overleaf only shows it once — copy immediately.** |

!!! danger "Treat the token like a password"
    Anyone with it can read and write your project. Never paste it into chat, screenshots, or a tracked file. If it leaks, revoke it on Overleaf and generate a new one.

## 3. Make a `.env`

The tool reads from two `.env` files plus environment variables. Highest precedence first:

1. Environment variables
2. `./.env` (current working directory)
3. `~/.config/claude-to-overleaf/.env` (global)

The two files are **merged** — CWD overrides per key, the global file is the base layer. For a single-project setup, just put everything in one file. For multiple projects, see the [Reference](reference.md#multiple-overleaf-projects).

For a global setup:

```bash
mkdir -p ~/.config/claude-to-overleaf
curl -fsSL https://raw.githubusercontent.com/srezaeeucr/claude-to-overleaf/main/.env.example \
  > ~/.config/claude-to-overleaf/.env
```

Then open it and fill in:

```bash
OVERLEAF_TOKEN=olp_your_real_token
OVERLEAF_PROJECT_ID=abcdef1234567890...
REPO_PATH=/absolute/path/to/your/latex/repo
```

The repo at `REPO_PATH` should have your `.tex` file at the **root** (e.g. `thesis.tex`, not `thesis/main.tex`). For per-project configs, drop a `.env` next to where you run the command instead.

## 4. Wire it up

```bash
claude-to-overleaf setup
```

This adds an `overleaf` remote to your LaTeX repo and runs a test fetch. Seeing `OK — 'overleaf' is reachable.` means you're done.

## 5. Sync

Edit. Commit. Push to GitHub as usual. Then either:

=== "With Claude Code"

    !!! quote ""
        *"sync to overleaf"*

    Claude runs the tool, handles the safety checks, and reports back.

=== "From the terminal"

    ```bash
    claude-to-overleaf sync
    ```

Refresh Overleaf in the browser — the changes are there.

[:octicons-arrow-right-24: Day-to-day workflow](reference.md#day-to-day-workflow)
