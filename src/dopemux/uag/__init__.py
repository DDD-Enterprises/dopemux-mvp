"""Universal Agent Gateway (UAG) semantic core.

Provider-neutral semantic primitives only. No provider SDK, socket, filesystem,
environment, credential, subprocess, or network I/O on import. No execution,
approval, retry, fallback, or tool authority.
"""

from dopemux.uag.attempt import AttemptLineage, AttemptRecord
from dopemux.uag.core import SemanticCore
from dopemux.uag.enums import (
    AttemptSemanticState,
    AttestationClass,
    CompatibilityStatus,
    Confidence,
    EvidenceStatus,
    ExecutionAuthority,
    IdentityStageName,
    OutputContractClass,
    PrivateStateReplayScope,
    SemanticLossClass,
)
from dopemux.uag.identity import (
    ConflictItem,
    IdentityChain,
    IdentityStage,
    UnknownItem,
)
from dopemux.uag.ir import (
    FamilyEnvelope,
    PrivateStateCapsuleRef,
    PublicCore,
    RequestedOutputContract,
)
from dopemux.uag.ledger import CorrelationKind, LedgerEntry, MappingLedger
from dopemux.uag.primitives import (
    DigestRef,
    canonical_digest,
    canonical_json,
    is_sha256,
    sha256_bytes,
    sha256_text,
)
from dopemux.uag.receipt import Receipt, deterministic_receipt
from dopemux.uag.request import LogicalRequest, WorkspaceBinding

__all__ = [
    "AttemptLineage",
    "AttemptRecord",
    "AttemptSemanticState",
    "AttestationClass",
    "CompatibilityStatus",
    "Confidence",
    "ConflictItem",
    "CorrelationKind",
    "DigestRef",
    "EvidenceStatus",
    "ExecutionAuthority",
    "FamilyEnvelope",
    "IdentityChain",
    "IdentityStage",
    "IdentityStageName",
    "LedgerEntry",
    "LogicalRequest",
    "MappingLedger",
    "OutputContractClass",
    "PrivateStateCapsuleRef",
    "PrivateStateReplayScope",
    "PublicCore",
    "Receipt",
    "RequestedOutputContract",
    "SemanticCore",
    "SemanticLossClass",
    "UnknownItem",
    "WorkspaceBinding",
    "canonical_digest",
    "canonical_json",
    "deterministic_receipt",
    "is_sha256",
    "sha256_bytes",
    "sha256_text",
]
