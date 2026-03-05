#!/usr/bin/env python3
"""
TP-008 Automated Audit (JSON-managed only)

Audits per-partition raw outputs under a run directory:
- Parses outputs (including FAILED.txt with JSON on first line)
- Validates contract: expected artifacts present + item minimums (id/path/line_range)
- Validates line_range: [start,end], ints, start>0, end>=start
- Produces deterministic rollups and first-failure context

Usage:
  python audit_tp008.py --run-dir /path/to/runs/<RUN_ID> --out-dir /path/to/audit_out

Assumptions:
- PHASE_CONTRACT_MAP.json exists somewhere under run-dir (we search for it).
- Raw outputs are under **/raw/** directories (we search for step__partition.* files).
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STEP_PART_RE = re.compile(r"^(?P<step>[A-Z]\d+)__?(?P<part>[A-Z]_[Pp]\d{4})\.(?P<ext>.+)$")
STEP_PART_RE2 = re.compile(r"^(?P<step>[A-Z]\d+)__?(?P<part>[A-Z]_P\d{4})\.(?P<ext>.+)$")


@dataclass(frozen=True)
class Failure:
    kind: str
    detail: str
    artifact_name: Optional[str] = None
    item_index: Optional[int] = None
    item_id: Optional[str] = None
    item_path: Optional[str] = None


def read_json_lenient(p: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None, f"read_error:{e}"

    text = text.strip()
    if not text:
        return None, "empty_file"

    if p.suffix.lower() == ".txt":
        first_line = text.splitlines()[0].strip()
        try:
            return json.loads(first_line), None
        except Exception as e:
            return None, f"json_parse_error_first_line:{e}"

    try:
        return json.loads(text), None
    except Exception as e:
        return None, f"json_parse_error:{e}"


def find_contract_map(run_dir: Path) -> Path:
    hits = list(run_dir.rglob("PHASE_CONTRACT_MAP.json"))
    if not hits:
        raise FileNotFoundError(f"PHASE_CONTRACT_MAP.json not found under {run_dir}")
    hits.sort(key=lambda p: (len(str(p)), str(p)))
    return hits[0]


def load_contract_map(p: Path) -> Dict[str, Any]:
    obj, err = read_json_lenient(p)
    if err or not isinstance(obj, dict):
        raise ValueError(f"Failed to parse contract map: {p} err={err}")
    return obj


def expected_artifacts_for_step(contract_map: Dict[str, Any], step_id: str) -> List[str]:
    steps = contract_map.get("steps") or contract_map.get("step_contracts") or contract_map
    if not isinstance(steps, dict):
        return []
    sc = steps.get(step_id)
    if not isinstance(sc, dict):
        return []
    exp = sc.get("expected_artifacts") or sc.get("expected_json_artifacts") or sc.get("expected_outputs")
    if isinstance(exp, list):
        return [str(x) for x in exp]
    arts = sc.get("artifacts")
    if isinstance(arts, list):
        names = []
        for a in arts:
            if isinstance(a, dict) and "artifact_name" in a:
                names.append(str(a["artifact_name"]))
        return names
    return []


def validate_line_range(v: Any) -> Optional[str]:
    if not isinstance(v, list) or len(v) != 2:
        return "line_range_not_len2_list"
    a, b = v[0], v[1]
    if not isinstance(a, int) or not isinstance(b, int):
        return "line_range_not_ints"
    if a <= 0:
        return "line_range_start_leq_0"
    if b < a:
        return "line_range_end_lt_start"
    return None


def validate_item_minimums(item: Any) -> Optional[Failure]:
    if not isinstance(item, dict):
        return Failure("item_not_object", "items[] entry is not an object")
    if "id" not in item:
        return Failure("schema_missing_key", "missing_key:id")
    if "path" not in item:
        return Failure(
            "schema_missing_key",
            "missing_key:path",
            item_id=str(item.get("id")) if "id" in item else None,
        )
    if "line_range" not in item:
        return Failure(
            "schema_missing_key",
            "missing_key:line_range",
            item_id=str(item.get("id")) if "id" in item else None,
            item_path=str(item.get("path")) if "path" in item else None,
        )
    lr_err = validate_line_range(item.get("line_range"))
    if lr_err:
        return Failure(
            "schema_invalid_line_range",
            lr_err,
            item_id=str(item.get("id")),
            item_path=str(item.get("path")),
        )
    return None


def validate_artifact(artifact: Any) -> Optional[Failure]:
    if not isinstance(artifact, dict):
        return Failure("artifact_not_object", "artifact entry is not an object")
    name = artifact.get("artifact_name")
    if not isinstance(name, str) or not name:
        return Failure("schema_missing_key", "missing_key:artifact_name")
    payload = artifact.get("payload")
    if not isinstance(payload, dict):
        return Failure("schema_invalid_payload", "payload not object", artifact_name=name)

    if "items" in payload:
        items = payload.get("items")
        if not isinstance(items, list):
            return Failure(
                "contract_items_not_list",
                "payload.items is not a list",
                artifact_name=name,
            )
        for idx, it in enumerate(items):
            f = validate_item_minimums(it)
            if f:
                return Failure(
                    f.kind,
                    f.detail,
                    artifact_name=name,
                    item_index=idx,
                    item_id=f.item_id,
                    item_path=f.item_path,
                )
    return None


def audit_partition_file(
    contract_map: Dict[str, Any],
    step_id: str,
    part_id: str,
    path: Path,
) -> Dict[str, Any]:
    obj, parse_err = read_json_lenient(path)
    result: Dict[str, Any] = {
        "step": step_id,
        "partition": part_id,
        "file": str(path),
        "parse_ok": parse_err is None,
        "parse_error": parse_err,
        "contract_ok": False,
        "failures": [],
        "artifacts_present": [],
        "schema_values": [],
    }
    if parse_err or not isinstance(obj, dict):
        result["failures"].append({"kind": "parse_failure", "detail": parse_err or "not_object"})
        return result

    artifacts = obj.get("artifacts")
    if not isinstance(artifacts, list):
        result["failures"].append(
            {"kind": "schema_missing_key", "detail": "missing_or_invalid:artifacts"}
        )
        return result

    exp = expected_artifacts_for_step(contract_map, step_id)
    present_names: List[str] = []
    for a in artifacts:
        if isinstance(a, dict) and isinstance(a.get("artifact_name"), str):
            present_names.append(a["artifact_name"])
            payload = a.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("schema"), str):
                result["schema_values"].append(payload["schema"])
    present_names_sorted = sorted(set(present_names))
    result["artifacts_present"] = present_names_sorted

    if exp:
        missing = sorted(set(exp) - set(present_names_sorted))
        if missing:
            result["failures"].append(
                {"kind": "missing_expected_artifacts", "detail": ",".join(missing)}
            )

    for a in artifacts:
        f = validate_artifact(a)
        if f:
            result["failures"].append(
                {
                    "kind": f.kind,
                    "detail": f.detail,
                    "artifact_name": f.artifact_name,
                    "item_index": f.item_index,
                    "item_id": f.item_id,
                    "item_path": f.item_path,
                }
            )
            break

    result["contract_ok"] = len(result["failures"]) == 0
    return result


def discover_raw_files(run_dir: Path) -> List[Path]:
    raw_dirs = [p for p in run_dir.rglob("raw") if p.is_dir()]
    files: List[Path] = []
    for rd in raw_dirs:
        for p in rd.iterdir():
            if p.is_file() and p.suffix.lower() in (".json", ".txt"):
                if "__" in p.name or "_P" in p.name:
                    files.append(p)
    files.sort(key=lambda p: str(p))
    return files


def parse_step_part(filename: str) -> Optional[Tuple[str, str]]:
    m = STEP_PART_RE.match(filename) or STEP_PART_RE2.match(filename)
    if not m:
        return None
    return m.group("step"), m.group("part")


def write_outputs(out_dir: Path, results: List[Dict[str, Any]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(results)
    ok = sum(1 for r in results if r.get("contract_ok"))
    parse_fail = sum(1 for r in results if not r.get("parse_ok"))
    fail = total - ok
    hist: Dict[str, int] = {}
    for r in results:
        for f in r.get("failures", []):
            k = f.get("kind", "unknown")
            hist[k] = hist.get(k, 0) + 1
    rollup = {
        "total_partitions_seen": total,
        "contract_ok": ok,
        "contract_failed": fail,
        "parse_failed": parse_fail,
        "failure_histogram": dict(sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))),
        "first_failures": [
            {
                "step": r["step"],
                "partition": r["partition"],
                "file": r["file"],
                "failure": (r["failures"][0] if r.get("failures") else None),
            }
            for r in results
            if not r.get("contract_ok")
        ][:50],
    }
    (out_dir / "AUDIT_contract_rollup.json").write_text(
        json.dumps(rollup, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out_dir / "AUDIT_partition_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = []
    lines.append("TP-008 AUDIT ROLLUP")
    lines.append(f"total={total} ok={ok} fail={fail} parse_fail={parse_fail}")
    lines.append("")
    lines.append("Failure histogram:")
    for k, v in rollup["failure_histogram"].items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("First failures (up to 50):")
    for ff in rollup["first_failures"]:
        f = ff["failure"] or {}
        lines.append(
            f"- {ff['step']} {ff['partition']} :: {f.get('kind')} :: {f.get('detail')} :: {ff['file']}"
        )
    (out_dir / "AUDIT_contract_rollup.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--run-dir",
        required=True,
        help="Run root directory (contains PHASE_CONTRACT_MAP.json somewhere below)",
    )
    ap.add_argument("--out-dir", required=True, help="Where to write audit outputs")
    ap.add_argument("--only-step", default="", help="Optional: audit only a single step_id (e.g. D1)")
    args = ap.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    only_step = args.only_step.strip().upper()
    contract_path = find_contract_map(run_dir)
    contract_map = load_contract_map(contract_path)
    raw_files = discover_raw_files(run_dir)
    results: List[Dict[str, Any]] = []
    for p in raw_files:
        sp = parse_step_part(p.name)
        if not sp:
            continue
        step_id, part_id = sp
        if only_step and step_id != only_step:
            continue
        results.append(audit_partition_file(contract_map, step_id, part_id, p))
    results.sort(key=lambda r: (r["step"], r["partition"], r["file"]))
    meta = {
        "run_dir": str(run_dir),
        "contract_map": str(contract_path),
        "only_step": only_step or None,
        "partitions_scanned": len(results),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "AUDIT_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
    write_outputs(out_dir, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
