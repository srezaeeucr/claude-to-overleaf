"""Sync a local Git repo to an Overleaf project, prompt-driven via Claude Code."""

__version__ = "0.3.0"

from .cli import main

__all__ = ["main", "__version__"]
