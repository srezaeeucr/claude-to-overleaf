# Reference

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

## Configuration

Settings are resolved in this order, **highest precedence first**:

1. Environment variables
2. `./.env` (current working directory)
3. `~/.config/claude-to-overleaf/.env` (global)

The two `.env` files are **merged** — values in CWD `.env` override only the keys they define. The global file is the base layer. So you can keep one shared `OVERLEAF_TOKEN` in the global file and just put `OVERLEAF_PROJECT_ID` in each repo's local `.env` for multi-project setups.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OVERLEAF_TOKEN` | yes | — | Personal access token (starts with `olp_`) |
| `OVERLEAF_PROJECT_ID` | yes | — | Hex id from the Overleaf git URL |
| `REPO_PATH` | yes | — | Absolute path to the local git repo |
| `OVERLEAF_BRANCH` | no | `master` | Branch name on the Overleaf side |
| `OVERLEAF_REMOTE` | no | `overleaf` | What to call the remote in your repo |

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

## The one rule

!!! warning "Don't edit the same file in Overleaf and locally between syncs."
    Pick one editor per file per session, sync, then switch sides. The safety check catches the common version of this mistake, but discipline beats tooling.

## Safety nets baked in

- Refuses to push when the working tree has uncommitted changes (Overleaf only sees committed state — uncommitted edits would silently not sync, leaving you confused later)
- Refuses to push when Overleaf has commits the local repo doesn't have (no silent overwrites of web-editor work)
- `.env` is in `.gitignore` so your token can't accidentally land on GitHub
- Token is URL-encoded before being embedded in the remote URL (handles weird characters cleanly)
- The bundled Claude Code skill explicitly tells Claude never to use `--force` without confirmation, never to log the token, and never to edit `.env` without asking

## Troubleshooting

??? failure "`error: missing required config: OVERLEAF_TOKEN`"
    The tool can't find a `.env` (it looks in CWD then `~/.config/claude-to-overleaf/`) or the key isn't in it. Re-do [Step 3 of getting started](getting-started.md#3-make-a-env).

??? failure "`Authentication failed` during `setup`"
    Token is wrong, expired, or revoked. Generate a new one in Overleaf, update `.env`, re-run `setup`. Sanity-check the token directly:

    ```bash
    curl -u git:$OVERLEAF_TOKEN -I \
      "https://git.overleaf.com/$OVERLEAF_PROJECT_ID/info/refs?service=git-upload-pack"
    ```

    `HTTP/2 200` = token is valid. `HTTP/2 401` = bad token.

??? failure "`error: ... is not a git repo`"
    `REPO_PATH` points somewhere without a `.git` directory. Fix the path or `git init` there.

??? failure "`WARNING: overleaf/master has N commit(s) not in your local repo`"
    Working as designed. Run `pull`, cherry-pick what you want, then `sync` again.

## What it does under the hood

`sync` is the textbook Overleaf-git recipe in Python:

1. `git fetch overleaf master`
2. Compare `HEAD^{tree}` to `overleaf/master^{tree}` — exit early if equal
3. `git commit-tree HEAD^{tree} -p overleaf/master -m "Sync from GitHub @<short>"`
4. `git push overleaf <new-commit>:master`

The trick is step 3. Overleaf rejects non-fast-forward pushes, so the script grafts your local tree onto Overleaf's history as a brand-new commit. From Overleaf's perspective, it's a normal forward step — even though your local branch and Overleaf's branch share no recent history.

## Multiple Overleaf projects

Put your shared token once in `~/.config/claude-to-overleaf/.env`:

```bash
OVERLEAF_TOKEN=olp_your_real_token
```

Then drop a per-repo `.env` in each LaTeX project directory with just the bits that differ:

```bash
# inside ~/repos/thesis/.env
OVERLEAF_PROJECT_ID=thesis_hex_id

# inside ~/repos/conference-paper/.env
OVERLEAF_PROJECT_ID=paper_hex_id
```

CWD overrides global **per key**, so the token is inherited from the global file and the project id comes from the local one. `cd` to whichever repo you want to sync, run `claude-to-overleaf sync`. Don't forget to add `.env` to each repo's `.gitignore`.

## Limitations

- Assumes your LaTeX project is at the **root** of the repo. If it lives in a subfolder, you'd need `git subtree split` instead — open an issue and we'll add it.
- Tested on macOS. Should work on Linux. Windows is unverified.
