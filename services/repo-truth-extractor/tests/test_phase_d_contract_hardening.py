from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_v3_module():
    root = _repo_root()
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _prompt_text(name: str) -> str:
    root = _repo_root()
    path = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "prompts" / name
    return path.read_text(encoding="utf-8")


def test_d0_and_d1_prompts_harden_line_range_contract() -> None:
    for name in (
        "PROMPT_D0_INVENTORY___PARTITION_PLAN.md",
        "PROMPT_D1_CLAIMS___BOUNDARIES___SUPERSESSION.md",
    ):
        text = _prompt_text(name)
        assert "line_range" in text
        assert "do not guess" in text.lower()
        assert '"items": []' in text
        assert "Minimal Example" in text
        assert "line-numbered evidence" in text
        assert "Output exactly one JSON object" in text


def test_schema_gate_failure_context_is_deterministic() -> None:
    runner = _load_v3_module()

    missing_line_range = runner.describe_schema_gate_failure(
        [{"artifact_name": "OUT.json", "payload": {"items": [{"id": "x", "path": "docs/a.md"}]}}],
        ("OUT.json",),
    )
    assert missing_line_range == {
        "artifact_name": "OUT.json",
        "item_index": 0,
        "item_id": "x",
        "item_path": "docs/a.md",
        "failure_reason": "schema_missing_key:line_range",
        "missing_key": "line_range",
        "constraint": None,
    }

    invalid_line_range = runner.describe_schema_gate_failure(
        [
            {
                "artifact_name": "OUT.json",
                "payload": {"items": [{"id": "x", "path": "docs/a.md", "line_range": [0, 1]}]},
            }
        ],
        ("OUT.json",),
    )
    assert invalid_line_range == {
        "artifact_name": "OUT.json",
        "item_index": 0,
        "item_id": "x",
        "item_path": "docs/a.md",
        "failure_reason": "schema_invalid_line_range",
        "missing_key": None,
        "constraint": "line_range",
    }

    missing_path = runner.describe_schema_gate_failure(
        [{"artifact_name": "OUT.json", "payload": {"items": [{"id": "x", "line_range": [1, 2]}]}}],
        ("OUT.json",),
    )
    assert missing_path == {
        "artifact_name": "OUT.json",
        "item_index": 0,
        "item_id": "x",
        "item_path": None,
        "failure_reason": "schema_missing_key:path",
        "missing_key": "path",
        "constraint": None,
    }


def test_phase_d_line_numbering_is_zero_padded_and_stable() -> None:
    runner = _load_v3_module()
    content = "alpha\nbeta\ngamma\n"
    first = runner._format_line_numbered_content(content, 200)
    second = runner._format_line_numbered_content(content, 200)
    assert first == second
    assert "0001: alpha" in first
    assert "0002: beta" in first
    assert "0003: gamma" in first


def test_balanced_grok_openrouter_routes_use_contract_lane_map_for_d_steps() -> None:
    runner = _load_v3_module()
    runner.apply_model_overrides(runner.DEFAULT_GEMINI_MODEL_ID, "balanced_grok_openrouter")
    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D0") == [
        ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
        ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ]
    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D1") == [
        ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
        ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ]
    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D2") == [
        ("xai", "grok-4-1-fast-reasoning", "XAI_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]


def test_artifacts_registry_and_runner_minimum_contract_cover_d0_d1() -> None:
    runner = _load_v3_module()
    artifacts_path = _repo_root() / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "artifacts.yaml"
    payload = yaml.safe_load(artifacts_path.read_text(encoding="utf-8"))
    rows = [
        row
        for row in payload.get("artifacts", [])
        if isinstance(row, dict) and str(row.get("phase")) == "D" and str(row.get("canonical_writer_step_id")) in {"D0", "D1"}
    ]
    assert rows
    d0_rows = [row for row in rows if str(row.get("canonical_writer_step_id")) == "D0"]
    assert d0_rows
    for row in d0_rows:
        assert set(row.get("required_fields", [])) == {"path", "line_range", "id"}

    ok, reason = runner.artifacts_pass_schema_gate(
        [{"artifact_name": "OUT.json", "payload": {"items": [{"id": "x", "path": "docs/a.md", "line_range": [1, 2]}]}}],
        ("OUT.json",),
    )
    assert ok is True
    assert reason is None


def _make_cfg(runner):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
    )


def _fake_context(**_kwargs):  # type: ignore[no-untyped-def]
    return (
        "--- FILE: docs/example.md ---\n0001: line one\n0002: line two\n",
        {"files_included": 1, "files_skipped": 0, "context_bytes": 60, "redaction_hits": 0},
    )


def test_d1_calls_use_strict_openai_response_format(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3_module()
    phase_dir = tmp_path / "D_docs_pipeline"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_D1_TEST.md"
    prompt.write_text("Goal: D1 strict output\n", encoding="utf-8")
    contract = runner._step_contract_for("D", "D1")
    assert contract is not None
    outputs = tuple(contract["artifact_order"])
    prompt_spec = runner.PromptSpec(
        step_id="D1",
        prompt_path=prompt,
        output_artifacts=outputs,
        contract=contract,
    )
    partitions = [{"id": "D_P0001", "paths": ["docs/example.md"]}]

    captured = {"kwargs": []}

    def _item(item_id: str, *, with_index_fields: bool = False) -> dict:
        row = {
            "id": item_id,
            "path": "docs/example.md",
            "line_range": [1, 2],
            "evidence": [{"path": "docs/example.md", "line_range": [1, 2], "excerpt": "0001: line one"}],
        }
        if with_index_fields:
            row["name"] = "Example"
            row["kind"] = "guide"
        return row

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        captured["kwargs"].append(dict(kwargs))
        payload = {
            "artifacts": [
                {"artifact_name": "DOC_INDEX.partX.json", "payload": {"schema": "DOC_INDEX@v1", "items": [_item("DOC_INDEX:item", with_index_fields=True)]}},
                {"artifact_name": "DOC_CONTRACT_CLAIMS.partX.json", "payload": {"schema": "DOC_CONTRACT_CLAIMS@v1", "items": [_item("DOC_CONTRACT_CLAIMS:item")]}},
                {"artifact_name": "DOC_BOUNDARIES.partX.json", "payload": {"schema": "DOC_BOUNDARIES@v1", "items": [_item("DOC_BOUNDARIES:item")]}},
                {"artifact_name": "DOC_SUPERSESSION.partX.json", "payload": {"schema": "DOC_SUPERSESSION@v1", "items": [_item("DOC_SUPERSESSION:item")]}},
                {"artifact_name": "CAP_NOTICES.partX.json", "payload": {"schema": "CAP_NOTICES@v1", "items": [_item("CAP_NOTICES:item")]}},
            ]
        }
        return {
            "text": json.dumps(payload),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="D",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["ok"] == 1
    assert captured["kwargs"]
    first = captured["kwargs"][0]
    response_format = first.get("response_format_override")
    assert isinstance(response_format, dict)
    assert response_format.get("type") == "json_schema"
    json_schema = response_format.get("json_schema")
    assert isinstance(json_schema, dict)
    assert json_schema.get("strict") is True
    structured_override = first.get("structured_output_override")
    assert isinstance(structured_override, dict)
    assert structured_override.get("strict") is True


def test_non_contract_steps_do_not_force_strict_json_schema(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_v3_module()
    phase_dir = tmp_path / "D_docs_pipeline"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_D2_TEST.md"
    prompt.write_text("Goal: D2 output\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(
        step_id="D2",
        prompt_path=prompt,
        output_artifacts=("DOC_INTERFACES.partX.json",),
    )
    partitions = [{"id": "D_P0001", "paths": ["docs/example.md"]}]
    captured = {"kwargs": []}

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        captured["kwargs"].append(dict(kwargs))
        payload = {
            "artifacts": [
                {
                    "artifact_name": "DOC_INTERFACES.partX.json",
                    "payload": {
                        "schema": "DOC_INTERFACES@v1",
                        "items": [
                            {
                                "id": "DOC_INTERFACES:item",
                                "path": "docs/example.md",
                                "line_range": [1, 2],
                            }
                        ],
                    },
                }
            ]
        }
        return {
            "text": json.dumps(payload),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    runner.execute_step_for_partitions(
        phase="D",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert captured["kwargs"]
    first = captured["kwargs"][0]
    assert first.get("response_format_override") is None
    assert first.get("structured_output_override") is None
