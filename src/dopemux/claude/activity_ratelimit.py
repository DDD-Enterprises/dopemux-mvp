"""Producer-side rate limiting for low-signal/heartbeat activity events.

ADR-mcpint-004 (Authenticated /events as the Single Event Ingress) names this
module's job explicitly: "Heartbeat rate-limiting lives here, at the
producer ... session heartbeats are coalesced/dropped client-side so the
24.5K-row spam class cannot recur regardless of consumer-side policy."
(packet MCPINT-FND-HYG-007).

Two known producers emit content-free "session is alive" / "a tool ran"
pings that carry no decision-worthy payload:

- ``dopemux.claude.native_hooks._emit_activity_event`` — UserPromptSubmit /
  PreToolUse / PostToolUse / PostToolUseFailure pings, xadd'd straight to the
  ``dopemux:events`` Redis stream on every single hook invocation.
- ``dopemux.hooks.claude_code_hooks.ClaudeCodeHooks._check_claude_session``
  — a background daemon (``monitor_daemon.py``) that polls ``pgrep`` every
  2s and, while a Claude Code process is detected, shells out to
  ``dopemux memory capture emit`` with a ``session-active`` event on every
  tick. Capture's event id is content-addressed at *second* granularity
  (``capture_client._deterministic_event_id``), so a 2s poll interval writes
  a near-unique row on almost every tick — this is the dominant source of
  the audited 24,539 heartbeat rows.

Both call into :func:`should_emit_heartbeat` before emitting. High-signal
event types (the promotion allowlist —
``dopemux.memory.capture_client.PROMOTABLE_CAPTURE_EVENT_TYPES``: decision.*,
task.*, error.encountered, workflow.phase_changed, work.untracked_*) are
never routed through this gate by any current caller, and this module
actively refuses to rate-limit them even if a caller passes one in — that
invariant is enforced here, not left to caller discipline alone.

Fail-open by design: any cache read/write error (corrupt JSON, missing
directory, permission error, concurrent-writer races) falls back to "emit
now" rather than silently dropping a signal. Cooldown state is a best-effort
JSON cache under ``.claude/`` in the same spirit as the other Dopemux hook
caches (see ``.claude/hooks/mcp_health_probe.py``); it is not a distributed
lock and does not need to be one — worst case under a race is one extra
emission inside the cooldown window, never a blocked caller.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

DEFAULT_COOLDOWN_SECONDS = 300
ENV_COOLDOWN_SECONDS = "DOPEMUX_ACTIVITY_HEARTBEAT_COOLDOWN"

_CACHE_FILENAME = ".activity-heartbeat-cache.json"
_CACHE_DIRNAME = ".claude"
_MAX_CACHE_ENTRIES = 500
_CACHE_TRIM_TO = 250

try:
    from dopemux.memory.capture_client import PROMOTABLE_CAPTURE_EVENT_TYPES
except Exception:  # pragma: no cover - defensive: never let an import wobble
    # gate a heartbeat call. Falling back to an empty set only means the
    # (unused-by-any-current-caller) bypass path is inert, never that a
    # heartbeat call raises.
    PROMOTABLE_CAPTURE_EVENT_TYPES = frozenset()


def _normalize_event_type(event_type: str) -> str:
    normalized = event_type.strip().lower()
    if "." not in normalized:
        normalized = normalized.replace("_", ".").replace("-", ".")
    return normalized


def is_high_signal_event_type(event_type: str) -> bool:
    """True when `event_type` is on the promotion allowlist.

    High-signal events must never be coalesced/dropped by this module —
    :func:`should_emit_heartbeat` checks this first and always returns True
    for them, independent of cooldown state.
    """
    try:
        return _normalize_event_type(event_type) in PROMOTABLE_CAPTURE_EVENT_TYPES
    except Exception:  # pragma: no cover - defensive
        return False


def _cooldown_seconds(override: Optional[int]) -> int:
    if override is not None:
        return override
    raw = os.environ.get(ENV_COOLDOWN_SECONDS, "").strip()
    if not raw:
        return DEFAULT_COOLDOWN_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_COOLDOWN_SECONDS
    return value if value >= 0 else DEFAULT_COOLDOWN_SECONDS


def _cache_path(project_root: Path) -> Path:
    return project_root / _CACHE_DIRNAME / _CACHE_FILENAME


def _load_cache(project_root: Path) -> dict:
    try:
        raw = _cache_path(project_root).read_text()
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        # Missing file, corrupt JSON, permission error, not-a-dict payload —
        # all fail open to "no cooldown state known yet".
        return {}


def _save_cache(project_root: Path, cache: dict) -> None:
    try:
        path = _cache_path(project_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache))
    except Exception:
        # Best-effort only; a failed write just means this tick's cooldown
        # timestamp doesn't stick — never blocks or raises for the caller.
        return None


def should_emit_heartbeat(
    event_type: str,
    *,
    session_id: Optional[str] = None,
    project_root: Optional[Path | str] = None,
    cooldown_seconds: Optional[int] = None,
) -> bool:
    """Return True if a low-signal activity ping should be emitted now.

    Coalesces identical low-signal events — keyed by (session_id,
    event_type) — to at most one emission per cooldown window (default
    ``DEFAULT_COOLDOWN_SECONDS``, tunable via ``DOPEMUX_ACTIVITY_HEARTBEAT_
    COOLDOWN`` or the ``cooldown_seconds`` kwarg).

    High-signal event types (see ``is_high_signal_event_type``) always
    return True and never touch the cooldown cache.

    Fails open: any cache error (corrupt file, permission denied, missing
    directory) returns True so a broken cache never suppresses a signal.
    """
    if is_high_signal_event_type(event_type):
        return True

    try:
        window = _cooldown_seconds(cooldown_seconds)
        if window <= 0:
            return True

        # Coerce str paths (e.g. monitor_daemon assigns str watched_paths).
        root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
        key = f"{session_id or 'unknown'}::{_normalize_event_type(event_type)}"

        cache = _load_cache(root)
        now = time.time()
        last_emitted = cache.get(key)
        if isinstance(last_emitted, (int, float)) and (now - last_emitted) < window:
            return False

        cache[key] = now
        if len(cache) > _MAX_CACHE_ENTRIES:
            # Bound cache growth on long-running hosts / many-session repos:
            # keep only the most recently touched keys.
            cache = dict(
                sorted(cache.items(), key=lambda kv: kv[1], reverse=True)[:_CACHE_TRIM_TO]
            )
        _save_cache(root, cache)
        return True
    except Exception:
        # Any unexpected failure (e.g. an unresolvable project_root) must
        # never block emission of the underlying signal.
        return True
