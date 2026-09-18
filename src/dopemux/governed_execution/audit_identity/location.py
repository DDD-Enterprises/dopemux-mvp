"""Evidence-location classification and exact-head binding.

Pure module. Distinguishes the substantive candidate branch from the
evidence store, and enforces AUDITED_HEAD == FINALITY_HEAD == FREEZE_HEAD as
a pure structural check. Target architecture: the candidate branch carries
only substantive candidate content; the evidence store carries validation,
audit and finality evidence (``proof/``, ``proofs/``, ``out/``, ``reports/``
and the ``.proof.json`` / ``PROOF.json`` / ``AUDITOR_REPORT.md`` file
family). This module produces no readiness, approval or merge signal; every
output carries authority ``"NONE"``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")

_EVIDENCE_STORE_PREFIXES = ("proof/", "proofs/", "out/", "reports/")
_EVIDENCE_STORE_SUFFIXES = (".proof.json", "PROOF.json", "AUDITOR_REPORT.md")


class EvidenceKind(Enum):
    CANDIDATE_BRANCH = "CANDIDATE_BRANCH"
    EVIDENCE_STORE = "EVIDENCE_STORE"


@dataclass(frozen=True)
class EvidenceLocation:
    kind: EvidenceKind
    ref: str
    authority: str = "NONE"


def classify_location(path: str) -> EvidenceKind:
    """Classify one repo-relative path. Top-level prefix match only (``proof/**``
    etc.), never a mid-path segment match.
    """
    if path.startswith(_EVIDENCE_STORE_PREFIXES):
        return EvidenceKind.EVIDENCE_STORE
    if path.endswith(_EVIDENCE_STORE_SUFFIXES):
        return EvidenceKind.EVIDENCE_STORE
    return EvidenceKind.CANDIDATE_BRANCH


def split(changed_paths: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Partition ``changed_paths`` into ``(candidate_paths, evidence_paths)``."""
    candidate: list[str] = []
    evidence: list[str] = []
    for path in changed_paths:
        if classify_location(path) is EvidenceKind.EVIDENCE_STORE:
            evidence.append(path)
        else:
            candidate.append(path)
    return tuple(candidate), tuple(evidence)


@dataclass(frozen=True)
class HeadBinding:
    bound: bool
    reasons: tuple[str, ...]
    authority: str = "NONE"


def exact_head_binding(audited_head: str, finality_head: str, freeze_head: str) -> HeadBinding:
    """Bound only when all three inputs are equal, well-formed 40-hex git oids.
    Any inequality or malformed value yields ``bound=False`` with the
    mismatching pair(s) named. No other path in this module can produce
    ``bound=True``.
    """
    candidates = {
        "audited_head": audited_head,
        "finality_head": finality_head,
        "freeze_head": freeze_head,
    }
    malformed = sorted(name for name, value in candidates.items() if not _GIT_OID_RE.fullmatch(value))
    if malformed:
        return HeadBinding(bound=False, reasons=(f"malformed oid: {', '.join(malformed)}",))

    if audited_head == finality_head == freeze_head:
        return HeadBinding(bound=True, reasons=())

    mismatches = []
    if audited_head != finality_head:
        mismatches.append("audited_head != finality_head")
    if finality_head != freeze_head:
        mismatches.append("finality_head != freeze_head")
    if audited_head != freeze_head:
        mismatches.append("audited_head != freeze_head")
    return HeadBinding(bound=False, reasons=tuple(mismatches))
