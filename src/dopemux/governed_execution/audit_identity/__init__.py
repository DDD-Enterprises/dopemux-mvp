"""W07: structured audit identity, evidence location and PR Steward boundary.

Pure, deterministic modules only. No readiness, approval or merge authority
is produced anywhere in this package; every output dataclass carries
``authority = "NONE"``.
"""

from dopemux.governed_execution.audit_identity.identity import (
    AuditIdentity,
    IdentityLayer,
    QualificationReceiptRef,
    layers,
)
from dopemux.governed_execution.audit_identity.independence import (
    IndependenceAssessment,
    independence,
)
from dopemux.governed_execution.audit_identity.legacy import (
    LegacyProjection,
    project_legacy_embedded_audit,
)
from dopemux.governed_execution.audit_identity.location import (
    EvidenceKind,
    EvidenceLocation,
    HeadBinding,
    classify_location,
    exact_head_binding,
    split,
)
from dopemux.governed_execution.audit_identity.steward_boundary import (
    classify_steward_action,
)

__all__ = [
    "AuditIdentity",
    "IdentityLayer",
    "QualificationReceiptRef",
    "layers",
    "IndependenceAssessment",
    "independence",
    "LegacyProjection",
    "project_legacy_embedded_audit",
    "EvidenceKind",
    "EvidenceLocation",
    "HeadBinding",
    "classify_location",
    "exact_head_binding",
    "split",
    "classify_steward_action",
]
