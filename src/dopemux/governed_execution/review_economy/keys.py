"""Review receipt identity: keys, records and the shared timestamp parser.

Pure module: no process spawning, no clock reads, no filesystem, no network.
Every timestamp handled here is a caller-supplied RFC 3339 UTC string; this
module never reads the wall clock.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime

REVIEW_TYPES: frozenset[str] = frozenset(
    {
        "CI",
        "CODE_REVIEW",
        "SEMANTIC_REVIEW",
        "SECURITY_REVIEW",
        "FINAL_INDEPENDENT_AUDIT",
    }
)

REVIEWER_CLASSES: frozenset[str] = frozenset(
    {
        "DETERMINISTIC",
        "MODEL_STANDARD",
        "MODEL_PREMIUM",
        "HUMAN",
    }
)

MODEL_REVIEWER_CLASSES: frozenset[str] = frozenset(
    {cls for cls in REVIEWER_CLASSES if cls.startswith("MODEL_")}
)

_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RFC3339_UTC_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$"
)


def is_git_oid(value: object) -> bool:
    """Return True iff value is a lowercase 40-hex-digit git object id string."""
    return isinstance(value, str) and bool(_GIT_OID_RE.fullmatch(value))


def is_sha256(value: object) -> bool:
    """Return True iff value is a lowercase 64-hex-digit sha256 digest string."""
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def is_rfc3339_utc(value: object) -> bool:
    """Return True iff value matches the RFC 3339 UTC (trailing Z) pattern."""
    return isinstance(value, str) and bool(_RFC3339_UTC_RE.fullmatch(value))


def parse_rfc3339_utc(value: str) -> datetime:
    """Parse a caller-supplied RFC 3339 UTC string into a datetime.

    The trailing Z is replaced with an explicit +00:00 offset before handing
    the string to datetime.fromisoformat, per the caller-supplied-timestamp
    contract for this package: no wall-clock read ever occurs here.
    """
    if not is_rfc3339_utc(value):
        raise ValueError(f"not an RFC3339 UTC timestamp: {value!r}")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _require_ascii(value: str, field_name: str) -> None:
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be ASCII: {value!r}") from exc


@dataclass(frozen=True)
class ReviewReceiptKey:
    """Identity of a reviewable subject: what kind of review, at what head,
    under what policy, by what class of reviewer.

    Equality of two keys is equality of their four fields, which is in turn
    equality of their digests: digest is a pure function of the fields.
    """

    review_type: str
    head_sha: str
    policy_digest: str
    reviewer_class: str

    def __post_init__(self) -> None:
        if self.review_type not in REVIEW_TYPES:
            raise ValueError(f"review_type not in closed set: {self.review_type!r}")
        if self.reviewer_class not in REVIEWER_CLASSES:
            raise ValueError(
                f"reviewer_class not in closed set: {self.reviewer_class!r}"
            )
        if not is_git_oid(self.head_sha):
            raise ValueError(f"head_sha is not a git object id: {self.head_sha!r}")
        if not is_sha256(self.policy_digest):
            raise ValueError(
                f"policy_digest is not a sha256 digest: {self.policy_digest!r}"
            )

    @property
    def digest(self) -> str:
        """sha256 of the four fields joined by newline, in fixed order."""
        joined = "\n".join(
            (
                self.review_type,
                self.head_sha,
                self.policy_digest,
                self.reviewer_class,
            )
        )
        return hashlib.sha256(joined.encode("ascii")).hexdigest()


@dataclass(frozen=True)
class ReceiptRef:
    """A reference to a receipt artifact on disk: path plus content digest."""

    path: str
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or len(self.path) == 0:
            raise ValueError(f"path must be a non-empty string: {self.path!r}")
        _require_ascii(self.path, "path")
        if not is_sha256(self.sha256):
            raise ValueError(f"sha256 is not a sha256 digest: {self.sha256!r}")


@dataclass(frozen=True)
class ReviewReceiptRecord:
    """A previously issued review outcome, evaluated for reuse eligibility."""

    key: ReviewReceiptKey
    verdict: str
    issued_at: str
    expires_at: str
    invalidated: bool
    subject_head: str
    receipt_ref: ReceiptRef

    def __post_init__(self) -> None:
        if not isinstance(self.key, ReviewReceiptKey):
            raise ValueError("key must be a ReviewReceiptKey")
        if not isinstance(self.verdict, str) or len(self.verdict) == 0:
            raise ValueError(f"verdict must be a non-empty string: {self.verdict!r}")
        _require_ascii(self.verdict, "verdict")
        if not is_rfc3339_utc(self.issued_at):
            raise ValueError(f"issued_at is not RFC3339 UTC: {self.issued_at!r}")
        if not is_rfc3339_utc(self.expires_at):
            raise ValueError(f"expires_at is not RFC3339 UTC: {self.expires_at!r}")
        if not isinstance(self.invalidated, bool):
            raise ValueError(f"invalidated must be a bool: {self.invalidated!r}")
        if not is_git_oid(self.subject_head):
            raise ValueError(
                f"subject_head is not a git object id: {self.subject_head!r}"
            )
        if not isinstance(self.receipt_ref, ReceiptRef):
            raise ValueError("receipt_ref must be a ReceiptRef")
        # issued_at <= expires_at is a well-formedness check, not a reuse
        # eligibility check (reuse eligibility compares expires_at to the
        # caller-supplied now, done in the decision module).
        if parse_rfc3339_utc(self.issued_at) > parse_rfc3339_utc(self.expires_at):
            raise ValueError("issued_at must not be after expires_at")
