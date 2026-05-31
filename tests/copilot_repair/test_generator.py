"""Tests for Copilot repair packet generation and rendering."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.copilot_repair.generator import generate_repair_packet
from tools.copilot_repair.renderer import render_repair_packet


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "copilot" / "repair_packet.schema.json"
FIXED_TS = "2026-01-01T00:00:00Z"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(packet: dict) -> None:
    jsonschema.Draft202012Validator(_schema()).validate(packet)


def _action_plan(actions: list[dict]) -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at": FIXED_TS,
        "pr_number": 704,
        "repo": "DDD-Enterprises/dopemux-mvp",
        "readiness": "NEEDS_IMPLEMENTER",
        "actions": actions,
        "mutation_performed": False,
    }


def _action(
    *,
    action_id: str,
    category: str,
    target_role: str,
    source_blocker: str,
    source_item_id: str | None = None,
) -> dict:
    return {
        "id": action_id,
        "category": category,
        "target_role": target_role,
        "source_blocker": source_blocker,
        "source_item_id": source_item_id,
        "rationale": f"{source_blocker} requires attention.",
    }


def test_generate_repair_packet_filters_to_implementer_items() -> None:
    action_plan = _action_plan(
        [
            _action(
                action_id="action-0001",
                category="failed-check",
                target_role="implementer",
                source_blocker="FAILED_CHECK",
                source_item_id="unit",
            ),
            _action(
                action_id="action-0002",
                category="proof-stale",
                target_role="supervisor",
                source_blocker="PROOF_STALE",
            ),
            _action(
                action_id="action-0003",
                category="pending-check",
                target_role="ci",
                source_blocker="PENDING_CHECK",
            ),
        ]
    )

    packet = generate_repair_packet(
        action_plan,
        source_action_plan_id="ACTION_PLAN.json",
    )

    _validate(packet)
    assert packet["copilot_authority"] == "implementer-only"
    assert packet["mutation_performed"] is False
    assert packet["source_action_plan_id"] == "ACTION_PLAN.json"
    assert [item["id"] for item in packet["items"]] == ["repair-0001"]
    assert packet["items"][0]["category"] == "failed-check"
    assert packet["items"][0]["source_item_id"] == "unit"
    assert "Fix the failing CI check" in packet["items"][0]["suggested_action"]


def test_generate_repair_packet_renumbers_multiple_implementer_items() -> None:
    action_plan = _action_plan(
        [
            _action(
                action_id="action-0010",
                category="request-changes",
                target_role="implementer",
                source_blocker="REQUEST_CHANGES",
            ),
            _action(
                action_id="action-0011",
                category="must-fix",
                target_role="implementer",
                source_blocker="REVIEW_ITEM_MUST_FIX",
            ),
        ]
    )

    packet = generate_repair_packet(action_plan)

    _validate(packet)
    assert [item["id"] for item in packet["items"]] == ["repair-0001", "repair-0002"]
    assert [item["category"] for item in packet["items"]] == [
        "request-changes",
        "must-fix",
    ]


def test_generate_repair_packet_normalizes_fractional_source_timestamp() -> None:
    action_plan = _action_plan([])
    action_plan["generated_at"] = "2026-01-01T00:00:00.123456Z"

    packet = generate_repair_packet(action_plan)

    _validate(packet)
    assert packet["generated_at"] == FIXED_TS


def test_generate_repair_packet_rejects_mutated_action_plan() -> None:
    action_plan = _action_plan([])
    action_plan["mutation_performed"] = True

    with pytest.raises(ValueError, match="mutation_performed"):
        generate_repair_packet(action_plan)


def test_generate_repair_packet_rejects_invalid_implementer_category() -> None:
    action_plan = _action_plan(
        [
            _action(
                action_id="action-0001",
                category="proof-stale",
                target_role="implementer",
                source_blocker="PROOF_STALE",
            )
        ]
    )

    with pytest.raises(ValueError, match="implementer category"):
        generate_repair_packet(action_plan)


def test_render_repair_packet_uses_template_without_mutation_language() -> None:
    packet = generate_repair_packet(
        _action_plan(
            [
                _action(
                    action_id="action-0001",
                    category="failed-check",
                    target_role="implementer",
                    source_blocker="FAILED_CHECK",
                    source_item_id="unit",
                )
            ]
        )
    )

    rendered = render_repair_packet(packet)

    assert "Copilot MUST NOT post" in rendered
    assert "Copilot MUST NOT approve" in rendered
    assert "Copilot MUST NOT merge" in rendered
    assert "tools/pr_merge" in rendered
    assert "repair-0001" in rendered
    assert "failed-check" in rendered
    assert "unit" in rendered
