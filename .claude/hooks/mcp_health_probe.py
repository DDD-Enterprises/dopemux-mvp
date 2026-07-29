"""
MCP health probe for SessionStart.

Surfaces dead per-worktree servers and leaked task-orchestrator containers
at session start instead of as confusing mid-task failures.

All functions are pure and never raise; hook failures must not block work.
Container naming: task-orchestrator-<workspace-slug>-<16-char-sha256>
  (per scripts/mcp-wrappers/task-orchestrator-current-stdio.sh:103-141)
"""
from __future__ import annotations

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
_PORT_RE = re.compile(r":(?:\$\{([A-Z0-9_]+):-(\d+)\}|(\d+))/")

_SERVER_REMEDIATION = {
    "task-orchestrator": "scripts/mcp-wrappers/task-orchestrator-http-singleton.sh",
}


def _cache_path(project_root: Path) -> Path:
    return project_root / ".claude" / _CACHE_FILENAME


def _load_cache(project_root: Path) -> dict | None:
    """Return cached health dict if < 15 min old, else None."""
    try:
        data = json.loads(_cache_path(project_root).read_text())
        ts = data.get("written_at", "")
        if ts:
            age_min = (
                datetime.now(timezone.utc) - datetime.fromisoformat(ts)
            ).total_seconds() / 60
            if age_min < _CACHE_MAX_AGE_MIN:
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


def _extract_port(url: str) -> int | None:
    """Parse port from .mcp.json URL template; prefer env-var override."""
    m = _PORT_RE.search(url)
    if not m:
        return None
    var_name, default_str, literal_str = m.group(1), m.group(2), m.group(3)
    if literal_str:
        return int(literal_str)
    if var_name:
        env_val = os.environ.get(var_name, "")
        if env_val.isdigit():
            return int(env_val)
        if default_str:
            return int(default_str)
    return None


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


def _probe_servers(project_root: Path) -> dict:
    """Probe declared .mcp.json servers; return health dict."""
    mcp_file = project_root / ".mcp.json"
    if not mcp_file.exists():
        return {}

    try:
        config = json.loads(mcp_file.read_text())
    except Exception:
        return {}

    servers = config.get("mcpServers", {})
    results: dict[str, dict] = {}
    for name, entry in servers.items():
        transport = entry.get("type", "")
        if transport in ("http", "sse"):
            url = entry.get("url", "")
            port = _extract_port(url)
            if port:
                results[name] = {"up": _probe_port(port), "port": port}
            else:
                results[name] = {"up": None}  # can't probe
        elif transport == "stdio":
            results[name] = {"up": None}  # stdio health is container-level
    return results


def emit_mcp_health(project_root: Path) -> str | None:
    """Return a compact health line for SessionStart injection, or None.

    Uses cache when < 15 min old. Never raises; returns None on any failure.
    """
    try:
        cached = _load_cache(project_root)
        if cached:
            return _format_health(cached, project_root)

        health: dict = {}
        health["servers"] = _probe_servers(project_root)
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
