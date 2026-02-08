"""Shared lightweight utilities for working-memory-assistant."""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured module logger.

    Centralized helper kept for compatibility with existing imports.
    """
    return logging.getLogger(name)
