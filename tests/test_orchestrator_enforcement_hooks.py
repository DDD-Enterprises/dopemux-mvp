"""
Unit tests for .claude/hooks/orchestrator_enforcement.py
and its wiring into native_hooks.py (PreToolUse / PostToolUse).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make .claude/hooks/ importable (matches tests/test_orchestrator_hooks.py).
_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from orchestrator_enforcement import (  # noqa: E402
    MIN_SUBSTANTIVE_LENGTH,
    POST_PLAN_GUIDANCE,
    PRE_PLAN_GUIDANCE,
    actor_attribution_block,
    actor_attribution_violation,
    actor_authentication_enabled,
    find_orchestrator_config,
    note_skill_map,
    skill_enforcement_warnings,
)
from dopemux.claude.native_hooks import handle_event  # noqa: E402

_ENABLED_CFG = "actor_authentication:\n  enabled: true\n"
_DISABLED_CFG = "actor_authentication:\n  enabled: false\n"
_INLINE_CFG = "actor_authentication: {enabled: true}\n"
_SKILL_CFG = """\
work_item_schemas:
  task-packet:
    notes:
      - key: analyze
        skill: pal:analyze
      - key: proof-bundle
        skill: verify
traits:
  needs-security-review:
    notes:
      - key: security-review
        skill: pal:secaudit
"""

_LONG_BODY = "x" * (MIN_SUBSTANTIVE_LENGTH + 50)


def _write_config(tmp_path: Path, content: str) -> Path:
    cfg = tmp_path / ".taskorchestrator" / "config.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(content)
    return cfg


# ---------------------------------------------------------------------------
# actor_authentication_enabled
# ---------------------------------------------------------------------------

def test_actor_auth_enabled_block_form():
    assert actor_authentication_enabled(_ENABLED_CFG) is True


def test_actor_auth_disabled_block_form():
    assert actor_authentication_enabled(_DISABLED_CFG) is False


def test_actor_auth_enabled_inline_form():
    assert actor_authentication_enabled(_INLINE_CFG) is True


def test_actor_auth_absent_section_is_false():
    assert actor_authentication_enabled("some_other_key: 1\n") is False


def test_actor_auth_none_or_garbage_is_false():
    assert actor_authentication_enabled(None) is False
    assert actor_authentication_enabled("::: not yaml :::\n  - [") is False


# ---------------------------------------------------------------------------
# actor_attribution_violation
# ---------------------------------------------------------------------------

def test_violation_advance_item_missing_actor():
    assert actor_attribution_violation(
        "mcp__task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start"}]},
    ) is True


def test_no_violation_advance_item_with_actor():
    assert actor_attribution_violation(
        "mcp__task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start", "actor": {"id": "a", "kind": "subagent"}}]},
    ) is False


def test_violation_note_upsert_missing_actor():
    assert actor_attribution_violation(
        "mcp__task-orchestrator__manage_notes",
        {"operation": "upsert", "notes": [{"itemId": "x", "key": "analyze", "body": "..."}]},
    ) is True


def test_no_violation_note_delete_operation():
    # Only upsert is enforced.
    assert actor_attribution_violation(
        "mcp__task-orchestrator__manage_notes",
        {"operation": "delete", "ids": ["n1"]},
    ) is False


def test_no_violation_non_orchestrator_tool():
    assert actor_attribution_violation("Read", {"file_path": "/x"}) is False


def test_violation_prefix_agnostic():
    # Works for the upstream double-namespace prefix too.
    assert actor_attribution_violation(
        "mcp__mcp-task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start"}]},
    ) is True


# ---------------------------------------------------------------------------
# actor_attribution_block (enabled gate)
# ---------------------------------------------------------------------------

def test_block_when_enabled_and_violation():
    reason = actor_attribution_block(
        "mcp__task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start"}]},
        _ENABLED_CFG,
    )
    assert reason and "actor" in reason.lower()


def test_no_block_when_disabled():
    assert actor_attribution_block(
        "mcp__task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start"}]},
        _DISABLED_CFG,
    ) is None


def test_no_block_when_config_absent():
    assert actor_attribution_block(
        "mcp__task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start"}]},
        None,
    ) is None


def test_no_block_when_actor_present():
    assert actor_attribution_block(
        "mcp__task-orchestrator__advance_item",
        {"transitions": [{"itemId": "x", "trigger": "start", "actor": {"id": "a", "kind": "user"}}]},
        _ENABLED_CFG,
    ) is None


# ---------------------------------------------------------------------------
# note_skill_map + skill_enforcement_warnings
# ---------------------------------------------------------------------------

def test_note_skill_map_collects_nested_keys():
    skill_map = note_skill_map(_SKILL_CFG)
    assert skill_map["analyze"] == "pal:analyze"
    assert skill_map["proof-bundle"] == "verify"
    assert skill_map["security-review"] == "pal:secaudit"


def test_note_skill_map_empty_when_no_config():
    assert note_skill_map(None) == {}


def test_skill_warning_on_thin_body():
    warnings = skill_enforcement_warnings(
        "mcp__task-orchestrator__manage_notes",
        {"operation": "upsert", "notes": [{"key": "analyze", "body": "n/a"}]},
        _SKILL_CFG,
    )
    assert len(warnings) == 1
    assert "pal:analyze" in warnings[0]


def test_skill_no_warning_on_substantive_body():
    warnings = skill_enforcement_warnings(
        "mcp__task-orchestrator__manage_notes",
        {"operation": "upsert", "notes": [{"key": "analyze", "body": _LONG_BODY}]},
        _SKILL_CFG,
    )
    assert warnings == []


def test_skill_no_warning_on_non_skill_key():
    warnings = skill_enforcement_warnings(
        "mcp__task-orchestrator__manage_notes",
        {"operation": "upsert", "notes": [{"key": "freeform", "body": "x"}]},
        _SKILL_CFG,
    )
    assert warnings == []


def test_skill_no_warning_without_config():
    warnings = skill_enforcement_warnings(
        "mcp__task-orchestrator__manage_notes",
        {"operation": "upsert", "notes": [{"key": "analyze", "body": "n/a"}]},
        None,
    )
    assert warnings == []


def test_skill_no_warning_for_non_note_tool():
    assert skill_enforcement_warnings("Read", {"file_path": "/x"}, _SKILL_CFG) == []


# ---------------------------------------------------------------------------
# find_orchestrator_config (worktree-safe walk)
# ---------------------------------------------------------------------------

def test_find_config_walks_up_from_nested_dir(tmp_path):
    _write_config(tmp_path, _ENABLED_CFG)
    nested = tmp_path / ".claude" / "worktrees" / "wt-x" / "deep"
    nested.mkdir(parents=True, exist_ok=True)
    found = find_orchestrator_config(nested)
    assert found is not None
    assert "actor_authentication" in found


def test_find_config_returns_none_when_absent(tmp_path):
    assert find_orchestrator_config(tmp_path) is None


# ---------------------------------------------------------------------------
# Dispatcher integration (native_hooks handle_event shim)
# ---------------------------------------------------------------------------

def test_dispatcher_blocks_advance_item_missing_actor_when_enabled(tmp_path):
    _write_config(tmp_path, _ENABLED_CFG)
    response = handle_event("PreToolUse", {
        "cwd": str(tmp_path),
        "tool_name": "mcp__task-orchestrator__advance_item",
        "tool_input": {"transitions": [{"itemId": "x", "trigger": "start"}]},
    })
    assert response.get("decision") == "block"


def test_dispatcher_allows_advance_item_with_actor_when_enabled(tmp_path):
    _write_config(tmp_path, _ENABLED_CFG)
    response = handle_event("PreToolUse", {
        "cwd": str(tmp_path),
        "tool_name": "mcp__task-orchestrator__advance_item",
        "tool_input": {"transitions": [{"itemId": "x", "trigger": "start", "actor": {"id": "a", "kind": "user"}}]},
    })
    assert response.get("decision") != "block"


def test_dispatcher_skill_warning_on_thin_note(tmp_path):
    _write_config(tmp_path, _SKILL_CFG)
    response = handle_event("PreToolUse", {
        "cwd": str(tmp_path),
        "tool_name": "mcp__task-orchestrator__manage_notes",
        "tool_input": {"operation": "upsert", "notes": [{"key": "analyze", "body": "tbd"}]},
    })
    ctx = response.get("hookSpecificOutput", {}).get("additionalContext", "")
    assert "SKILL REQUIRED" in ctx


def test_dispatcher_enter_plan_mode_injects_guidance():
    response = handle_event("PreToolUse", {"tool_name": "EnterPlanMode", "tool_input": {}})
    ctx = response.get("hookSpecificOutput", {}).get("additionalContext", "")
    assert PRE_PLAN_GUIDANCE.strip()[:30] in ctx


def test_dispatcher_exit_plan_mode_injects_guidance():
    response = handle_event("PostToolUse", {"tool_name": "ExitPlanMode", "tool_input": {}})
    ctx = response.get("hookSpecificOutput", {}).get("additionalContext", "")
    assert POST_PLAN_GUIDANCE.strip()[:30] in ctx
