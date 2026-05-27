from __future__ import annotations

import json
import os
import shlex
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .models import ClinkConfigInspection, pal_clink_route_from_inspection


REPO_CLINK_CONFIG_RELATIVE = Path(
    "docker/mcp-servers-source/pal/pal-mcp-server/conf/cli_clients"
)
CLI_CLIENTS_CONFIG_ENV_VAR = "CLI_CLIENTS_CONFIG_PATH"
USER_CLINK_CONFIG_RELATIVE = Path(".zen/cli_clients")
SUPPORTED_AUDIT_CLIENTS = {
    "claude-audit": "claude",
    "gemini-audit": "gemini",
}
AUDIT_ROLE_NAMES = {"default", "codereviewer"}
AUDIT_PROMPT_PATH = PurePosixPath("systemprompts/clink/default_codereviewer.txt")

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
    roots = _default_config_roots(repo_root) if config_roots is None else list(config_roots)
    paths_by_client: dict[str, Path] = {}
    for root in roots:
        for path in _iter_config_root_paths(root):
            try:
                config = json.loads(path.read_text(encoding="utf-8"))
                client = config.get("client")
                if client in SUPPORTED_AUDIT_CLIENTS:
                    paths_by_client[client] = path
                elif path.stem in SUPPORTED_AUDIT_CLIENTS:
                    paths_by_client[path.stem] = path
            except Exception:
                if path.stem in SUPPORTED_AUDIT_CLIENTS:
                    paths_by_client[path.stem] = path
    return sorted(paths_by_client.values(), key=_candidate_sort_key)


def load_clink_client_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_args(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    raise ValueError("Arguments field must be a list or a string.")


def effective_args_for_config(
    config: dict[str, Any],
    *,
    internal_args: Iterable[str] | None = None,
) -> list[str]:
    args = [str(item) for item in (internal_args or [])]
    for key in ("additional_args", "config_args", "args"):
        val = config.get(key)
        if val is not None:
            args.extend(_as_args(val))
    roles = config.get("roles")
    if roles is None:
        roles = {}
    if not isinstance(roles, dict):
        return args
    for role_name in sorted(roles):
        role = roles.get(role_name)
        if role is None:
            role = {}
        if not isinstance(role, dict):
            continue
        role_args_val = role.get("role_args")
        if role_args_val is not None:
            args.extend(_as_args(role_args_val))
    return args


def detect_mutation_flags(args: Iterable[str]) -> list[str]:
    tokens = [str(item) for item in args]
    found: list[str] = []
    for token in tokens:
        if token in MUTATION_TOKENS:
            _append_once(found, token)
            continue
        if "=" in token:
            flag, value = token.split("=", 1)
            if (
                flag in MUTATION_TOKENS
                or (flag, value) in VALUE_COUPLED_MUTATION_PATTERNS
            ):
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
    if not isinstance(config, dict):
        return _unsafe(
            path,
            None,
            None,
            "Config payload must be a JSON object.",
        )

    raw_client_name = config.get("name")
    raw_underlying_cli = config.get("runner")
    client_name = str(raw_client_name or "").strip()
    underlying_cli = str(raw_underlying_cli or "").strip()
    declared_client = config.get("client") or path.stem
    expected_cli = SUPPORTED_AUDIT_CLIENTS.get(declared_client)
    if expected_cli is None:
        return _unsafe(
            path,
            client_name,
            underlying_cli,
            "Only claude-audit and gemini-audit configs are supported.",
            config=config,
        )
    if not client_name or not underlying_cli:
        return _unsafe(
            path,
            client_name or None,
            underlying_cli or None,
            "Audit config must explicitly define name and runner.",
            config=config,
        )
    if client_name != declared_client or underlying_cli != expected_cli:
        return _unsafe(
            path,
            client_name,
            underlying_cli,
            "Audit config name and runner must match the supported audit client.",
            config=config,
        )

    command_error = _command_contract_error(config, expected_cli)
    if command_error:
        return _unsafe(path, client_name, underlying_cli, command_error, config=config)

    try:
        effective_args = effective_args_for_config(config, internal_args=internal_args)
    except ValueError as err:
        inspection = _unsafe(path, client_name, underlying_cli, str(err), config=config)
        inspection.status = "INVALID"
        return inspection

    mutation_flags = detect_mutation_flags(effective_args)
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
        inspection = _unsafe(path, client_name, underlying_cli, role_error, config=config)
        if "invalid role_args" in role_error:
            inspection.status = "INVALID"
        return inspection

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
    from collections.abc import Mapping
    if not isinstance(payload, Mapping):
        return build_pal_clink_embedded_audit_object(
            status="NEEDS_SUPERVISOR",
            route=route,
            report_path=report_path,
            findings=[],
            remaining_risks=["PAL clink payload was not a valid mapping."],
            exit_code=1,
        )
    raw_findings = list(payload.get("findings") or [])
    findings = [_normalize_finding(item) for item in raw_findings]
    blocking_findings = [
        item for item in raw_findings if _raw_finding_is_blocking(item)
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
    roles = config.get("roles")
    if roles is None:
        roles = {}
    if not isinstance(roles, dict):
        return "Audit roles must be an object with default,codereviewer entries."
    if set(roles) != AUDIT_ROLE_NAMES:
        return "Audit roles must be exactly default,codereviewer."
    for role_name in sorted(AUDIT_ROLE_NAMES):
        role = roles.get(role_name)
        if role is None:
            role = {}
        if not isinstance(role, dict):
            return f"Role {role_name} must be an object."
        prompt_path = _canonical_role_prompt_path(role.get("prompt_path"))
        if prompt_path != AUDIT_PROMPT_PATH:
            return f"Role {role_name} must use {AUDIT_PROMPT_PATH}."
        role_args_val = role.get("role_args")
        if role_args_val is not None:
            if not isinstance(role_args_val, list):
                return f"Role {role_name} has invalid role_args: must be a list"
            try:
                role_args = _as_args(role_args_val)
            except ValueError as err:
                return f"Role {role_name} has invalid role_args: {err}"
            if role_args != []:
                return f"Role {role_name} must have empty role_args."
    return None


def _command_contract_error(config: dict[str, Any], expected_cli: str) -> str | None:
    command = str(config.get("command") or "").strip()
    if not command:
        return f"Audit config command must be exactly {expected_cli}."
    try:
        parts = shlex.split(command)
    except ValueError:
        return "Audit config command could not be parsed safely."
    if parts != [expected_cli]:
        return f"Audit config command must be exactly {expected_cli}."
    return None


def _default_config_roots(repo_root: Path | None) -> list[Path]:
    root = repo_root or Path.cwd()
    roots = [root / REPO_CLINK_CONFIG_RELATIVE]
    env_path_raw = os.environ.get(CLI_CLIENTS_CONFIG_ENV_VAR)
    if env_path_raw:
        roots.append(Path(env_path_raw).expanduser())
    roots.append(Path.home() / USER_CLINK_CONFIG_RELATIVE)
    return roots


def _iter_config_root_paths(root: Path) -> list[Path]:
    if root.is_file() and root.suffix.lower() == ".json":
        return [root]
    if root.is_dir():
        return sorted(root.glob("*-audit.json"), key=_candidate_sort_key)
    return []


def _canonical_role_prompt_path(value: Any) -> PurePosixPath | None:
    raw_path = str(value or "")
    raw_parts = raw_path.split("/")
    prompt_path = PurePosixPath(raw_path)
    if (
        prompt_path.is_absolute()
        or any(part in {"", ".", ".."} for part in raw_parts)
    ):
        return None
    return prompt_path


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


def _raw_finding_is_blocking(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return str(item.get("severity") or "INFO") == "BLOCKING" or bool(
        item.get("blocking", False)
    )


def _embedded_audit_model(route: dict[str, Any]) -> str:
    if route.get("underlying_cli") == "claude":
        return "sonnet"
    if route.get("underlying_cli") == "gemini":
        return "gemini"
    return "unknown"
