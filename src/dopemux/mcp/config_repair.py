"""MCP config repair planner/applier (Packet 003).

Previewable local repair for ``.mcp.json``, ``.envrc.dopemux-mcp``, and agent
bootstrap docs. Never starts/stops containers and never mutates ``~/.claude.json``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .agent_bootstrap import (
    apply_agent_bootstrap,
    default_agent_doc_path,
    plan_agent_bootstrap,
)
from .envrc import (
    is_secret_like_key,
    load_envrc,
    parse_envrc_text,
    redact_value,
)
from .mcp_json import (
    PROJECT_MCP_FILENAME,
    dump_mcp_json,
    is_catalog_owned,
    load_mcp_json_document,
    plan_mcp_json_repairs,
    write_mcp_json,
)
from .runtime_state import (
    ENVRC_FILENAME,
    load_global_claude,
    resolve_identity_view,
)

SCHEMA_VERSION = "1.0"

# Catalog-owned env keys regenerated from init generators (not secret-bearing).
_IDENTITY_KEYS = {
    "DOPEMUX_WORKSPACE_ID",
    "DOPEMUX_WORKSPACE_ROOT",
    "DOPEMUX_PROJECT_ROOT",
    "TASK_ORCHESTRATOR_PROJECT_ROOT",
    "DOPEMUX_INSTANCE_ID",
    "DOPE_MEMORY_WORKSPACE_ID",
    "DOPE_MEMORY_INSTANCE_ID",
    "WORKSPACE_ID",
}


@dataclass
class RepairPlan:
    """Structured repair plan (JSON schema §8)."""

    schema_version: str = SCHEMA_VERSION
    operation: str = "repair-config"
    dry_run: bool = True
    status: str = "PLANNED"  # PLANNED|APPLIED|NOOP|BLOCKED|UNKNOWN
    repo: str = ""
    project_identity: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    planned_changes: List[Dict[str, Any]] = field(default_factory=list)
    preserved_entries: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    blocking_findings: List[Dict[str, Any]] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    # Internal apply payloads (not always dumped in full)
    _mcp_servers: Dict[str, Any] = field(default_factory=dict, repr=False)
    _mcp_other_keys: Dict[str, Any] = field(default_factory=dict, repr=False)
    _envrc_text: Optional[str] = field(default=None, repr=False)
    _agent_plan: Any = field(default=None, repr=False)
    _write_mcp: bool = field(default=False, repr=False)
    _write_envrc: bool = field(default=False, repr=False)
    _write_agent: bool = field(default=False, repr=False)
    # Deferred lease persistence: plan never writes the registry; apply does.
    _lease_persist: Optional[Dict[str, Any]] = field(default=None, repr=False)
    _allocate_ports_fn: Any = field(default=None, repr=False)
    _catalog: Any = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "dry_run": self.dry_run,
            "status": self.status,
            "repo": self.repo,
            "project_identity": dict(self.project_identity),
            "inputs": dict(self.inputs),
            "planned_changes": list(self.planned_changes),
            "preserved_entries": list(self.preserved_entries),
            "warnings": list(self.warnings),
            "blocking_findings": list(self.blocking_findings),
            "next_actions": list(self.next_actions),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False) + "\n"


def _warn(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    item: Dict[str, Any] = {"code": code, "message": message}
    item.update(extra)
    return item


def _block(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    return _warn(code, message, **extra)


def _catalog_owned_env_keys(catalog: Mapping[str, Any], server_names: Sequence[str]) -> set[str]:
    keys = set(_IDENTITY_KEYS)
    servers = catalog.get("servers") or {}
    for name in server_names:
        spec = servers.get(name) or {}
        if not isinstance(spec, dict):
            continue
        if not is_catalog_owned(str(name), catalog):
            continue
        port_var = spec.get("port_var")
        if port_var:
            keys.add(str(port_var))
        for extra in spec.get("extra_port_vars") or []:
            if isinstance(extra, dict) and extra.get("var"):
                keys.add(str(extra["var"]))
        for env_key in list(spec.get("requires_env") or []) + list(spec.get("optional_env") or []):
            # Never treat secret-like required keys as regenerable owned keys
            if not is_secret_like_key(str(env_key)):
                keys.add(str(env_key))
    return keys


def _desired_env_map(
    worktree: str,
    project_root: str,
    server_names: Sequence[str],
    catalog: Mapping[str, Any],
    *,
    allocate_ports_fn: Callable[..., Dict[str, int]],
    project_env_exports_fn: Callable[[str, str], Dict[str, str]],
    dry_run: bool = True,
    existing_envrc: Optional[Mapping[str, str]] = None,
    persist_leases: bool = False,
) -> Dict[str, str]:
    exports = {k: str(v) for k, v in project_env_exports_fn(worktree, project_root).items()}
    # Lease-aware allocation. Planning never persists; only explicit post-apply
    # calls pass persist_leases=True so a blocked/failed apply cannot consume leases.
    try:
        ports = allocate_ports_fn(
            worktree,
            list(server_names),
            catalog,
            project_root=project_root,
            persist=persist_leases and not dry_run,
            dry_run=dry_run or not persist_leases,
            existing_envrc=dict(existing_envrc or {}),
            source="dopemux mcp repair-config",
        )
    except TypeError:
        # Test doubles / legacy callables without lease kwargs
        ports = allocate_ports_fn(
            worktree,
            list(server_names),
            catalog,
            project_root=project_root,
        )
    for k, v in ports.items():
        exports[str(k)] = str(v)
    return exports


def _build_envrc_text(
    worktree: str,
    project_root: str,
    desired: Mapping[str, str],
    *,
    preserve_values: Optional[Mapping[str, str]] = None,
) -> str:
    """Build envrc body: catalog-owned desired keys + preserved safe customs."""
    lines = [
        "# Generated by `dopemux mcp repair-config` / `dopemux mcp init`.",
        f"# Worktree: {worktree}",
        f"# Project:  {project_root}",
        f"# Generated: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "",
    ]
    # Identity exports first (stable order)
    identity_order = [
        "DOPEMUX_WORKSPACE_ID",
        "DOPEMUX_WORKSPACE_ROOT",
        "DOPEMUX_PROJECT_ROOT",
        "TASK_ORCHESTRATOR_PROJECT_ROOT",
        "DOPEMUX_INSTANCE_ID",
        "DOPE_MEMORY_WORKSPACE_ID",
        "DOPE_MEMORY_INSTANCE_ID",
        "WORKSPACE_ID",
    ]
    written: set[str] = set()
    for key in identity_order:
        if key in desired:
            lines.append(f"export {key}={_shell_quote(desired[key])}")
            written.add(key)
    lines.append("")
    # Port / remaining catalog keys sorted
    for key in sorted(k for k in desired if k not in written):
        lines.append(f"export {key}={_shell_quote(desired[key])}")
        written.add(key)

    # Preserve custom non-secret keys not in desired/catalog block
    if preserve_values:
        custom = []
        for key, value in sorted(preserve_values.items()):
            if key in written:
                continue
            if is_secret_like_key(key):
                continue
            custom.append((key, value))
        if custom:
            lines.append("")
            lines.append("# Preserved non-catalog custom exports (repair-config)")
            for key, value in custom:
                lines.append(f"export {key}={_shell_quote(value)}")
    return "\n".join(lines) + "\n"


def _shell_quote(value: str) -> str:
    import shlex

    return shlex.quote(str(value))


def plan_repair(
    repo: Path | str,
    catalog: Mapping[str, Any],
    *,
    dry_run: bool = True,
    process_env: Optional[Mapping[str, str]] = None,
    catalog_paths: Optional[Sequence[str]] = None,
    allocate_ports_fn: Optional[Callable[..., Dict[str, int]]] = None,
    project_env_exports_fn: Optional[Callable[[str, str], Dict[str, str]]] = None,
    render_local_fn: Any = None,
    global_claude_path: Optional[Path] = None,
) -> RepairPlan:
    """Build a deterministic repair plan for the target repo/worktree."""
    repo_path = Path(repo).expanduser().resolve()
    mcp_path = repo_path / PROJECT_MCP_FILENAME
    envrc_path = repo_path / ENVRC_FILENAME
    agent_path = default_agent_doc_path(repo_path)

    plan = RepairPlan(
        dry_run=dry_run,
        status="PLANNED",
        repo=str(repo_path),
        inputs={
            "mcp_json_path": str(mcp_path),
            "envrc_path": str(envrc_path),
            "catalog_paths": list(catalog_paths or []),
            "agent_doc_path": str(agent_path),
        },
        next_actions=[
            "dopemux mcp start",
            "source .envrc.dopemux-mcp",
            "dopemux mcp doctor",
        ],
    )

    # Always emit allocator limitation warnings
    plan.warnings.append(
        _warn(
            "PORT_HASH_BUCKET_COLLISION_RISK",
            "Port allocation uses worktree hash % 100; multi-worktree collisions remain possible.",
        )
    )
    plan.warnings.append(
        _warn(
            "PORT_REBIND_MISSING",
            "Live free-port rebind is not implemented; repair reuses the deterministic allocator only.",
        )
    )
    plan.warnings.append(
        _warn(
            "GLOBAL_CONFIG_NOT_MODIFIED",
            "repair-config never mutates ~/.claude.json; use dopemux mcp sync-globals explicitly.",
        )
    )

    # Identity
    envrc_parsed = load_envrc(envrc_path)
    identity = resolve_identity_view(repo_path, envrc_values=envrc_parsed.values)
    plan.project_identity = {
        "project_id": identity.project_id,
        "workspace_id": identity.workspace_id,
        "project_root": identity.project_root,
        "worktree_root": identity.worktree_root,
        "worktree_hash": identity.worktree_hash,
        "identity_confidence": identity.identity_confidence,
    }

    worktree = identity.worktree_root or str(repo_path)
    project_root = identity.project_root or str(repo_path)

    # Lazy default generators (avoid circular import at module load)
    if allocate_ports_fn is None or project_env_exports_fn is None:
        from dopemux.commands import mcp_commands as _mc

        if allocate_ports_fn is None:
            allocate_ports_fn = _mc._allocate_ports
        if project_env_exports_fn is None:
            project_env_exports_fn = _mc._project_env_exports

    # --- .mcp.json ---
    mcp_doc = load_mcp_json_document(mcp_path)
    if mcp_doc["parse_status"] == "ERROR":
        plan.blocking_findings.append(
            _block(
                "MCP_JSON_PARSE_ERROR",
                f"Malformed .mcp.json: {mcp_doc.get('error')}",
            )
        )
        plan.status = "BLOCKED"
        return plan

    existing_servers = mcp_doc.get("servers") or {}
    raw_doc = mcp_doc.get("raw_document") or {}
    other_keys = {k: v for k, v in raw_doc.items() if k != "mcpServers"} if isinstance(raw_doc, dict) else {}

    # Detect secret-like values inside mcp.json entries (block apply)
    for name, entry in existing_servers.items():
        if not isinstance(entry, dict):
            continue
        blob = json.dumps(entry)
        if re.search(r"(?i)(BEGIN (RSA |OPENSSH )?PRIVATE KEY|password\s*=)", blob):
            plan.blocking_findings.append(
                _block(
                    "MCP_JSON_SECRET_LIKE",
                    f"Secret-like material detected in mcpServers.{name}; manual intervention required.",
                    service=str(name),
                )
            )

    merged_servers, mcp_changes, preserved = plan_mcp_json_repairs(
        existing_servers,
        catalog,
        mcp_json_path=str(mcp_path),
        include_defaults=True,
        render_fn=render_local_fn,
    )
    plan.planned_changes.extend(mcp_changes)
    plan.preserved_entries.extend(preserved)
    plan._mcp_servers = merged_servers
    plan._mcp_other_keys = other_keys
    plan._write_mcp = bool(mcp_changes) or mcp_doc["parse_status"] == "MISSING"

    if mcp_doc["parse_status"] == "MISSING":
        plan.planned_changes.insert(
            0,
            {
                "path": str(mcp_path),
                "kind": "create",
                "reason": "MISSING_MCP_JSON",
                "service": None,
                "before": None,
                "after": {"servers": sorted(merged_servers.keys())},
                "safe": True,
            },
        )
        plan._write_mcp = True

    # Annotate transport repair codes for report consumers
    for ch in plan.planned_changes:
        if ch.get("reason") == "TRANSPORT_MISMATCH":
            ch["finding_code"] = "MCP_JSON_TRANSPORT_REPAIRED"
        elif ch.get("reason") == "URL_MISMATCH":
            ch["finding_code"] = "MCP_JSON_URL_REPAIRED"

    # --- envrc ---
    # Services for port allocation: defaults + any catalog-owned already present
    server_names: List[str] = []
    for name in (catalog.get("defaults") or {}).get("per_worktree") or []:
        if is_catalog_owned(str(name), catalog) and name not in server_names:
            server_names.append(str(name))
    for name in existing_servers:
        if is_catalog_owned(str(name), catalog) and name not in server_names:
            server_names.append(str(name))

    # Always compute ports without writing leases during plan construction.
    # Leases are persisted only after apply_repair successfully writes config.
    desired_env = _desired_env_map(
        worktree,
        project_root,
        server_names,
        catalog,
        allocate_ports_fn=allocate_ports_fn,
        project_env_exports_fn=project_env_exports_fn,
        dry_run=True,
        persist_leases=False,
        existing_envrc=envrc_parsed.values if envrc_parsed.present else {},
    )
    plan._allocate_ports_fn = allocate_ports_fn
    plan._catalog = catalog
    plan._lease_persist = {
        "worktree": worktree,
        "project_root": project_root,
        "server_names": list(server_names),
        "existing_envrc": dict(desired_env),
    }
    owned_keys = _catalog_owned_env_keys(catalog, server_names)

    # Secret-like handling on existing envrc
    secret_block = False
    preserve_customs: Dict[str, str] = {}
    if envrc_parsed.present and envrc_parsed.values:
        for key, value in envrc_parsed.values.items():
            if key in owned_keys:
                continue
            if is_secret_like_key(key):
                plan.warnings.append(
                    _warn(
                        "ENVRC_SECRET_LIKE_VALUE_REDACTED",
                        f"Secret-like key {key} redacted in plan; value not printed.",
                        key=key,
                        value=redact_value(key, value),
                    )
                )
                # Uncertain preservation of secrets → block apply
                secret_block = True
                plan.blocking_findings.append(
                    _block(
                        "ENVRC_SECRET_LIKE_UNCERTAIN",
                        f"Envrc contains secret-like key `{key}` that is not catalog-owned; "
                        "apply blocked for manual review.",
                        key=key,
                    )
                )
            else:
                preserve_customs[key] = value

    if secret_block:
        plan.status = "BLOCKED"

    envrc_missing = not envrc_parsed.present
    envrc_stale = False
    if envrc_parsed.present and envrc_parsed.parse_status in {"OK", "PARTIAL"}:
        for key, want in desired_env.items():
            if envrc_parsed.values.get(key) != want:
                envrc_stale = True
                break
        for key in owned_keys:
            if key in desired_env and key not in envrc_parsed.values:
                envrc_stale = True
                break
        # Partial parse is repairable (regenerate), not a hard block.
        if envrc_parsed.parse_status == "PARTIAL":
            envrc_stale = True
    elif envrc_parsed.present and envrc_parsed.parse_status == "ERROR":
        plan.blocking_findings.append(
            _block(
                "ENVRC_PARSE_ERROR",
                f"Envrc parse errors: {'; '.join(envrc_parsed.errors)}",
            )
        )
        plan.status = "BLOCKED"

    new_envrc_text = _build_envrc_text(
        worktree,
        project_root,
        desired_env,
        preserve_values=preserve_customs,
    )
    plan._envrc_text = new_envrc_text

    if envrc_missing:
        plan.planned_changes.append(
            {
                "path": str(envrc_path),
                "kind": "create",
                "reason": "ENVRC_REGENERATED",
                "service": None,
                "before": None,
                "after": {
                    "keys": sorted(desired_env.keys()),
                    "sample": {
                        k: redact_value(k, desired_env[k])
                        for k in sorted(desired_env.keys())[:8]
                    },
                },
                "safe": not secret_block,
            }
        )
        plan._write_envrc = True
    elif envrc_stale and plan.status != "BLOCKED":
        plan.planned_changes.append(
            {
                "path": str(envrc_path),
                "kind": "rewrite",
                "reason": "ENVRC_PATCHED",
                "service": None,
                "before": {
                    "keys_present": list(envrc_parsed.keys_present),
                },
                "after": {
                    "keys": sorted(desired_env.keys()) + sorted(preserve_customs.keys()),
                },
                "safe": not secret_block,
            }
        )
        plan._write_envrc = True
    elif not envrc_stale and not envrc_missing:
        # noop envrc
        pass

    # --- agent bootstrap ---
    agent_plan = plan_agent_bootstrap(repo_path, doc_path=agent_path)
    plan._agent_plan = agent_plan
    if agent_plan.kind != "noop":
        plan.planned_changes.append(agent_plan.to_change_dict())
        plan._write_agent = True

    # --- global/local duplicate warnings (read-only) ---
    global_info = load_global_claude(global_claude_path)
    if global_info.get("parse_status") == "OK":
        global_servers = global_info.get("servers") or {}
        for name in merged_servers:
            if name in global_servers and is_catalog_owned(str(name), catalog):
                plan.warnings.append(
                    _warn(
                        "GLOBAL_LOCAL_DUPLICATE",
                        f"`{name}` appears in both local .mcp.json and ~/.claude.json; "
                        "prefer local per-worktree entry and clean global duplicates manually.",
                        service=str(name),
                    )
                )

    # Status synthesis
    if plan.status == "BLOCKED":
        plan.next_actions = [
            "Resolve blocking_findings manually",
            "dopemux mcp repair-config --dry-run --json",
        ]
        return plan

    if not plan.planned_changes:
        plan.status = "NOOP"
        plan.warnings.append(_warn("REPAIR_NOOP", "Config already matches catalog-owned desired state."))
    else:
        plan.status = "PLANNED"
        plan.warnings.append(
            _warn("REPAIR_PLAN_CREATED", f"{len(plan.planned_changes)} planned change(s).")
        )

    return plan


def apply_repair(plan: RepairPlan) -> RepairPlan:
    """Apply a plan to the target repo. Never touches globals or Docker."""
    if plan.status == "BLOCKED":
        return plan
    if plan.dry_run:
        # Caller mistake — do not write
        plan.blocking_findings.append(
            _block("APPLY_ON_DRY_RUN", "apply_repair called with dry_run=True; refusing writes.")
        )
        plan.status = "BLOCKED"
        return plan
    if plan.status == "NOOP" and not (plan._write_mcp or plan._write_envrc or plan._write_agent):
        return plan

    repo = Path(plan.repo)
    mcp_path = Path(plan.inputs["mcp_json_path"])
    envrc_path = Path(plan.inputs["envrc_path"])

    try:
        if plan._write_mcp:
            write_mcp_json(mcp_path, plan._mcp_servers, other_keys=plan._mcp_other_keys or None)
        if plan._write_envrc and plan._envrc_text is not None:
            envrc_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = envrc_path.with_suffix(envrc_path.suffix + ".tmp")
            tmp.write_text(plan._envrc_text, encoding="utf-8")
            tmp.replace(envrc_path)
        if plan._write_agent and plan._agent_plan is not None:
            apply_agent_bootstrap(plan._agent_plan)
    except OSError as exc:
        plan.blocking_findings.append(_block("APPLY_IO_ERROR", str(exc)))
        plan.status = "BLOCKED"
        return plan

    # Persist port leases only after config files were written successfully.
    if plan._lease_persist and plan._allocate_ports_fn is not None and plan._catalog is not None:
        lp = plan._lease_persist
        try:
            _desired_env_map(
                str(lp["worktree"]),
                str(lp["project_root"]),
                list(lp.get("server_names") or []),
                plan._catalog,
                allocate_ports_fn=plan._allocate_ports_fn,
                project_env_exports_fn=lambda w, p: {},
                dry_run=False,
                persist_leases=True,
                existing_envrc=dict(lp.get("existing_envrc") or {}),
            )
        except Exception as exc:  # noqa: BLE001 — config already written; warn only
            plan.warnings.append(
                _warn(
                    "LEASE_PERSIST_FAILED",
                    f"Config applied but lease registry write failed: {exc}",
                )
            )

    plan.status = "APPLIED"
    plan.warnings.append(_warn("REPAIR_APPLIED", f"Wrote repairs under {repo}."))
    plan.dry_run = False
    return plan


def format_repair_human(plan: RepairPlan) -> str:
    """Compact human summary for CLI."""
    lines = [
        f"repair-config {plan.status}  dry_run={plan.dry_run}",
        f"repo: {plan.repo}",
        f"changes: {len(plan.planned_changes)}  preserved: {len(plan.preserved_entries)}  "
        f"warnings: {len(plan.warnings)}  blocking: {len(plan.blocking_findings)}",
    ]
    for ch in plan.planned_changes[:10]:
        lines.append(
            f"  • {ch.get('kind')} {ch.get('path')} "
            f"[{ch.get('reason')}] service={ch.get('service')}"
        )
    if len(plan.planned_changes) > 10:
        lines.append(f"  … {len(plan.planned_changes) - 10} more")
    for b in plan.blocking_findings[:5]:
        lines.append(f"  ✗ {b.get('code')}: {b.get('message')}")
    if plan.next_actions:
        lines.append("next:")
        for a in plan.next_actions:
            lines.append(f"  → {a}")
    return "\n".join(lines) + "\n"
