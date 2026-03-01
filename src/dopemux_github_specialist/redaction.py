from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .errors import RedactionError


DEFAULT_DENY_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----",
    r"(?i)\bpassword\b\s*[:=]\s*\S+",
    r"(?i)\bapi[_-]?key\b\s*[:=]\s*\S+",
    r"(?i)\bsecret\b\s*[:=]\s*\S+",
    r"(?i)\btoken\b\s*[:=]\s*\S+",
]

DEFAULT_MAX_BYTES = 64 * 1024


@dataclass(frozen=True)
class RedactionPolicy:
    deny_patterns: Iterable[str] = tuple(DEFAULT_DENY_PATTERNS)
    max_bytes: int = DEFAULT_MAX_BYTES

    def assert_safe_text(self, text: str) -> None:
        b = text.encode("utf-8", errors="replace")
        if len(b) > self.max_bytes:
            raise RedactionError(f"payload too large: {len(b)} > {self.max_bytes}")

        for pat in self.deny_patterns:
            if re.search(pat, text):
                raise RedactionError(f"sensitive pattern matched: {pat}")
