"""Shared fixtures for the Governed Execution Contract v2 schema test suite.

Builds a referencing.Registry keyed by $id from every schema in
schemas/governed_execution/ so that cross-file $ref (e.g. macro_packet.v2
referencing enums.v1) resolves under jsonschema 4.25. A bare relative $ref
that fails resolution is a test failure, not a skip.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "schemas" / "governed_execution"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
VALID_DIR = FIXTURES_DIR / "valid"
INVALID_DIR = FIXTURES_DIR / "invalid"

# schema shortname (filename minus the trailing ".schema.json") -> path, for
# every *.schema.json file. manifest.v1.json is data, not a schema, and has
# no $id, so it is intentionally excluded from this map.
_SUFFIX = ".schema.json"
SCHEMA_FILES: dict[str, Path] = {
    p.name[: -len(_SUFFIX)]: p
    for p in sorted(SCHEMA_DIR.glob("*.schema.json"))
}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="ascii") as fh:
        return json.load(fh)


def build_registry() -> Registry:
    resources = []
    for path in SCHEMA_FILES.values():
        schema = _load(path)
        Draft7Validator.check_schema(schema)
        resources.append(Resource(contents=schema, specification=DRAFT7))
    registry: Registry = Registry().with_resources(
        (resource.id(), resource) for resource in resources
    )
    return registry


@pytest.fixture(scope="session")
def registry() -> Registry:
    return build_registry()


@pytest.fixture(scope="session")
def schemas() -> dict[str, dict[str, Any]]:
    return {stem: _load(path) for stem, path in SCHEMA_FILES.items()}


@pytest.fixture(scope="session")
def validator_factory(registry: Registry):
    def _make(schema: dict[str, Any]) -> Draft7Validator:
        return Draft7Validator(schema, registry=registry)

    return _make


def iter_valid_fixtures() -> Iterator[tuple[str, Path]]:
    # valid fixtures are named <schema-shortname>.json, or
    # <schema-shortname>__<variant>.json for a schema that needs more than
    # one representative valid instance (e.g. the W01..W08 DAG macro).
    for path in sorted(VALID_DIR.glob("*.json")):
        schema_shortname = path.stem.split("__", 1)[0]
        yield schema_shortname, path


def iter_invalid_fixtures() -> Iterator[tuple[str, Path]]:
    # invalid fixtures are named <schema-shortname>__<reason>.json
    for path in sorted(INVALID_DIR.glob("*.json")):
        schema_shortname = path.stem.split("__", 1)[0]
        yield schema_shortname, path


def semantic_violations(schema_stem: str, instance: dict[str, Any]) -> list[str]:
    """Cross-field rules that a Draft7 schema cannot express on its own.

    A fixture may be schema-valid yet still be an intentionally invalid
    fixture because it violates one of these rules (e.g. FinalityReceipt's
    exact-head equality, which the schema documents but cannot enforce).
    """
    violations: list[str] = []
    if schema_stem == "finality_receipt.v1":
        audited = instance.get("audited_head")
        finality = instance.get("finality_head")
        if audited is not None and finality is not None and audited != finality:
            violations.append("audited_head != finality_head")
    return violations
