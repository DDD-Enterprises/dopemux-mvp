"""
Redactor - Secret and PII scrubbing for Dope-Memory.

Implements the redaction gate per spec 05_promotion_redaction.md:
- Denylist path prefixes
- Sensitive key names
- Pattern detectors (regex)
- Size caps with truncation
"""

import hashlib
import json
import re
from typing import Any

# Maximum payload size in bytes
MAX_PAYLOAD_SIZE = 64 * 1024  # 64KB

# Denylist path prefixes - these paths are hashed, not stored raw
DENYLIST_PATH_PREFIXES = (
    ".env",
    "secrets/",
    "secret/",
    "keys/",
    ".ssh/",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "config/credentials",
    "private/",
    "certs/private",
    ".aws/credentials",
    ".npmrc",
    ".pypirc",
)

# Sensitive key names (case-insensitive) - these fields are dropped
SENSITIVE_KEY_NAMES = frozenset(
    [
        "password",
        "passwd",
        "pwd",
        "secret",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "set-cookie",
        "private_key",
        "ssh_key",
        "client_secret",
        "session",
        "bearer",
        "jwt",
        "signature",
    ]
)

# Secret patterns - these are replaced with [REDACTED]
SECRET_PATTERNS = [
    # AWS Access Key ID
    (re.compile(r"\b(A3T|AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA|ASCA)[A-Z0-9]{16}\b"), "[REDACTED:AWS_KEY_ID]"),
    # AWS Secret Access Key (heuristic)
    (
        re.compile(r"(?i)\baws(.{0,20})?(secret|access).{0,20}([A-Za-z0-9/+=]{40})\b"),
        "[REDACTED:AWS_SECRET]",
    ),
    # Bearer token
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b"), "[REDACTED:BEARER]"),
    # JWT (three base64url parts)
    (
        re.compile(r"\beyJ[A-Za-z0-9\-_]+?\.[A-Za-z0-9\-_]+?\.[A-Za-z0-9\-_]+?\b"),
        "[REDACTED:JWT]",
    ),
    # Private key blocks
    (
        re.compile(
            r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----[\s\S]+?-----END (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"
        ),
        "[REDACTED:PRIVATE_KEY]",
    ),
    # GitHub tokens (classic + fine-grained)
    (re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b"), "[REDACTED:GITHUB_TOKEN]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{80,}\b"), "[REDACTED:GITHUB_PAT]"),
    # Slack tokens
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED:SLACK_TOKEN]"),
    # OpenAI keys
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "[REDACTED:OPENAI_KEY]"),
    # Generic API key assignment
    (
        re.compile(
            r'(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?([A-Za-z0-9\-._~+/]{12,})["\']?\b'
        ),
        "[REDACTED:GENERIC_SECRET]",
    ),
]


class Redactor:
    """Redacts sensitive content from event payloads.

    Fail-closed: If redaction fails, the payload is dropped or fully stripped.
    """

    def __init__(self) -> None:
        self._patterns = SECRET_PATTERNS

    def redact_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive content from a payload dict.

        Args:
            payload: Raw event payload

        Returns:
            Redacted payload with secrets removed/replaced
        """
        try:
            redacted = self._redact_dict(payload)
            return self._enforce_size_limit(redacted)
        except Exception:
            # Fail closed - return minimal safe payload
            return {"redaction_error": True, "original_keys": list(payload.keys())}

    def _redact_dict(self, obj: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact a dictionary."""
        result = {}
        for key, value in obj.items():
            # Drop sensitive keys
            if key.lower() in SENSITIVE_KEY_NAMES:
                continue

            # Handle nested structures
            if isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = self._redact_list(value)
            elif isinstance(value, str):
                result[key] = self._redact_string(value)
            else:
                result[key] = value

        return result

    def _redact_list(self, items: list[Any]) -> list[Any]:
        """Recursively redact a list."""
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(self._redact_dict(item))
            elif isinstance(item, list):
                result.append(self._redact_list(item))
            elif isinstance(item, str):
                result.append(self._redact_string(item))
            else:
                result.append(item)
        return result

    def _redact_string(self, value: str) -> str:
        """Apply regex patterns to redact secrets from a string."""
        result = value
        for pattern, replacement in self._patterns:
            result = pattern.sub(replacement, result)
        return result

    def _enforce_size_limit(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Truncate payload if it exceeds size limit."""
        serialized = json.dumps(payload)
        if len(serialized) <= MAX_PAYLOAD_SIZE:
            return payload

        # Truncate and mark
        return {
            "truncated": True,
            "original_size": len(serialized),
            "redaction_note": "Payload exceeded 64KB limit",
        }

    def redact_file_path(self, path: str) -> dict[str, str]:
        """Redact a file path if it matches denylist.

        Args:
            path: File path to check

        Returns:
            Either {"path": original_path} or {"path_hash": hash, "note": "denied_path"}
        """
        normalized = path.lower().replace("\\", "/")

        for prefix in DENYLIST_PATH_PREFIXES:
            if prefix in normalized:
                path_hash = hashlib.sha256(path.encode()).hexdigest()[:16]
                return {"path_hash": path_hash, "note": "denied_path"}

        return {"path": path}

    def redact_linked_files(
        self, files: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Redact a list of linked files, hashing denied paths."""
        result = []
        for file_entry in files:
            path = file_entry.get("path", "")
            action = file_entry.get("action", "unknown")

            redacted_path = self.redact_file_path(path)
            result.append({**redacted_path, "action": action})

        return result
