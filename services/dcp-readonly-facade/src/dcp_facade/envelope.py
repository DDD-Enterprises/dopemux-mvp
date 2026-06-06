"""Canonical response envelope.

Every facade tool result — successful, partial, or blocked — is wrapped in the
structure defined by
docs/03-reference/dcp/chatgpt-mcp-readonly/RESPONSE_ENVELOPE_SCHEMA.md.

A missing capability or denied read yields PARTIAL/BLOCKED, never guessed data.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

# --- status tokens ---------------------------------------------------------
OK = "OK"
PARTIAL = "PARTIAL"
BLOCKED = "BLOCKED"

# --- source systems / authority labels ------------------------------------
SOURCE_FACADE = "facade"
SOURCE_GIT = "git"
SOURCE_CONPORT = "conport"
SOURCE_DOPE_MEMORY = "dope-memory"
SOURCE_DOPE_CONTEXT = "dope-context"
SOURCE_TASK_ORCHESTRATOR = "task-orchestrator"

AUTHORITY_FACADE = "facade"
AUTHORITY_GIT = "OBSERVED/git"
AUTHORITY_FS = "OBSERVED/fs"
AUTHORITY_CANONICAL = "CANONICAL"
AUTHORITY_DERIVED = "DERIVED"

# Canonical field order (also the full key set the envelope always carries).
ENVELOPE_FIELDS = (
    "project_id",
    "branch",
    "head_sha",
    "dirty",
    "source_system",
    "authority_label",
    "status",
    "freshness",
    "limitations",
    "warnings",
    "redactions",
    "blocked_reasons",
    "data",
)


def build_envelope(
    *,
    project_id: Optional[str],
    status: str,
    source_system: str,
    authority_label: str,
    data: Any = None,
    branch: Optional[str] = None,
    head_sha: Optional[str] = None,
    dirty: Optional[bool] = None,
    freshness: Optional[str] = None,
    limitations: Optional[Iterable[str]] = None,
    warnings: Optional[Iterable[str]] = None,
    redactions: Optional[Iterable[str]] = None,
    blocked_reasons: Optional[Iterable[str]] = None,
) -> dict:
    """Return a canonical envelope dict with every field always present."""
    if status not in (OK, PARTIAL, BLOCKED):
        raise ValueError(f"invalid status: {status!r}")
    return {
        "project_id": project_id,
        "branch": branch,
        "head_sha": head_sha,
        "dirty": dirty,
        "source_system": source_system,
        "authority_label": authority_label,
        "status": status,
        "freshness": freshness,
        "limitations": list(limitations or []),
        "warnings": list(warnings or []),
        "redactions": list(redactions or []),
        "blocked_reasons": list(blocked_reasons or []),
        "data": data,
    }


def blocked(
    project_id: Optional[str],
    reason: str,
    *,
    source_system: str = SOURCE_FACADE,
    authority_label: str = AUTHORITY_FACADE,
) -> dict:
    """Convenience: a BLOCKED envelope with a single reason and no data."""
    return build_envelope(
        project_id=project_id,
        status=BLOCKED,
        source_system=source_system,
        authority_label=authority_label,
        data=None,
        blocked_reasons=[reason],
    )
