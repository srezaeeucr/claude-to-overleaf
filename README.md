# claude-to-overleaf

[![CI](https://github.com/srezaeeucr/claude-to-overleaf/actions/workflows/ci.yml/badge.svg)](https://github.com/srezaeeucr/claude-to-overleaf/actions/workflows/ci.yml)
[![Docs](https://github.com/srezaeeucr/claude-to-overleaf/actions/workflows/docs.yml/badge.svg)](https://srezaeeucr.github.io/claude-to-overleaf/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

📖 **Full documentation:** <https://srezaeeucr.github.io/claude-to-overleaf/>

**One prompt to push your LaTeX repo to Overleaf. No web-UI tab-juggling. No copy-paste. No "wait, did I save that?"**

A tiny, zero-dependency Python package that ships with a [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills). Edit locally in your editor of choice, commit, then tell Claude:

> *"sync to overleaf"*

Claude invokes the skill, runs the tool, handles the safety checks, and your Overleaf project reflects the changes within seconds. (No Claude Code? It's also a normal CLI — `claude-to-overleaf sync`.)

---

## Why this exists

Overleaf gives every project a git URL — but actually using it day-to-day means:

- remembering to add a remote
- juggling a token you saw exactly once
- knowing the magic incantation (`commit-tree`, `HEAD^{tree}`, fast-forward push) because Overleaf rejects normal pushes
- *not* blowing away edits made in the Overleaf web editor

This script does all of that for you, and refuses to push when it would silently destroy work.

---

## Features

- **Ships a Claude Code skill** — one command (`claude-to-overleaf install-skill`) drops a skill file into `~/.claude/skills/` so Claude reliably knows when and how to invoke it
- **Prompt-driven by default** — say `"sync to overleaf"` and Claude does the rest, including handling the "Overleaf is ahead" cherry-pick flow
- **Standalone CLI for anyone** — `claude-to-overleaf sync` works without Claude Code
- **Installable as a real package** — `pipx install` it once and the command lives on your PATH
- **Five subcommands** — `setup`, `status`, `sync`, `pull`, `install-skill`
- **Zero runtime dependencies** — pure Python 3 stdlib (3.9+)
- **Safe by default** — refuses to push when Overleaf is ahead, or when the working tree is dirty
- **`.env`-driven config** — your token never lives in shell history or the LaTeX repo
- **Idempotent setup** — re-run anytime; only updates the remote URL if the token rotated
- **Works from anywhere** — point `REPO_PATH` at any LaTeX repo on disk

---

## Quick start

### 1. Install

The recommended way — using [pipx](https://pipx.pypa.io/) so the tool gets its own isolated environment:

```bash
pipx install claude-to-overleaf
```

Or with regular pip:

```bash
pip install --user claude-to-overleaf
```

Either way, you should now have a `claude-to-overleaf` command on your PATH:

```bash
claude-to-overleaf --help
```

(For development: `git clone` the repo and `pip install -e .` from inside it.)

### 1a. Install the Claude Code skill (optional, recommended)

If you use Claude Code, run this once:

```bash
claude-to-overleaf install-skill
```

It drops a skill file at `~/.claude/skills/claude-to-overleaf/SKILL.md`. Restart Claude Code and from then on Claude knows to use this tool whenever you say things like *"sync to overleaf"* or *"push my latex to overleaf"* — including the right way to handle "Overleaf has commits ahead" warnings (cherry-pick first, never `--force` without asking).

### 2. Grab your Overleaf credentials

Two things from Overleaf:

| What | Where to find it |
|---|---|
| **Project ID** | Open your project → Menu (top left) → Sync → Git. The URL looks like `https://git.overleaf.com/<long-hex-id>`. The hex string is the project id. |
| **Access token** | Account Settings → Git Integration → "Generate token". Starts with `olp_`. **Overleaf only shows it once — copy immediately.** |

> **Treat the token like a password.** Anyone with it can read and write your project. Never paste it into chat, screenshots, or a tracked file. If it leaks, revoke it on Overleaf and generate a new one.

### 3. Make a `.env`

The tool looks for `.env` in (in order):

1. Your current working directory
2. `~/.config/claude-to-overleaf/.env`

Pick whichever fits. For a global setup:

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

### 4. Wire it up

```bash
claude-to-overleaf setup
```

Adds an `overleaf` remote to your LaTeX repo and runs a test fetch. `OK — 'overleaf' is reachable.` means you're done.

### 5. Sync

Edit. Commit. Push to GitHub as usual. Then either:

**With Claude Code:**

> *"sync to overleaf"*

Claude runs the tool, handles the safety checks, and reports back.

**Or run it directly:**

```bash
claude-to-overleaf sync
```

Refresh Overleaf in the browser — the changes are there.

---

## Commands

| Command | What it does |
|---|---|
| `setup` | Adds (or updates) the `overleaf` git remote and verifies auth. Idempotent — safe to re-run. |
| `status` | Shows whether local HEAD matches Overleaf. Lists Overleaf-only commits if any. |
| `sync` | Pushes local HEAD's tree to Overleaf. Refuses if Overleaf is ahead, or the working tree is dirty. |
| `sync --force` | Push anyway, overwriting Overleaf-side commits. Use deliberately. |
| `pull` | Lists Overleaf-only commits so you can `git cherry-pick` them. |
| `install-skill` | Installs the bundled Claude Code skill to `~/.claude/skills/claude-to-overleaf/`. |

Run `claude-to-overleaf --help` for the same info from the CLI. (Or `python -m claude_to_overleaf --help` if you'd rather not rely on the entry-point shim.)

---

## Config reference

All settings come from `.env` (or environment variables — env vars take precedence over `.env`).

`.env` is searched for in: the current working directory first, then `~/.config/claude-to-overleaf/.env`.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OVERLEAF_TOKEN` | yes | — | Personal access token (starts with `olp_`) |
| `OVERLEAF_PROJECT_ID` | yes | — | Hex id from the Overleaf git URL |
| `REPO_PATH` | yes | — | Absolute path to the local git repo |
| `OVERLEAF_BRANCH` | no | `master` | Branch name on the Overleaf side |
| `OVERLEAF_REMOTE` | no | `overleaf` | What to call the remote in your repo |

---

## Day-to-day workflow

### Case 1 — you only edited locally

```bash
git add .
git commit -m "..."
git push origin main                  # GitHub
```

Then ask Claude *"sync to overleaf"* — or run `claude-to-overleaf sync` directly.

### Case 2 — someone (or you) edited on Overleaf

`sync` will refuse and tell you exactly what's there. Bring those edits home first:

```bash
claude-to-overleaf pull               # see what's on Overleaf only
cd $REPO_PATH
git cherry-pick <hash>                # bring each one onto local main
claude-to-overleaf sync               # now safe
```

### Case 3 — both sides edited the same file

Same as Case 2, but expect conflicts during cherry-pick. Resolve by hand, then:

```bash
git add <files>
git cherry-pick --continue
```

---

## The one rule

**Don't edit the same file in Overleaf and locally between syncs.**

Pick one editor per file per session, sync, then switch sides. The safety check catches the common version of this mistake, but discipline beats tooling.

---

## Safety nets baked in

- Refuses to push when the working tree has uncommitted changes (Overleaf only sees committed state — uncommitted edits would silently not sync, leaving you confused later)
- Refuses to push when Overleaf has commits the local repo doesn't have (no silent overwrites of web-editor work)
- `.env` is in `.gitignore` so your token can't accidentally land on GitHub
- Token is URL-encoded before being embedded in the remote URL (handles weird characters cleanly)

---

## Troubleshooting

**`error: missing required config: OVERLEAF_TOKEN`**
The tool can't find a `.env` (it looks in CWD then `~/.config/claude-to-overleaf/`) or the key isn't in it. Re-do Step 3.

**`Authentication failed` during `setup`**
Token is wrong, expired, or revoked. Generate a new one in Overleaf, update `.env`, re-run `setup`. Sanity-check the token directly:

```bash
curl -u git:$OVERLEAF_TOKEN -I \
  "https://git.overleaf.com/$OVERLEAF_PROJECT_ID/info/refs?service=git-upload-pack"
```

`HTTP/2 200` = token is valid. `HTTP/2 401` = bad token.

**`error: ... is not a git repo`**
`REPO_PATH` points somewhere without a `.git` directory. Fix the path or `git init` there.

**`WARNING: overleaf/master has N commit(s) not in your local repo`**
Working as designed. Run `pull`, cherry-pick what you want, then `sync` again.

---

## What it does under the hood

`sync` is the textbook Overleaf-git recipe in Python:

1. `git fetch overleaf master`
2. Compare `HEAD^{tree}` to `overleaf/master^{tree}` — exit early if equal
3. `git commit-tree HEAD^{tree} -p overleaf/master -m "Sync from GitHub @<short>"`
4. `git push overleaf <new-commit>:master`

The trick is step 3. Overleaf rejects non-fast-forward pushes, so the script grafts your local tree onto Overleaf's history as a brand-new commit. From Overleaf's perspective, it's a normal forward step — even though your local branch and Overleaf's branch share no recent history.

---

## Limitations

- Assumes your LaTeX project is at the **root** of the repo. If it lives in a subfolder, you'd need `git subtree split` instead — open an issue and we'll add it.
- One Overleaf project per `.env`. To sync multiple, drop a `.env` in each repo's directory (CWD takes precedence over the global one in `~/.config/claude-to-overleaf/`).
- Tested on macOS. Should work on Linux. Windows is unverified.
