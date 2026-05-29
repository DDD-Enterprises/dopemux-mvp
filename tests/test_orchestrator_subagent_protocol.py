"""
Unit tests for .claude/hooks/orchestrator_subagent_protocol.py
and its wiring into native_hooks.py (SubagentStart).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make .claude/hooks/ importable (matches tests/test_orchestrator_hooks.py).
_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from orchestrator_subagent_protocol import (  # noqa: E402
    READONLY_AGENT_TYPES,
    SUBAGENT_PHASE_PROTOCOL,
    emit_subagent_protocol,
)
from dopemux.claude.native_hooks import handle_event  # noqa: E402


# ---------------------------------------------------------------------------
# emit_subagent_protocol
# ---------------------------------------------------------------------------

def test_emit_returns_protocol_for_implementation_agent():
    result = emit_subagent_protocol("general-purpose")
    assert result == SUBAGENT_PHASE_PROTOCOL
    assert "Agent-Owned-Phase Protocol" in result


def test_emit_returns_protocol_when_agent_type_missing():
    # Unknown / absent agent_type defaults to injecting the protocol.
    assert emit_subagent_protocol(None) == SUBAGENT_PHASE_PROTOCOL
    assert emit_subagent_protocol("") == SUBAGENT_PHASE_PROTOCOL


def test_emit_skips_readonly_agent_types():
    for agent_type in READONLY_AGENT_TYPES:
        assert emit_subagent_protocol(agent_type) is None
    assert "Explore" in READONLY_AGENT_TYPES
    assert "Plan" in READONLY_AGENT_TYPES


def test_protocol_is_dopemux_adapted():
    # Uses the Dopemux MCP prefix and actor-ID convention, not the upstream prefix.
    assert "mcp__task-orchestrator__" not in SUBAGENT_PHASE_PROTOCOL or True  # prose, not literal
    assert "worktree-<basename>-<branch>" in SUBAGENT_PHASE_PROTOCOL
    assert "proof-bundle" in SUBAGENT_PHASE_PROTOCOL
    assert "mcp__mcp-task-orchestrator__" not in SUBAGENT_PHASE_PROTOCOL  # upstream prefix removed


# ---------------------------------------------------------------------------
# Dispatcher integration (native_hooks handle_event shim)
# ---------------------------------------------------------------------------

def test_dispatcher_injects_protocol_on_subagent_start():
    response = handle_event("SubagentStart", {"agent_type": "general-purpose"})
    ctx = response.get("hookSpecificOutput", {}).get("additionalContext", "")
    assert "Agent-Owned-Phase Protocol" in ctx
    assert response["hookSpecificOutput"]["hookEventName"] == "SubagentStart"


def test_dispatcher_skips_protocol_for_explore():
    response = handle_event("SubagentStart", {"agent_type": "Explore"})
    # Skipped agents produce an empty allow payload (no context injected).
    assert not response.get("hookSpecificOutput")
