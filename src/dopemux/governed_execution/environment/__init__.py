"""Environment planning and writer custody receipt authoring.

W03 of MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001. Pure, deterministic
modelling only: plan_environment computes an EnvironmentPlan from an
EnvironmentSpec with no filesystem, process or clock access, and
author_custody_receipt renders a WriterCustodyReceipt dict from a plan,
writer identity, lease and caller-observed facts. Applying a plan (real
provisioning) is out of scope for this workstream.
"""
from __future__ import annotations

from .custody import (
    CustodyRefused,
    ObservedFacts,
    WriterIdentity,
    WriterLease,
    author_custody_receipt,
)
from .plan import (
    EnvironmentPlan,
    EnvironmentSpec,
    PlanRejected,
    RepoIdentity,
    RollbackLocality,
    plan_environment,
)

__all__ = [
    "CustodyRefused",
    "EnvironmentPlan",
    "EnvironmentSpec",
    "ObservedFacts",
    "PlanRejected",
    "RepoIdentity",
    "RollbackLocality",
    "WriterIdentity",
    "WriterLease",
    "author_custody_receipt",
    "plan_environment",
]
