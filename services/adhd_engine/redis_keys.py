"""Redis key namespacing helpers for ADHD Engine state."""
from __future__ import annotations

import os


def redis_key_prefix() -> str:
    """Return the configured ADHD Engine Redis namespace prefix, if any."""
    raw_prefix = (
        os.getenv("ADHD_ENGINE_REDIS_PREFIX")
        or os.getenv("ADHD_ENGINE_INSTANCE_ID")
        or os.getenv("DOPEMUX_INSTANCE_ID")
        or ""
    )
    return raw_prefix.strip().strip(":")


def redis_key(key: str) -> str:
    """Prefix a concrete Redis key when an ADHD Engine instance id is configured."""
    prefix = redis_key_prefix()
    normalized_key = key.strip(":")
    return f"{prefix}:{normalized_key}" if prefix else normalized_key


def redis_pattern(pattern: str) -> str:
    """Prefix a Redis key pattern using the same namespace as concrete keys."""
    return redis_key(pattern)
