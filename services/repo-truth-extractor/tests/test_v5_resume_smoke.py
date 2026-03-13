from __future__ import annotations

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import build_smoke_run


def test_v5_resume_smoke_validates_existing_run_and_skip_behavior(tmp_path: Path) -> None:
    built = build_smoke_run(tmp_path, "resume_smoke")
    runner = built["runner"]
    dirs = built["dirs"]
    success_json = built["success_json"]
    success_payload = built["success_payload"]

    runner._validate_existing_run_dir(tmp_path, "resume_smoke")  # type: ignore[attr-defined]

    failed_text = dirs["D"] / "raw" / "D1__D_P0001.FAILED.txt"
    failed_json = dirs["D"] / "raw" / "D1__D_P0001.FAILED.json"
    failed_text.write_text("stale failure\n", encoding="utf-8")
    failed_json.write_text('{"failure_type":"provider"}\n', encoding="utf-8")
    success_mtime = success_json.stat().st_mtime
    stale_mtime = success_mtime - 10
    os.utime(failed_text, (stale_mtime, stale_mtime))
    os.utime(failed_json, (stale_mtime, stale_mtime))

    decision = runner.compute_resume_decision(
        success_json_path=success_json,
        raw_dir=dirs["D"] / "raw",
        phase="D",
        step_id="D1",
        partition_id="D_P0001",
        expected_artifact_names=tuple(
            artifact["artifact_name"] for artifact in success_payload["artifacts"]
        ),
    )
    assert decision["action"] == "SKIP"
    assert decision["prune_failed"] is True
    assert decision["reason"] == "valid_success_stale_failed"

    qa_path = dirs["D"] / "qa" / "D1_QA.json"
    qa_path.write_text(
        '{\n'
        '  "step_id": "D1",\n'
        '  "resume_skipped_partitions": 1,\n'
        '  "recomputed_partitions": 0,\n'
        '  "written_files": []\n'
        '}\n',
        encoding="utf-8",
    )
    resume_proof = runner.write_resume_proof(dirs, "resume_smoke", ["D"])
    assert resume_proof["totals"]["resume_skipped_partitions"] == 1
    assert resume_proof["totals"]["recomputed_partitions"] == 0


def test_v5_resume_smoke_missing_run_dir_fails_closed(tmp_path: Path) -> None:
    runner = build_smoke_run(tmp_path, "existing_run")["runner"]
    missing = "missing_run"
    try:
        runner._validate_existing_run_dir(tmp_path, missing)  # type: ignore[attr-defined]
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing run dir should fail closed")
