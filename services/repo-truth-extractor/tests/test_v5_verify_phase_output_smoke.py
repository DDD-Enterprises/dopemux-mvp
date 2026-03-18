from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import build_smoke_run


def test_v5_verify_phase_output_smoke_passes_for_valid_run_dir(tmp_path) -> None:
    built = build_smoke_run(tmp_path, "verify_valid")
    runner = built["runner"]
    assert runner.verify_phase_output(built["dirs"], ["D"]) == 0


def test_v5_verify_phase_output_smoke_fails_for_incomplete_run_dir(tmp_path) -> None:
    built = build_smoke_run(tmp_path, "verify_invalid")
    runner = built["runner"]
    for qa_path in built["dirs"]["D"].joinpath("qa").glob("*"):
        qa_path.unlink()
    assert runner.verify_phase_output(built["dirs"], ["D"]) != 0
