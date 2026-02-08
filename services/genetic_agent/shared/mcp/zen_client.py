"""Zen MCP compatibility client.

Genetic agent modules historically import ``ZenClient`` for chat-style LLM calls.
The current MCP stack uses PAL-compatible chat semantics, so this shim keeps the
existing interface stable while delegating to ``PALClient``.
"""

from .pal_client import PALClient


class ZenClient(PALClient):
    """Backwards-compatible alias for PAL chat-based MCP interactions."""

