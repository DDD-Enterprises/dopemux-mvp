from __future__ import annotations

import importlib.util
import json
import re
import time
from pathlib import Path

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner, *, workers: int, fail_fast_auth: bool = True):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=fail_fast_auth,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=5,
        partition_workers=workers,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
    )


def test_partition_concurrency_writes_in_stable_order(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))

    partitions = [
        {"id": "A_P0003", "paths": ["/tmp/p3"]},
        {"id": "A_P0001", "paths": ["/tmp/p1"]},
        {"id": "A_P0002", "paths": ["/tmp/p2"]},
    ]

    def fake_build_partition_context(**kwargs):  # type: ignore[no-untyped-def]
        path = str(kwargs["partition_paths"][0])
        return (
            f"PARTITION_PATH={path}",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        user_content = str(kwargs["user_content"])
        match = re.search(r"PARTITION_PATH=.*/p(\d)", user_content)
        assert match is not None
        part_num = match.group(1)
        if part_num == "1":
            time.sleep(0.05)
        elif part_num == "2":
            time.sleep(0.01)
        payload = {
            "artifacts": [
                {
                    "artifact_name": "OUT.json",
                    "payload": {"partition": f"A_P000{part_num}"},
                }
            ]
        }
        return {"text": json.dumps(payload), "meta": {"failure_type": None, "status_code": 200}}

    write_order: list[str] = []
    original_write_json = runner.write_json

    def capturing_write_json(path: Path, payload):  # type: ignore[no-untyped-def]
        if path.name.startswith("A0__A_P") and path.suffix == ".json" and ".FAILED" not in path.name:
            write_order.append(path.name)
        return original_write_json(path, payload)

    monkeypatch.setattr(runner, "build_partition_context", fake_build_partition_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)
    monkeypatch.setattr(runner, "write_json", capturing_write_json)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=3),
    )

    assert stats["ok"] == 3
    assert stats["failed"] == 0
    assert stats["recomputed"] == 3
    assert write_order == ["A0__A_P0001.json", "A0__A_P0002.json", "A0__A_P0003.json"]


def test_partition_concurrency_auth_failfast_uses_stable_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))

    partitions = [
        {"id": "A_P0002", "paths": ["/tmp/p2"]},
        {"id": "A_P0001", "paths": ["/tmp/p1"]},
    ]

    def fake_build_partition_context(**kwargs):  # type: ignore[no-untyped-def]
        path = str(kwargs["partition_paths"][0])
        return (
            f"PARTITION_PATH={path}",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        user_content = str(kwargs["user_content"])
        match = re.search(r"PARTITION_PATH=.*/p(\d)", user_content)
        assert match is not None
        part_num = match.group(1)
        if part_num == "1":
            time.sleep(0.08)
            return {"text": "", "meta": {"failure_type": "auth_rejected", "status_code": 401}}
        return {
            "text": json.dumps(
                {
                    "artifacts": [
                        {
                            "artifact_name": "OUT.json",
                            "payload": {"partition": "A_P0002"},
                        }
                    ]
                }
            ),
            "meta": {"failure_type": None, "status_code": 200},
        }

    monkeypatch.setattr(runner, "build_partition_context", fake_build_partition_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    with pytest.raises(RuntimeError, match="Fail-fast auth triggered"):
        runner.execute_step_for_partitions(
            phase="A",
            prompt_spec=prompt_spec,
            partitions=partitions,
            phase_dir=phase_dir,
            cfg=_make_cfg(runner, workers=3, fail_fast_auth=True),
        )

    assert sorted(path.name for path in (phase_dir / "raw").glob("A0__*.json")) == []


def test_partition_workers_one_still_writes_in_stable_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))

    partitions = [
        {"id": "A_P0003", "paths": ["/tmp/p3"]},
        {"id": "A_P0001", "paths": ["/tmp/p1"]},
        {"id": "A_P0002", "paths": ["/tmp/p2"]},
    ]

    def fake_build_partition_context(**kwargs):  # type: ignore[no-untyped-def]
        path = str(kwargs["partition_paths"][0])
        return (
            f"PARTITION_PATH={path}",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        user_content = str(kwargs["user_content"])
        match = re.search(r"PARTITION_PATH=.*/p(\d)", user_content)
        assert match is not None
        part_num = match.group(1)
        payload = {
            "artifacts": [
                {
                    "artifact_name": "OUT.json",
                    "payload": {"partition": f"A_P000{part_num}"},
                }
            ]
        }
        return {"text": json.dumps(payload), "meta": {"failure_type": None, "status_code": 200}}

    write_order: list[str] = []
    original_write_json = runner.write_json

    def capturing_write_json(path: Path, payload):  # type: ignore[no-untyped-def]
        if path.name.startswith("A0__A_P") and path.suffix == ".json" and ".FAILED" not in path.name:
            write_order.append(path.name)
        return original_write_json(path, payload)

    monkeypatch.setattr(runner, "build_partition_context", fake_build_partition_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)
    monkeypatch.setattr(runner, "write_json", capturing_write_json)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=1),
    )

    assert stats["ok"] == 3
    assert stats["failed"] == 0
    assert write_order == ["A0__A_P0001.json", "A0__A_P0002.json", "A0__A_P0003.json"]


def test_process_executor_falls_back_to_threaded_execution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))

    partitions = [
        {"id": "A_P0002", "paths": ["/tmp/p2"]},
        {"id": "A_P0001", "paths": ["/tmp/p1"]},
    ]

    def fake_build_partition_context(**kwargs):  # type: ignore[no-untyped-def]
        path = str(kwargs["partition_paths"][0])
        return (
            f"PARTITION_PATH={path}",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        user_content = str(kwargs["user_content"])
        match = re.search(r"PARTITION_PATH=.*/p(\d)", user_content)
        assert match is not None
        part_num = match.group(1)
        payload = {
            "artifacts": [
                {
                    "artifact_name": "OUT.json",
                    "payload": {"partition": f"A_P000{part_num}"},
                }
            ]
        }
        return {"text": json.dumps(payload), "meta": {"failure_type": None, "status_code": 200}}

    monkeypatch.setattr(runner, "build_partition_context", fake_build_partition_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    cfg = runner.replace(_make_cfg(runner, workers=2), executor="process")
    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=cfg,
    )

    assert stats["ok"] == 2
    assert stats["failed"] == 0
    assert sorted(path.name for path in (phase_dir / "raw").glob("A0__*.json")) == [
        "A0__A_P0001.json",
        "A0__A_P0002.json",
    ]


def test_partition_worker_exception_synthesizes_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))

    partitions = [
        {"id": "A_P0001", "paths": ["/tmp/p1"]},
        {"id": "A_P0002", "paths": ["/tmp/p2"]},
    ]

    def fake_build_partition_context(**kwargs):  # type: ignore[no-untyped-def]
        path = str(kwargs["partition_paths"][0])
        if path.endswith("/p1"):
            raise RuntimeError("boom from worker")
        return (
            f"PARTITION_PATH={path}",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        )

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"ok": True}}]}),
            "meta": {"failure_type": None, "status_code": 200},
        }

    monkeypatch.setattr(runner, "build_partition_context", fake_build_partition_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=2, fail_fast_auth=False),
    )

    assert stats["ok"] == 1
    assert stats["failed"] == 1
    assert (phase_dir / "raw" / "A0__A_P0001.FAILED.json").exists()
