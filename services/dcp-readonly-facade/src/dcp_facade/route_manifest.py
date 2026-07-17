"""Backend route manifest — explicit allow/deny data for Phase-1 adapters.

The ALLOWED set is exactly the inventory's CONFIRMED_READ_ONLY surfaces that
0005 exposes. The DENIED set documents the mutating / side-effect / proxy
routes the adapters must never construct — asserted by the denylist tests and
re-checked by the commit-verify grep. This module contains data only (no calls).
"""

from __future__ import annotations

CONPORT = "conport"
DOPE_MEMORY = "dope_memory"

# (method, path-template) the adapters are permitted to call.
ALLOWED_ROUTES: dict[str, tuple[tuple[str, str], ...]] = {
    CONPORT: (
        ("GET", "/api/decisions"),
        ("GET", "/api/decisions/{decision_id}"),
        ("GET", "/api/progress"),
        ("GET", "/api/search/{workspace_id}"),
    ),
    DOPE_MEMORY: (
        ("POST", "/tools/memory_search"),
        ("POST", "/tools/memory_replay_session"),
    ),
}

# Release-one public surface (TP-0015): ownership-gated ops only.
# Progress and broad ConPort search remain structurally available to legacy
# Phase-1 helpers but are NOT release-one operations (progress may auto-fork).
RELEASE_ONE_OPERATIONS: dict[str, tuple[str, ...]] = {
    CONPORT: ("list_decisions", "get_decision"),
    DOPE_MEMORY: ("memory_search", "memory_replay_session"),
}

RELEASE_ONE_ROUTES: dict[str, tuple[tuple[str, str], ...]] = {
    CONPORT: (
        ("GET", "/api/decisions"),
        ("GET", "/api/decisions/{decision_id}"),
    ),
    DOPE_MEMORY: (
        ("POST", "/tools/memory_search"),
        ("POST", "/tools/memory_replay_session"),
    ),
}


def is_release_one_operation(family: str, operation: str) -> bool:
    return operation in RELEASE_ONE_OPERATIONS.get(family, ())

# Only these POST paths may ever be issued (side-effect-free dope-memory reads).
DOPE_MEMORY_READ_PATHS = frozenset(
    {"/tools/memory_search", "/tools/memory_replay_session"}
)

# Routes/identifiers that must NEVER appear in an adapter call path. Used by
# tests + the commit-verify grep. (Mutating, proxy, or side-effect surfaces.)
DENIED_ROUTES: tuple[tuple[str, str], ...] = (
    ("POST", "/api/decisions"),                 # ConPort write
    ("POST", "/api/progress"),                  # ConPort write
    ("POST", "/api/custom_data"),               # ConPort write
    ("GET", "/api/custom_data"),                # deferred (redaction-sensitive)
    ("POST", "/tools/memory_correct"),          # dope-memory mutation
    ("POST", "/tools/memory_generate_reflection"),
    ("POST", "/tools/memory_store"),
    ("POST", "/tools/memory_mark_issue"),
    ("POST", "/tools/memory_link_resolution"),
    ("GET", "/ddg/decisions"),                  # dopecon-bridge proxy
)

# Operations explicitly blocked for release-one even if a low-level helper exists.
RELEASE_ONE_DENIED_OPERATIONS: tuple[str, ...] = (
    "get_progress",
    "search_progress",
    "search",
    "query",
    "memory_store",
    "memory_correct",
    "memory_generate_reflection",
    "memory_mark_issue",
    "memory_link_resolution",
    "log_decision",
)

# Token substrings that signal a denied route/operation (used by tests).
DENIED_TOKENS = (
    "memory_correct",
    "memory_generate_reflection",
    "memory_store",
    "memory_mark_issue",
    "memory_link_resolution",
    "log_decision",
    "upsert",
    "/ddg/",
    "/kg/",
    "/route/pm",
)
