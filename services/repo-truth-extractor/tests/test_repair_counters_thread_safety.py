"""Thread-safety test for _REPAIR_COUNTERS in run_extraction_v5.

Verifies that concurrent calls to _attempt_schema_repair_path_items()
do not lose increments due to unsynchronised read-modify-write on the
global _REPAIR_COUNTERS dict.
"""
from __future__ import annotations

import importlib.util
import sys
import threading
from pathlib import Path


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_repair_counters_no_lost_increments() -> None:
    runner = _load_runner_module()

    # Reset counters to a known baseline
    for k in runner._REPAIR_COUNTERS:
        runner._REPAIR_COUNTERS[k] = 0

    threads = 8
    iterations = 200
    barrier = threading.Barrier(threads)

    def worker() -> None:
        barrier.wait()
        for _ in range(iterations):
            # schema_reason="nope" triggers the "not_applicable" early-return
            # which increments "attempted" and "failed_ambiguous" each call.
            runner._attempt_schema_repair_path_items(
                artifacts=[],
                schema_reason="nope",
                partition_files=[],
            )

    pool = [threading.Thread(target=worker) for _ in range(threads)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()

    expected = threads * iterations  # 1600
    assert runner._REPAIR_COUNTERS["attempted"] == expected, (
        f"attempted: {runner._REPAIR_COUNTERS['attempted']} != {expected}"
    )
    assert runner._REPAIR_COUNTERS["failed_ambiguous"] == expected, (
        f"failed_ambiguous: {runner._REPAIR_COUNTERS['failed_ambiguous']} != {expected}"
    )
