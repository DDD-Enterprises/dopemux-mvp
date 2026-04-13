from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.registry.snapshot_capture import build_contract_snapshot, build_validator_suite


def test_contract_snapshot_capture_is_deterministic_for_same_inputs() -> None:
    snapshot_one = build_contract_snapshot()
    snapshot_two = build_contract_snapshot()

    assert snapshot_one.contract_snapshot_id == snapshot_two.contract_snapshot_id
    assert snapshot_one.snapshot_hash == snapshot_two.snapshot_hash
    assert snapshot_one.runtime_version == "v5"
    assert snapshot_one.contract_version == "promptsets/v4"
    assert "services/repo-truth-extractor/run_extraction_v5.py" in snapshot_one.source_files
    assert "services/repo-truth-extractor/promptsets/v4/promptset.yaml" in snapshot_one.source_files


def test_validator_suite_capture_uses_real_source_hashes() -> None:
    validator_suite = build_validator_suite(
        validator_suite_id="validators_phase_s_advisory_v1",
        surface_scope=["direct_provider_api", "openrouter_routed"],
        validators=["phase_s_registry_presence"],
        strength_class="moderate",
        contract_rigor="phase_s_weaker_contract_caveat",
        source_paths=[
            SERVICE_ROOT / "prompts" / "phase_s" / "registry.json",
            SERVICE_ROOT / "prompts" / "phase_s" / "PROMPT_SP11_CONTRACT_LINTER.md",
        ],
    )
    assert validator_suite.version_hash == validator_suite.content_hash
    assert "services/repo-truth-extractor/prompts/phase_s/registry.json" in validator_suite.source_files
    assert len(validator_suite.content_hashes) == 2
    assert all(len(value) == 64 for value in validator_suite.content_hashes.values())

