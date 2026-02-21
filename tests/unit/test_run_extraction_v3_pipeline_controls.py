from __future__ import annotations

import importlib.util
import json
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parents[2] / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def make_cfg(*, dry_run: bool, resume: bool) -> runner.RunnerConfig:
    return runner.RunnerConfig(
        dry_run=dry_run,
        max_files_docs=3,
        max_files_code=3,
        max_chars=2000,
        max_request_bytes=200000,
        file_truncate_chars=80,
        home_scan_mode="safe",
        resume=resume,
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
    )


def test_build_partitions_stable_order(tmp_path: Path) -> None:
    files = [
        tmp_path / "docs" / "guide.md",
        tmp_path / "src" / "main.py",
        tmp_path / "scripts" / "start_stack.sh",
        tmp_path / ".claude" / "settings.json",
        tmp_path / "docs" / "archive" / "old.md",
    ]
    for idx, file_path in enumerate(files):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"file-{idx}\n", encoding="utf-8")

    items = [{"path": str(path), "size": path.stat().st_size, "mtime": float(path.stat().st_mtime)} for path in files]
    inventory = runner.build_inventory(items, file_truncate_chars=80)

    first = runner.build_partitions("A", inventory, max_files=10, max_chars=5000)
    second = runner.build_partitions("A", list(reversed(inventory)), max_files=10, max_chars=5000)

    first_paths = [path for part in first for path in part.get("paths", [])]
    second_paths = [path for part in second for path in part.get("paths", [])]
    assert sorted(first_paths) == sorted(second_paths)
    assert sorted(first_paths) == sorted(str(path.resolve()) for path in files)


def test_home_safe_filter_blocks_non_allowlisted_paths(tmp_path: Path) -> None:
    home = tmp_path / "home"
    safe_file = home / ".config" / "dopemux" / "config.yaml"
    unsafe_file = home / ".ssh" / "id_rsa"
    safe_file.parent.mkdir(parents=True, exist_ok=True)
    unsafe_file.parent.mkdir(parents=True, exist_ok=True)
    safe_file.write_text("ok: true\n", encoding="utf-8")
    unsafe_file.write_text("secret\n", encoding="utf-8")

    filtered = runner.home_safe_filter(
        [
            {"path": str(safe_file.resolve()), "size": safe_file.stat().st_size, "mtime": float(safe_file.stat().st_mtime)},
            {"path": str(unsafe_file.resolve()), "size": unsafe_file.stat().st_size, "mtime": float(unsafe_file.stat().st_mtime)},
        ],
        home,
    )
    kept_paths = {item["path"] for item in filtered}
    assert str(safe_file.resolve()) in kept_paths
    assert str(unsafe_file.resolve()) not in kept_paths


def test_resume_skips_completed_partitions(tmp_path: Path) -> None:
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    source = tmp_path / "config" / "settings.toml"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("mode = 'safe'\n", encoding="utf-8")

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: TEST.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("TEST.json",))

    partitions = [{"id": "A_P0001", "paths": [str(source)]}]
    cfg = make_cfg(dry_run=True, resume=True)

    first = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=cfg,
    )
    second = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=cfg,
    )

    assert first["recomputed"] == 1
    assert second["resume_skipped"] == 1


def test_classify_failure_and_backoff_are_deterministic() -> None:
    assert runner.classify_failure_type(429, "", "rate limit") == "rate_limit"
    assert runner.classify_failure_type(401, "", "unauthorized") == "auth_rejected"
    assert runner.backoff_seconds(2, 1.0, 5.0) == 1.0
    assert runner.backoff_seconds(10, 1.0, 3.0) == 3.0
