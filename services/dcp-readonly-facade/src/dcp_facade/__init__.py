"""DCP read-only MCP evidence facade — Phase 1 scaffold.

A loopback-only, read-only projection layer. This package holds the pure
(MCP-independent) logic: response envelope, redaction, project registry,
workspace resolver, fixed read-only git state, and proof-bundle reads.

No module in this package performs filesystem writes, backend HTTP calls,
arbitrary shell, or accepts a caller-supplied path/URL/port/route. See
docs/03-reference/dcp/chatgpt-mcp-readonly/ for the contracts implemented here.
"""

from __future__ import annotations

__all__ = [
    "envelope",
    "redaction",
    "registry",
    "resolver",
    "gitstate",
    "proofs",
    "tools",
]
