from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models.entities import ContractSnapshot, ValidatorSuite
from ..storage.hashing import hash_file, hash_json, stable_json_dumps

REPO_ROOT = Path(__file__).resolve().parents[4]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"


@dataclass(frozen=True)
class SnapshotSource:
    path: Path
    role: str


def _rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_sources(sources: list[SnapshotSource]) -> dict[str, str]:
    return {_rel(source.path): hash_file(source.path) for source in sources}


def build_contract_snapshot(
    *,
    runtime_version: str = "v5",
    contract_version: str = "promptsets/v4",
    source_paths: list[Path] | None = None,
) -> ContractSnapshot:
    paths = source_paths or [
        SERVICE_ROOT / "run_extraction_v5.py",
        SERVICE_ROOT / "promptsets" / "v4" / "promptset.yaml",
        SERVICE_ROOT / "promptsets" / "v4" / "artifacts.yaml",
        SERVICE_ROOT / "promptsets" / "v4" / "model_map.yaml",
        SERVICE_ROOT / "promptsets" / "v4" / "prompt_artifact_coverage_map.json",
        SERVICE_ROOT / "prompts" / "phase_s" / "registry.json",
        SERVICE_ROOT / "fl_int" / "schema_input.json",
    ]
    sources = [SnapshotSource(path=path.resolve(), role="contract_or_runtime") for path in paths]
    content_hashes = _hash_sources(sources)
    payload = {
        "runtime_version": runtime_version,
        "contract_version": contract_version,
        "source_files": list(content_hashes.keys()),
        "content_hashes": content_hashes,
    }
    snapshot_hash = hash_json(payload)
    return ContractSnapshot(
        contract_snapshot_id=f"contract_{runtime_version}_{contract_version.replace('/', '_')}_{snapshot_hash[:12]}",
        runtime_version=runtime_version,
        contract_version=contract_version,
        source_files=list(content_hashes.keys()),
        content_hashes=content_hashes,
        strict_schema_expected=True,
        snapshot_hash=snapshot_hash,
        content_hash=snapshot_hash,
        source_ref="repo_truth_snapshot_capture",
        notes=[
            "Runtime authority stored separately from contract authority.",
            "Includes phase_s and FL_INT contract inputs for M1 registry linkage.",
        ],
    )


def build_validator_suite(
    *,
    validator_suite_id: str,
    surface_scope: list[str],
    validators: list[str],
    strength_class: str,
    contract_rigor: str,
    source_paths: list[Path],
    notes: list[str] | None = None,
) -> ValidatorSuite:
    sources = [SnapshotSource(path=path.resolve(), role="validator_suite") for path in source_paths]
    content_hashes = _hash_sources(sources)
    payload = {
        "validator_suite_id": validator_suite_id,
        "surface_scope": surface_scope,
        "validators": validators,
        "strength_class": strength_class,
        "contract_rigor": contract_rigor,
        "source_files": list(content_hashes.keys()),
        "content_hashes": content_hashes,
    }
    version_hash = hash_json(payload)
    return ValidatorSuite(
        validator_suite_id=validator_suite_id,
        surface_scope=surface_scope,
        validators=validators,
        strength_class=strength_class,
        contract_rigor=contract_rigor,
        source_files=list(content_hashes.keys()),
        content_hashes=content_hashes,
        version_hash=version_hash,
        content_hash=version_hash,
        source_ref="repo_truth_snapshot_capture",
        notes=notes or [],
    )


def snapshot_manifest_payload(snapshot: ContractSnapshot) -> dict[str, Any]:
    return snapshot.to_dict()


def validator_suite_manifest_payload(validator_suite: ValidatorSuite) -> dict[str, Any]:
    return validator_suite.to_dict()

