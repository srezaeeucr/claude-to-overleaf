# claude-to-overleaf

**One prompt to push your LaTeX repo to Overleaf.** No web-UI tab-juggling. No copy-paste. No "wait, did I save that?"

A tiny, zero-dependency Python package that ships with a [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills). Edit locally in your editor of choice, commit, then tell Claude:

!!! quote ""
    *"sync to overleaf"*

Claude invokes the skill, runs the tool, handles the safety checks, and your Overleaf project reflects the changes within seconds. (No Claude Code? It's also a normal CLI — `claude-to-overleaf sync`.)

## Why this exists

Overleaf gives every project a git URL — but actually using it day-to-day means:

- remembering to add a remote
- juggling a token you saw exactly once
- knowing the magic incantation (`commit-tree`, `HEAD^{tree}`, fast-forward push) because Overleaf rejects normal pushes
- *not* blowing away edits made in the Overleaf web editor

This package does all of that for you, and refuses to push when it would silently destroy work.

## At a glance

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Prompt-driven**

    ---

    Designed for Claude Code. Tell Claude *"sync to overleaf"* and it runs the safe-by-default workflow.

    [:octicons-arrow-right-24: Using with Claude Code](using-with-claude-code.md)

-   :material-package-variant:{ .lg .middle } **Standard package**

    ---

    `pipx install claude-to-overleaf` and you get a CLI on your PATH. Zero runtime dependencies.

    [:octicons-arrow-right-24: Getting started](getting-started.md)

-   :material-shield-check:{ .lg .middle } **Safe by default**

    ---

    Refuses to push when Overleaf is ahead, or when the working tree is dirty. Your work doesn't get silently buried.

    [:octicons-arrow-right-24: Reference](reference.md)

-   :material-source-branch:{ .lg .middle } **Five subcommands**

    ---

    `setup`, `status`, `sync`, `pull`, `install-skill`. That's the whole surface.

    [:octicons-arrow-right-24: CLI reference](reference.md#commands)

</div>

## License

[MIT](https://github.com/srezaeeucr/claude-to-overleaf/blob/main/LICENSE).
