"""Deterministic MCP profile selection and inventory digests (ADR-DMX-MCPPROF-001).

Profiles are exposure projections declared in ``mcp_catalog.yaml``. This module
never mutates service authority, never invents an implicit ``all`` profile, and
fails closed on unknown profiles, unsafe domain facades, and inventory drift.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

# Explicit named compatibility default — never "all".
COMPATIBILITY_PROFILE = "core-code"

# Forbidden profile tokens (fail closed; no implicit full surface).
_FORBIDDEN_PROFILE_NAMES = frozenset({"all", "*", "any", "full", "everything"})

# Official GitHub MCP write / mutation tool names (normal profiles deny these).
GITHUB_WRITE_TOOLS = frozenset(
    {
        "create_or_update_file",
        "create_repository",
        "create_branch",
        "push_files",
        "create_issue",
        "update_issue",
        "add_issue_comment",
        "create_pull_request",
        "create_pull_request_review",
        "merge_pull_request",
        "update_pull_request",
        "update_pull_request_branch",
        "create_pull_request_comment",
        "add_comment_to_pending_review",
        "submit_pending_pull_request_review",
        "delete_pending_pull_request_review",
        "create_and_submit_pull_request_review",
        "request_copilot_review",
        "assign_copilot_to_issue",
        "delete_file",
        "fork_repository",
        "create_gist",
        "update_gist",
        "delete_gist",
        "star_repository",
        "unstar_repository",
        "follow_user",
        "unfollow_user",
        "create_repository_using_template",
        "run_workflow",
        "cancel_workflow_run",
        "rerun_workflow_run",
        "rerun_failed_jobs",
        "delete_workflow_run_logs",
    }
)

# Side-effect classifications allowed on repo-domain-read tools.
_DOMAIN_READ_OK_SIDE_EFFECTS = frozenset({"READ_ONLY_NO_DURABLE_SIDE_EFFECT"})

# Fixed domain facade paths (repo-root relative).
DOMAIN_READ_EXECUTABLE_REL = Path("scripts/mcp/domain-read")
DOMAIN_READ_MANIFEST_REL = Path("mcp/domain-read-tools.json")

# Global write / admin / shell exclusions for normal profiles (ADR §9).
_GLOBAL_EXCLUDED_TOOLS: frozenset[str] = frozenset(
    {
        # ConPort admin (also from catalog admin_tools; listed for defense in depth)
        "fork_instance",
        "promote",
        "promote_all",
        # Workflow transitions
        "advance_item",
        "claim_item",
        "complete_tree",
        "create_work_tree",
        "manage_dependencies",
        "manage_items",
        "manage_notes",
        # Memory durable writes / corrections
        "memory_correct",
        "memory_generate_reflection",
        "memory_store",
        "memory_mark_issue",
        # Index / sync / clear / autonomous control
        "clear_index",
        "clear_search_metrics",
        "configure_decision_auto_indexing",
        "index_docs",
        "index_workspace",
        "sync_docs",
        "sync_workspace",
        "start_autonomous_docs_indexing",
        "start_autonomous_indexing",
        "stop_autonomous_docs_indexing",
        "stop_autonomous_indexing",
        # Serena shell / editor mutation surface
        "execute_shell_command",
        "create_text_file",
        "replace_content",
        "replace_symbol_body",
        "insert_after_symbol",
        "insert_before_symbol",
        "rename_symbol",
        "write_memory",
        "delete_memory",
        "edit_memory",
        "rename_memory",
    }
)

_GITHUB_WRITE_NAME_RE = re.compile(
    r"^(create_|update_|delete_|merge_|push_|fork_|star_|unstar_|follow_|unfollow_|"
    r"assign_|request_|submit_|cancel_|rerun_|run_workflow)",
    re.IGNORECASE,
)


class ProfilePolicyError(ValueError):
    """Fail-closed profile policy error."""


@dataclass(frozen=True)
class ProfileInventory:
    """Locked inventory for one resolved profile."""

    profile: str
    description: str
    selected_servers: list[str]
    blocked_servers: dict[str, str]
    visible_tools: dict[str, list[str]]  # server -> sorted tool names
    excluded_tools: dict[str, list[str]]  # server -> sorted excluded names
    visible_tool_count: int
    profile_digest: str
    tool_schema_digest: str
    github_read_only: bool
    github_toolsets: list[str]
    inventory_baseline: int | None = None
    baseline_ok: bool = True
    baseline_message: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def list_profiles(catalog: Mapping[str, Any]) -> list[str]:
    """Return sorted profile names declared in the catalog."""
    profiles = catalog.get("profiles") or {}
    if not isinstance(profiles, dict):
        raise ProfilePolicyError("catalog `profiles` must be a mapping")
    names = sorted(str(k) for k in profiles.keys())
    for name in names:
        if name.lower() in _FORBIDDEN_PROFILE_NAMES:
            raise ProfilePolicyError(
                f"forbidden profile name `{name}` — no implicit/all profile is allowed"
            )
    return names


def get_profile(catalog: Mapping[str, Any], name: str) -> dict[str, Any]:
    """Return the raw profile object or raise for unknown/forbidden names."""
    if not name or not isinstance(name, str):
        raise ProfilePolicyError("profile name must be a non-empty string")
    if name.lower() in _FORBIDDEN_PROFILE_NAMES:
        raise ProfilePolicyError(
            f"profile `{name}` is forbidden — no implicit/all profile (ADR-DMX-MCPPROF-001)"
        )
    profiles = catalog.get("profiles") or {}
    if not isinstance(profiles, dict):
        raise ProfilePolicyError("catalog `profiles` must be a mapping")
    if name not in profiles:
        known = ", ".join(list_profiles(catalog)) or "(none declared)"
        raise ProfilePolicyError(
            f"unknown profile `{name}` — fail closed. Known profiles: {known}"
        )
    spec = profiles[name]
    if not isinstance(spec, dict):
        raise ProfilePolicyError(f"profile `{name}` must be a mapping")
    servers = spec.get("servers")
    if not isinstance(servers, list) or not servers:
        raise ProfilePolicyError(f"profile `{name}` must declare a non-empty servers list")
    if any(s in _FORBIDDEN_PROFILE_NAMES or s == "all" for s in servers):
        raise ProfilePolicyError(
            f"profile `{name}` must not include implicit/all server tokens"
        )
    return dict(spec)


def resolve_default_profile(catalog: Mapping[str, Any], profile: str | None) -> str:
    """Resolve CLI/default profile. None -> COMPATIBILITY_PROFILE when declared."""
    if profile is None or profile == "":
        names = list_profiles(catalog)
        if COMPATIBILITY_PROFILE not in names:
            raise ProfilePolicyError(
                "no profile selected and compatibility profile "
                f"`{COMPATIBILITY_PROFILE}` is not declared in mcp_catalog.yaml — "
                "pass an explicit --profile <name> (there is no implicit all)"
            )
        return COMPATIBILITY_PROFILE
    if profile.lower() in _FORBIDDEN_PROFILE_NAMES:
        raise ProfilePolicyError(
            f"profile `{profile}` is forbidden — select an explicit named profile "
            f"from: {', '.join(list_profiles(catalog))}"
        )
    get_profile(catalog, profile)  # validate exists
    return profile


def load_tool_surfaces(repo_root: Path) -> dict[str, Any]:
    """Load committed mcp_tool_surfaces.json (empty tools allowed with reason)."""
    path = Path(repo_root) / "mcp_tool_surfaces.json"
    if not path.is_file():
        return {"schema_version": 1, "servers": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ProfilePolicyError("mcp_tool_surfaces.json must be a JSON object")
    return data


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _snapshot_tools_for_server(
    surfaces: Mapping[str, Any],
    server_name: str,
    server_spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Return tools dict from snapshot; key via tools.snapshot_key or server name."""
    tools_meta = server_spec.get("tools") or {}
    key = tools_meta.get("snapshot_key") if isinstance(tools_meta, dict) else None
    key = key or server_name
    servers = surfaces.get("servers") or {}
    entry = servers.get(key) or servers.get(server_name) or {}
    tools = entry.get("tools") if isinstance(entry, dict) else None
    if not isinstance(tools, dict):
        return {}
    return tools


def _admin_tools(server_spec: Mapping[str, Any]) -> set[str]:
    raw = server_spec.get("admin_tools") or []
    if not isinstance(raw, list):
        return set()
    return {str(t) for t in raw}


def _is_github_write_tool(name: str) -> bool:
    if name in GITHUB_WRITE_TOOLS:
        return True
    # Heuristic for official GitHub MCP write verbs; allow get_/list_/search_ reads.
    if name.startswith(("get_", "list_", "search_", "read_")):
        return False
    return bool(_GITHUB_WRITE_NAME_RE.match(name))


def _filter_tools(
    *,
    server_name: str,
    tool_names: Iterable[str],
    server_spec: Mapping[str, Any],
    profile_spec: Mapping[str, Any],
) -> tuple[list[str], list[str]]:
    """Return (visible_sorted, excluded_sorted)."""
    admin = bool(profile_spec.get("admin"))
    admin_set = _admin_tools(server_spec)
    extra_exclude = {str(t) for t in (profile_spec.get("tool_exclude") or [])}
    include = profile_spec.get("tool_include")
    include_set = {str(t) for t in include} if isinstance(include, list) else None

    is_github = server_name == "github-official" or server_spec.get("authority_role") in {
        "github-read",
        "github-api",
    }

    visible: list[str] = []
    excluded: list[str] = []
    for name in sorted(set(tool_names)):
        reasons: list[str] = []
        if name in _GLOBAL_EXCLUDED_TOOLS:
            reasons.append("global_exclude")
        if not admin and name in admin_set:
            reasons.append("admin_tool")
        if name in extra_exclude:
            reasons.append("profile_exclude")
        if include_set is not None and name not in include_set:
            reasons.append("not_in_include")
        if is_github and _is_github_write_tool(name):
            reasons.append("github_write")
        if reasons:
            excluded.append(name)
        else:
            visible.append(name)
    return visible, excluded


def validate_repo_domain_read(
    repo_root: Path,
    *,
    require_tracked: bool = True,
) -> tuple[bool, str, list[str]]:
    """Validate fixed-path repo-domain-read contract.

    Returns (ok, message, tool_names_if_ok).
    """
    root = Path(repo_root).resolve()
    exe = (root / DOMAIN_READ_EXECUTABLE_REL).resolve()
    manifest = (root / DOMAIN_READ_MANIFEST_REL).resolve()

    try:
        exe.relative_to(root)
    except ValueError:
        return False, "domain executable path escapes repo root", []
    try:
        manifest.relative_to(root)
    except ValueError:
        return False, "domain manifest path escapes repo root", []

    if not exe.exists():
        return False, f"missing domain executable: {DOMAIN_READ_EXECUTABLE_REL}", []
    if exe.is_symlink():
        # Resolve and re-check containment after symlink resolution.
        target = exe.resolve()
        try:
            target.relative_to(root)
        except ValueError:
            return False, "domain executable symlink escapes repo root", []
        return False, "domain executable must be a regular tracked file (symlink blocked)", []
    if not exe.is_file():
        return False, "domain executable is not a regular file", []

    if require_tracked:
        tracked = _git_is_tracked(root, DOMAIN_READ_EXECUTABLE_REL)
        if tracked is False:
            return False, "domain executable is not a tracked git file", []
        if tracked is None:
            return False, "unable to verify domain executable is tracked", []

    if not manifest.exists():
        return False, f"missing domain manifest: {DOMAIN_READ_MANIFEST_REL}", []
    if manifest.is_symlink():
        return False, "domain manifest must not be a symlink", []

    try:
        with manifest.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"malformed domain manifest: {exc}", []

    if not isinstance(data, dict):
        return False, "domain manifest root must be an object", []
    tools = data.get("tools")
    if not isinstance(tools, list) or not tools:
        return False, "domain manifest must declare a non-empty tools array", []

    names: list[str] = []
    for idx, tool in enumerate(tools):
        if not isinstance(tool, dict):
            return False, f"domain manifest tools[{idx}] must be an object", []
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            return False, f"domain manifest tools[{idx}] missing name", []
        side = tool.get("side_effect") or tool.get("side_effect_class")
        if side not in _DOMAIN_READ_OK_SIDE_EFFECTS:
            return (
                False,
                f"domain tool `{name}` side_effect must be "
                f"READ_ONLY_NO_DURABLE_SIDE_EFFECT (got {side!r})",
                [],
            )
        if side is None:
            return False, f"domain tool `{name}` missing side_effect classification", []
        for digest_key in ("input_schema_digest", "output_schema_digest"):
            if digest_key not in tool:
                return False, f"domain tool `{name}` missing {digest_key}", []
        names.append(name)

    return True, "ok", sorted(set(names))


def _git_is_tracked(repo_root: Path, rel: Path) -> bool | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", str(rel)],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.returncode == 0


def resolve_profile(
    catalog: Mapping[str, Any],
    name: str,
    *,
    repo_root: Path | None = None,
    tool_surfaces: Mapping[str, Any] | None = None,
    check_inventory_baseline: bool = True,
    require_domain_tracked: bool = True,
) -> ProfileInventory:
    """Resolve a named profile to selected servers, visible tools, and digests."""
    profile_name = resolve_default_profile(catalog, name)
    spec = get_profile(catalog, profile_name)
    servers_map = catalog.get("servers") or {}
    if not isinstance(servers_map, dict):
        raise ProfilePolicyError("catalog `servers` must be a mapping")

    root = Path(repo_root).resolve() if repo_root is not None else None
    surfaces = (
        dict(tool_surfaces)
        if tool_surfaces is not None
        else (load_tool_surfaces(root) if root is not None else {"servers": {}})
    )

    selected: list[str] = []
    blocked: dict[str, str] = {}
    visible_tools: dict[str, list[str]] = {}
    excluded_tools: dict[str, list[str]] = {}
    notes: list[str] = []

    # Invariants enforced on selection.
    requested = [str(s) for s in spec["servers"]]
    if "pal" in requested and "pal-stdio" not in requested:
        # Selecting PAL HTTP as MCP is forbidden; block and note.
        blocked["pal"] = "PAL HTTP is health-only; use pal-stdio for PAL MCP"
    if "desktop-commander" in requested:
        blocked["desktop-commander"] = (
            "Desktop Commander is not allowed in normal profiles"
        )

    github_cfg = spec.get("github") if isinstance(spec.get("github"), dict) else {}
    github_read_only = bool(github_cfg.get("read_only", True))
    github_toolsets = [str(t) for t in (github_cfg.get("toolsets") or [])]

    for server_name in requested:
        if server_name in blocked:
            continue
        if server_name == "pal":
            blocked[server_name] = "PAL HTTP is health-only; not an MCP transport"
            continue
        if server_name == "desktop-commander":
            blocked[server_name] = "Desktop Commander excluded from normal profiles"
            continue
        if server_name not in servers_map:
            blocked[server_name] = "server not declared in catalog"
            continue
        server_spec = servers_map[server_name]
        if not isinstance(server_spec, dict):
            blocked[server_name] = "invalid server spec"
            continue

        # repo-domain-read: fixed-path validation when selected.
        if server_name == "repo-domain-read":
            if root is None:
                blocked[server_name] = "repo_root required to validate domain-read"
                continue
            ok, msg, domain_tools = validate_repo_domain_read(
                root, require_tracked=require_domain_tracked
            )
            if not ok:
                blocked[server_name] = msg
                continue
            selected.append(server_name)
            visible_tools[server_name] = list(domain_tools)
            excluded_tools[server_name] = []
            continue

        # lifecycle decision-required stay blocked from startable profile inventory.
        if server_spec.get("lifecycle") == "decision-required":
            blocked[server_name] = (
                f"lifecycle decision-required ({server_spec.get('follow_on_decision')})"
            )
            continue

        selected.append(server_name)
        snap_tools = _snapshot_tools_for_server(surfaces, server_name, server_spec)
        tool_names = list(snap_tools.keys())
        # Planned/empty snapshot still selects server with zero tools.
        vis, excl = _filter_tools(
            server_name=server_name,
            tool_names=tool_names,
            server_spec=server_spec,
            profile_spec=spec,
        )
        # Always exclude GitHub writes even if snapshot empty — record denylist.
        if server_name == "github-official":
            for w in sorted(GITHUB_WRITE_TOOLS):
                if w not in excl and w not in vis:
                    excl.append(w)
            excl = sorted(set(excl))
        visible_tools[server_name] = vis
        excluded_tools[server_name] = excl

    # Profile-level invariants: Playwright never in core-*.
    if profile_name.startswith("core-") and "playwright-mcp" in selected:
        selected = [s for s in selected if s != "playwright-mcp"]
        blocked["playwright-mcp"] = "Playwright MCP forbidden in core-* profiles"
        visible_tools.pop("playwright-mcp", None)
        excluded_tools.pop("playwright-mcp", None)

    # PAL HTTP must never be selected as MCP.
    if "pal" in selected:
        selected = [s for s in selected if s != "pal"]
        blocked["pal"] = "PAL HTTP is health-only; not selected as MCP"
        visible_tools.pop("pal", None)

    selected = list(dict.fromkeys(selected))  # stable unique
    total = sum(len(v) for v in visible_tools.values())

    inventory_payload = {
        "profile": profile_name,
        "servers": selected,
        "visible_tools": {k: visible_tools[k] for k in sorted(visible_tools)},
        "github_read_only": github_read_only,
        "github_toolsets": github_toolsets,
    }
    profile_digest = _sha256_hex(_canonical_json(inventory_payload))

    schema_tools: dict[str, dict[str, Any]] = {}
    for server in selected:
        snap = _snapshot_tools_for_server(
            surfaces, server, servers_map.get(server) or {}
        )
        schema_tools[server] = {
            name: snap.get(name) for name in visible_tools.get(server, [])
        }
    schema_payload = {"profile": profile_name, "tools": schema_tools}
    tool_schema_digest = _sha256_hex(_canonical_json(schema_payload))

    baseline = None
    baseline_ok = True
    baseline_message = ""
    inv = spec.get("inventory_baseline")
    if isinstance(inv, dict) and "visible_tool_count" in inv:
        baseline = int(inv["visible_tool_count"])
        if check_inventory_baseline and total > baseline:
            baseline_ok = False
            baseline_message = (
                f"visible tool count {total} exceeds inventory baseline {baseline} "
                "— unexplained inventory increase (update baseline with rationale)"
            )
            raise ProfilePolicyError(baseline_message)
        if check_inventory_baseline and total < baseline:
            notes.append(
                f"visible tool count {total} below baseline {baseline} "
                "(allowed; consider tightening baseline)"
            )
        elif check_inventory_baseline:
            baseline_message = "baseline match"

    return ProfileInventory(
        profile=profile_name,
        description=str(spec.get("description") or ""),
        selected_servers=selected,
        blocked_servers=blocked,
        visible_tools=visible_tools,
        excluded_tools=excluded_tools,
        visible_tool_count=total,
        profile_digest=profile_digest,
        tool_schema_digest=tool_schema_digest,
        github_read_only=github_read_only,
        github_toolsets=github_toolsets,
        inventory_baseline=baseline,
        baseline_ok=baseline_ok,
        baseline_message=baseline_message,
        notes=notes,
    )


def profile_server_names(
    catalog: Mapping[str, Any],
    name: str | None,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Selected server names for generation/init (blocked servers omitted)."""
    resolved = resolve_default_profile(catalog, name)
    inv = resolve_profile(
        catalog,
        resolved,
        repo_root=repo_root,
        check_inventory_baseline=False,
    )
    return list(inv.selected_servers)


def render_profile_doctor_report(inventory: ProfileInventory) -> dict[str, Any]:
    """Structured doctor overlay for a resolved profile (no Docker)."""
    return {
        "schema_version": "mcp-profile-doctor-1",
        "profile": inventory.profile,
        "description": inventory.description,
        "selected_servers": inventory.selected_servers,
        "blocked_servers": inventory.blocked_servers,
        "visible_tool_count": inventory.visible_tool_count,
        "visible_tools": inventory.visible_tools,
        "excluded_tools": inventory.excluded_tools,
        "profile_digest": inventory.profile_digest,
        "tool_schema_digest": inventory.tool_schema_digest,
        "github_read_only": inventory.github_read_only,
        "github_toolsets": inventory.github_toolsets,
        "inventory_baseline": inventory.inventory_baseline,
        "baseline_ok": inventory.baseline_ok,
        "baseline_message": inventory.baseline_message,
        "notes": inventory.notes,
        "invariants": {
            "no_implicit_all": True,
            "pal_http_selected": "pal" in inventory.selected_servers,
            "playwright_in_core": (
                inventory.profile.startswith("core-")
                and "playwright-mcp" in inventory.selected_servers
            ),
            "desktop_commander_selected": "desktop-commander"
            in inventory.selected_servers,
            "github_writes_visible": any(
                t in GITHUB_WRITE_TOOLS
                for tools in inventory.visible_tools.values()
                for t in tools
            ),
        },
    }


def format_profile_doctor_human(inventory: ProfileInventory) -> str:
    report = render_profile_doctor_report(inventory)
    lines = [
        f"Profile: {report['profile']}",
        f"Description: {report['description']}",
        f"Selected servers ({len(report['selected_servers'])}): "
        + ", ".join(report["selected_servers"]),
        f"Visible tools: {report['visible_tool_count']}",
        f"profile_digest: {report['profile_digest']}",
        f"tool_schema_digest: {report['tool_schema_digest']}",
        f"github_read_only: {report['github_read_only']}",
    ]
    if report["blocked_servers"]:
        lines.append("Blocked servers:")
        for name, reason in sorted(report["blocked_servers"].items()):
            lines.append(f"  - {name}: {reason}")
    for server, tools in sorted(report["visible_tools"].items()):
        lines.append(f"  {server}: {len(tools)} tools")
    if report["notes"]:
        lines.append("Notes:")
        for note in report["notes"]:
            lines.append(f"  - {note}")
    inv = report["invariants"]
    if inv["pal_http_selected"] or inv["playwright_in_core"] or inv["github_writes_visible"]:
        lines.append("INVARIANT VIOLATIONS DETECTED")
    return "\n".join(lines) + "\n"


def assert_no_implicit_all(profile_name: str | None) -> None:
    """Raise if caller requested the forbidden implicit-all profile."""
    if profile_name is not None and profile_name.lower() in _FORBIDDEN_PROFILE_NAMES:
        raise ProfilePolicyError(
            f"forbidden profile `{profile_name}` — no implicit/all profile "
            f"(use an explicit named profile such as `{COMPATIBILITY_PROFILE}`)"
        )
