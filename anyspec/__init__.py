"""
AnySpec CLI - Universal Chat History Export Tool

A unified CLI tool for exporting chat history from multiple AI assistants.
Supports Cursor AI and Claude Code with various export formats.
"""

__version__ = "1.0.0"
__author__ = "AnySpec Team"

from .cli import main

__all__ = ["main"] 