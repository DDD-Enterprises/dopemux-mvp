from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List


def _collect_missing_evidence(outputs: Dict[str, Dict[str, Any]]) -> List[str]:
    rows: List[str] = []
    for step_id, payload in sorted(outputs.items()):
        missing = payload.get("missing_evidence", [])
        if isinstance(missing, list):
            for row in missing:
                rows.append(f"{step_id}: {row}")
    return sorted(set(rows))


def compile_s_int_reports(run_root: Path, outputs: Dict[str, Dict[str, Any]]) -> Dict[str, Path]:
    statuses = {step_id: str(payload.get("status", "UNKNOWN")) for step_id, payload in outputs.items()}
    missing_evidence = _collect_missing_evidence(outputs)
    fail_closed = any(status not in {"OK", "PASS"} for status in statuses.values())

    summary_lines = [
        "# S_INT Summary",
        "",
        "## Step Status",
    ]
    for step_id in sorted(statuses):
        summary_lines.append(f"- {step_id}: {statuses[step_id]}")

    checklist_lines = [
        "# S_INT Checklist",
        "",
        f"- fail_closed: {'YES' if fail_closed else 'NO'}",
        f"- missing_evidence_count: {len(missing_evidence)}",
    ]
    for item in missing_evidence:
        checklist_lines.append(f"- missing_evidence: {item}")

    fail_closed_lines = [
        "# S_INT Fail Closed",
        "",
        f"- fail_closed: {'YES' if fail_closed else 'NO'}",
    ]
    if missing_evidence:
        fail_closed_lines.append("- missing_evidence:")
        for item in missing_evidence:
            fail_closed_lines.append(f"  - {item}")

    summary_path = run_root / "S_INT_SUMMARY.md"
    checklist_path = run_root / "S_INT_CHECKLIST.md"
    fail_closed_path = run_root / "S_INT_FAIL_CLOSED.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    checklist_path.write_text("\n".join(checklist_lines) + "\n", encoding="utf-8")
    fail_closed_path.write_text("\n".join(fail_closed_lines) + "\n", encoding="utf-8")
    return {
        "summary": summary_path,
        "checklist": checklist_path,
        "fail_closed": fail_closed_path,
    }
