#!/usr/bin/env python3
"""Deterministic run/phase/step probe for extraction debug bundles."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _err(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 1


def _bool_str(value: bool) -> str:
    return "true" if value else "false"


def _utc_mtime(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
    except Exception:
        return "-"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json_required(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Failed to load {label} JSON: {path} ({type(exc).__name__}: {exc})") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} JSON must be an object: {path}")
    return payload


def _load_runner_module(repo_root: Path) -> Any:
    runner_path = (repo_root / "services" / "repo-truth-extractor" / "run_extraction_v3.py").resolve()
    if not runner_path.exists():
        raise RuntimeError(f"Runner module not found: {runner_path}")
    spec = importlib.util.spec_from_file_location("run_extraction_v3_probe", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner module spec: {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _iter_files(path: Path) -> List[Path]:
    if not path.exists() or not path.is_dir():
        return []
    return sorted(p for p in path.rglob("*") if p.is_file())


def _partition_ids_from_payload(payload: Dict[str, Any]) -> List[str]:
    rows = payload.get("partitions")
    if not isinstance(rows, list):
        return []
    ids = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        partition_id = row.get("id")
        if isinstance(partition_id, str) and partition_id:
            ids.append(partition_id)
    return sorted(set(ids))


def _detect_phase_like_dirs(run_root: Path, phase_dir_names: Dict[str, str]) -> List[str]:
    if not run_root.exists():
        return []
    known = set(phase_dir_names.values())
    out: List[str] = []
    for child in sorted(run_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if child.name in known or re.match(r"^[A-Z]_[A-Za-z0-9_]+$", child.name):
            out.append(child.name)
    return out


def _search_raw_matches(
    search_root: Path,
    step_id: str,
    partition_ids: Sequence[str],
) -> Tuple[List[Path], str]:
    if not search_root.exists() or not search_root.is_dir() or not step_id:
        return [], "none"
    exact: List[Path] = []
    for partition_id in partition_ids:
        pattern = f"{step_id}__{partition_id}.json"
        exact.extend(p for p in search_root.rglob(pattern) if p.is_file())
    dedup_exact = sorted(set(p.resolve() for p in exact), key=lambda p: str(p))
    if dedup_exact:
        return dedup_exact, "exact"
    fallback = [p.resolve() for p in search_root.rglob(f"{step_id}__*.json") if p.is_file()]
    return sorted(set(fallback), key=lambda p: str(p)), "fallback"


def _to_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def _parse_failures(qa_payload: Dict[str, Any]) -> List[Dict[str, str]]:
    rows = qa_payload.get("parse_failures")
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        partition_id = str(row.get("partition_id") or "")
        reason = str(row.get("reason") or "")
        qa_file = str(row.get("file") or "")
        out.append(
            {
                "partition_id": partition_id,
                "reason": reason,
                "qa_reported_file": qa_file,
            }
        )
    return sorted(out, key=lambda row: (row["partition_id"], row["reason"], row["qa_reported_file"]))


def _fallback_partition_ids_from_raw(raw_dir: Path, step_id: str) -> List[str]:
    if not raw_dir.exists() or not step_id:
        return []
    out: List[str] = []
    pat = re.compile(rf"^{re.escape(step_id)}__(.+)\.json$")
    for path in sorted(raw_dir.glob(f"{step_id}__*.json")):
        if path.name.endswith(".FAILED.json"):
            continue
        match = pat.match(path.name)
        if match:
            out.append(match.group(1))
    return sorted(set(out))


def _print_section_header(name: str) -> None:
    print(f"SECTION: {name}")


def _print_list(prefix: str, values: Iterable[str]) -> None:
    collected = list(values)
    if not collected:
        print(f"{prefix}=-")
        return
    for value in collected:
        print(f"{prefix}={value}")


def main() -> int:
    parser = argparse.ArgumentParser("Deterministic extraction run probe")
    parser.add_argument("--phase", required=True)
    rid_group = parser.add_mutually_exclusive_group(required=True)
    rid_group.add_argument("--rid")
    rid_group.add_argument("--rid-from-latest", action="store_true")
    parser.add_argument("--step")
    parser.add_argument("--max-partitions", type=int, default=10)
    parser.add_argument("--max-failures", type=int, default=10)
    parser.add_argument("--search-root", default="extraction/repo-truth-extractor/v3/runs")
    args = parser.parse_args()

    if args.max_partitions <= 0:
        return _err("--max-partitions must be > 0")
    if args.max_failures <= 0:
        return _err("--max-failures must be > 0")

    repo_root = Path.cwd().resolve()
    try:
        runner = _load_runner_module(repo_root)
    except Exception as exc:
        return _err(str(exc))

    phases = getattr(runner, "PHASES", None)
    phase_dir_names = getattr(runner, "PHASE_DIR_NAMES", None)
    get_phase_prompts = getattr(runner, "get_phase_prompts", None)
    if not isinstance(phases, list) or not isinstance(phase_dir_names, dict) or not callable(get_phase_prompts):
        return _err("Runner module missing required symbols: PHASES, PHASE_DIR_NAMES, get_phase_prompts")

    phase = str(args.phase).strip()
    if phase not in phases:
        return _err(f"Invalid --phase {phase!r}. Valid phases: {','.join(phases)}")

    run_id: str
    if args.rid:
        run_id = str(args.rid).strip()
    else:
        latest_path = repo_root / "extraction" / "repo-truth-extractor" / "v3" / "latest_run_id.txt"
        if not latest_path.exists():
            return _err(f"latest_run_id.txt not found: {latest_path}")
        run_id = latest_path.read_text(encoding="utf-8").strip()
        if not run_id:
            return _err(f"latest_run_id.txt is empty: {latest_path}")

    run_root = (repo_root / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id).resolve()
    if not run_root.exists() or not run_root.is_dir():
        return _err(f"Run directory not found: {run_root}")

    phase_dir = run_root / str(phase_dir_names[phase])
    inputs_dir = phase_dir / "inputs"
    raw_dir = phase_dir / "raw"
    norm_dir = phase_dir / "norm"
    qa_dir = phase_dir / "qa"

    search_root = Path(args.search_root).expanduser()
    if not search_root.is_absolute():
        search_root = (repo_root / search_root).resolve()
    else:
        search_root = search_root.resolve()

    prompt_specs = sorted(get_phase_prompts(phase), key=lambda spec: str(spec.step_id))
    prompt_steps = [str(spec.step_id) for spec in prompt_specs]
    prompt_map = {str(spec.step_id): spec for spec in prompt_specs}

    step_id = args.step.strip() if args.step else ""
    if not step_id:
        if not prompt_specs:
            return _err(f"No prompt specs found for phase {phase}; provide --step explicitly.")
        step_id = str(prompt_specs[0].step_id)

    step_spec = prompt_map.get(step_id)
    expected_artifacts: List[str] = []
    step_in_prompts = step_spec is not None
    if step_spec is not None:
        expected_artifacts = sorted(str(name) for name in step_spec.output_artifacts)

    partitions_payload: Dict[str, Any] = {}
    partitions_path = inputs_dir / "PARTITIONS.json"
    if partitions_path.exists():
        try:
            partitions_payload = _load_json_required(partitions_path, "PARTITIONS")
        except Exception as exc:
            return _err(str(exc))
    partition_ids = _partition_ids_from_payload(partitions_payload)

    qa_payload: Dict[str, Any] = {}
    qa_path = qa_dir / f"{step_id}_QA.json"
    qa_missing = not qa_path.exists()
    if not qa_missing:
        try:
            qa_payload = _load_json_required(qa_path, f"{step_id}_QA")
        except Exception as exc:
            return _err(str(exc))

    parse_failures = _parse_failures(qa_payload)
    if not partition_ids:
        parse_partitions = [row["partition_id"] for row in parse_failures if row["partition_id"]]
        if parse_partitions:
            partition_ids = sorted(set(parse_partitions))
        else:
            partition_ids = _fallback_partition_ids_from_raw(raw_dir, step_id)

    expected_raw_paths = [raw_dir / f"{step_id}__{partition_id}.json" for partition_id in partition_ids]
    expected_existing = [path for path in expected_raw_paths if path.exists()]
    if not expected_existing:
        expected_existing = sorted(
            p for p in raw_dir.glob(f"{step_id}__*.json") if p.is_file() and not p.name.endswith(".FAILED.json")
        )

    search_matches, search_mode = _search_raw_matches(search_root, step_id, partition_ids)

    _print_section_header("RUN_SANITY")
    print(f"rid={run_id}")
    print(f"repo_root={repo_root}")
    print(f"run_root={run_root}")
    print(f"phase={phase}")
    print(f"phase_dir={phase_dir}")
    print(f"search_root={search_root}")
    print(f"valid_phases={','.join(phases)}")
    _print_list("detected_phase_dir", _detect_phase_like_dirs(run_root, phase_dir_names))
    inputs_files = _iter_files(inputs_dir)
    raw_files = _iter_files(raw_dir)
    norm_files = _iter_files(norm_dir)
    qa_files = _iter_files(qa_dir)
    raw_ok_count = sum(
        1 for path in raw_files if path.suffix == ".json" and not path.name.endswith(".FAILED.json")
    )
    raw_failed_count = sum(
        1 for path in raw_files if path.name.endswith(".FAILED.txt") or path.name.endswith(".FAILED.json")
    )
    norm_json_count = sum(1 for path in norm_files if path.suffix == ".json")
    print(f"inputs_exists={_bool_str(inputs_dir.exists())}")
    print(f"inputs_file_count={len(inputs_files)}")
    print(f"raw_exists={_bool_str(raw_dir.exists())}")
    print(f"raw_total_file_count={len(raw_files)}")
    print(f"raw_ok_json_count={raw_ok_count}")
    print(f"raw_failed_sidecar_count={raw_failed_count}")
    print(f"norm_exists={_bool_str(norm_dir.exists())}")
    print(f"norm_json_count={norm_json_count}")
    print(f"qa_exists={_bool_str(qa_dir.exists())}")
    print(f"qa_file_count={len(qa_files)}")
    print()

    _print_section_header("STEP_DECLARED_OUTPUTS")
    print(f"selected_step={step_id}")
    print(f"step_found_in_prompt_specs={_bool_str(step_in_prompts)}")
    if not step_in_prompts:
        print(f"note=step_not_found_in_prompt_specs_for_phase_{phase}")
    _print_list("expected_artifact", expected_artifacts)
    _print_list("phase_prompt_step", sorted(prompt_steps))
    print()

    _print_section_header("STEP_QA_SUMMARY")
    print(f"qa_file={qa_path}")
    print(f"qa_file_exists={_bool_str(not qa_missing)}")
    if qa_missing:
        print("qa_status=QA file missing")
    else:
        print(f"raw_ok={int(qa_payload.get('raw_ok', 0) or 0)}")
        print(f"raw_failed={int(qa_payload.get('raw_failed', 0) or 0)}")
        print(f"partitions_total={int(qa_payload.get('partitions_total', 0) or 0)}")
        missing_expected = qa_payload.get("missing_expected_artifacts")
        if isinstance(missing_expected, list):
            _print_list("missing_expected_artifact", sorted(str(x) for x in missing_expected))
        else:
            print("missing_expected_artifact=-")
        print(f"parse_failures_total={len(parse_failures)}")
    print()

    _print_section_header("PARSE_FAILURE_DETAILS")
    print(f"parse_failures_total={len(parse_failures)}")
    if not parse_failures:
        print("parse_failure=-")
    else:
        rows_to_print = parse_failures
        if len(parse_failures) > 25:
            rows_to_print = parse_failures[: args.max_failures]
            reason_hist = Counter(row["reason"] for row in parse_failures)
            for reason in sorted(reason_hist):
                print(f"parse_failure_reason_count[{reason}]={reason_hist[reason]}")
        for row in rows_to_print:
            partition_id = row.get("partition_id", "")
            expected_raw = raw_dir / f"{step_id}__{partition_id}.json" if partition_id else "-"
            print(
                "parse_failure="
                f"partition_id={partition_id or '-'} "
                f"reason={row.get('reason') or '-'} "
                f"qa_reported_file={row.get('qa_reported_file') or '-'} "
                f"expected_raw_path={expected_raw}"
            )
    print()

    _print_section_header("GLOBAL_RAW_SEARCH")
    print(f"search_mode={search_mode}")
    print(f"search_match_count={len(search_matches)}")
    for match in search_matches[:20]:
        print(f"search_match={_to_rel(match, search_root)}")
    if len(search_matches) > 20:
        print(f"search_match_truncated={len(search_matches) - 20}")
    print()

    _print_section_header("PARTITION_MATRIX")
    matrix_ids = sorted(partition_ids)[: args.max_partitions]
    print(f"partition_matrix_count={len(matrix_ids)}")
    if not matrix_ids:
        print("partition_matrix=-")
    for partition_id in matrix_ids:
        expected_raw = raw_dir / f"{step_id}__{partition_id}.json"
        failed_txt = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        trace_md = raw_dir / f"{step_id}__{partition_id}.TRACE.md"
        print(
            "partition="
            f"id={partition_id} "
            f"expected_raw={expected_raw} "
            f"raw_exists={_bool_str(expected_raw.exists())} "
            f"failed_txt_exists={_bool_str(failed_txt.exists())} "
            f"trace_exists={_bool_str(trace_md.exists())}"
        )
    print()

    _print_section_header("RAW_SAMPLE")
    sample_path: Optional[Path] = None
    if expected_existing:
        sample_path = sorted(expected_existing, key=lambda p: str(p))[0]
        print("sample_source=expected_raw")
    elif search_matches:
        sample_path = search_matches[0]
        print("sample_source=global_search")
    else:
        print("sample_source=-")
    if sample_path is None:
        print("sample_path=-")
        print("artifacts_count=-")
        print("failure_type=-")
        print("provider_signature=-")
    else:
        print(f"sample_path={sample_path}")
        try:
            sample_payload = _load_json_required(sample_path, "raw sample")
            artifacts = sample_payload.get("artifacts")
            artifacts_count = len(artifacts) if isinstance(artifacts, list) else 0
            request_meta = sample_payload.get("request_meta")
            failure_type = request_meta.get("failure_type") if isinstance(request_meta, dict) else None
            provider_signature = request_meta.get("provider_signature") if isinstance(request_meta, dict) else None
            print(f"artifacts_count={artifacts_count}")
            print(f"failure_type={failure_type or '-'}")
            print(f"provider_signature={provider_signature or '-'}")
        except Exception as exc:
            print(f"sample_error={type(exc).__name__}:{exc}")
    print()

    _print_section_header("COVERAGE_POINTERS")
    coverage_rollup = run_root / "COVERAGE_ROLLUP.json"
    coverage_report = run_root / "COVERAGE_REPORT.json"
    for label, path in [("COVERAGE_ROLLUP", coverage_rollup), ("COVERAGE_REPORT", coverage_report)]:
        print(f"{label}_exists={_bool_str(path.exists())}")
        if not path.exists():
            continue
        print(f"{label}_path={path}")
        print(f"{label}_mtime_utc={_utc_mtime(path)}")
        try:
            payload = _load_json_required(path, label)
        except Exception as exc:
            print(f"{label}_summary=parse_error:{type(exc).__name__}:{exc}")
            continue
        if label == "COVERAGE_REPORT":
            phase_payload = payload.get("phases", {}).get(phase, {})
            if isinstance(phase_payload, dict):
                attempted = phase_payload.get("partitions_attempted")
                ok = phase_payload.get("partitions_ok")
                failed = phase_payload.get("partitions_failed")
                print(f"{label}_phase_attempted={attempted if attempted is not None else '-'}")
                print(f"{label}_phase_ok={ok if ok is not None else '-'}")
                print(f"{label}_phase_failed={failed if failed is not None else '-'}")
            else:
                print(f"{label}_phase_summary=-")
        else:
            phase_payload = payload.get("phases", {}).get(phase, {})
            if isinstance(phase_payload, dict):
                counts = phase_payload.get("counts", {})
                ok = counts.get("ok") if isinstance(counts, dict) else None
                failed = counts.get("failed") if isinstance(counts, dict) else None
                skipped = counts.get("skipped") if isinstance(counts, dict) else None
                print(f"{label}_phase_ok={ok if ok is not None else '-'}")
                print(f"{label}_phase_failed={failed if failed is not None else '-'}")
                print(f"{label}_phase_skipped={skipped if skipped is not None else '-'}")
            else:
                print(f"{label}_run_status={payload.get('run_status') or '-'}")
    print()

    if expected_existing:
        truth_state = "RAW_EXPECTED_PRESENT"
    elif search_matches:
        truth_state = "RAW_FOUND_ELSEWHERE"
    else:
        truth_state = "RAW_NOT_FOUND_ANYWHERE"

    _print_section_header("TRUTH_STATE")
    print(f"TRUTH_STATE={truth_state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
