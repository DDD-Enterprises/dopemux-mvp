#!/usr/bin/env python3
"""Validate P0 contract relationships JSON Schema Draft 7 cannot express."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any


RUN_CONTEXT_SCHEMA = "schemas/dcp/run_context_packet.schema.json"
AUDIT_RESULT_SCHEMA = "schemas/audit_broker/audit_result.schema.json"
IDENTITY_LAYERS = (
    "requested",
    "configured",
    "response_claimed",
    "proxy_reported",
    "provider_attested",
)


def _normalized_schema_path(schema_path: str) -> str:
    return PurePosixPath(schema_path.replace("\\", "/")).as_posix()


def _run_context_errors(instance: dict[str, Any]) -> list[str]:
    if instance.get("readiness") != "READY":
        return []

    context_items = instance.get("context_items")
    mandatory_evidence = instance.get("mandatory_evidence")
    if not isinstance(context_items, list) or not isinstance(mandatory_evidence, dict):
        return []
    bindings = mandatory_evidence.get("bindings")
    if not isinstance(bindings, list):
        return []

    items_by_ref: dict[str, list[dict[str, Any]]] = {}
    mandatory_refs: list[str] = []
    for item in context_items:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            continue
        ref = item["ref"]
        items_by_ref.setdefault(ref, []).append(item)
        if item.get("mandatory") is True:
            mandatory_refs.append(ref)

    errors: list[str] = []
    bound_context_refs: set[str] = set()
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            continue
        required_ref = binding.get("required_ref")
        context_item_ref = binding.get("context_item_ref")
        if not isinstance(required_ref, str) or not isinstance(context_item_ref, str):
            continue
        if required_ref != context_item_ref:
            errors.append(
                f"mandatory_evidence.bindings[{index}] required_ref must equal context_item_ref"
            )
        matches = items_by_ref.get(context_item_ref, [])
        if len(matches) != 1:
            errors.append(
                f"mandatory_evidence.bindings[{index}].context_item_ref must resolve to exactly one context item"
            )
        elif matches[0].get("mandatory") is not True:
            errors.append(
                f"mandatory_evidence.bindings[{index}].context_item_ref must resolve to a mandatory context item"
            )
        if required_ref not in items_by_ref:
            errors.append(
                f"mandatory_evidence.bindings[{index}].required_ref must resolve to a context item"
            )
        bound_context_refs.add(context_item_ref)

    for ref in mandatory_refs:
        if ref not in bound_context_refs:
            errors.append(f"mandatory context item {ref!r} has no evidence binding")
    return errors


def _audit_result_errors(instance: dict[str, Any]) -> list[str]:
    requirement = instance.get("identity_requirement")
    identities = instance.get("identities")
    if not isinstance(requirement, dict) or not isinstance(identities, dict):
        return []
    if requirement.get("disposition") != "SATISFIED":
        return []

    requested = identities.get("requested")
    expected = requested.get("value") if isinstance(requested, dict) else None
    if not isinstance(expected, str):
        return []

    errors: list[str] = []
    for layer in IDENTITY_LAYERS[1:]:
        observation = identities.get(layer)
        observed = observation.get("value") if isinstance(observation, dict) else None
        if observed != expected:
            errors.append(f"SATISFIED identity {layer} must exactly match requested")
    return errors


def validate_p0_contract_semantics(schema_path: str, instance: Any) -> list[str]:
    """Return stable semantic errors for one schema/instance pair."""

    if not isinstance(instance, dict):
        return ["instance must be an object"]
    normalized = _normalized_schema_path(schema_path)
    if normalized.endswith(RUN_CONTEXT_SCHEMA):
        return _run_context_errors(instance)
    if normalized.endswith(AUDIT_RESULT_SCHEMA):
        return _audit_result_errors(instance)
    return []


def _validate_fixture_file(path: Path) -> list[str]:
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for fixture in fixtures:
        name = fixture.get("name", "<unnamed>")
        schema = fixture.get("schema")
        instance = fixture.get("instance")
        if not isinstance(schema, str):
            errors.append(f"{name}: schema path is missing")
            continue
        errors.extend(
            f"{name}: {error}"
            for error in validate_p0_contract_semantics(schema, instance)
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    errors = _validate_fixture_file(args.fixtures)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: P0 semantic validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
