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
