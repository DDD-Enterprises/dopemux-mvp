"""Closed local operator input validation. Never creates registry identities."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .ownership import StrictModel, ID, Key, Digest, Positive, ContractError, parse_json_object

ACTION = Literal[
    "task.read",
    "task.create",
    "task.transition.start",
    "task.transition.block",
    "task.transition.resume",
    "task.transition.done",
]


class Grant(StrictModel):
    principal_id: ID
    client_ids: list[ID]
    verifier_ids: list[ID]
    credential_generations: list[ID]
    actions: list[ACTION]


class SourceAllocation(StrictModel):
    project_id: ID
    source_system: ID
    source_instance_id: ID
    external_project_id: ID


class SourceMapping(StrictModel):
    source_system: ID
    source_instance_id: ID
    external_project_id: ID
    producer_principal_ids: list[ID]


class LegacyAllocation(StrictModel):
    project_id: ID
    task_id: ID
    source_system: ID
    source_instance_id: ID
    source_task_id: ID


class AllocationInventory(StrictModel):
    schema_version: Literal["dopemux.pm.allocation-inventory.v1"]
    revision: Positive
    complete: bool
    composite_consumers_qualified: bool
    admissions: list[ID]
    sources: list[SourceAllocation]
    legacy_allocations: list[LegacyAllocation]

    @model_validator(mode="after")
    def uniqueness(self):
        if self.complete is not True or self.composite_consumers_qualified is not True:
            raise ContractError("Complete inventory and composite consumers required")
        if len(self.admissions) != len(set(self.admissions)):
            raise ContractError("Duplicate admission allocation")
        sources, identities, ids = set(), set(), set()
        for s in self.sources:
            key = (s.source_system, s.source_instance_id, s.external_project_id)
            if key in sources or s.project_id not in self.admissions:
                raise ContractError("Conflicting source allocation")
            sources.add(key)
        for a in self.legacy_allocations:
            key = (a.source_system, a.source_instance_id, a.source_task_id)
            scoped = (a.project_id, a.task_id)
            if key in identities or scoped in ids or a.project_id not in self.admissions:
                raise ContractError("Conflicting legacy allocation")
            identities.add(key)
            ids.add(scoped)
        return self


class CompletionPolicy(StrictModel):
    id: ID
    version: Positive
    kind: Literal["workflow-kernel-v1"]


class AdmissionBundle(StrictModel):
    schema_version: Literal["dopemux.pm.admission-bundle.v1"]
    idempotency_key: Key
    project_id: ID
    workspace_id: ID
    instance_id: ID
    admission_id: ID
    expected_epoch: Annotated[int, Field(strict=True, ge=0)]
    store_uuid: ID
    status: Literal["ACTIVE", "SUSPENDED"]
    registry_path: ID
    registry_sha256: Digest
    registry_generation: Annotated[int, Field(strict=True, ge=0)]
    operator_decision_ref: ID
    created_at_utc: ID
    sources: list[SourceMapping]
    grants: list[Grant]
    completion_policies: list[CompletionPolicy]
    destinations: list[ID]
    inventory: AllocationInventory

    @model_validator(mode="after")
    def authorized_inventory(self):
        if self.project_id not in self.inventory.admissions:
            raise ContractError("Missing active admission inventory")
        for field in (
            self.destinations,
            [g.principal_id for g in self.grants],
            [p.id for p in self.completion_policies],
        ):
            if len(field) != len(set(field)):
                raise ContractError("Duplicate policy entry")
        mappings = set()
        for s in self.sources:
            key = (s.source_system, s.source_instance_id)
            if key in mappings:
                raise ContractError("Ambiguous source instance")
            mappings.add(key)
            if not any(
                a.project_id == self.project_id
                and a.source_system == s.source_system
                and a.source_instance_id == s.source_instance_id
                and a.external_project_id == s.external_project_id
                for a in self.inventory.sources
            ):
                raise ContractError("Missing source allocation")
        return self


def merge_known_inventory(previous: dict | None, incoming: dict) -> dict:
    """Replay-only union of admitted/imported allocations; never choose a winner.

    Historical imports could add allocations without advancing policy revision.
    Keep that history readable while retaining every known immutable allocation.
    """
    incoming = AllocationInventory.model_validate(incoming).model_dump()
    if previous is None:
        previous = incoming
    previous = AllocationInventory.model_validate(previous).model_dump()
    merged = dict(incoming, revision=max(previous["revision"], incoming["revision"]))
    merged["admissions"] = sorted(
        set(previous["admissions"]) | set(incoming["admissions"])
    )
    for field, keys in (
        ("sources", ("source_system", "source_instance_id", "external_project_id")),
        (
            "legacy_allocations",
            ("source_system", "source_instance_id", "source_task_id"),
        ),
    ):
        allocations = {}
        for allocation in previous[field] + incoming[field]:
            key = tuple(allocation[k] for k in keys)
            if key in allocations and allocations[key] != allocation:
                raise ContractError("Conflicting historical allocation")
            allocations[key] = allocation
        merged[field] = [allocations[key] for key in sorted(allocations)]
    # Also checks the reverse legacy (project, task) uniqueness across manifests.
    return AllocationInventory.model_validate(merged).model_dump()


def validate_admission_replacement(previous, replacement, tasks, known_inventory):
    """Shared live/replay invariant, independent of mutable grants and status."""
    candidate = dict(replacement)
    candidate.pop("admission_epoch", None)
    AdmissionBundle.model_validate(candidate)
    inventory = replacement["inventory"]
    merged = merge_known_inventory(known_inventory, inventory)
    normalized = merge_known_inventory(None, inventory)
    if inventory["revision"] < known_inventory["revision"] or merged != normalized:
        raise ContractError("Allocation inventory regression")
    if (
        inventory["revision"] == known_inventory["revision"]
        and normalized != known_inventory
    ):
        raise ContractError("Inventory change requires a newer revision")
    for task in tasks:
        identity = task["identity"]
        key = (identity["source_system"], identity["source_instance_id"])

        def source(policy):
            return next(
                (
                    s
                    for s in policy["sources"]
                    if (s["source_system"], s["source_instance_id"]) == key
                ),
                None,
            )

        old_source, new_source = source(previous), source(replacement)
        if (
            old_source is None
            or new_source is None
            or any(
                old_source[field] != new_source[field]
                for field in (
                    "source_system",
                    "source_instance_id",
                    "external_project_id",
                )
            )
        ):
            raise ContractError("Existing task source binding is immutable")
        old_policy = next(
            (
                p
                for p in previous["completion_policies"]
                if p["id"] == task["completion_policy_id"]
                and p["version"] == task["completion_policy_version"]
            ),
            None,
        )
        if old_policy is None or old_policy not in replacement["completion_policies"]:
            raise ContractError("Existing task completion policy is immutable")
        if (
            task["task_id_scheme"] == "legacy-v1"
            and dict(task_id=task["task_id"], **identity)
            not in inventory["legacy_allocations"]
        ):
            raise ContractError("Missing existing legacy allocation")
    return normalized


class Alias(StrictModel):
    kind: ID
    value: ID


class RegistryInstance(StrictModel):
    instance_id: ID
    aliases: list[Alias]


class RegistryWorkspace(StrictModel):
    workspace_id: ID
    aliases: list[Alias]
    instances: dict[ID, RegistryInstance]


class RegistryProject(StrictModel):
    project_id: ID
    aliases: list[Alias]
    workspaces: dict[ID, RegistryWorkspace]


class RegistrySnapshot(StrictModel):
    schema_version: Literal["dopemux.mcp.identity-registry.v1"]
    generation: Annotated[int, Field(strict=True, ge=0)]
    updated_at: ID
    projects: dict[ID, RegistryProject]

    @model_validator(mode="after")
    def full_chain(self):
        aliases, workspaces, instances = {}, set(), set()

        def check(record, project):
            for alias in record.aliases:
                key = (alias.kind, alias.value)
                if key in aliases and aliases[key] != project:
                    raise ContractError("Conflicting registry alias")
                aliases[key] = project

        for pid, project in self.projects.items():
            if project.project_id != pid:
                raise ContractError("Registry project key mismatch")
            check(project, pid)
            for wid, workspace in project.workspaces.items():
                if workspace.workspace_id != wid or wid in workspaces:
                    raise ContractError("Registry workspace mismatch")
                workspaces.add(wid)
                check(workspace, pid)
                for iid, instance in workspace.instances.items():
                    if instance.instance_id != iid or iid in instances:
                        raise ContractError("Registry instance mismatch")
                    instances.add(iid)
                    check(instance, pid)
        return self


def safe_path(path: Path, *, exists: bool = True) -> Path:
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ContractError("Explicit absolute path required")
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ContractError("Symlink path forbidden")
    if not path.parent.is_dir():
        raise ContractError("Parent must already exist")
    parent = path.parent.stat()
    if parent.st_uid != os.getuid() or parent.st_mode & 0o077:
        raise ContractError("Operator-only parent permissions required")
    if path.exists():
        info = path.stat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
            or info.st_nlink != 1
        ):
            raise ContractError("Operator-only regular file required")
    elif exists:
        raise ContractError("Required local file absent")
    return path


@dataclass(frozen=True)
class OperatorLocalContext:
    principal_id: str
    approval_sha256: str
    bundle_bytes: bytes
    registry_path: Path
    registry_sha256: str

    def recheck(self):
        if (
            hashlib.sha256(safe_path(self.registry_path).read_bytes()).hexdigest()
            != self.registry_sha256
        ):
            raise ContractError("Registry handoff drift")


def approved_admission(
    path: Path, expected_sha256: str
) -> tuple[AdmissionBundle, OperatorLocalContext]:
    raw = safe_path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ContractError("Approval digest mismatch")
    bundle = AdmissionBundle.model_validate(parse_json_object(raw))
    registry_path = safe_path(Path(bundle.registry_path))
    registry_raw = registry_path.read_bytes()
    if hashlib.sha256(registry_raw).hexdigest() != bundle.registry_sha256:
        raise ContractError("Registry digest mismatch")
    registry = RegistrySnapshot.model_validate(parse_json_object(registry_raw))
    try:
        registry.projects[bundle.project_id].workspaces[bundle.workspace_id].instances[
            bundle.instance_id
        ]
    except KeyError as exc:
        raise ContractError("Registry chain absent") from exc
    if registry.generation != bundle.registry_generation:
        raise ContractError("Registry generation mismatch")
    return bundle, OperatorLocalContext(
        "operator-local:" + str(os.getuid()),
        expected_sha256,
        raw,
        registry_path,
        bundle.registry_sha256,
    )
