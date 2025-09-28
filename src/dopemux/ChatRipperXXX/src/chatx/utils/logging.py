"""Logging utilities for ChatX."""

import logging

from rich.logging import RichHandler


def setup_logging(
    level: int = logging.INFO,
    logger_name: str | None = None,
    show_time: bool = True,
    show_path: bool = False,
) -> logging.Logger:
    """Set up structured logging with Rich formatting.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        logger_name: Name of the logger (defaults to root)
        show_time: Whether to show timestamps
        show_path: Whether to show file paths
        
    Returns:
        Configured logger instance
    """
    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create rich handler
    handler = RichHandler(
        console=None,  # Use default console
        show_time=show_time,
        show_path=show_path,
        show_level=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_width=100,
        tracebacks_show_locals=level == logging.DEBUG,
    )
    
    # Set up formatting
    handler.setFormatter(logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]",
    ))
    
    # Configure the logger
    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.setLevel(level)
    
    # Set chatx package logger to the same level
    chatx_logger = logging.getLogger("chatx")
    chatx_logger.setLevel(level)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
