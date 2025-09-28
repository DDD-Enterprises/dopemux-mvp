from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from chatx.utils.run_report import (
    append_metrics_event,
    validate_run_report,
    write_extract_run_report,
)


def test_run_report_and_metrics_schema(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)

    started = datetime.now(UTC)
    finished = started + timedelta(seconds=2)

    # Write run report
    report_path = write_extract_run_report(
        out_dir=out,
        started_at=started,
        finished_at=finished,
        messages_total=10,
        attachments_total=3,
        images_total=3,
        images_copied=2,
        bytes_copied=456,
        throughput_msgs_min=300.0,
        artifacts=[str(out / "messages.json")],
        warnings=["warn"],
    )
    assert report_path.exists()
    assert validate_run_report(report_path) is True

    # Append metrics event
    metrics_path = append_metrics_event(
        out_dir=out,
        component="extract",
        started_at=started,
        finished_at=finished,
        counters={
            "messages_total": 10,
            "attachments_total": 3,
            "images_total": 3,
            "images_copied": 2,
            "bytes_copied": 456,
            "throughput_msgs_min": 300.0,
        },
        warnings=["warn"],
        errors=[],
        artifacts=[str(out / "messages.json")],
    )
    assert metrics_path.exists()
    text = metrics_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(text) >= 1
    # Check JSONL entry is well-formed and includes required fields
    obj = json.loads(text[-1])
    assert obj["component"] == "extract"
    assert obj["counters"]["messages_total"] == 10
    assert obj["counters"]["attachments_total"] == 3
    assert obj["counters"]["images_total"] == 3
    assert obj["counters"]["throughput_msgs_min"] == 300.0

