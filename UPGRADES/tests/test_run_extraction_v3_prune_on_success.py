from __future__ import annotations

import importlib.util
import json
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


def _patch_success_stubs(monkeypatch: pytest.MonkeyPatch, runner, *, call_counter: dict[str, int]) -> None:
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


@pytest.mark.parametrize("workers", [1, 2])
def test_prune_failed_sidecars_after_success_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, workers: int
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    step_id = "A3"
    partition_id = "A_P0011"
    prompt = tmp_path / "PROMPT_A3_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    source = tmp_path / "source.py"
    source.write_text("print('ok')\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id=step_id, prompt_path=prompt, output_artifacts=("OUT.json",))
    partitions = [{"id": partition_id, "paths": [str(source)]}]

    (raw_dir / f"{step_id}__{partition_id}.FAILED.txt").write_text("failed\n", encoding="utf-8")
    (raw_dir / f"{step_id}__{partition_id}.FAILED.json").write_text('{"failure_type":"parse"}\n', encoding="utf-8")
    (raw_dir / f"{step_id}__{partition_id}.FAILED.trace").write_text("trace\n", encoding="utf-8")

    call_counter = {"count": 0}
    _patch_success_stubs(monkeypatch, runner, call_counter=call_counter)
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

    assert call_counter["count"] == 1
    assert stats["resume_skipped"] == 0
    assert (raw_dir / f"{step_id}__{partition_id}.json").exists()
    assert not (raw_dir / f"{step_id}__{partition_id}.FAILED.txt").exists()
    assert not (raw_dir / f"{step_id}__{partition_id}.FAILED.json").exists()
    assert not (raw_dir / f"{step_id}__{partition_id}.FAILED.trace").exists()
    assert any(
        f"Resume: prune stale FAILED after success for {step_id} {partition_id} count=3" in line for line in info_logs
    )
