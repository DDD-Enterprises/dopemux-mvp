"""Denylist: mutating/proxy routes are unreachable and absent from adapter call paths."""

from __future__ import annotations

from pathlib import Path

from dcp_facade import route_manifest as RM

_SRC = Path(__file__).resolve().parents[1] / "src" / "dcp_facade"
_ADAPTER_FILES = ("conport.py", "dope_memory.py", "http_client.py")


def test_allowed_and_denied_are_disjoint():
    allowed = set(RM.ALLOWED_ROUTES["conport"]) | set(RM.ALLOWED_ROUTES["dope_memory"])
    denied = set(RM.DENIED_ROUTES)
    assert allowed.isdisjoint(denied)


def test_post_read_paths_are_the_only_post_allowlist():
    assert RM.DOPE_MEMORY_READ_PATHS == frozenset(
        {"/tools/memory_search", "/tools/memory_replay_session"}
    )
    # the mutating route is never in the read allowlist
    assert "/tools/memory_correct" not in RM.DOPE_MEMORY_READ_PATHS


def test_adapter_source_has_no_denied_tokens():
    # No denied route token/string appears in any adapter call-path module.
    for fname in _ADAPTER_FILES:
        text = (_SRC / fname).read_text(encoding="utf-8")
        for token in RM.DENIED_TOKENS:
            assert token not in text, f"denied token {token!r} found in {fname}"


def test_adapter_source_has_no_mutating_http_verbs():
    for fname in _ADAPTER_FILES:
        text = (_SRC / fname).read_text(encoding="utf-8")
        # the read client never references put/patch/delete call helpers
        for verb in (".put(", ".patch(", ".delete(", "PUT", "PATCH", "DELETE"):
            assert verb not in text, f"mutating verb {verb!r} found in {fname}"
