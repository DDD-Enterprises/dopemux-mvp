from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _runner_script() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"


def test_cli_help_includes_expected_flags(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--help"],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    assert "--phase" in result.stdout
    assert "--status-json" in result.stdout
    assert "--doctor" in result.stdout
    assert "--batch-watch" in result.stdout
    assert "--batch-submit-only" in result.stdout
    assert "--print-run-order" in result.stdout
    assert "--print-phase-routing" in result.stdout
    assert "--print-phase-prompts" in result.stdout
    assert "--tail-run-log" in result.stdout
    assert "--show-provider-usage" in result.stdout


def test_cli_status_json_stable_output(tmp_path: Path) -> None:
    run_id = "test_status_json"
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--status-json", "--run-id", run_id],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["run_id"] == run_id
    assert "summary" in payload
    assert "phases" in payload


def test_cli_print_run_order_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--print-run-order", "--run-id", "test_print_run_order"],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    phase_order = payload["phase_order"]
    assert isinstance(phase_order, list)
    assert phase_order[0]["phase_id"] == "A"
    assert phase_order[-1]["phase_id"] == "S"


def test_cli_print_phase_routing_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_runner_script()),
            "--print-phase-routing",
            "--phase",
            "Q",
            "--dry-run",
            "--run-id",
            "test_print_phase_routing",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert "Q" in payload["phases"]
    assert isinstance(payload["phases"]["Q"], list)


def test_cli_print_phase_prompts_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_runner_script()),
            "--print-phase-prompts",
            "Q",
            "--run-id",
            "test_print_phase_prompts",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    prompts = payload["phases"]["Q"]
    assert isinstance(prompts, list)
    assert any(str(row.get("step_id", "")).startswith("Q") for row in prompts)


def test_cli_tail_run_log_filters_phase_and_step(tmp_path: Path) -> None:
    run_id = "test_tail_run_log"
    run_root = tmp_path / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    run_log = run_root / "RUN.log"
    run_log.write_text(
        "\n".join(
            [
                "10:00:00 [INFO] STEP_START phase=C step=C0 provider=openai model=gpt-5-mini",
                "10:00:01 [INFO] STEP_START phase=C step=C1 provider=gemini model=gemini-2.5-pro",
                "10:00:02 [INFO] STEP_DONE phase=C step=C0 routes={\"openai/gpt-5-mini\":1}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(_runner_script()),
            "--tail-run-log",
            "--run-id",
            run_id,
            "--phase",
            "C",
            "--step",
            "C0",
            "--tail-lines",
            "100",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    assert "step=C0" in result.stdout
    assert "step=C1" not in result.stdout


def test_cli_show_provider_usage_from_run_log(tmp_path: Path) -> None:
    run_id = "test_provider_usage"
    run_root = tmp_path / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    run_log = run_root / "RUN.log"
    run_log.write_text(
        "\n".join(
            [
                "10:00:00 [INFO] STEP_START phase=C step=C0 partitions=1 prompt=foo outputs=[] tier=extract provider=openai model=gpt-5-mini routing_policy=balanced",
                "10:00:01 [INFO] STEP_START phase=C step=C1 partitions=1 prompt=bar outputs=[] tier=extract provider=gemini model=gemini-2.5-pro routing_policy=balanced",
                "10:00:02 [INFO] STEP_DONE phase=C step=C1 ok=1 failed=0 retries=0 skipped=0 elapsed_ms=1 norm_written=1 qa_file=q.json hops={} escalated=0 exec_mode={} routes={\"gemini/gemini-2.5-pro\": 1}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(_runner_script()),
            "--show-provider-usage",
            "--run-id",
            run_id,
            "--phase",
            "C",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["step_start_counts"]["openai/gpt-5-mini"] == 1
    assert payload["step_start_counts"]["gemini/gemini-2.5-pro"] == 1
    assert payload["step_done_route_counts"]["gemini/gemini-2.5-pro"] == 1
