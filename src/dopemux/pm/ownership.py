"""Strict project ownership wire contracts. No store, provider or process effects."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, AfterValidator, model_validator


class ContractError(ValueError):
    pass


def _scalars(value):
    if isinstance(value, str):
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ContractError("Invalid Unicode scalar")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError("Object keys must be strings")
            _scalars(key)
            _scalars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _scalars(item)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ContractError("Nonfinite number")
    return value


def canonical_json(value) -> bytes:
    return json.dumps(
        _scalars(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def parse_json_object(raw: bytes | str) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid(_):
        raise ContractError("Nonfinite JSON number")

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(result, dict):
        raise ContractError("Expected JSON object")
    return _scalars(result)


def identifier(value: str) -> str:
    _scalars(value)
    if not value or value != value.strip():
        raise ContractError("Invalid identifier")
    return value


def _key(value: str) -> str:
    identifier(value)
    if len(value) > 128 or any(not 32 <= ord(c) <= 126 for c in value):
        raise ContractError("Invalid idempotency key")
    return value


ID = Annotated[str, AfterValidator(identifier)]
Key = Annotated[str, AfterValidator(_key)]
Positive = Annotated[int, Field(strict=True, ge=1)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def scalar_values(cls, value):
        return _scalars(value)


class Identity(StrictModel):
    project_id: ID
    source_system: ID
    source_instance_id: ID
    source_task_id: ID


class EvidenceRef(StrictModel):
    id: ID
    sha256: Digest


class TransitionCommand(StrictModel):
    schema_version: Literal["dopemux.pm.transition-command.v1"]
    task_id: ID
    transition: Literal["start", "resume", "block", "done"]
    expected_version: Positive
    expected_binding_version: Positive
    admission_epoch: Positive
    idempotency_key: Key
    reason: Annotated[str, Field(max_length=4096)] | None
    completion_evidence_ref: EvidenceRef | None

    @model_validator(mode="after")
    def conditional_fields(self):
        if self.transition in ("resume", "done") and not (self.reason and self.reason.strip()):
            raise ContractError("Reason required")
        if (self.transition == "done") != (self.completion_evidence_ref is not None):
            raise ContractError("Completion reference required only for done")
        return self


class CreateTaskCommand(StrictModel):
    schema_version: Literal["dopemux.pm.create-command.v1"]
    idempotency_key: Key
    admission_epoch: Positive
    identity: Identity
    title: Annotated[str, Field(min_length=1)]
    description: str | None
    dependencies: list[ID]
    linked_ids: dict[ID, ID]
    completion_policy_id: ID

    @model_validator(mode="after")
    def ordered_edges(self):
        if self.identity.source_system == "dopemux":
            try:
                uuid.UUID(self.identity.source_task_id)
            except ValueError as exc:
                raise ContractError("Native creation requires a persisted operation UUID") from exc
        if self.dependencies != sorted(set(self.dependencies)):
            raise ContractError("Dependencies must be sorted and unique")
        return self


class CompletionVerification(StrictModel):
    policy_id: ID
    policy_version: Positive
    snapshot_sha256: Digest
    gate_scope: ID


class TransitionReceipt(StrictModel):
    schema_version: Literal["dopemux.pm.transition-receipt.v1"]
    outcome: Literal["APPLIED"]
    receipt_id: ID
    event_id: ID
    event_sequence: Positive
    project_id: ID
    task_id: ID
    principal_id: ID
    client_id: ID
    verifier_id: ID
    credential_generation: ID
    operation_kind: Literal["task.transition"]
    idempotency_key: Key
    request_sha256: Digest
    binding_version: Positive
    admission_epoch_at_commit: Positive
    from_status: Literal["TODO", "IN_PROGRESS", "BLOCKED"]
    to_status: Literal["IN_PROGRESS", "BLOCKED", "DONE"]
    version_before: Positive
    version_after: Positive
    committed_at_utc: str
    source_binding_ref: ID
    completion_verification: CompletionVerification | None

    @model_validator(mode="after")
    def relational(self):
        parsed = datetime.fromisoformat(self.committed_at_utc.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ContractError("UTC timestamp required")
        if self.version_after != self.version_before + 1:
            raise ContractError("Invalid lifecycle version")
        if (self.to_status == "DONE") != (self.completion_verification is not None):
            raise ContractError("Invalid completion result")
        if (self.from_status, self.to_status) not in {
            ("TODO", "IN_PROGRESS"),
            ("BLOCKED", "IN_PROGRESS"),
            ("TODO", "BLOCKED"),
            ("IN_PROGRESS", "BLOCKED"),
            ("IN_PROGRESS", "DONE"),
        }:
            raise ContractError("Illegal receipt transition")
        return self


def command_digest(
    body: dict, *, project_id: str, principal_id: str, client_id: str, operation_kind: str
) -> str:
    context = {
        "project_id": project_id,
        "principal_id": principal_id,
        "client_id": client_id,
        "operation_kind": operation_kind,
    }
    if set(body) & set(context):
        raise ContractError("Protected command context")
    for value in context.values():
        identifier(value)
    fields = {**context, **{k: v for k, v in body.items() if k != "idempotency_key"}}
    return hashlib.sha256(b"dopemux.pm.command.v1\0" + canonical_json(fields)).hexdigest()


def new_task_id(identity: dict) -> str:
    body = Identity.model_validate(identity).model_dump()
    return "pmt_" + hashlib.sha256(b"dopemux.pm.task.v2\0" + canonical_json(body)).hexdigest()


def validate_receipt(
    receipt: dict, command: dict, *, project_id: str, principal_id: str, client_id: str
) -> dict:
    cmd = TransitionCommand.model_validate(command)
    result = TransitionReceipt.model_validate(receipt)
    expected = dict(
        project_id=project_id,
        principal_id=principal_id,
        client_id=client_id,
        task_id=cmd.task_id,
        idempotency_key=cmd.idempotency_key,
        version_before=cmd.expected_version,
        binding_version=cmd.expected_binding_version,
        admission_epoch_at_commit=cmd.admission_epoch,
        request_sha256=command_digest(
            cmd.model_dump(),
            project_id=project_id,
            principal_id=principal_id,
            client_id=client_id,
            operation_kind="task.transition",
        ),
    )
    if any(getattr(result, k) != v for k, v in expected.items()):
        raise ContractError("Receipt does not match command")
    states = {
        "start": ({"TODO"}, "IN_PROGRESS"),
        "resume": ({"BLOCKED"}, "IN_PROGRESS"),
        "block": ({"TODO", "IN_PROGRESS"}, "BLOCKED"),
        "done": ({"IN_PROGRESS"}, "DONE"),
    }
    before, after = states[cmd.transition]
    if result.from_status not in before or result.to_status != after:
        raise ContractError("Receipt transition does not match command")
    if cmd.transition == "done" and (
        result.completion_verification.snapshot_sha256 != cmd.completion_evidence_ref.sha256
    ):
        raise ContractError("Receipt completion snapshot does not match command")
    return result.model_dump()
