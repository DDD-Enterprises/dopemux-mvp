"""Read-only DCP CLI projection — DMX-DCP-MODEL-ROUTING-MVP-0004."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from dopemux.dcp.routing_backend_policy import select_backend_policy
from dopemux.dcp.routing_classifier import RoutingClassificationInput, classify_route
from dopemux.dcp.routing_model import (
    AuthorityClass,
    BackendKind,
    ComplexityClass,
    ConnectorKind,
    RouteDecision,
    RiskClass,
    RuntimeImpact,
    TaskSource,
    TaskType,
)


def _enum_value(enum_cls: type, raw: object, default: Any) -> Any:
    if raw is None:
        return default
    try:
        return enum_cls(str(raw))
    except ValueError:
        return default


def _input_from_dict(data: dict[str, Any]) -> RoutingClassificationInput:
    return RoutingClassificationInput(
        task_source=_enum_value(TaskSource, data.get("task_source"), TaskSource.UNKNOWN),
        task_type=_enum_value(TaskType, data.get("task_type"), TaskType.UNKNOWN),
        risk_class=_enum_value(RiskClass, data.get("risk_class"), RiskClass.UNKNOWN),
        complexity_class=_enum_value(
            ComplexityClass, data.get("complexity_class"), ComplexityClass.UNKNOWN
        ),
        authority_class=_enum_value(
            AuthorityClass, data.get("authority_class"), AuthorityClass.UNKNOWN
        ),
        runtime_impact=_enum_value(
            RuntimeImpact, data.get("runtime_impact"), RuntimeImpact.UNKNOWN
        ),
        backend_kind=_enum_value(BackendKind, data.get("backend_kind"), BackendKind.NONE),
        connector_kind=_enum_value(
            ConnectorKind, data.get("connector_kind"), ConnectorKind.NONE
        ),
        description=str(data.get("description", "")),
        evidence_refs=list(data.get("evidence_refs", [])),
        requested_actions=list(data.get("requested_actions", [])),
        touches_files=bool(data.get("touches_files", False)),
        touches_tests=bool(data.get("touches_tests", False)),
        touches_docs=bool(data.get("touches_docs", False)),
        touches_ci=bool(data.get("touches_ci", False)),
        touches_security=bool(data.get("touches_security", False)),
        touches_auth=bool(data.get("touches_auth", False)),
        touches_secrets=bool(data.get("touches_secrets", False)),
        touches_public_behavior=bool(data.get("touches_public_behavior", False)),
        touches_destructive_path=bool(data.get("touches_destructive_path", False)),
        requires_network=bool(data.get("requires_network", False)),
        requires_external_service=bool(data.get("requires_external_service", False)),
        requires_live_write=bool(data.get("requires_live_write", False)),
        requires_runner_execution=bool(data.get("requires_runner_execution", False)),
        requires_connector_call=bool(data.get("requires_connector_call", False)),
        requires_mcp_call=bool(data.get("requires_mcp_call", False)),
        requires_dopetask_execution=bool(data.get("requires_dopetask_execution", False)),
        requires_task_orchestrator_write=bool(
            data.get("requires_task_orchestrator_write", False)
        ),
        has_unknown_authority=bool(data.get("has_unknown_authority", True)),
        has_conflicting_evidence=bool(data.get("has_conflicting_evidence", False)),
        has_stale_proof=bool(data.get("has_stale_proof", False)),
        has_missing_proof=bool(data.get("has_missing_proof", False)),
        authority_via_bridge_proxy=bool(data.get("authority_via_bridge_proxy", False)),
        evidence_is_retrieval_derived=bool(
            data.get("evidence_is_retrieval_derived", False)
        ),
        exact_source_fetched=bool(data.get("exact_source_fetched", False)),
        is_ecc_external_intake=bool(data.get("is_ecc_external_intake", False)),
        has_backend_wrapper_proof=bool(data.get("has_backend_wrapper_proof", False)),
        is_repo_changing=bool(data.get("is_repo_changing", False)),
        is_non_trivial=bool(data.get("is_non_trivial", False)),
    )


def _load_json_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        text = Path(input_path).read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            raise click.ClickException(
                "No --input provided and stdin is a TTY; pass JSON via --input or pipe stdin."
            )
        text = sys.stdin.read()
    if not text.strip():
        raise click.ClickException(
            "No JSON payload provided; pass --input or pipe JSON on stdin."
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise click.ClickException("JSON payload must be an object.")
    return payload


def _emit_json(data: dict[str, Any]) -> None:
    click.echo(json.dumps(data, indent=2, sort_keys=True))


@click.group()
def dcp():
    """Read-only DCP routing projection (classify + backend policy recommend)."""


@dcp.command("classify")
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, dir_okay=False),
    help="JSON file with RoutingClassificationInput fields.",
)
def classify_cmd(input_path: str | None) -> None:
    """Classify task attributes into a conservative RouteDecision (JSON)."""
    payload = _load_json_payload(input_path)
    decision = classify_route(_input_from_dict(payload))
    _emit_json(decision.to_dict())


@dcp.command("recommend-backend")
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, dir_okay=False),
    help="JSON file with RouteDecision fields.",
)
def recommend_backend_cmd(input_path: str | None) -> None:
    """Return inert backend policy recommendation for a RouteDecision (JSON)."""
    payload = _load_json_payload(input_path)
    decision = RouteDecision.from_dict(payload)
    recommendation = select_backend_policy(decision)
    _emit_json(recommendation.to_dict())
