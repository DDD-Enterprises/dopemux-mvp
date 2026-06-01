from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


AVAILABLE_STATUSES = {"AVAILABLE", "AVAILABLE_WITH_RISKS"}
PAL_CLINK_TOOL = "pal-mcp-clink"
PAL_CLINK_SCHEMA_SAFE_CLIS = {"claude", "gemini"}


@dataclass
class ClinkConfigInspection:
    path: Path | None
    client_name: str | None
    underlying_cli: str | None
    status: str
    risk: str
    reason: str
    mutation_flags: list[str]
    audit_safe_config_proven: bool
    config: dict[str, Any] | None = None


def pal_clink_route_from_inspection(
    inspection: ClinkConfigInspection,
) -> dict[str, Any]:
    model = inspection.client_name if inspection.audit_safe_config_proven else None
    invocation_template = None
    if inspection.client_name:
        invocation_template = (
            "pal-clink --client "
            f"{inspection.client_name} --role codereviewer "
            "--input PAL_CLINK_AUDIT_INPUT.md "
            "--output PAL_CLINK_AUDIT_OUTPUT.json"
        )
    return {
        "tool": PAL_CLINK_TOOL,
        "installed": inspection.audit_safe_config_proven,
        "executable": None,
        "version": None,
        "help_command": None,
        "help_exit_code": None,
        "noninteractive_mode_proven": inspection.audit_safe_config_proven,
        "model_selector_proven": inspection.audit_safe_config_proven,
        "model": model,
        "auth_status": "NOT_CHECKED",
        "timeout_used": False,
        "repo_context_sent": False,
        "tools_disabled": True,
        "status": inspection.status,
        "risk": inspection.risk,
        "reason": inspection.reason,
        "underlying_cli": _schema_safe_underlying_cli(inspection.underlying_cli),
        "clink_client_name": inspection.client_name,
        "clink_role": "codereviewer" if inspection.client_name else None,
        "clink_config_path": str(inspection.path) if inspection.path else None,
        "clink_mutation_flags_detected": inspection.mutation_flags,
        "audit_safe_config_proven": inspection.audit_safe_config_proven,
        "requires_operator_approval": True,
        "invocation_template": invocation_template,
    }


def _schema_safe_underlying_cli(value: str | None) -> str | None:
    if value in PAL_CLINK_SCHEMA_SAFE_CLIS:
        return value
    return None


def needs_supervisor_route(reason: str) -> dict[str, Any]:
    return pal_clink_route_from_inspection(
        ClinkConfigInspection(
            path=None,
            client_name=None,
            underlying_cli=None,
            status="NEEDS_SUPERVISOR",
            risk="HIGH",
            reason=reason,
            mutation_flags=[],
            audit_safe_config_proven=False,
        )
    )


def normalize_route_record(route: dict[str, Any]) -> dict[str, Any]:
    if route.get("tool") == PAL_CLINK_TOOL:
        return route
    status = str(route.get("status") or "NEEDS_SUPERVISOR")
    return {
        "tool": str(route.get("tool") or "unknown"),
        "installed": status in AVAILABLE_STATUSES,
        "executable": route.get("executable"),
        "version": route.get("version"),
        "help_command": route.get("help_command"),
        "help_exit_code": route.get("help_exit_code"),
        "noninteractive_mode_proven": bool(
            route.get("noninteractive_mode_proven", status in AVAILABLE_STATUSES)
        ),
        "model_selector_proven": bool(
            route.get("model_selector_proven", status in AVAILABLE_STATUSES)
        ),
        "model": route.get("model"),
        "auth_status": _auth_status_for_route(route),
        "timeout_used": bool(route.get("timeout_used", status == "TIMEOUT")),
        "repo_context_sent": bool(route.get("repo_context_sent", False)),
        "tools_disabled": bool(route.get("tools_disabled", True)),
        "status": status,
        "risk": str(route.get("risk") or "HIGH"),
        "reason": str(route.get("reason") or "No route reason recorded."),
    }


def _auth_status_for_route(route: dict[str, Any]) -> str:
    if route.get("auth_status"):
        return str(route["auth_status"])
    if route.get("status") == "AUTH_REQUIRED":
        return "AUTH_REQUIRED"
    return "NOT_CHECKED"
