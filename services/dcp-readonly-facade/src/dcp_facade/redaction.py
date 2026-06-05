"""Redaction baseline.

Strips absolute filesystem paths and secret/token patterns from any payload
before it leaves the facade. No equivalent utility exists in dopemux core
(verified during TP-DCP-MCP-RO-0004 discovery), so this is purpose-built and
intentionally conservative: when unsure, redact.

`redact_value` walks arbitrary JSON-like data (str/dict/list/scalars) and
returns `(clean_value, redactions)` where `redactions` is a sorted list of the
categories applied, e.g. ["absolute_paths", "secrets"].
"""

from __future__ import annotations

import re
from typing import Any, Iterable

ABS_PATHS = "absolute_paths"
SECRETS = "secrets"

_PATH_PLACEHOLDER = "<redacted-path>"

# Secret patterns. Order matters (most specific first). Each maps a compiled
# pattern to its replacement.
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{8,}"), "sk-<redacted>"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"), "gh<redacted>"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AKIA<redacted>"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]+"), "Bearer <redacted>"),
    (
        # KEY=VALUE / KEY: VALUE style for sensitive keys
        re.compile(
            r"(?i)\b([A-Z0-9_]*(?:API[_-]?KEY|TOKEN|PASSWORD|SECRET|PASSWD))\b(\s*[=:]\s*)(\S+)"
        ),
        r"\1\2<redacted>",
    ),
]

# Generic absolute-path roots that should never leak even if not a registered
# workspace (home dirs, common unix roots).
_GENERIC_ABS_ROOTS = (
    "/Users/",
    "/home/",
    "/root/",
    "/private/",
    "/mnt/",
    "/media/",
    "/var/",
    "/opt/",
    "/srv/",
    "/usr/",
    "/etc/",
    "/data/",
    "/tmp/",
)

# Defence-in-depth: any absolute unix path with >= 3 segments (e.g.
# ``/some/deep/internal/path``) — conservative so short route-like strings such
# as ``/api/decisions`` (2 segments) are preserved. "When unsure, redact."
_DEEP_PATH = re.compile(r"(?<![\w.])/(?:[^\s\"'/]+/){2,}[^\s\"'/]*")


def redact_secrets(text: str) -> tuple[str, bool]:
    """Return (clean, changed) after masking known secret patterns."""
    changed = False
    out = text
    for pattern, repl in _SECRET_PATTERNS:
        new = pattern.sub(repl, out)
        if new != out:
            changed = True
            out = new
    return out, changed


def redact_abs_paths(text: str, abs_roots: Iterable[str]) -> tuple[str, bool]:
    """Mask absolute paths.

    Registered `abs_roots` are replaced with the placeholder first (longest
    first so nested roots collapse correctly); then any residual generic
    absolute path token (``/Users/...`` etc.) is masked.
    """
    changed = False
    out = text
    for root in sorted((r for r in abs_roots if r), key=len, reverse=True):
        if root in out:
            out = out.replace(root, _PATH_PLACEHOLDER)
            changed = True
    # Residual generic absolute paths (defence in depth).
    for prefix in _GENERIC_ABS_ROOTS:
        # Match prefix + path chars (no whitespace).
        pat = re.compile(re.escape(prefix) + r"[^\s\"']*")
        new = pat.sub(_PATH_PLACEHOLDER, out)
        if new != out:
            out = new
            changed = True
    # Any remaining deep absolute path (>= 3 segments).
    new = _DEEP_PATH.sub(_PATH_PLACEHOLDER, out)
    if new != out:
        out = new
        changed = True
    return out, changed


def _redact_str(text: str, abs_roots: Iterable[str], cats: set[str]) -> str:
    out, changed = redact_abs_paths(text, abs_roots)
    if changed:
        cats.add(ABS_PATHS)
    out, changed = redact_secrets(out)
    if changed:
        cats.add(SECRETS)
    return out


def redact_value(value: Any, abs_roots: Iterable[str]) -> tuple[Any, list[str]]:
    """Recursively redact a JSON-like value.

    Returns (clean_value, sorted_categories). Dict keys are left intact
    (only values are redacted) but string keys are not expected to carry
    secrets; values and nested structures are scrubbed.
    """
    cats: set[str] = set()
    roots = list(abs_roots)

    def _walk(v: Any) -> Any:
        if isinstance(v, str):
            return _redact_str(v, roots, cats)
        if isinstance(v, dict):
            # Redact string keys too — proof content (e.g. JSON) is untrusted and
            # could carry secrets/paths in keys.
            return {
                (_redact_str(k, roots, cats) if isinstance(k, str) else k): _walk(sub)
                for k, sub in v.items()
            }
        if isinstance(v, (list, tuple)):
            return [_walk(sub) for sub in v]
        return v

    clean = _walk(value)
    return clean, sorted(cats)
