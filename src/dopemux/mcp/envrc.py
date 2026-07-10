"""Read-only parser for `.envrc.dopemux-mcp` (and similar export files).

Loads KEY=value / export KEY=value lines for doctor/status inspection.
Never mutates files. Redacts secret-like values for report output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

# Lines we accept: optional "export ", KEY=VALUE with optional quotes.
_LINE_RE = re.compile(
    r"""^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$"""
)
_COMMENT_OR_BLANK = re.compile(r"^\s*(?:#|$)")

# Substring markers that indicate a value should never appear in doctor output.
_SECRET_MARKERS = (
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASSWD",
    "CREDENTIAL",
    "PRIVATE",
    "AUTH",
    "API_KEY",
    "ACCESS_KEY",
    "SESSION",
)

# Safe identity / port-ish keys that may appear as paths or numbers.
_SAFE_VALUE_PREFIXES = (
    "DOPEMUX_",
    "DOPE_MEMORY_",
    "TASK_ORCHESTRATOR_",
    "CONPORT_",
    "WORKSPACE_ID",
    "COMPOSE_",
    "SERENA_",
)


@dataclass(frozen=True)
class EnvrcParseResult:
    """Result of parsing an envrc file."""

    path: Optional[Path]
    present: bool
    parse_status: str  # OK | ERROR | MISSING
    values: Dict[str, str] = field(default_factory=dict)
    keys_present: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    redacted: bool = True

    def to_report_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path) if self.path else None,
            "present": self.present,
            "parse_status": self.parse_status,
            "keys_present": list(self.keys_present),
            "redacted": True,
        }


def _strip_quotes(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    # Trailing inline comment (unquoted only)
    if " #" in value and not (value.startswith("'") or value.startswith('"')):
        value = value.split(" #", 1)[0].rstrip()
    return value


def is_secret_like_key(key: str) -> bool:
    """True when the env key name suggests a secret value."""
    upper = key.upper()
    # Port and path identity keys are never secret-like even if they contain KEY substring patterns.
    if upper.endswith("_PORT") or upper.endswith("_PORTS"):
        return False
    if upper.endswith("_PATH") or upper.endswith("_ROOT") or upper.endswith("_DIR"):
        return False
    if upper.endswith("_ID") or upper.endswith("_URL") or upper.endswith("_HOST"):
        return False
    if upper in {
        "WORKSPACE_ID",
        "DOPEMUX_WORKSPACE_ID",
        "DOPEMUX_WORKSPACE_ROOT",
        "DOPEMUX_PROJECT_ROOT",
        "DOPEMUX_INSTANCE_ID",
        "DOPE_MEMORY_WORKSPACE_ID",
        "DOPE_MEMORY_INSTANCE_ID",
        "TASK_ORCHESTRATOR_PROJECT_ROOT",
        "COMPOSE_PROJECT_NAME",
        "CONPORT_CONTAINER_NAME",
        "SERENA_CONTAINER_NAME",
    }:
        return False
    for marker in _SECRET_MARKERS:
        if marker in upper:
            return True
    return False


def redact_value(key: str, value: str) -> str:
    """Return a report-safe representation of an env value."""
    if is_secret_like_key(key):
        return "[REDACTED]"
    # Allow localhost URLs without credentials; redact everything else URL-like.
    if "://" in value:
        if "@" in value.split("://", 1)[1].split("/", 1)[0]:
            return "[REDACTED_URL_WITH_CREDENTIALS]"
        if "localhost" in value or "127.0.0.1" in value:
            return value
        # Non-localhost URLs may leak internal hostnames into doctor/CI output.
        return "[REDACTED_URL]"
    # Numeric ports are always safe
    if value.isdigit():
        return value
    # Paths are allowed
    if value.startswith("/") or value.startswith("~"):
        return value
    # Default: allow short non-secret values (instance ids, project names)
    if len(value) <= 128 and not any(c in value for c in "\n\r\t"):
        return value
    return "[REDACTED]"


def parse_envrc_text(text: str) -> Tuple[Dict[str, str], List[str]]:
    """Parse envrc body text into {key: value} and error messages."""
    values: Dict[str, str] = {}
    errors: List[str] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\n")
        if _COMMENT_OR_BLANK.match(line):
            continue
        match = _LINE_RE.match(line)
        if not match:
            errors.append(f"line {lineno}: malformed (expected KEY=value or export KEY=value)")
            continue
        key, raw_val = match.group(1), match.group(2)
        values[key] = _strip_quotes(raw_val)
    return values, errors


def load_envrc(path: Path | str | None) -> EnvrcParseResult:
    """Load and parse an envrc file. Missing path → MISSING, unreadable → ERROR."""
    if path is None:
        return EnvrcParseResult(path=None, present=False, parse_status="MISSING")

    envrc_path = Path(path).expanduser()
    if not envrc_path.exists():
        return EnvrcParseResult(
            path=envrc_path,
            present=False,
            parse_status="MISSING",
        )
    if not envrc_path.is_file():
        return EnvrcParseResult(
            path=envrc_path,
            present=True,
            parse_status="ERROR",
            errors=[f"not a regular file: {envrc_path}"],
        )

    try:
        text = envrc_path.read_text(encoding="utf-8")
    except OSError as exc:
        return EnvrcParseResult(
            path=envrc_path,
            present=True,
            parse_status="ERROR",
            errors=[f"read failed: {exc}"],
        )

    values, errors = parse_envrc_text(text)
    # Partial parse: useful keys still count as OK so doctor does not hard-fail
    # on minor envrc noise. errors[] retains malformed-line diagnostics.
    if values:
        status = "OK"
    elif errors:
        status = "ERROR"
    else:
        status = "OK"

    return EnvrcParseResult(
        path=envrc_path,
        present=True,
        parse_status=status,
        values=values,
        keys_present=sorted(values.keys()),
        errors=errors,
        redacted=True,
    )


def merge_envrc_into_environ(
    base: Mapping[str, str] | None,
    envrc: EnvrcParseResult,
    *,
    override: bool = True,
) -> Dict[str, str]:
    """Return a new env mapping with envrc values applied (envrc wins when override=True)."""
    merged = dict(base or {})
    if envrc.parse_status in {"OK", "ERROR"} and envrc.values:
        for key, value in envrc.values.items():
            if override or key not in merged:
                merged[key] = value
    return merged


def safe_port_int(values: Mapping[str, str], key: str) -> Optional[int]:
    """Parse a numeric port from env values; None if missing/invalid."""
    raw = values.get(key)
    if raw is None or raw == "":
        return None
    try:
        port = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if 1 <= port <= 65535:
        return port
    return None


def redacted_snapshot(values: Mapping[str, str], keys: Iterable[str] | None = None) -> Dict[str, str]:
    """Build a redacted key→value snapshot for reports."""
    selected = list(keys) if keys is not None else sorted(values.keys())
    return {k: redact_value(k, values[k]) for k in selected if k in values}
