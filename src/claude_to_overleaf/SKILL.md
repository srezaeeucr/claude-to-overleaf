---
name: claude-to-overleaf
description: Sync the current local Git repo to its paired Overleaf project. Use when the user asks to push to Overleaf, sync to Overleaf, update Overleaf, or get their local LaTeX changes onto Overleaf.
---

# claude-to-overleaf

This skill wraps the `claude-to-overleaf` CLI. The user has paired a local Git repo with an Overleaf project via a personal access token, and wants you to push their committed local changes up to Overleaf.

## When to use

Match user phrases like:
- "sync to overleaf"
- "push to overleaf"
- "update overleaf"
- "send my changes to overleaf"
- "get this onto overleaf"

## Required tooling

The user must have the `claude-to-overleaf` package installed. If `which claude-to-overleaf` returns nothing, suggest:

```
pipx install claude-to-overleaf
```

Then `claude-to-overleaf setup` once to configure the Overleaf remote.

## Workflow

1. **Check for uncommitted changes.** Run `git -C <REPO_PATH> status --porcelain`. If non-empty, ask the user whether to commit first — the script refuses to push with a dirty tree, on purpose, because Overleaf only sees committed state.

2. **Run the sync.** Execute `claude-to-overleaf sync`. Read the output and act on it:
   - `Already in sync ...` → nothing was needed; report that.
   - `Done. Overleaf should reflect changes within seconds.` → success; tell the user to refresh Overleaf in the browser.
   - `WARNING: overleaf/master has N commit(s) not in your local repo` → **do NOT use `--force`.** Run `claude-to-overleaf pull` to list the Overleaf-only commits, show them to the user, and ask whether to cherry-pick them. After cherry-picking, re-run `sync`.
   - `error: working tree has uncommitted changes` → see step 1.
   - `error: missing required config` → walk the user through the setup flow below.

3. **Confirm.** Tell the user the sync succeeded and to refresh Overleaf in the browser.

## Never do

- Never run `claude-to-overleaf sync --force` without explicit user confirmation. The non-force mode exists to prevent silently overwriting edits made in the Overleaf web editor.
- Never paste the user's `OVERLEAF_TOKEN` into responses, logs, or commit messages.
- Never edit `.env` directly without asking — it contains the access token.

## Setup help (if `setup` hasn't been run yet)

If `sync` complains the `overleaf` remote isn't configured, or that required config is missing:

1. Project ID — Overleaf project → Menu → Sync → Git. URL looks like `https://git.overleaf.com/<hex>`. Copy the hex.
2. Token — Account Settings → Git Integration → "Generate token". Starts with `olp_`. Shown once — copy immediately.
3. Save to `.env` (in the LaTeX repo's directory, or `~/.config/claude-to-overleaf/.env`):
   ```
   OVERLEAF_TOKEN=olp_...
   OVERLEAF_PROJECT_ID=<hex>
   REPO_PATH=/absolute/path/to/repo
   ```
4. Run `claude-to-overleaf setup`.

## Reference

- Source / docs: https://github.com/srezaeeucr/claude-to-overleaf
- Subcommands: `setup`, `status`, `sync`, `pull`, `install-skill`
