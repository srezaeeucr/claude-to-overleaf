# claude-to-overleaf

**One prompt to push your LaTeX repo to Overleaf. No web-UI tab-juggling. No copy-paste. No "wait, did I save that?"**

A tiny, zero-dependency Python pipeline you hand to Claude Code. Edit locally in your editor of choice, commit, then say:

> *"sync to overleaf"*

Claude runs the script, handles the safety checks, and your Overleaf project reflects the changes within seconds. (Prefer to run it yourself? It's also a one-liner: `python3 overleaf_sync.py sync` — see Quick start.)

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

- **Prompt-driven** — designed to be invoked by Claude Code (`"sync to overleaf"`); runnable as a CLI too
- **Four subcommands** — `setup`, `status`, `sync`, `pull`
- **Zero `pip install`s** — pure Python 3 stdlib, runs anywhere Python runs
- **Safe by default** — refuses to push when Overleaf is ahead, refuses to push with a dirty working tree
- **`.env`-driven config** — your token never lives in shell history or the LaTeX repo
- **Idempotent setup** — re-run anytime; it'll only update the remote URL if the token rotated
- **Works from anywhere** — point `REPO_PATH` at any LaTeX repo on disk

---

## Quick start

### 1. Clone this repo

```bash
git clone git@github.com:srezaeeucr/claude-to-overleaf.git
cd claude-to-overleaf
```

### 2. Grab your Overleaf credentials

Two things from Overleaf:

| What | Where to find it |
|---|---|
| **Project ID** | Open your project → Menu (top left) → Sync → Git. The URL looks like `https://git.overleaf.com/<long-hex-id>`. The hex string is the project id. |
| **Access token** | Account Settings → Git Integration → "Generate token". Starts with `olp_`. **Overleaf only shows it once — copy immediately.** |

> **Treat the token like a password.** Anyone with it can read and write your project. Never paste it into chat, screenshots, or a tracked file. If it leaks, revoke it on Overleaf and generate a new one.

### 3. Make a `.env`

```bash
cp .env.example .env
```

Open `.env` and fill in:

```bash
OVERLEAF_TOKEN=olp_your_real_token
OVERLEAF_PROJECT_ID=abcdef1234567890...
REPO_PATH=/absolute/path/to/your/latex/repo
```

The repo at `REPO_PATH` should have your `.tex` file at the **root** (e.g. `thesis.tex`, not `thesis/main.tex`).

### 4. Wire it up

```bash
python3 overleaf_sync.py setup
```

Adds an `overleaf` remote to your repo and runs a test fetch. `OK — 'overleaf' is reachable.` means you're done.

### 5. Sync

Edit. Commit. Push to GitHub as usual. Then either:

**With Claude Code:**

> *"sync to overleaf"*

Claude runs the script, handles the safety checks, and reports back.

**Or run it directly:**

```bash
python3 overleaf_sync.py sync
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

Run `python3 overleaf_sync.py --help` for the same info from the CLI.

---

## Config reference

All settings come from `.env` (or environment variables — env vars take precedence over `.env`).

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

Then ask Claude *"sync to overleaf"* — or run `python3 overleaf_sync.py sync` directly.

### Case 2 — someone (or you) edited on Overleaf

`sync` will refuse and tell you exactly what's there. Bring those edits home first:

```bash
python3 overleaf_sync.py pull         # see what's on Overleaf only
cd $REPO_PATH
git cherry-pick <hash>                # bring each one onto local main
python3 overleaf_sync.py sync         # now safe
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
No `.env` file, or that key isn't in it. Re-do Step 3.

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
- One Overleaf project per local repo. To sync against multiple, clone this tool into separate folders with different `.env` files.
- Tested on macOS. Should work on Linux. Windows is unverified.
