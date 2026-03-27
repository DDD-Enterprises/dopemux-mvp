from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict


FIXED_STARTED_AT = "2026-03-12T00:00:00+00:00"
FIXED_FINISHED_AT = "2026-03-12T00:05:00+00:00"
DEFAULT_MAX_FILES_DOCS = 35
DEFAULT_MAX_FILES_CODE = 20
DEFAULT_MAX_CHARS = 650000
DEFAULT_MAX_REQUEST_BYTES = 200000
DEFAULT_FILE_TRUNCATE_CHARS = 70000


def load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixture_repo_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "golden_repo_min"


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_cfg(runner: Any, routing_policy: str = "balanced_openrouter"):
    return runner.RunnerConfig(
        dry_run=True,
        max_files_docs=DEFAULT_MAX_FILES_DOCS,
        max_files_code=DEFAULT_MAX_FILES_CODE,
        max_chars=DEFAULT_MAX_CHARS,
        max_request_bytes=DEFAULT_MAX_REQUEST_BYTES,
        file_truncate_chars=DEFAULT_FILE_TRUNCATE_CHARS,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="default",
        retry_max_attempts=4,
        retry_base_seconds=2.0,
        retry_max_seconds=30.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy=routing_policy,
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=86400,
        batch_max_requests_per_job=2000,
        batch_submit_only=False,
        webhook_url="",
        webhook_secret="",
        webhook_timeout_seconds=5,
        webhook_required=False,
        webhook_auto_continue=False,
        live_ok=False,
        selected_s_steps=None,
        selected_execution_step=None,
        d0_max_files=None,
        d1_max_files=None,
        provider_denylist=(),
    )


def make_valid_d1_success_payload(runner: Any) -> Dict[str, Any]:
    fixture_doc = fixture_repo_root() / "docs" / "example.md"
    contract = runner._step_contract_for("D", "D1")  # type: ignore[attr-defined]
    assert isinstance(contract, dict)
    artifacts = []
    for artifact_name, artifact_meta in contract["artifacts"].items():
        item = {
            "id": f"{artifact_name}:row1",
            "path": str(fixture_doc),
            "line_range": [1, 2],
            "evidence": ["fixture"],
        }
        if "name" in set(artifact_meta.get("prompt_required_item_fields") or []):
            item["name"] = fixture_doc.name
        if "kind" in set(artifact_meta.get("prompt_required_item_fields") or []):
            item["kind"] = "doc"
        row = {
            "artifact_name": artifact_name,
            "payload": {
                "schema": artifact_meta["canonical_schema_id"],
                "items": [item],
            },
        }
        artifacts.append(row)
    return {
        "phase": "D",
        "step_id": "D1",
        "partition_id": "D_P0001",
        "artifacts": artifacts,
    }


def build_smoke_run(tmp_root: Path, run_id: str) -> Dict[str, Any]:
    runner = load_runner_module()
    run_root = tmp_root / runner.V3_RUNS_ROOT / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    dirs = runner.get_run_dirs(tmp_root, run_id)

    runner.write_runner_identity(tmp_root, dirs["root"], run_id)
    contract_map_path = runner.write_phase_contract_map(dirs["root"], run_id)
    runner.update_run_manifest_contract_map(dirs["root"], contract_map_path)
    runner.write_run_routing_fingerprint(dirs["root"], run_id, make_cfg(runner), ["D"])

    fixture_doc = fixture_repo_root() / "docs" / "example.md"
    write_json(
        dirs["D"] / "inputs" / "INVENTORY.json",
        {"files": [{"path": str(fixture_doc), "id": "doc:example"}]},
    )
    write_json(
        dirs["D"] / "inputs" / "PARTITIONS.json",
        {"partitions": [{"id": "D_P0001", "paths": [str(fixture_doc)]}]},
    )

    success_payload = make_valid_d1_success_payload(runner)
    write_json(dirs["D"] / "raw" / "D1__D_P0001.json", success_payload)

    normalized_names = [
        "DOC_INDEX.part1.json",
        "DOC_CONTRACT_CLAIMS.part1.json",
        "DOC_BOUNDARIES.part1.json",
        "DOC_SUPERSESSION.part1.json",
        "CAP_NOTICES.part1.json",
    ]
    for name in normalized_names:
        write_json(
            dirs["D"] / "norm" / name,
            {
                "artifact_name": name,
                "items": [{"id": f"{name}:row1", "path": str(fixture_doc), "line_range": [1, 2]}],
            },
        )

    write_json(
        dirs["D"] / "qa" / "D1_QA.json",
        {
            "step_id": "D1",
            "resume_skipped_partitions": 0,
            "recomputed_partitions": 1,
            "written_files": normalized_names,
        },
    )
    write_json(
        dirs["D"] / "qa" / "PHASE_D_COVERAGE.json",
        {
            "status": "PASS",
            "missing_required_artifacts": [],
            "counts": {"ok": 1, "failed": 0, "skipped": 0, "dry_run": 0},
            "contract_metrics": {},
            "blocked_promptset": False,
        },
    )

    promptset_report = runner.promptset_fingerprint(["D"])
    runner.write_coverage_rollup(tmp_root, dirs, run_id, promptset_report)
    runner.write_resume_proof(dirs, run_id, ["D"], promptset_report=promptset_report)
    counts = runner.gather_phase_counts(dirs["D"])
    runner.update_proof_pack(
        tmp_root,
        dirs,
        run_id,
        FIXED_STARTED_AT,
        "D",
        counts,
        FIXED_STARTED_AT,
        FIXED_FINISHED_AT,
    )
    runner.refresh_run_manifest_artifacts(dirs["root"], dirs)

    return {
        "runner": runner,
        "dirs": dirs,
        "run_id": run_id,
        "success_json": dirs["D"] / "raw" / "D1__D_P0001.json",
        "success_payload": success_payload,
        "fixture_doc": fixture_doc,
    }


def normalize_for_determinism(payload: Any) -> Any:
    volatile = {
        "generated_at",
        "created_at",
        "updated_at",
        "started_at",
        "finished_at",
        "run_id",
        "artifacts_updated_at",
        "phase_contract_map_updated_at",
    }
    if isinstance(payload, dict):
        out = {}
        for key, value in sorted(payload.items()):
            if key in volatile:
                continue
            if key in {"inventory_file", "partitions_file", "coverage_file", "resume_proof", "run_routing_fingerprint", "phase_contract_map"}:
                continue
            out[key] = normalize_for_determinism(value)
        return out
    if isinstance(payload, list):
        return [normalize_for_determinism(item) for item in payload]
    if isinstance(payload, str) and "/runs/" in payload:
        return payload.split("/runs/")[0] + "/runs/<RUN>"
    return payload
