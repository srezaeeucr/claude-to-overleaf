"""Sync a local Git repo (root = LaTeX project) to an Overleaf project.

Subcommands:
  setup   Configure the 'overleaf' git remote and verify auth.
  status  Show whether local HEAD matches Overleaf.
  sync    Push local HEAD's tree to Overleaf (with safety checks).
  pull    List Overleaf-only commits to cherry-pick locally.

Config sources, in precedence order (highest first):
  1. Environment variables
  2. ./.env (current working directory)
  3. ~/.config/claude-to-overleaf/.env

The two .env files are merged: values in the CWD .env override values from
the global one. This lets you keep a shared OVERLEAF_TOKEN globally and put
per-project OVERLEAF_PROJECT_ID values in each repo's local .env.

Recognized keys:
  OVERLEAF_TOKEN       Personal access token (starts with olp_)
  OVERLEAF_PROJECT_ID  Hex project id from the Overleaf git URL
  REPO_PATH            Absolute path to the local git repo
  OVERLEAF_BRANCH      Default: master
  OVERLEAF_REMOTE      Default: overleaf
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote


def load_env_file(path: Path) -> dict:
    """Parse a simple KEY=VALUE .env file."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def find_env_files() -> list:
    """Return existing .env files in precedence order, lowest first.

    The global file at ~/.config/claude-to-overleaf/.env is the base layer;
    a .env in the current working directory overrides keys from it. This lets
    a user keep one shared OVERLEAF_TOKEN in the global file and per-project
    OVERLEAF_PROJECT_ID values in each repo's local .env.
    """
    candidates = [
        Path.home() / ".config" / "claude-to-overleaf" / ".env",
        Path.cwd() / ".env",
    ]
    return [p for p in candidates if p.exists()]


def load_config() -> dict:
    file_env = {}
    for env_file in find_env_files():
        file_env.update(load_env_file(env_file))

    def pick(key, default=""):
        return os.environ.get(key) or file_env.get(key, default)

    return {
        "token": pick("OVERLEAF_TOKEN"),
        "project_id": pick("OVERLEAF_PROJECT_ID"),
        "repo_path": pick("REPO_PATH"),
        "branch": pick("OVERLEAF_BRANCH", "master"),
        "remote_name": pick("OVERLEAF_REMOTE", "overleaf"),
    }


CONFIG_ENV_NAME = {
    "token": "OVERLEAF_TOKEN",
    "project_id": "OVERLEAF_PROJECT_ID",
    "repo_path": "REPO_PATH",
}


def require(cfg: dict, *keys: str) -> None:
    missing = [CONFIG_ENV_NAME.get(k, k.upper()) for k in keys if not cfg.get(k)]
    if missing:
        sys.exit(
            f"error: missing required config: {', '.join(missing)}. "
            "Set in .env or the environment."
        )


def repo_root(cfg: dict) -> Path:
    path = Path(cfg["repo_path"]).expanduser() if cfg["repo_path"] else Path.cwd()
    if not (path / ".git").exists():
        sys.exit(f"error: {path} is not a git repo (no .git directory).")
    return path


def git(args: list, cwd: Path) -> None:
    """Run git, streaming output to the terminal. Raise on non-zero exit."""
    subprocess.run(["git", *args], cwd=cwd, check=True)


def git_out(args: list, cwd: Path) -> str:
    """Run git and capture stdout. Stderr passes through to the terminal."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, text=True, stdout=subprocess.PIPE
    )
    return result.stdout.strip()


def remote_exists(cwd: Path, name: str) -> bool:
    return (
        subprocess.run(
            ["git", "remote", "get-url", name],
            cwd=cwd,
            capture_output=True,
        ).returncode
        == 0
    )


def overleaf_url(cfg: dict) -> str:
    return f"https://git:{quote(cfg['token'], safe='')}@git.overleaf.com/{cfg['project_id']}"


# ---------- subcommands ----------

def cmd_setup(cfg: dict) -> None:
    require(cfg, "token", "project_id")
    cwd = repo_root(cfg)
    name = cfg["remote_name"]
    target = overleaf_url(cfg)

    if remote_exists(cwd, name):
        current = git_out(["remote", "get-url", name], cwd)
        if current == target:
            print(f"[setup] '{name}' already configured with current token.")
        else:
            print(f"[setup] Updating '{name}' remote URL.")
            git(["remote", "set-url", name, target], cwd)
    else:
        print(f"[setup] Adding '{name}' remote.")
        git(["remote", "add", name, target], cwd)

    print(f"[setup] Testing fetch from {name}...")
    git(["fetch", name], cwd)
    print(f"[setup] OK — '{name}' is reachable.")


def ensure_setup(cfg: dict) -> Path:
    cwd = repo_root(cfg)
    if not remote_exists(cwd, cfg["remote_name"]):
        cmd_setup(cfg)
    return cwd


def cmd_status(cfg: dict) -> None:
    require(cfg, "token", "project_id")
    cwd = ensure_setup(cfg)
    name, branch = cfg["remote_name"], cfg["branch"]

    print(f"[status] Fetching {name}/{branch}...")
    git(["fetch", name, branch], cwd)

    head_tree = git_out(["rev-parse", "HEAD^{tree}"], cwd)
    overleaf_tree = git_out(["rev-parse", f"{name}/{branch}^{{tree}}"], cwd)

    if head_tree == overleaf_tree:
        print("[status] In sync — local HEAD tree matches Overleaf.")
        return

    ahead = git_out(["rev-list", "--count", f"{name}/{branch}..HEAD"], cwd)
    behind = git_out(["rev-list", "--count", f"HEAD..{name}/{branch}"], cwd)
    print(f"[status] Local is {ahead} ahead, {behind} behind {name}/{branch}.")
    if int(behind) > 0:
        print("[status] Overleaf-only commits:")
        for line in git_out(
            ["log", "--oneline", f"{name}/{branch}", "^HEAD"], cwd
        ).splitlines():
            print(f"  {line}")


def cmd_sync(cfg: dict, force: bool = False) -> None:
    require(cfg, "token", "project_id")
    cwd = ensure_setup(cfg)
    name, branch = cfg["remote_name"], cfg["branch"]

    if git_out(["status", "--porcelain"], cwd):
        sys.exit("error: working tree has uncommitted changes. Commit or stash first.")

    print(f"[1/3] Fetching {name}/{branch}...")
    git(["fetch", name, branch], cwd)

    head_tree = git_out(["rev-parse", "HEAD^{tree}"], cwd)
    overleaf_tree = git_out(["rev-parse", f"{name}/{branch}^{{tree}}"], cwd)

    if head_tree == overleaf_tree:
        print(f"[2/3] Already in sync with {name}/{branch}. Nothing to push.")
        return

    behind = int(git_out(["rev-list", "--count", f"HEAD..{name}/{branch}"], cwd))
    if behind > 0:
        print()
        print(f"WARNING: {name}/{branch} has {behind} commit(s) not in your local repo.")
        print("Pushing now would bury those changes. Inspect with:")
        print(f"  git log --oneline {name}/{branch} ^HEAD")
        print("  git show <hash>")
        print("Then cherry-pick wanted commits, or re-run with --force to overwrite.")
        if not force:
            sys.exit(1)
        print("--force given — proceeding anyway.")

    print(f"[2/3] Building fast-forward commit on top of {name}/{branch}...")
    latest_overleaf = git_out(["rev-parse", f"{name}/{branch}"], cwd)
    gh_head_short = git_out(["rev-parse", "--short", "HEAD"], cwd)
    new_commit = git_out(
        [
            "commit-tree", head_tree,
            "-p", latest_overleaf,
            "-m", f"Sync from GitHub @{gh_head_short}",
        ],
        cwd,
    )

    print(f"[3/3] Pushing {new_commit[:8]} to {name}/{branch}...")
    git(["push", name, f"{new_commit}:{branch}"], cwd)
    print("Done. Overleaf should reflect changes within seconds.")


def cmd_install_skill() -> None:
    """Copy the bundled SKILL.md to ~/.claude/skills/claude-to-overleaf/."""
    src = Path(__file__).resolve().parent / "SKILL.md"
    if not src.exists():
        sys.exit(f"error: bundled SKILL.md not found at {src}")
    target_dir = Path.home() / ".claude" / "skills" / "claude-to-overleaf"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "SKILL.md"
    target.write_text(src.read_text())
    print(f"[install-skill] Wrote {target}")
    print("[install-skill] Restart Claude Code to pick up the new skill.")


def cmd_pull(cfg: dict) -> None:
    require(cfg, "token", "project_id")
    cwd = ensure_setup(cfg)
    name, branch = cfg["remote_name"], cfg["branch"]

    print(f"[pull] Fetching {name}/{branch}...")
    git(["fetch", name, branch], cwd)

    log = git_out(["log", "--oneline", f"{name}/{branch}", "^HEAD"], cwd)
    if not log:
        print("[pull] No Overleaf-only commits.")
        return
    print("[pull] Overleaf-only commits:")
    for line in log.splitlines():
        print(f"  {line}")
    print()
    print("To bring them into local:  git cherry-pick <hash>")


# ---------- entry point ----------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="Configure the overleaf git remote and test auth.")
    sub.add_parser("status", help="Show whether local and Overleaf are in sync.")
    p_sync = sub.add_parser("sync", help="Push local HEAD's tree to Overleaf.")
    p_sync.add_argument(
        "--force", action="store_true",
        help="Overwrite Overleaf even if it has commits ahead.",
    )
    sub.add_parser("pull", help="List Overleaf-only commits to cherry-pick.")
    sub.add_parser(
        "install-skill",
        help="Install the bundled Claude Code skill to ~/.claude/skills/.",
    )

    args = parser.parse_args()
    cfg = load_config()

    handlers = {
        "setup": lambda: cmd_setup(cfg),
        "status": lambda: cmd_status(cfg),
        "sync": lambda: cmd_sync(cfg, force=args.force),
        "pull": lambda: cmd_pull(cfg),
        "install-skill": lambda: cmd_install_skill(),
    }
    try:
        handlers[args.cmd]()
    except subprocess.CalledProcessError as e:
        sys.exit(f"error: `{' '.join(e.cmd)}` failed with exit {e.returncode}.")
