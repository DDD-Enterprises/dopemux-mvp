from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import yaml


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v4", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_numeric_step_sort_handles_c10_after_c9() -> None:
    runner = _load_runner_module()
    assert runner.numeric_step_sort_key("C9") < runner.numeric_step_sort_key("C10")


def test_strip_forbidden_keys_recursive() -> None:
    runner = _load_runner_module()
    payload = {
        "generated_at": "2026-02-20T00:00:00Z",
        "run_id": "abc",
        "items": [
            {"id": "A", "timestamp": "x", "value": 1},
            {"id": "B", "nested": {"created_at": "y", "ok": True}},
        ],
    }
    stripped = runner.strip_forbidden_keys(
        payload,
        ["generated_at", "timestamp", "created_at", "updated_at", "run_id"],
    )
    assert "generated_at" not in stripped
    assert "run_id" not in stripped
    assert "timestamp" not in stripped["items"][0]
    assert "created_at" not in stripped["items"][1]["nested"]


def test_merge_item_list_payloads_dedup_by_id() -> None:
    runner = _load_runner_module()
    merged = runner.merge_item_list_payloads(
        [
            {"items": [{"id": "A", "value": "x", "evidence": [{"path": "a", "line_range": [1, 1], "excerpt": "x"}]}]},
            {"items": [{"id": "A", "value": "x2", "evidence": [{"path": "a", "line_range": [1, 1], "excerpt": "x"}]}]},
            {"items": [{"id": "B", "value": "z"}]},
        ]
    )
    items = merged["items"]
    assert [row["id"] for row in items] == ["A", "B"]
    assert isinstance(items[0].get("evidence"), list)


def test_build_service_coverage_payload_flags_missing() -> None:
    runner = _load_runner_module()
    # Intentionally incomplete catalog so coverage must fail.
    payload = runner.build_service_coverage_payload(
        {
            "schema": "SERVICE_CATALOG@v1",
            "items": [
                {
                    "id": "SERVICE:postgres",
                    "service_id": "postgres",
                    "category": "infrastructure",
                    "description": "Postgres",
                    "ports": {"port": 5432, "container_port": 5432},
                    "health": {"path": None, "method": None, "timeout_ms": 5000, "expected_status": 200},
                    "repo_locations": [],
                    "entrypoints": [],
                    "interfaces": [],
                    "dependencies": [],
                    "config": {},
                }
            ],
        }
    )
    assert payload["status"] == "FAIL"
    assert payload["service_count_expected"] >= 1
    assert "missing_services" in payload


def test_build_service_catalog_covers_registry_services() -> None:
    runner = _load_runner_module()
    catalog = runner.build_service_catalog()
    coverage = runner.build_service_coverage_payload(catalog)

    registry = yaml.safe_load((Path(__file__).resolve().parents[3] / "services" / "registry.yaml").read_text(encoding="utf-8"))
    expected = sorted(
        str(row.get("name", "")).strip()
        for row in registry.get("services", [])
        if isinstance(row, dict) and str(row.get("name", "")).strip()
    )

    observed = sorted(
        str(item.get("service_id", "")).strip()
        for item in catalog.get("items", [])
        if isinstance(item, dict) and str(item.get("service_id", "")).strip()
    )

    assert observed == expected
    assert coverage["status"] == "PASS"
    assert coverage["service_count_expected"] == len(expected)
    assert coverage["service_count_observed"] == len(expected)


def test_build_v4_status_payload_uses_v4_run_root() -> None:
    runner = _load_runner_module()
    payload = runner.build_v4_status_payload("run_that_does_not_exist")
    parsed = json.loads(json.dumps(payload))
    assert parsed["pipeline_version"] == "v4"
    assert "/extraction/repo-truth-extractor/v4/runs/" in parsed["run_dir"]


def test_build_v3_cmd_passes_routing_and_batch_flags() -> None:
    runner = _load_runner_module()
    cmd = runner.build_v3_cmd(
        phase="A",
        run_id="rid",
        dry_run=True,
        resume=True,
        partition_workers=2,
        executor="process",
        doctor=False,
        doctor_auto_reprocess=False,
        doctor_reprocess_dry_run=False,
        doctor_reprocess_phases="",
        status=False,
        status_json=False,
        doctor_auth=False,
        preflight_providers=False,
        coverage_report=False,
        routing_policy="cost",
        disable_escalation=True,
        escalation_max_hops=3,
        batch_mode=True,
        batch_provider="openai",
        batch_poll_seconds=15,
        batch_wait_timeout_seconds=120,
        batch_max_requests_per_job=99,
        ui="rich",
        pretty=True,
        quiet=True,
        jsonl_events=True,
    )
    cmd_text = " ".join(cmd)
    assert "--routing-policy cost" in cmd_text
    assert "--executor process" in cmd_text
    assert "--disable-escalation" in cmd_text
    assert "--escalation-max-hops 3" in cmd_text
    assert "--batch-mode" in cmd_text
    assert "--batch-provider openai" in cmd_text
    assert "--batch-poll-seconds 15" in cmd_text
    assert "--batch-wait-timeout-seconds 120" in cmd_text
    assert "--batch-max-requests-per-job 99" in cmd_text
    assert "--ui rich" in cmd_text
    assert "--pretty" in cmd_text
    assert "--quiet" in cmd_text
    assert "--jsonl-events" in cmd_text


def test_call_v3_runner_sets_prompt_root_env(monkeypatch) -> None:
    runner = _load_runner_module()
    captured = {}

    class _Proc:
        returncode = 0

    def _fake_run(cmd, cwd=None, env=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["env"] = env or {}
        return _Proc()

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)
    prompt_root = Path("/tmp/rte_v4_prompts")
    rc = runner.call_v3_runner(["python", "run_extraction_v3.py"], prompt_root=prompt_root)
    assert rc == 0
    assert captured["env"]["REPO_TRUTH_EXTRACTOR_PROMPT_ROOT"] == str(prompt_root.resolve())
    assert captured["env"]["UPGRADES_PROMPT_ROOT"] == str(prompt_root.resolve())


def test_verify_resume_proof_prompt_paths_rejects_legacy_prompt_paths(tmp_path: Path, monkeypatch) -> None:
    runner = _load_runner_module()
    run_id = "v4_prompt_proof_bad"
    run_root = tmp_path / "v3" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "RESUME_PROOF.json").write_text(
        json.dumps(
            {
                "prompt_hashes": [
                    {
                        "path": str(tmp_path / "services" / "repo-truth-extractor" / "prompts" / "v3" / "PROMPT_A0.md"),
                        "prompt_id": "A0",
                        "sha256": "abc",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "V3_RUNS_ROOT", tmp_path / "v3" / "runs")
    prompt_root = tmp_path / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "prompts"
    prompt_root.mkdir(parents=True, exist_ok=True)

    try:
        runner.verify_resume_proof_prompt_paths(run_id, prompt_root)
        assert False, "Expected verify_resume_proof_prompt_paths to fail"
    except RuntimeError as exc:
        assert "non-v4 prompts" in str(exc)


def test_verify_resume_proof_prompt_paths_accepts_v4_prompt_paths(tmp_path: Path, monkeypatch) -> None:
    runner = _load_runner_module()
    run_id = "v4_prompt_proof_ok"
    prompt_root = tmp_path / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "prompts"
    prompt_root.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_root / "PROMPT_A0_EXAMPLE.md"
    prompt_path.write_text("# prompt", encoding="utf-8")
    run_root = tmp_path / "v3" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "RESUME_PROOF.json").write_text(
        json.dumps({"prompt_hashes": [{"path": str(prompt_path.resolve()), "prompt_id": "A0", "sha256": "abc"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "V3_RUNS_ROOT", tmp_path / "v3" / "runs")

    runner.verify_resume_proof_prompt_paths(run_id, prompt_root)
