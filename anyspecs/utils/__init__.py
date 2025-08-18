"""
Utility functions and helpers.
"""

from .logging import setup_logging
from .paths import get_project_name, normalize_path

__all__ = ["setup_logging", "get_project_name", "normalize_path"] 