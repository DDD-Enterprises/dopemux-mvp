"""AggregateReturnEnvelope builder (W05).

Referential and non-authoritative: only refs and digests are carried, never
a copy of evidence bytes. merge_authorized, activation_authorized, authority
and is_canonical_truth are hardcoded to their contract-fixed values
regardless of caller input, matching
schemas/governed_execution/aggregate_return_envelope.v1.schema.json.

Schema files are read (not written) via pathlib.Path.read_text rather than
a builtin file-open call, per the W05 write-surface verify rule.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

from .types import JoinResult, WorkstreamResult

_SCHEMA_DIR = Path(__file__).resolve().parents[4] / "schemas" / "governed_execution"
_ENVELOPE_SCHEMA_NAME = "aggregate_return_envelope.v1.schema.json"
_SCHEMA_VERSION = "dopemux.governed_execution.aggregate_return_envelope.v1"


class EnvelopeInvalid(ValueError):
    """Raised when a built envelope fails schema validation.

    errors carries every violation, sorted, so a caller sees the full set
    rather than only the first jsonschema error.
    """

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors: tuple[str, ...] = tuple(errors)
        super().__init__("; ".join(self.errors))


def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="ascii"))


@lru_cache(maxsize=1)
def _registry() -> Registry:
    resources = []
    for path in sorted(_SCHEMA_DIR.glob("*.schema.json")):
        schema = _load_schema(path)
        resources.append(Resource(contents=schema, specification=DRAFT7))
    registry: Registry = Registry().with_resources((r.id(), r) for r in resources)
    return registry


@lru_cache(maxsize=1)
def _validator() -> Draft7Validator:
    schema = _load_schema(_SCHEMA_DIR / _ENVELOPE_SCHEMA_NAME)
    return Draft7Validator(schema, registry=_registry())


def build_envelope(
    macro_id: str,
    results: Sequence[WorkstreamResult],
    join_results: Sequence[JoinResult],
    macro_status: str,
    model_calls: Mapping[str, int],
    mcp: Mapping[str, Any],
    github_mutations: int,
    drift_classifications: Sequence[Mapping[str, str]],
    blockers: Sequence[str],
    unknowns: Sequence[str],
    residual_risks: Sequence[str],
    operator_gates_used: Sequence[str],
    operator_gates_needed: Sequence[str],
    next_legal_action: str,
) -> dict[str, Any]:
    """Build and validate an AggregateReturnEnvelope.

    Raises ValueError if model_calls['total'] does not equal the sum of
    team_lead + implementers + auditors. Raises EnvelopeInvalid (with every
    schema violation, sorted) if the assembled envelope is not schema-valid.
    No evidence bytes are copied in: workstreams carry only status and a
    return_ref (path, sha256), never the referenced content itself.
    """
    parts_total = (
        model_calls.get("team_lead", 0)
        + model_calls.get("implementers", 0)
        + model_calls.get("auditors", 0)
    )
    if model_calls.get("total") != parts_total:
        raise ValueError(
            "model_calls['total'] "
            f"({model_calls.get('total')!r}) does not equal "
            f"team_lead + implementers + auditors ({parts_total!r})"
        )

    workstreams = sorted(
        (
            {
                "workstream_id": result.workstream_id,
                "status": result.status,
                "subject_sha": result.subject_sha,
                "return_ref": {
                    "path": result.return_ref.path,
                    "sha256": result.return_ref.sha256,
                },
            }
            for result in results
        ),
        key=lambda workstream: workstream["workstream_id"],
    )

    join_results_payload = [
        {
            "join_id": join_result.join_id,
            "join_type": join_result.join_type,
            "satisfied": join_result.satisfied,
            "affected_workstreams": list(join_result.affected_workstreams),
            "unaffected_workstreams": list(join_result.unaffected_workstreams),
        }
        for join_result in join_results
    ]

    envelope: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "macro_id": macro_id,
        "macro_status": macro_status,
        "workstreams": workstreams,
        "join_results": join_results_payload,
        "model_calls": dict(model_calls),
        "mcp": dict(mcp),
        "github_mutations": github_mutations,
        "drift_classifications": [dict(entry) for entry in drift_classifications],
        "blockers": list(blockers),
        "unknowns": list(unknowns),
        "residual_risks": list(residual_risks),
        "operator_gates_used": list(operator_gates_used),
        "operator_gates_needed": list(operator_gates_needed),
        "merge_authorized": False,
        "activation_authorized": False,
        "next_legal_action": next_legal_action,
        "authority": "NONE",
        "is_canonical_truth": False,
    }

    errors = sorted(
        f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
        for error in _validator().iter_errors(envelope)
    )
    if errors:
        raise EnvelopeInvalid(errors)
    return envelope
