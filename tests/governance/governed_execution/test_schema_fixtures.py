"""Positive/negative fixture validation for schemas/governed_execution/*.

Every valid fixture must validate against its schema. Every invalid fixture
must either fail schema validation, or (for the one fixture that is
schema-valid but semantically wrong, per conftest.semantic_violations)
trip a semantic violation. Every schema must declare
additionalProperties: false at every object level it defines.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from tests.governance.governed_execution.conftest import (
    SCHEMA_FILES,
    iter_invalid_fixtures,
    iter_valid_fixtures,
    semantic_violations,
)

VALID_FIXTURES = list(iter_valid_fixtures())
INVALID_FIXTURES = list(iter_invalid_fixtures())


def _load(path) -> dict[str, Any]:
    with path.open("r", encoding="ascii") as fh:
        return json.load(fh)


@pytest.mark.parametrize(
    "schema_shortname,path",
    VALID_FIXTURES,
    ids=[f"{s}:{p.name}" for s, p in VALID_FIXTURES],
)
def test_valid_fixture_validates(schema_shortname, path, validator_factory, schemas) -> None:
    assert schema_shortname in schemas, f"unknown schema shortname {schema_shortname!r} for {path}"
    validator = validator_factory(schemas[schema_shortname])
    instance = _load(path)
    errors = list(validator.iter_errors(instance))
    assert not errors, f"{path} should validate against {schema_shortname}: {[e.message for e in errors]}"


@pytest.mark.parametrize(
    "schema_shortname,path",
    INVALID_FIXTURES,
    ids=[f"{s}:{p.name}" for s, p in INVALID_FIXTURES],
)
def test_invalid_fixture_fails(schema_shortname, path, validator_factory, schemas) -> None:
    assert schema_shortname in schemas, f"unknown schema shortname {schema_shortname!r} for {path}"
    validator = validator_factory(schemas[schema_shortname])
    instance = _load(path)
    errors = list(validator.iter_errors(instance))
    violations = semantic_violations(schema_shortname, instance) if not errors else []
    assert errors or violations, (
        f"{path} was expected to be invalid (schema error or semantic violation) "
        f"but validated cleanly with no semantic violation detected"
    )


def test_at_least_one_valid_fixture_per_schema(schemas) -> None:
    covered = {s for s, _ in VALID_FIXTURES}
    missing = set(schemas) - covered
    assert not missing, f"schemas with no valid fixture: {sorted(missing)}"


def test_at_least_three_invalid_fixtures_per_schema(schemas) -> None:
    counts: dict[str, int] = {}
    for shortname, _ in INVALID_FIXTURES:
        counts[shortname] = counts.get(shortname, 0) + 1
    short_of_three = {s: counts.get(s, 0) for s in schemas if counts.get(s, 0) < 3}
    assert not short_of_three, f"schemas with fewer than 3 invalid fixtures: {short_of_three}"


def test_fixture_count_minimums() -> None:
    assert len(VALID_FIXTURES) >= 10, f"expected >=10 valid fixtures, found {len(VALID_FIXTURES)}"
    assert len(INVALID_FIXTURES) >= 40, f"expected >=40 invalid fixtures, found {len(INVALID_FIXTURES)}"


def _walk_additional_properties_false(node: Any, path: str, errors: list[str]) -> None:
    if isinstance(node, dict):
        node_type = node.get("type")
        is_object_schema = node_type == "object" or (
            isinstance(node_type, list) and "object" in node_type
        )
        if is_object_schema and "additionalProperties" not in node:
            errors.append(path or "<root>")
        for key, value in node.items():
            if key in ("properties", "definitions", "patternProperties"):
                if isinstance(value, dict):
                    for prop_name, prop_schema in value.items():
                        _walk_additional_properties_false(prop_schema, f"{path}.{key}.{prop_name}", errors)
            elif key in ("items",):
                _walk_additional_properties_false(value, f"{path}.{key}", errors)
            elif key in ("if", "then", "else", "allOf", "anyOf", "oneOf"):
                if isinstance(value, dict):
                    _walk_additional_properties_false(value, f"{path}.{key}", errors)
                elif isinstance(value, list):
                    for i, sub in enumerate(value):
                        _walk_additional_properties_false(sub, f"{path}.{key}[{i}]", errors)


@pytest.mark.parametrize("shortname,path", sorted(SCHEMA_FILES.items()))
def test_additional_properties_false_everywhere(shortname, path) -> None:
    schema = _load(path)
    errors: list[str] = []
    _walk_additional_properties_false(schema, "", errors)
    assert not errors, f"{shortname}: object nodes missing additionalProperties: {errors}"
