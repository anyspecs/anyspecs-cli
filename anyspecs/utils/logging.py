"""
Logging configuration and utilities.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None, verbose: bool = False) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR)
        verbose: Enable verbose logging (sets to DEBUG)
    
    Returns:
        Configured logger instance
    """
    if verbose:
        log_level = logging.DEBUG
    elif level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Return logger for the package
    logger = logging.getLogger('anyspecs')
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(f'anyspecs.{name}') 