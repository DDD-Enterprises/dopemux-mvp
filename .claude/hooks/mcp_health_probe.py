"""
MCP health probe for SessionStart.

Surfaces dead per-worktree servers and leaked task-orchestrator containers
at session start instead of as confusing mid-task failures.

All functions are pure and never raise; hook failures must not block work.
Container naming: task-orchestrator-<workspace-slug>-<16-char-sha256>
  (per scripts/mcp-wrappers/task-orchestrator-current-stdio.sh:103-141)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

_CACHE_FILENAME = ".mcp-health-cache.json"
_CACHE_MAX_AGE_MIN = 15
_PORT_TIMEOUT_SEC = 0.25
_DOCKER_TIMEOUT_SEC = 0.8
_TOTAL_BUDGET_SEC = 2.0

# Matches ${VAR:-default_port} in .mcp.json URL strings
_PORT_RE = re.compile(
    r"^https?://(?:localhost|127\.0\.0\.1):"
    r"(?:\$\{([A-Z0-9_]+):-(\d+)\}|(\d+))(?:/|$)"
)
_ENVRC_KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)(?=\s|=|$)")
_PORT_VALUE_RE = re.compile(r"^\s*(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=\s*"
                            r"(?:([0-9]+)|'([0-9]+)'|\"([0-9]+)\")\s*(?:#.*)?$")

_SERVER_REMEDIATION = {
    "task-orchestrator": "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh",
}


def _cache_path(project_root: Path) -> Path:
    return project_root / ".claude" / _CACHE_FILENAME


def _load_cache(project_root: Path, signature: str) -> dict | None:
    """Return cached health dict if < 15 min old, else None."""
    try:
        data = json.loads(_cache_path(project_root).read_text())
        if data.get("endpoint_signature") != signature:
            return None
        ts = data.get("written_at", "")
        if ts:
            age_min = (
                datetime.now(timezone.utc) - datetime.fromisoformat(ts)
            ).total_seconds() / 60
            if 0 <= age_min < _CACHE_MAX_AGE_MIN:
                return data
    except Exception:
        pass
    return None


def _save_cache(project_root: Path, health: dict) -> None:
    try:
        p = _cache_path(project_root)
        p.parent.mkdir(parents=True, exist_ok=True)
        health["written_at"] = datetime.now(timezone.utc).isoformat()
        p.write_text(json.dumps(health))
    except Exception:
        pass


def _valid_port(value: str) -> int | None:
    if re.fullmatch(r"[0-9]{1,5}", value):
        port = int(value)
        if 1 <= port <= 65535:
            return port
    return None


def _extract_port(url: str) -> int | None:
    """Standalone compatibility helper: ambient override, then URL default.

    Only IPv4 loopback URLs can be checked by the local TCP probe. Invalid explicit
    overrides are unprobeable, rather than a reason to silently use a default.
    Target-repo probes resolve template variables separately from this helper.
    """
    m = _PORT_RE.match(url)
    if not m:
        return None
    var_name, default_str, literal_str = m.groups()
    if literal_str:
        return _valid_port(literal_str)
    return _valid_port(os.environ.get(var_name) or default_str) if var_name else None


def _repo_ports(project_root: Path, keys: set[str]) -> dict[str, int | None]:
    """Read selected operational port assignments only; never evaluate shell.

    No parent-checkout or ambient fallback: both may belong to another repo.
    Duplicate assignments and unsupported shell expressions are ambiguous.
    """
    values: dict[str, int | None] = {}
    try:
        with (project_root / ".envrc.dopemux-mcp").open(encoding="utf-8") as handle:
            for line in handle:
                key_match = _ENVRC_KEY_RE.match(line)
                if not key_match or key_match.group(1) not in keys:
                    continue
                key = key_match.group(1)
                match = _PORT_VALUE_RE.fullmatch(line.rstrip("\n"))
                port = None
                if match:
                    port = _valid_port(next(v for v in match.groups() if v is not None))
                values[key] = None if key in values else port
    except (OSError, UnicodeError):
        return {}
    return values


def _resolve_servers(project_root: Path) -> tuple[dict, str]:
    """Resolve one snapshot for probing and cache identity, without side effects."""
    try:
        config = json.loads((project_root / ".mcp.json").read_text())
    except (OSError, ValueError):
        config = {}
    servers = config.get("mcpServers", {})
    keys = set()
    for entry in servers.values():
        if entry.get("type") in ("http", "sse"):
            match = _PORT_RE.match(entry.get("url", ""))
            if match and match.group(1) and match.group(1).endswith("_PORT"):
                keys.add(match.group(1))
    ports = _repo_ports(project_root, keys) if keys else {}
    resolved = {}
    for name, entry in servers.items():
        transport = entry.get("type", "")
        if transport in ("http", "sse"):
            match = _PORT_RE.match(entry.get("url", ""))
            port = None
            if match:
                var, _default, literal = match.groups()
                port = _valid_port(literal) if literal else ports.get(var)
            resolved[name] = {"port": port} if port else {
                "up": None, "error": "invalid or missing target endpoint configuration"}
        elif transport == "stdio":
            resolved[name] = {"up": None}
    # Hash only declared endpoints + resolved ports, not envrc credentials/body.
    signature = hashlib.sha256(json.dumps(
        {"version": 1, "resolved": resolved, "endpoints": {
            name: {"type": entry.get("type"), "url": entry.get("url")}
            for name, entry in servers.items()
        }}, sort_keys=True).encode()).hexdigest()
    return resolved, signature


def _probe_port(port: int) -> bool:
    """True if TCP port is listening (non-blocking, 0.25s timeout)."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=_PORT_TIMEOUT_SEC):
            return True
    except OSError:
        return False


def _count_leaked_containers() -> int | None:
    """Return count of running task-orchestrator stdio containers, or None if docker unavailable."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            timeout=_DOCKER_TIMEOUT_SEC,
        )
        if result.returncode != 0:
            return None
        names = result.stdout.decode(errors="replace").splitlines()
        return sum(1 for n in names if n.startswith("task-orchestrator-"))
    except Exception:
        return None


def _probe_servers(project_root: Path, resolved: dict | None = None) -> dict:
    """Probe resolved local endpoints; retain visible configuration failures."""
    if resolved is None:
        resolved, _signature = _resolve_servers(project_root)
    return {
        name: {**info, "up": _probe_port(info["port"])} if info.get("port") else dict(info)
        for name, info in resolved.items()
    }


def emit_mcp_health(project_root: Path) -> str | None:
    """Return a compact health line for SessionStart injection, or None.

    Reuses cache only for unchanged resolved endpoints and age < 15 min.
    Never raises; returns None on unexpected failure.
    """
    try:
        resolved, signature = _resolve_servers(project_root)
        cached = _load_cache(project_root, signature)
        if cached:
            return _format_health(cached, project_root)

        health: dict = {}
        health["endpoint_signature"] = signature
        health["servers"] = _probe_servers(project_root, resolved)
        health["leaked_containers"] = _count_leaked_containers()

        _save_cache(project_root, health)
        return _format_health(health, project_root)
    except Exception:
        return None


def _format_health(health: dict, project_root: Path | None = None) -> str | None:
    """Format health dict into the SessionStart injection line(s).

    Remediation must recommend the repo-aware ``dopemux mcp start`` (with
    ``--repo`` when a project root is known), never bare ``mcp up`` — the
    no-``--repo`` ``mcp up`` path is legacy cwd-compose and fails in worktrees
    or external repos without a compose.yml.
    """
    servers: dict = health.get("servers", {})
    leaked: int | None = health.get("leaked_containers")

    problems: list[str] = []
    status_parts: list[str] = []

    for name, info in servers.items():
        up = info.get("up")
        port = info.get("port")
        if up is True:
            status_parts.append(f"{name} ✅")
        elif up is False:
            status_parts.append(f"{name} ❌")
            port_str = f":{port}" if port else ""
            repo_arg = f" --repo {shlex.quote(str(project_root))}" if project_root else ""
            remediation = _SERVER_REMEDIATION.get(
                name, f"dopemux mcp start{repo_arg} --services {name}"
            )
            problems.append(
                f"⚠️ {name} {port_str} not listening → "
                f"{remediation}"
            )
        else:
            if info.get("error"):
                problems.append(f"⚠️ {name}: {info['error']} (not probed)")
            status_parts.append(f"{name} ⚙️")  # stdio / unprobed

    if leaked is not None and leaked > 2:
        problems.append(
            f"⚠️ {leaked} task-orchestrator stdio containers "
            f"(SQLite-contention risk) → /mcp:doctor --prune"
        )
    elif leaked is not None and leaked > 1:
        problems.append(
            f"⚠️ {leaked} task-orchestrator containers running "
            f"(expected ≤1) → /mcp:doctor to inspect"
        )

    if not status_parts and not problems:
        return None

    summary = "🩺 MCP: " + " · ".join(status_parts) if status_parts else "🩺 MCP: (no http/sse servers)"
    if not problems:
        return summary

    # Cap at 3 problem lines (ADHD: don't overwhelm)
    shown = problems[:3]
    rest = len(problems) - 3
    lines = [summary] + shown
    if rest > 0:
        lines.append(f"  … {rest} more issue(s) → /mcp:doctor for full sweep")
    return "\n".join(lines)
