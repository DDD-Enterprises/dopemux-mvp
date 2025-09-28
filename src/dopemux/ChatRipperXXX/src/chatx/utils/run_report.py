"""Utilities to emit a pipeline run report conforming to run_report.schema.json."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_extract_run_report(
    *,
    out_dir: Path,
    started_at: datetime,
    finished_at: datetime,
    messages_total: int,
    attachments_total: int,
    images_total: int,
    images_copied: int,
    bytes_copied: int,
    throughput_msgs_min: float,
    artifacts: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> Path:
    """Write a run report JSON for the extract component.

    Returns the path to the report file.
    """
    run_id = os.environ.get("CHATX_RUN_ID") or str(uuid.uuid4())
    s_at = started_at.astimezone(timezone.utc).isoformat()
    f_at = finished_at.astimezone(timezone.utc).isoformat()

    component: Dict[str, Any] = {
        "component": "extract",
        "run_id": run_id,
        "started_at": s_at,
        "finished_at": f_at,
        "duration_s": max((finished_at - started_at).total_seconds(), 0.0),
        "counters": {
            "messages_total": messages_total,
            "attachments_total": attachments_total,
            "images_total": images_total,
            "images_copied": images_copied,
            "bytes_copied": bytes_copied,
            "throughput_msgs_min": max(0.0, float(throughput_msgs_min)),
        },
        "warnings": warnings or [],
        "errors": [],
        "artifacts": artifacts or [],
    }

    report: Dict[str, Any] = {
        "run_id": run_id,
        "started_at": s_at,
        "finished_at": f_at,
        "components": [component],
        "summary": {
            "messages_total": messages_total,
            "chunks_total": 0,
            "coverage_min": 0,
            "coverage_max": 0,
            "duration_s": component["duration_s"],
        },
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "run_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report_path


def validate_run_report(report_path: Path) -> bool:
    """Validate run_report.json against JSON Schema.

    Returns True if valid or schema/jsonschema not available; False on validation failure.
    """
    try:
        import jsonschema
        from jsonschema import Draft202012Validator

        # Locate schemas directory
        schemas_dir = Path(__file__).parent.parent.parent.parent / "schemas"
        run_schema_path = schemas_dir / "run_report.schema.json"
        metrics_schema_path = schemas_dir / "metrics.schema.json"

        if not run_schema_path.exists():
            return True  # Schema not available in environment

        with open(run_schema_path, "r", encoding="utf-8") as f:
            run_schema = json.load(f)

        # Prepare ref store for external refs
        store: Dict[str, Any] = {}
        if metrics_schema_path.exists():
            with open(metrics_schema_path, "r", encoding="utf-8") as f:
                metrics_schema = json.load(f)
            store["metrics.schema.json"] = metrics_schema
            # Also register by $id if present
            if "$id" in metrics_schema:
                store[metrics_schema["$id"]] = metrics_schema

        # Load the report
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        validator = Draft202012Validator(run_schema, resolver=jsonschema.RefResolver.from_schema(run_schema, store=store))
        validator.validate(report_data)
        return True

    except ImportError:
        return True
    except (jsonschema.ValidationError, json.JSONDecodeError, OSError):
        return False


def append_metrics_event(
    *,
    out_dir: Path,
    component: str,
    started_at: datetime,
    finished_at: datetime,
    counters: Dict[str, Any],
    warnings: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    artifacts: Optional[List[str]] = None,
) -> Path:
    """Append a single component metrics payload to metrics.jsonl.

    Returns the metrics.jsonl path.
    """
    run_id = os.environ.get("CHATX_RUN_ID") or str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "component": component,
        "run_id": run_id,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "finished_at": finished_at.astimezone(timezone.utc).isoformat(),
        "duration_s": max((finished_at - started_at).total_seconds(), 0.0),
        "counters": counters,
        "warnings": warnings or [],
        "errors": errors or [],
        "artifacts": artifacts or [],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / "metrics.jsonl"
    with open(metrics_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

    return metrics_path
