# Using with Claude Code

This package was built primarily to be invoked by [Claude Code](https://docs.claude.com/en/docs/claude-code/overview). The CLI works fine on its own, but the prompt-driven flow is the design center.

## Install the skill

Once the package is installed:

```bash
claude-to-overleaf install-skill
```

This copies a [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) to:

```
~/.claude/skills/claude-to-overleaf/SKILL.md
```

Restart Claude Code to pick it up. From then on Claude will recognize when you're asking to sync to Overleaf and invoke the tool with the right arguments.

## What you can say

The skill triggers on phrases like:

- *"sync to overleaf"*
- *"push to overleaf"*
- *"update overleaf"*
- *"send my changes to overleaf"*
- *"get this onto overleaf"*

## What Claude does

Once invoked, the skill walks Claude through this workflow:

1. **Check for uncommitted changes.** If `git status --porcelain` is non-empty, Claude asks whether to commit first — the script refuses to push with a dirty tree on purpose, because Overleaf only sees committed state.
2. **Run `claude-to-overleaf sync`.** Claude reads the output and acts on it:
    - `Already in sync ...` → reports nothing was needed.
    - `Done. Overleaf should reflect changes within seconds.` → tells you the sync worked and to refresh Overleaf.
    - `WARNING: overleaf/master has N commit(s) not in your local repo` → **does not** use `--force`. Instead runs `claude-to-overleaf pull` to list the Overleaf-only commits, shows them to you, and asks whether to cherry-pick them.
    - `error: missing required config` → walks you through the setup flow.
3. **Confirm.** Reports success and reminds you to refresh Overleaf in the browser.

## Guardrails baked into the skill

The skill explicitly tells Claude to **never**:

- Run `claude-to-overleaf sync --force` without explicit user confirmation. The non-force mode exists to prevent silently overwriting edits made in the Overleaf web editor.
- Paste the user's `OVERLEAF_TOKEN` into responses, logs, or commit messages.
- Edit `.env` directly without asking — it contains the access token.

## Why a skill instead of "Claude figures it out"?

Without the skill, Claude would still notice the `claude-to-overleaf` command exists on your PATH and probably figure out to use it. But it would do that from scratch each time — sometimes using `--force` when it shouldn't, sometimes trying raw `git push` instead, sometimes asking unnecessary questions.

The skill gives Claude a **defined workflow with named failure modes**. The result is the same prompt-driven UX every time: you say *"sync"*, Claude does the right thing.
