"""
Structured application logging for Autonomous Coding Agent.
"""
from __future__ import annotations

import sys
from typing import Optional
from loguru import logger

from autonomous_agent.config.settings import Settings


def setup_logging(settings: Optional[Settings] = None) -> None:
    """
    Set up structured application logging.

    Args:
        settings: Application settings. If None, loads default settings.
    """
    if settings is None:
        settings = Settings()

    # Remove default logger
    logger.remove()

    # Add stdout logger with formatting
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Optionally add file logging
    # logger.add("logs/agent_{time}.log", rotation="500 MB", level=settings.log_level)


# Create a logger instance with context
bound_logger = logger.bind(name="autonomous_agent")

# Convenience function to get a logger with context
def get_logger(name: str):
    """
    Get a logger with additional context.

    Args:
        name: Logger name (usually __module__)

    Returns:
        Configured logger instance
    """
    return bound_logger.bind(name=name)
