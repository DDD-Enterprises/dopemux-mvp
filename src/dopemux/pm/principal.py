"""Authentication port; identity claims are not a verifier implementation."""

from dataclasses import dataclass
import hashlib
from typing import Protocol
from urllib.parse import quote

from .ownership import canonical_json


def request_binding(project_id: str, operation: str, body: dict) -> str:
    method = "GET" if operation == "task.read" else "POST"
    suffix = {"task.create": "tasks", "task.transition": "transition"}.get(operation)
    if operation == "task.read":
        suffix = (
            "tasks/" + quote(body["task_id"], safe="")
            if "task_id" in body
            else ("receipts" if "operation_kind" in body else "state")
        )
    if suffix is None:
        raise ValueError("Unknown principal operation")
    route = f"/api/v2/projects/{quote(project_id,safe='')}/workflow/{suffix}"
    return hashlib.sha256(
        canonical_json(
            {
                "method": method,
                "route": route,
                "project_id": project_id,
                "operation_kind": operation,
                "body_sha256": hashlib.sha256(canonical_json(body)).hexdigest(),
            }
        )
    ).hexdigest()


@dataclass(frozen=True)
class VerifiedPrincipal:
    """Server-created verifier output. Never deserialize this from request JSON."""

    principal_id: str
    client_id: str
    verifier_id: str
    credential_generation: str
    audience: str
    expires_at: float
    request_binding: str


class PrincipalVerifier(Protocol):
    def verify(
        self, *, project_id: str, operation: str, body: dict, credential: str | None
    ) -> VerifiedPrincipal: ...


class DenyPrincipalVerifier:
    def verify(self, **_):
        raise PermissionError("Principal verifier unavailable")
