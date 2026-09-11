"""Tests for dopemux.governed_execution.environment.custody.

Every authored receipt is validated against writer_custody_receipt.v1
through a local referencing.Registry built from schemas/governed_execution
(mirrors the pattern in tests/governance/governed_execution/conftest.py,
which is read-only and not imported here). Covers HELD, RELEASED and
AMBIGUOUS branches, CustodyRefused on out-of-scope writes, allowlist and
patch digest equality against an independent hashlib computation, and the
authority literal.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from dopemux.governed_execution.environment.custody import (
    CustodyRefused,
    ObservedFacts,
    WriterIdentity,
    WriterLease,
    author_custody_receipt,
)
from dopemux.governed_execution.environment.plan import (
    EnvironmentSpec,
    plan_environment,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_DIR = REPO_ROOT / "schemas" / "governed_execution"

BASE_SHA = "1c915b9141e9a5c3d835a5c7ea953381782ae875"
HEAD_SHA = "eff38e97f788af09f49eb5887f3a312e40cfaadd"
BRANCH = "feat/gec-v2-w03-isolation-custody-001"


def _build_registry() -> Registry:
    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="ascii"))
        Draft7Validator.check_schema(schema)
        resources.append(Resource(contents=schema, specification=DRAFT7))
    registry: Registry = Registry().with_resources(
        (resource.id(), resource) for resource in resources
    )
    return registry


@pytest.fixture(scope="module")
def receipt_validator() -> Draft7Validator:
    registry = _build_registry()
    schema = json.loads(
        (SCHEMA_DIR / "writer_custody_receipt.v1.schema.json").read_text(
            encoding="ascii"
        )
    )
    return Draft7Validator(schema, registry=registry)


def make_plan(allowed_paths: tuple[str, ...] = ("src/example.py",)):
    spec = EnvironmentSpec(
        repo_origin_url="https://github.com/DDD-Enterprises/dopemux-mvp.git",
        repo_toplevel="/Users/hue/code/dopemux-mvp",
        packet_id="TP-DMX-GEC-V2-W03-ISOLATION-CUSTODY-001",
        base_sha=BASE_SHA,
        branch=BRANCH,
        worktree_root="/Users/hue/code/dopemux-mvp/.worktrees",
        allowed_paths=allowed_paths,
    )
    return plan_environment(spec)


def make_writer() -> WriterIdentity:
    return WriterIdentity(runner="claude", session_ref="sess-1", agent_role="implementer")


def make_lease(expires_at: str = "2026-09-11T23:59:59Z") -> WriterLease:
    return WriterLease(
        lease_id="lease-1",
        issued_at="2026-09-11T00:00:00Z",
        expires_at=expires_at,
    )


def make_facts(**overrides: Any) -> ObservedFacts:
    fields: dict[str, Any] = {
        "head_sha": HEAD_SHA,
        "patch_bytes": b"diff --git a/x b/x",
        "outside_root_writes": False,
        "worktree_exists": True,
        "branch_matches": True,
    }
    fields.update(overrides)
    return ObservedFacts(**fields)


def test_held_receipt_validates_against_schema(receipt_validator: Draft7Validator) -> None:
    plan = make_plan()
    receipt = author_custody_receipt(
        plan, make_writer(), make_lease(), make_facts(), now="2026-09-11T12:00:00Z"
    )
    receipt_validator.validate(receipt)
    assert receipt["custody_state"] == "HELD"
    assert receipt["authority"] == "NONE"


def test_released_when_lease_expired(receipt_validator: Draft7Validator) -> None:
    plan = make_plan()
    lease = make_lease(expires_at="2026-09-11T00:00:01Z")
    receipt = author_custody_receipt(
        plan, make_writer(), lease, make_facts(), now="2026-09-12T00:00:00Z"
    )
    receipt_validator.validate(receipt)
    assert receipt["custody_state"] == "RELEASED"


def test_released_when_now_equals_expiry(receipt_validator: Draft7Validator) -> None:
    plan = make_plan()
    lease = make_lease(expires_at="2026-09-11T12:00:00Z")
    receipt = author_custody_receipt(
        plan, make_writer(), lease, make_facts(), now="2026-09-11T12:00:00Z"
    )
    receipt_validator.validate(receipt)
    assert receipt["custody_state"] == "RELEASED"


@pytest.mark.parametrize(
    "overrides",
    [
        {"worktree_exists": None},
        {"branch_matches": None},
        {"worktree_exists": False},
        {"branch_matches": False},
        {"worktree_exists": None, "branch_matches": None},
    ],
)
def test_ambiguous_on_unprovable_or_false_facts(
    receipt_validator: Draft7Validator, overrides: dict[str, Any]
) -> None:
    plan = make_plan()
    receipt = author_custody_receipt(
        plan, make_writer(), make_lease(), make_facts(**overrides), now="2026-09-11T12:00:00Z"
    )
    receipt_validator.validate(receipt)
    assert receipt["custody_state"] == "AMBIGUOUS"


@pytest.mark.parametrize("outside_root_writes", [True, None])
def test_custody_refused_on_out_of_scope_writes(outside_root_writes: bool | None) -> None:
    plan = make_plan()
    facts = make_facts(outside_root_writes=outside_root_writes)
    with pytest.raises(CustodyRefused) as excinfo:
        author_custody_receipt(
            plan, make_writer(), make_lease(), facts, now="2026-09-11T12:00:00Z"
        )
    assert excinfo.value.reason


def test_allowlist_digest_matches_independent_hashlib_computation() -> None:
    plan = make_plan(allowed_paths=("b/two.py", "a/one.py"))
    receipt = author_custody_receipt(
        plan, make_writer(), make_lease(), make_facts(), now="2026-09-11T12:00:00Z"
    )
    expected = hashlib.sha256(
        "\n".join(sorted(plan.allowed_paths)).encode("ascii")
    ).hexdigest()
    assert receipt["allowlist_digest"] == expected


def test_patch_sha256_matches_independent_hashlib_computation() -> None:
    plan = make_plan()
    patch = b"diff --git a/foo b/foo\n+bar\n"
    receipt = author_custody_receipt(
        plan,
        make_writer(),
        make_lease(),
        make_facts(patch_bytes=patch),
        now="2026-09-11T12:00:00Z",
    )
    expected = hashlib.sha256(patch).hexdigest()
    assert receipt["diff_provenance"]["patch_sha256"] == expected


def test_patch_sha256_of_none_is_sha256_of_empty_bytes() -> None:
    plan = make_plan()
    receipt = author_custody_receipt(
        plan,
        make_writer(),
        make_lease(),
        make_facts(patch_bytes=None),
        now="2026-09-11T12:00:00Z",
    )
    expected = hashlib.sha256(b"").hexdigest()
    assert receipt["diff_provenance"]["patch_sha256"] == expected


def test_authority_is_always_none_literal(receipt_validator: Draft7Validator) -> None:
    plan = make_plan()
    receipt = author_custody_receipt(
        plan, make_writer(), make_lease(), make_facts(), now="2026-09-11T12:00:00Z"
    )
    receipt_validator.validate(receipt)
    assert receipt["authority"] == "NONE"


def test_filesystem_scope_outside_root_writes_is_always_false(
    receipt_validator: Draft7Validator,
) -> None:
    plan = make_plan()
    receipt = author_custody_receipt(
        plan, make_writer(), make_lease(), make_facts(), now="2026-09-11T12:00:00Z"
    )
    receipt_validator.validate(receipt)
    assert receipt["filesystem_scope"]["outside_root_writes"] is False
