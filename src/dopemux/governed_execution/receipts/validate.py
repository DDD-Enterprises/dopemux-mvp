"""Runtime schema-validation boundary for Governed Execution Contract receipts.

This module is the only place a Governed Execution Contract receipt is turned
from raw bytes into a validated dict at runtime. It builds a
``referencing.Registry`` from every ``schemas/governed_execution/*.schema.json``
file, keyed by that schema's ``$id``, and validates raw bytes against the
schema selected by ``kind`` (the schema file's shortname, e.g.
``"freeze_receipt.v1"`` for ``freeze_receipt.v1.schema.json``).

No clock reads and no child-process calls happen here: provenance timestamps
are always caller-supplied.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

_SCHEMA_SUFFIX = ".schema.json"

# src/dopemux/governed_execution/receipts/validate.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SCHEMA_DIR = _REPO_ROOT / "schemas" / "governed_execution"


class ReceiptInvalid(Exception):
    """Raised when raw receipt bytes fail schema validation for ``kind``.

    ``errors`` is a list of ``"<json-path>: <message>"`` strings sorted by
    the json path of the failing instance location.
    """

    def __init__(self, kind: str, errors: list[str]) -> None:
        self.kind = kind
        self.errors = errors
        super().__init__(f"{kind}: {'; '.join(errors)}" if errors else kind)


class UnknownReceiptKind(Exception):
    """Raised when ``kind`` has no matching ``<kind>.schema.json`` file."""


@dataclass(frozen=True)
class Provenance:
    """Caller-supplied provenance attached to a validated receipt."""

    verified_by: str
    verified_at: str
    schema_set_digest: str


@dataclass(frozen=True)
class ValidatedReceipt:
    """A receipt that has passed schema validation."""

    kind: str
    payload: Mapping[str, Any]
    sha256: str
    provenance: Provenance


def _schema_files(schema_dir: Path) -> dict[str, Path]:
    return {
        path.name[: -len(_SCHEMA_SUFFIX)]: path
        for path in sorted(schema_dir.glob(f"*{_SCHEMA_SUFFIX}"))
    }


def _load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="ascii") as handle:
        return json.load(handle)


def load_registry(schema_dir: Path) -> Registry:
    """Build a ``referencing.Registry`` from every schema under ``schema_dir``.

    Every ``*.schema.json`` file is loaded, checked against the Draft 7
    metaschema, and registered under its own ``$id`` so that cross-file
    ``$ref`` (e.g. a receipt schema referencing ``enums.v1.schema.json``)
    resolves.
    """
    resources = []
    for path in _schema_files(schema_dir).values():
        schema = _load_schema(path)
        Draft7Validator.check_schema(schema)
        resources.append(Resource(contents=schema, specification=DRAFT7))
    registry: Registry = Registry().with_resources(
        (resource.id(), resource) for resource in resources
    )
    return registry


def validate_receipt(
    kind: str,
    raw_bytes: bytes,
    provenance: Provenance,
    schema_dir: Path = DEFAULT_SCHEMA_DIR,
) -> ValidatedReceipt:
    """Validate ``raw_bytes`` against the schema named by ``kind``.

    ``kind`` maps to ``<schema_dir>/<kind>.schema.json``; a ``kind`` with no
    matching schema file raises ``UnknownReceiptKind``. Bytes that are not
    valid JSON, or that are valid JSON failing schema validation, raise
    ``ReceiptInvalid`` with errors sorted by their json path.
    """
    schema_files = _schema_files(schema_dir)
    if kind not in schema_files:
        raise UnknownReceiptKind(kind)

    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptInvalid(kind, [f"$: not valid JSON ({exc})"]) from exc

    schema = _load_schema(schema_files[kind])
    registry = load_registry(schema_dir)
    validator = Draft7Validator(schema, registry=registry)
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if errors:
        formatted = [
            f"{'/'.join(str(part) for part in error.absolute_path) or '$'}: {error.message}"
            for error in errors
        ]
        raise ReceiptInvalid(kind, formatted)

    digest = sha256(raw_bytes).hexdigest()
    return ValidatedReceipt(kind=kind, payload=payload, sha256=digest, provenance=provenance)
