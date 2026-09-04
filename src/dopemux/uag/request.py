"""UAG immutable logical request identity.

A logical request is the durable identity under which physical attempts are
grouped. Its identity is immutable: the request id, workspace binding, and
correlation surface are frozen and hashable. Attempts live in a separate
append-only lineage (``attempt.py``) and never mutate the request.
"""

from __future__ import annotations

from dataclasses import dataclass

from dopemux.uag.ir import RequestedOutputContract
from dopemux.uag.primitives import canonical_digest


@dataclass(frozen=True)
class WorkspaceBinding:
    """Exact project/workspace binding for a logical request."""

    project_id: str
    workspace_ref: str
    request_id: str
    repository: str | None = None

    def __post_init__(self) -> None:
        for name in ("project_id", "workspace_ref", "request_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"WorkspaceBinding.{name} must be non-empty")


@dataclass(frozen=True)
class LogicalRequest:
    """Immutable logical request identity.

    Frozen and hashable. Any attempt to mutate a field raises
    ``FrozenInstanceError``; there is no setter path.
    """

    logical_request_id: str
    binding: WorkspaceBinding
    requested_output_contract: RequestedOutputContract

    def __post_init__(self) -> None:
        if not isinstance(self.logical_request_id, str) or not self.logical_request_id:
            raise ValueError("logical_request_id must be a non-empty string")
        if not isinstance(self.binding, WorkspaceBinding):
            raise ValueError("binding must be a WorkspaceBinding")
        if not isinstance(self.requested_output_contract, RequestedOutputContract):
            raise ValueError("requested_output_contract must be a RequestedOutputContract")

    @property
    def identity_digest(self) -> str:
        """Deterministic digest of the request identity (binding + id + contract)."""
        return canonical_digest(
            {
                "logical_request_id": self.logical_request_id,
                "project_id": self.binding.project_id,
                "workspace_ref": self.binding.workspace_ref,
                "request_id": self.binding.request_id,
                "repository": self.binding.repository,
                "output_class": self.requested_output_contract.output_class,
            }
        )
