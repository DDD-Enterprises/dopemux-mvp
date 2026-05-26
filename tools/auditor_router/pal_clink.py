from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import ClinkConfigInspection, pal_clink_route_from_inspection


REPO_CLINK_CONFIG_RELATIVE = Path(
    "docker/mcp-servers-source/pal/pal-mcp-server/conf/cli_clients"
)
SUPPORTED_AUDIT_CLIENTS = {
    "claude-audit": "claude",
    "gemini-audit": "gemini",
}
AUDIT_ROLE_NAMES = {"default", "codereviewer"}
AUDIT_PROMPT_NAME = "default_codereviewer.txt"

MUTATION_TOKENS = {
    "--yolo",
    "-y",
    "acceptEdits",
    "bypassPermissions",
    "dontAsk",
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-skip-permissions",
    "--allow-all",
    "--allow-all-tools",
    "--allow-all-paths",
    "--allow-all-urls",
    "--autopilot",
    "auto_edit",
    "--add-dir",
}
VALUE_COUPLED_MUTATION_PATTERNS = {
    ("--permission-mode", "acceptEdits"),
    ("--permission-mode", "bypassPermissions"),
    ("--permission-mode", "dontAsk"),
    ("--approval-mode", "yolo"),
    ("--approval-mode", "auto_edit"),
    ("--mode", "autopilot"),
}


def discover_clink_config_paths(
    *,
    repo_root: Path | None = None,
    config_roots: Iterable[Path] | None = None,
) -> list[Path]:
    roots = list(config_roots) if config_roots is not None else []
    if not roots:
        root = repo_root or Path.cwd()
        roots = [root / REPO_CLINK_CONFIG_RELATIVE]

    paths: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*-audit.json"), key=_candidate_sort_key):
            if path.stem in SUPPORTED_AUDIT_CLIENTS:
                paths.append(path)
    return paths


def load_clink_client_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def effective_args_for_config(
    config: dict[str, Any],
    *,
    internal_args: Iterable[str] | None = None,
) -> list[str]:
    args = [str(item) for item in (internal_args or [])]
    for key in ("additional_args", "config_args", "args"):
        args.extend(str(item) for item in config.get(key) or [])
    roles = config.get("roles") or {}
    for role_name in sorted(roles):
        role = roles.get(role_name) or {}
        args.extend(str(item) for item in role.get("role_args") or [])
    return args


def detect_mutation_flags(args: Iterable[str]) -> list[str]:
    tokens = [str(item) for item in args]
    found: list[str] = []
    for token in tokens:
        if token in MUTATION_TOKENS:
            _append_once(found, token)
    for index, token in enumerate(tokens[:-1]):
        pair = (token, tokens[index + 1])
        if pair in VALUE_COUPLED_MUTATION_PATTERNS:
            _append_once(found, f"{pair[0]} {pair[1]}")
    return found


def resolve_or_classify_clink_config(
    path: Path,
    *,
    internal_args: Iterable[str] | None = None,
) -> ClinkConfigInspection:
    return inspect_clink_client_config(path, internal_args=internal_args)


def inspect_clink_client_config(
    path: Path,
    *,
    internal_args: Iterable[str] | None = None,
) -> ClinkConfigInspection:
    try:
        config = load_clink_client_config(path)
    except Exception as exc:
        return _unsafe(path, None, None, f"Config could not be parsed: {exc}")

    client_name = str(config.get("name") or path.stem)
    underlying_cli = str(config.get("runner") or "").strip() or client_name.split("-")[0]
    expected_cli = SUPPORTED_AUDIT_CLIENTS.get(path.stem)
    if expected_cli is None:
        return _unsafe(
            path,
            client_name,
            underlying_cli,
            "Only claude-audit and gemini-audit configs are supported.",
            config=config,
        )
    if client_name != path.stem or underlying_cli != expected_cli:
        return _unsafe(
            path,
            client_name,
            underlying_cli,
            "Audit config name and runner must match the supported audit client.",
            config=config,
        )

    mutation_flags = detect_mutation_flags(
        effective_args_for_config(config, internal_args=internal_args)
    )
    if mutation_flags:
        return _unsafe(
            path,
            client_name,
            underlying_cli,
            "Mutation-capable clink args detected.",
            mutation_flags=mutation_flags,
            config=config,
        )

    role_error = _role_contract_error(config)
    if role_error:
        return _unsafe(path, client_name, underlying_cli, role_error, config=config)

    return ClinkConfigInspection(
        path=path,
        client_name=client_name,
        underlying_cli=underlying_cli,
        status="AVAILABLE",
        risk="LOW",
        reason="Audit-safe PAL clink config is available by static inspection.",
        mutation_flags=[],
        audit_safe_config_proven=True,
        config=config,
    )


def classify_pal_clink_route(
    *,
    repo_root: Path | None = None,
    config_roots: Iterable[Path] | None = None,
    internal_args: Iterable[str] | None = None,
) -> dict[str, Any]:
    paths = discover_clink_config_paths(repo_root=repo_root, config_roots=config_roots)
    inspections = [
        inspect_clink_client_config(path, internal_args=internal_args) for path in paths
    ]
    for inspection in inspections:
        if inspection.status == "AVAILABLE":
            return pal_clink_route_from_inspection(inspection)
    if inspections:
        return pal_clink_route_from_inspection(inspections[0])
    reason = "No supported claude-audit or gemini-audit PAL clink configs found."
    if _contains_copilot_audit(config_roots):
        reason = (
            "Copilot PAL clink support is deferred; no supported claude-audit "
            "or gemini-audit configs found."
        )
    return pal_clink_route_from_inspection(
        ClinkConfigInspection(
            path=None,
            client_name=None,
            underlying_cli=None,
            status="TOOLING_UNSAFE",
            risk="HIGH",
            reason=reason,
            mutation_flags=[],
            audit_safe_config_proven=False,
        )
    )


def normalize_pal_clink_audit_output(
    payload: dict[str, Any],
    *,
    route: dict[str, Any],
    report_path: str,
) -> dict[str, Any]:
    findings = [_normalize_finding(item) for item in payload.get("findings") or []]
    blocking_findings = [
        item
        for item in findings
        if item["severity"] == "BLOCKING" or bool(item.get("blocking"))
    ]
    risks = [str(item) for item in payload.get("risks") or []]

    status = "NEEDS_SUPERVISOR"
    supervisor_risk: str | None = None
    if route.get("clink_mutation_flags_detected") or not route.get(
        "audit_safe_config_proven"
    ):
        supervisor_risk = "PAL clink route used a mutation-capable or unproven config."
    elif payload.get("truncated") or payload.get("is_truncated"):
        supervisor_risk = "PAL clink output was truncated."
    elif blocking_findings:
        status = "FAIL"
    elif payload.get("status") == "error":
        supervisor_risk = "PAL clink ToolOutput status was error."
    elif not payload.get("verdict"):
        supervisor_risk = "PAL clink output did not include an explicit verdict."
    else:
        verdict = str(payload["verdict"])
        if verdict == "FAIL":
            status = "FAIL"
        elif verdict == "PASS_WITH_RISKS" or risks:
            status = "PASS_WITH_RISKS"
        elif verdict == "PASS":
            status = "PASS"
        else:
            supervisor_risk = f"Unsupported PAL clink verdict: {verdict}"

    if supervisor_risk:
        status = "NEEDS_SUPERVISOR"
        risks = [supervisor_risk]

    return build_pal_clink_embedded_audit_object(
        status=status,
        route=route,
        report_path=report_path,
        findings=findings,
        remaining_risks=risks,
        exit_code=0 if status in {"PASS", "PASS_WITH_RISKS"} else 1,
    )


def build_pal_clink_embedded_audit_object(
    *,
    status: str,
    route: dict[str, Any],
    report_path: str,
    findings: list[dict[str, Any]],
    remaining_risks: list[str],
    exit_code: int,
) -> dict[str, Any]:
    return {
        "required": True,
        "status": status,
        "auditor_tool": "pal-mcp-clink",
        "auditor_model": _embedded_audit_model(route),
        "invocation": route.get("invocation_template") or "PAL MCP clink host handoff",
        "exit_code": exit_code,
        "report_path": report_path,
        "findings": findings,
        "fixes_applied": [],
        "remaining_risks": remaining_risks,
        "skip_reason": None,
    }


def _role_contract_error(config: dict[str, Any]) -> str | None:
    roles = config.get("roles") or {}
    if set(roles) != AUDIT_ROLE_NAMES:
        return "Audit roles must be exactly default,codereviewer."
    for role_name in sorted(AUDIT_ROLE_NAMES):
        role = roles.get(role_name) or {}
        prompt_name = Path(str(role.get("prompt_path") or "")).name
        if prompt_name != AUDIT_PROMPT_NAME:
            return f"Role {role_name} must use {AUDIT_PROMPT_NAME}."
        if list(role.get("role_args") or []) != []:
            return f"Role {role_name} must have empty role_args."
    return None


def _candidate_sort_key(path: Path) -> tuple[int, str]:
    priority = {"claude-audit": 0, "gemini-audit": 1}
    return (priority.get(path.stem, 99), path.name)


def _contains_copilot_audit(config_roots: Iterable[Path] | None) -> bool:
    if config_roots is None:
        return False
    return any((root / "copilot-audit.json").exists() for root in config_roots)


def _unsafe(
    path: Path | None,
    client_name: str | None,
    underlying_cli: str | None,
    reason: str,
    *,
    mutation_flags: list[str] | None = None,
    config: dict[str, Any] | None = None,
) -> ClinkConfigInspection:
    return ClinkConfigInspection(
        path=path,
        client_name=client_name,
        underlying_cli=underlying_cli,
        status="TOOLING_UNSAFE",
        risk="HIGH",
        reason=reason,
        mutation_flags=mutation_flags or [],
        audit_safe_config_proven=False,
        config=config,
    )


def _append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _normalize_finding(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        item = {"body": str(item)}
    return {
        "id": str(item.get("id") or "PAL-CLINK-FINDING"),
        "severity": str(item.get("severity") or "INFO"),
        "title": str(item.get("title") or "PAL clink finding"),
        "status": str(item.get("status") or "OPEN"),
        "body": str(item.get("body") or ""),
    }


def _embedded_audit_model(route: dict[str, Any]) -> str:
    if route.get("underlying_cli") == "claude":
        return "sonnet"
    if route.get("underlying_cli") == "gemini":
        return "gemini"
    return "unknown"
