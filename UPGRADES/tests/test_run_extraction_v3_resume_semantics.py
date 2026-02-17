from __future__ import annotations

import importlib.util
import json
import os
import time
from pathlib import Path

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "UPGRADES" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner, *, workers: int):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=True,
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
        partition_workers=workers,
    )


def _write_success_json(path: Path, *, phase: str, step_id: str, partition_id: str, artifact_name: str) -> None:
    payload = {
        "phase": phase,
        "step_id": step_id,
        "partition_id": partition_id,
        "artifacts": [
            {
                "artifact_name": artifact_name,
                "payload": {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "items": [{"id": f"{step_id}-{partition_id}", "path": "/tmp/f.py", "line_range": [1, 2]}],
                },
            }
        ],
        "request_meta": {"failure_type": None, "status_code": 200},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _touch(path: Path, ts: float) -> None:
    os.utime(path, (ts, ts))


def _basic_partition(tmp_path: Path) -> tuple[Path, dict[str, object], Path]:
    source = tmp_path / "source.py"
    source.write_text("print('ok')\n", encoding="utf-8")
    partition = {"id": "A_P0001", "paths": [str(source)]}
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    return prompt, partition, phase_dir


def _patch_execution_stubs(monkeypatch: pytest.MonkeyPatch, runner, *, call_counter: dict[str, int]) -> None:
    def fake_build_partition_context(**kwargs):  # type: ignore[no-untyped-def]
        path = str(kwargs["partition_paths"][0]) if kwargs.get("partition_paths") else "none"
        return (
            f"PARTITION_PATH={path}",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        )

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        call_counter["count"] += 1
        return {
            "text": json.dumps(
                {
                    "artifacts": [
                        {
                            "artifact_name": "OUT.json",
                            "payload": {"items": [{"id": "ok", "path": "x.py", "line_range": [1, 1]}]},
                        }
                    ]
                }
            ),
            "meta": {"failure_type": None, "status_code": 200},
        }

    monkeypatch.setattr(runner, "build_partition_context", fake_build_partition_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)


def test_resume_reruns_when_only_failed_sidecars_exist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    prompt, partition, phase_dir = _basic_partition(tmp_path)
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    raw_dir = phase_dir / "raw"
    (raw_dir / "A0__A_P0001.FAILED.txt").write_text("failed\n", encoding="utf-8")
    (raw_dir / "A0__A_P0001.FAILED.json").write_text('{"failure_type":"parse"}\n', encoding="utf-8")
    call_counter = {"count": 0}
    _patch_execution_stubs(monkeypatch, runner, call_counter=call_counter)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=[partition],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=1),
    )

    assert call_counter["count"] == 1
    assert stats["resume_skipped"] == 0
    assert stats["recomputed"] == 1


def test_resume_reruns_when_success_json_is_malformed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    prompt, partition, phase_dir = _basic_partition(tmp_path)
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    raw_dir = phase_dir / "raw"
    (raw_dir / "A0__A_P0001.json").write_text("{invalid", encoding="utf-8")
    call_counter = {"count": 0}
    _patch_execution_stubs(monkeypatch, runner, call_counter=call_counter)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=[partition],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=1),
    )

    assert call_counter["count"] == 1
    assert stats["resume_skipped"] == 0
    assert stats["recomputed"] == 1


def test_resume_skips_when_valid_success_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    prompt, partition, phase_dir = _basic_partition(tmp_path)
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    raw_dir = phase_dir / "raw"
    _write_success_json(
        raw_dir / "A0__A_P0001.json",
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        artifact_name="OUT.json",
    )
    call_counter = {"count": 0}
    _patch_execution_stubs(monkeypatch, runner, call_counter=call_counter)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=[partition],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=1),
    )

    assert call_counter["count"] == 0
    assert stats["resume_skipped"] == 1
    assert stats["recomputed"] == 0


def test_resume_skips_and_prunes_when_failed_is_older(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    prompt, partition, phase_dir = _basic_partition(tmp_path)
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    raw_dir = phase_dir / "raw"
    success_path = raw_dir / "A0__A_P0001.json"
    failed_txt_path = raw_dir / "A0__A_P0001.FAILED.txt"
    failed_json_path = raw_dir / "A0__A_P0001.FAILED.json"
    _write_success_json(
        success_path,
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        artifact_name="OUT.json",
    )
    failed_txt_path.write_text("old failed\n", encoding="utf-8")
    failed_json_path.write_text('{"failure_type":"parse"}\n', encoding="utf-8")
    base = time.time()
    _touch(failed_txt_path, base)
    _touch(failed_json_path, base)
    _touch(success_path, base + 3.0)
    call_counter = {"count": 0}
    _patch_execution_stubs(monkeypatch, runner, call_counter=call_counter)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=[partition],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=1),
    )

    assert call_counter["count"] == 0
    assert stats["resume_skipped"] == 1
    assert not failed_txt_path.exists()
    assert not failed_json_path.exists()


def test_resume_reruns_when_failed_is_newer_than_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    prompt, partition, phase_dir = _basic_partition(tmp_path)
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    raw_dir = phase_dir / "raw"
    success_path = raw_dir / "A0__A_P0001.json"
    failed_txt_path = raw_dir / "A0__A_P0001.FAILED.txt"
    failed_json_path = raw_dir / "A0__A_P0001.FAILED.json"
    _write_success_json(
        success_path,
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        artifact_name="OUT.json",
    )
    failed_txt_path.write_text("new failed\n", encoding="utf-8")
    failed_json_path.write_text('{"failure_type":"parse"}\n', encoding="utf-8")
    base = time.time()
    _touch(success_path, base)
    _touch(failed_txt_path, base + 3.0)
    _touch(failed_json_path, base + 3.0)
    call_counter = {"count": 0}
    _patch_execution_stubs(monkeypatch, runner, call_counter=call_counter)
    info_logs: list[str] = []

    def capture_info(msg, *args, **_kwargs):  # type: ignore[no-untyped-def]
        rendered = (msg % args) if args else str(msg)
        info_logs.append(rendered)

    monkeypatch.setattr(runner.logger, "info", capture_info)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=[partition],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=1),
    )

    assert call_counter["count"] == 1
    assert stats["resume_skipped"] == 0
    assert any("Resume: rerun failed_newer_than_success for A0 A_P0001" in line for line in info_logs)


@pytest.mark.parametrize("workers", [1, 2])
def test_resume_prune_and_decision_logs_are_in_stable_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, workers: int
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))

    source1 = tmp_path / "source1.py"
    source2 = tmp_path / "source2.py"
    source1.write_text("print('one')\n", encoding="utf-8")
    source2.write_text("print('two')\n", encoding="utf-8")
    partitions = [
        {"id": "A_P0002", "paths": [str(source2)]},
        {"id": "A_P0001", "paths": [str(source1)]},
    ]

    raw_dir = phase_dir / "raw"
    for partition_id in ("A_P0001", "A_P0002"):
        success_path = raw_dir / f"A0__{partition_id}.json"
        failed_txt_path = raw_dir / f"A0__{partition_id}.FAILED.txt"
        failed_json_path = raw_dir / f"A0__{partition_id}.FAILED.json"
        _write_success_json(
            success_path,
            phase="A",
            step_id="A0",
            partition_id=partition_id,
            artifact_name="OUT.json",
        )
        failed_txt_path.write_text("old failed\n", encoding="utf-8")
        failed_json_path.write_text('{"failure_type":"parse"}\n', encoding="utf-8")
        base = time.time()
        _touch(failed_txt_path, base)
        _touch(failed_json_path, base)
        _touch(success_path, base + 2.0)

    info_logs: list[str] = []

    def capture_info(msg, *args, **_kwargs):  # type: ignore[no-untyped-def]
        rendered = (msg % args) if args else str(msg)
        info_logs.append(rendered)

    monkeypatch.setattr(runner.logger, "info", capture_info)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, workers=workers),
    )

    assert stats["resume_skipped"] == 2
    assert stats["recomputed"] == 0
    for partition_id in ("A_P0001", "A_P0002"):
        assert not (raw_dir / f"A0__{partition_id}.FAILED.txt").exists()
        assert not (raw_dir / f"A0__{partition_id}.FAILED.json").exists()

    resume_logs = [line for line in info_logs if line.startswith("Resume:")]
    assert resume_logs == [
        "Resume: skip valid success for A0 A_P0001",
        "Resume: prune stale FAILED for A0 A_P0001",
        "Resume: skip valid success for A0 A_P0002",
        "Resume: prune stale FAILED for A0 A_P0002",
        "Resume: skipped 2 existing outputs for step A0",
    ]
