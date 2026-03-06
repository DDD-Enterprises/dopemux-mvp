from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys


SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from lib.promptgen.io import read_json
from lib.promptgen.promptpack_v1 import compile_promptpack_v1
from lib.promptgen.promptpack_v2 import (
    RULE_ENABLE_STRICT_ENVELOPE_ON_PARSE,
    RULE_REDUCE_MAX_FILES_ON_PARSE_OR_EMPTY,
    RULE_SHRINK_BUDGET_ON_PAYLOAD_UNSHRINKABLE,
    RULE_SPLIT_STEP_ON_MISSING_ARTIFACTS,
    adjust_promptpack_v2,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "promptgen"
PROMPT_ROOT = FIXTURES / "v1" / "prompts"
PROFILES_DIR = SERVICE_DIR / "lib" / "promptgen" / "profiles"
V4_PROMPT_ROOT = SERVICE_DIR / "promptsets" / "v4" / "prompts"


def _profile_payload(profile_id: str) -> dict:
    return read_json(PROFILES_DIR / f"{profile_id}.json")


def test_promptpack_v1_is_stable_for_fixed_inputs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "services").mkdir(parents=True, exist_ok=True)
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")

    promptpack_root = tmp_path / "promptpacks"
    profile = _profile_payload("P00_GENERIC")
    profile_selection = {"selected_profile_id": "P00_GENERIC", "selected_profile_version": "1.0.0"}
    archetypes = {"contracts_present": {"event_taxonomy": True, "db_schema": False, "api_specs": True, "adrs": True}}

    first = compile_promptpack_v1(
        run_id="stable_v1_fixture",
        root=repo_root,
        prompt_root=PROMPT_ROOT,
        promptpack_root=promptpack_root,
        phases=["C"],
        profile_selection=profile_selection,
        profile_payload=profile,
        archetypes_payload=archetypes,
    )
    first_pack_text = Path(first["promptpack_json"]).read_text(encoding="utf-8")
    first_hash_text = (promptpack_root / "PROMPTPACK.v1.sha256.json").read_text(encoding="utf-8")

    second = compile_promptpack_v1(
        run_id="stable_v1_fixture",
        root=repo_root,
        prompt_root=PROMPT_ROOT,
        promptpack_root=promptpack_root,
        phases=["C"],
        profile_selection=profile_selection,
        profile_payload=profile,
        archetypes_payload=archetypes,
    )

    second_pack_text = Path(second["promptpack_json"]).read_text(encoding="utf-8")
    second_hash_text = (promptpack_root / "PROMPTPACK.v1.sha256.json").read_text(encoding="utf-8")
    assert first_pack_text == second_pack_text
    assert first_hash_text == second_hash_text


def test_promptpack_v2_adjustments_are_deterministic(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    shutil.copytree(FIXTURES / "v2" / "run_root", run_root)

    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")

    profile = _profile_payload("P05_EVENT_DRIVEN_SYSTEM")
    profile_selection = {"selected_profile_id": "P05_EVENT_DRIVEN_SYSTEM", "selected_profile_version": "1.0.0"}
    archetypes = {"contracts_present": {"event_taxonomy": True, "db_schema": False, "api_specs": False, "adrs": False}}
    promptpack_root = run_root / "promptpacks"
    promptpack_root.mkdir(parents=True, exist_ok=True)

    v1 = compile_promptpack_v1(
        run_id="stable_v2_fixture",
        root=repo_root,
        prompt_root=PROMPT_ROOT,
        promptpack_root=promptpack_root,
        phases=["C"],
        profile_selection=profile_selection,
        profile_payload=profile,
        archetypes_payload=archetypes,
    )

    one = adjust_promptpack_v2(
        run_id="stable_v2_fixture",
        run_root=run_root,
        promptpack_root=promptpack_root,
        promptpack_v1_payload=v1["payload"],
        profile_payload=profile,
    )
    two = adjust_promptpack_v2(
        run_id="stable_v2_fixture",
        run_root=run_root,
        promptpack_root=promptpack_root,
        promptpack_v1_payload=v1["payload"],
        profile_payload=profile,
    )

    assert one["payload"] == two["payload"]
    assert one["hash_payload"]["pack_sha256"] == two["hash_payload"]["pack_sha256"]

    rules = {row["rule"] for row in one["adjustments"]}
    assert RULE_SHRINK_BUDGET_ON_PAYLOAD_UNSHRINKABLE in rules
    assert RULE_REDUCE_MAX_FILES_ON_PARSE_OR_EMPTY in rules
    assert RULE_ENABLE_STRICT_ENVELOPE_ON_PARSE in rules
    assert RULE_SPLIT_STEP_ON_MISSING_ARTIFACTS in rules


def test_promptpack_v1_carries_contract_metadata_for_d0_d1(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "README.md").write_text("fixture\n", encoding="utf-8")

    promptpack_root = tmp_path / "promptpacks"
    profile = _profile_payload("P00_GENERIC")
    profile_selection = {"selected_profile_id": "P00_GENERIC", "selected_profile_version": "1.0.0"}
    archetypes = {"contracts_present": {"event_taxonomy": True}}

    result = compile_promptpack_v1(
        run_id="promptpack_contract_metadata",
        root=repo_root,
        prompt_root=V4_PROMPT_ROOT,
        promptpack_root=promptpack_root,
        phases=["D"],
        profile_selection=profile_selection,
        profile_payload=profile,
        archetypes_payload=archetypes,
    )

    phase_rows = result["payload"]["phases"]["D"]
    d1_row = next(row for row in phase_rows if row["step_id"] == "D1")
    assert d1_row["contract_lane"] == "CE"
    assert d1_row["strict_schema_required"] is True
    contract_metadata = d1_row["contract_metadata"]
    assert contract_metadata["lane"]["provider"] == "openrouter"
    assert contract_metadata["lane"]["strict_schema_required"] is True
    assert contract_metadata["lane"]["lane_class"] == "CE"
    assert contract_metadata["lane"]["primary_routes"][0]["strict_json_schema"] is True
    assert contract_metadata["lane"]["primary_routes"][0]["strict_passthrough_verified"] is True
    assert "CAP_NOTICES.partX.json" in contract_metadata["expected_artifacts"]

    rendered_path = Path(d1_row["rendered_prompt"])
    rendered_text = rendered_path.read_text(encoding="utf-8")
    assert "contract_map" in rendered_text
    assert "CE" in rendered_text
