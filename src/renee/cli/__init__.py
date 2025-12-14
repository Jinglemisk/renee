"""CLI and REPL for the Renee game framework.

This module provides:
- Main CLI entry point with typer
- REPL for interactive game manipulation
- Output formatting (JSON and human-readable)
- Command modules for various operations
"""

from renee.cli.main import app
from renee.cli.output import OutputFormatter
from renee.cli.repl import GameREPL, REPLOutput

__all__ = [
    "app",
    "OutputFormatter",
    "GameREPL",
    "REPLOutput",
]
