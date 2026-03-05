#!/usr/bin/env python3
"""Repo Truth Extractor v4 runner.

This runner keeps v5 execution intact and enforces v4 prompt/artifact contracts by:
- loading v4 prompt/artifact manifests from services/repo-truth-extractor/promptsets/v4/
- executing v5 for supported phases
- rebuilding deterministic v4 norm outputs under extraction/repo-truth-extractor/v4/runs/<run_id>/
- preserving per-step normalized outputs in norm/by_step/<STEP_ID>/
- promoting only canonical-writer artifacts to phase norm root
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import typer
import yaml

APP = typer.Typer(help="Repo Truth Extractor v4 runner")

SERVICE_ROOT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
PROMPTSET_PATH = SERVICE_ROOT / "promptsets" / "v4" / "promptset.yaml"
ARTIFACTS_PATH = SERVICE_ROOT / "promptsets" / "v4" / "artifacts.yaml"
V4_PROMPT_ROOT = SERVICE_ROOT / "promptsets" / "v4" / "prompts"
V3_RUNNER = SERVICE_ROOT / "run_extraction_v5.py"
SERVICES_REGISTRY = ROOT / "services" / "registry.yaml"
V3_RUNS_ROOT = ROOT / "extraction" / "repo-truth-extractor" / "v3" / "runs"
V4_RUNS_ROOT = ROOT / "extraction" / "repo-truth-extractor" / "v4" / "runs"
V4_DOCTOR_ROOT = ROOT / "extraction" / "repo-truth-extractor" / "v4" / "doctor"
V3_DOCTOR_ROOT = ROOT / "extraction" / "repo-truth-extractor" / "v3" / "doctor"
V4_LATEST_FILE = ROOT / "extraction" / "repo-truth-extractor" / "v4" / "latest_run_id.txt"

PHASE_DIR_NAMES: Dict[str, str] = {
    "A": "A_repo_control_plane",
    "H": "H_home_control_plane",
    "D": "D_docs_pipeline",
    "C": "C_code_surfaces",
    "E": "E_execution_plane",
    "W": "W_workflow_plane",
    "B": "B_boundary_plane",
    "G": "G_governance_plane",
    "Q": "Q_quality_assurance",
    "R": "R_arbitration",
    "X": "X_feature_index",
    "T": "T_task_packets",
    "Z": "Z_handoff_freeze",
    "M": "M_runtime_exports",
    "S": "S_synthesis_trace",
}

SUPPORTED_V3_PHASES = {"A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S"}
SUPPORTED_V3_SPECIAL_PHASES = {"S_INT"}
STEP_ID_RE = re.compile(r"^([A-Z])(\d+)$")
RAW_STEP_FILE_RE = re.compile(r"^(?P<step>[A-Z]\d+)__(?P<partition>.+)\.json$")
ARTIFACT_NAME_RE = re.compile(r"\b[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)\b")
DEFAULT_ROUTING_POLICY = "cost"
ENV_TOKEN_RE = re.compile(r"\$\{([^}]+)\}")


@dataclass(frozen=True)
class ArtifactRule:
    phase: str
    artifact_name: str
    canonical_writer_step_id: str
    kind: str
    norm_artifact: bool
    allow_timestamp_keys: bool
    merge_strategy: str
    required_fields: Tuple[str, ...]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def read_yaml(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not decode to object")
    return payload


def load_promptset() -> Dict[str, Any]:
    return read_yaml(PROMPTSET_PATH)


def load_artifacts() -> Tuple[Dict[Tuple[str, str], ArtifactRule], List[str]]:
    payload = read_yaml(ARTIFACTS_PATH)
    forbidden = [str(v) for v in payload.get("forbidden_norm_keys", []) if isinstance(v, str)]
    rules: Dict[Tuple[str, str], ArtifactRule] = {}
    for row in payload.get("artifacts", []):
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase", "")).strip()
        name = str(row.get("artifact_name", "")).strip()
        if not phase or not name:
            continue
        rules[(phase, name)] = ArtifactRule(
            phase=phase,
            artifact_name=name,
            canonical_writer_step_id=str(row.get("canonical_writer_step_id", "")).strip(),
            kind=str(row.get("kind", "json_item_list")).strip(),
            norm_artifact=bool(row.get("norm_artifact", True)),
            allow_timestamp_keys=bool(row.get("allow_timestamp_keys", False)),
            merge_strategy=str(row.get("merge_strategy", "itemlist_by_id")).strip(),
            required_fields=tuple(str(x) for x in row.get("required_fields", []) if isinstance(x, str)),
        )
    return rules, forbidden


def numeric_step_sort_key(step_id: str) -> Tuple[str, int]:
    match = STEP_ID_RE.match(step_id)
    if not match:
        return (step_id[:1], 999999)
    return (match.group(1), int(match.group(2)))


def phase_steps(promptset: Dict[str, Any], phase: str) -> List[Dict[str, Any]]:
    phase_payload = promptset.get("phases", {}).get(phase, {})
    steps = list(phase_payload.get("steps", []))
    return sorted(steps, key=lambda row: numeric_step_sort_key(str(row.get("step_id", ""))))


def expected_phase_order(promptset: Dict[str, Any]) -> List[str]:
    default = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
    values = promptset.get("all_phase_order")
    if isinstance(values, list) and values:
        return [str(v) for v in values]
    return default


def run_promptset_audit(strict: bool = True) -> Dict[str, Any]:
    audit_script = ROOT / "scripts" / "repo_truth_extractor_promptset_audit_v4.py"
    cmd = [sys.executable, str(audit_script), "--repo-root", str(ROOT)]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError("v4 promptset audit failed")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return {"status": "PASS"}


def build_v3_cmd(
    *,
    phase: Optional[str],
    run_id: Optional[str],
    dry_run: bool,
    resume: bool,
    partition_workers: int,
    executor: str,
    doctor: bool,
    doctor_auto_reprocess: bool,
    doctor_reprocess_dry_run: bool,
    doctor_reprocess_phases: str,
    status: bool,
    status_json: bool,
    doctor_auth: bool,
    preflight_providers: bool,
    coverage_report: bool,
    routing_policy: str,
    disable_escalation: bool,
    escalation_max_hops: int,
    batch_mode: bool,
    batch_provider: str,
    batch_poll_seconds: int,
    batch_wait_timeout_seconds: int,
    batch_max_requests_per_job: int,
    step: Optional[str] = None,
    s_prompts: Optional[str] = None,
    s_steps: Optional[str] = None,
    d0_max_files: Optional[int] = None,
    d1_max_files: Optional[int] = None,
    ui: str,
    pretty: bool,
    quiet: bool,
    jsonl_events: bool,
) -> List[str]:
    cmd = [sys.executable, str(V3_RUNNER)]
    if phase:
        cmd.extend(["--phase", phase])
    if run_id:
        cmd.extend(["--run-id", run_id])
    if dry_run:
        cmd.append("--dry-run")
    if resume:
        cmd.append("--resume")
    if partition_workers > 0:
        cmd.extend(["--partition-workers", str(partition_workers)])
    if executor.strip():
        cmd.extend(["--executor", executor.strip()])
    cmd.extend(["--routing-policy", routing_policy])
    if step and step.strip():
        cmd.extend(["--step", step.strip()])
    if s_prompts and s_prompts.strip():
        cmd.extend(["--s-prompts", s_prompts.strip()])
    if s_steps and s_steps.strip():
        cmd.extend(["--s-steps", s_steps.strip()])
    if d0_max_files is not None:
        cmd.extend(["--d0-max-files", str(int(d0_max_files))])
    if d1_max_files is not None:
        cmd.extend(["--d1-max-files", str(int(d1_max_files))])
    if disable_escalation:
        cmd.append("--disable-escalation")
    cmd.extend(["--escalation-max-hops", str(max(0, int(escalation_max_hops)))])
    if batch_mode:
        cmd.append("--batch-mode")
    cmd.extend(["--batch-provider", batch_provider])
    cmd.extend(["--batch-poll-seconds", str(max(1, int(batch_poll_seconds)))])
    cmd.extend(["--batch-wait-timeout-seconds", str(max(60, int(batch_wait_timeout_seconds)))])
    cmd.extend(["--batch-max-requests-per-job", str(max(1, int(batch_max_requests_per_job)))])
    cmd.extend(["--ui", ui])
    if pretty:
        cmd.append("--pretty")
    if quiet:
        cmd.append("--quiet")
    if jsonl_events:
        cmd.append("--jsonl-events")
    if doctor:
        cmd.append("--doctor")
    if doctor_auto_reprocess:
        cmd.append("--doctor-auto-reprocess")
    if doctor_reprocess_dry_run:
        cmd.append("--doctor-reprocess-dry-run")
    if doctor_reprocess_phases.strip():
        cmd.extend(["--doctor-reprocess-phases", doctor_reprocess_phases.strip()])
    if status:
        cmd.append("--status")
    if status_json:
        cmd.append("--status-json")
    if doctor_auth:
        cmd.append("--doctor-auth")
    if preflight_providers:
        cmd.append("--preflight-providers")
    if coverage_report:
        cmd.append("--coverage-report")
    return cmd


def call_v3_runner(cmd: Sequence[str], *, prompt_root: Optional[Path] = None) -> int:
    env = os.environ.copy()
    if prompt_root is not None:
        prompt_root_value = str(prompt_root.resolve())
        env["REPO_TRUTH_EXTRACTOR_PROMPT_ROOT"] = prompt_root_value
        env["UPGRADES_PROMPT_ROOT"] = prompt_root_value
    proc = subprocess.run(list(cmd), cwd=Path.cwd(), env=env)
    return proc.returncode


def _path_is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def verify_resume_proof_prompt_paths(run_id: str, prompt_root: Path) -> None:
    resume_proof_path = V3_RUNS_ROOT / run_id / "RESUME_PROOF.json"
    payload = read_json(resume_proof_path)
    if not isinstance(payload, dict):
        return
    prompt_hashes = payload.get("prompt_hashes")
    candidate_paths: List[str] = []
    if isinstance(prompt_hashes, dict):
        candidate_paths = [value for value in prompt_hashes.keys() if isinstance(value, str)]
    elif isinstance(prompt_hashes, list):
        candidate_paths = [
            str(row.get("path", "")).strip()
            for row in prompt_hashes
            if isinstance(row, dict) and str(row.get("path", "")).strip()
        ]
    if not candidate_paths:
        return
    invalid_paths: List[str] = []
    for raw_path in candidate_paths:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = (ROOT / candidate).resolve()
        if not _path_is_within(candidate, prompt_root):
            invalid_paths.append(str(candidate))
    if invalid_paths:
        preview = ", ".join(sorted(invalid_paths)[:5])
        raise RuntimeError(
            "v4 prompt routing verification failed: RESUME_PROOF prompt hashes reference non-v4 prompts "
            f"(examples: {preview})"
        )


def read_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return path.as_posix()


_LINE_CACHE: Dict[str, List[str]] = {}


def file_lines(path: Path) -> List[str]:
    key = str(path.resolve())
    if key in _LINE_CACHE:
        return _LINE_CACHE[key]
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        lines = []
    _LINE_CACHE[key] = lines
    return lines


def find_line_excerpt(path: Path, needle: str) -> Tuple[int, str]:
    token = needle.strip()
    if not token:
        return (1, "")
    for line_no, line in enumerate(file_lines(path), start=1):
        if token in line:
            return (line_no, line.strip()[:200])
    return (1, token[:200])


def evidence_for(path: Path, needle: str, fallback_excerpt: str = "") -> Dict[str, Any]:
    line_no, excerpt = find_line_excerpt(path, needle)
    excerpt_value = (excerpt or fallback_excerpt or needle).strip()[:200]
    return {
        "path": repo_relative(path),
        "line_range": [line_no, line_no],
        "excerpt": excerpt_value,
    }


def strip_forbidden_keys(payload: Any, forbidden: Sequence[str]) -> Any:
    forbidden_set = set(forbidden)
    if isinstance(payload, dict):
        out: Dict[str, Any] = {}
        for key in sorted(payload.keys()):
            if key in forbidden_set:
                continue
            out[key] = strip_forbidden_keys(payload[key], forbidden)
        return out
    if isinstance(payload, list):
        return [strip_forbidden_keys(item, forbidden) for item in payload]
    return payload


def stable_item_key(item: Dict[str, Any]) -> Tuple[str, str, str]:
    path = str(item.get("path", ""))
    line_range = item.get("line_range")
    if isinstance(line_range, list) and line_range:
        line = str(line_range[0])
    else:
        line = "0"
    item_id = str(item.get("id", ""))
    return (path, line, item_id)


def normalize_evidence(entries: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(entries, list):
        return out
    seen = set()
    for row in entries:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path", "")).strip()
        line_range = row.get("line_range")
        excerpt = str(row.get("excerpt", "")).strip()
        if not path:
            continue
        if not (isinstance(line_range, list) and len(line_range) == 2):
            line_range = [1, 1]
        key = (path, int(line_range[0]), int(line_range[1]), excerpt)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "excerpt": excerpt[:200],
                "line_range": [int(line_range[0]), int(line_range[1])],
                "path": path,
            }
        )
    out.sort(key=lambda r: (r["path"], r["line_range"][0], r["line_range"][1], r["excerpt"]))
    return out


def merge_scalar(current: Any, incoming: Any) -> Any:
    if current in ("", None, [], {}):
        return incoming
    if incoming in ("", None, [], {}):
        return current
    left = json.dumps(current, sort_keys=True, ensure_ascii=True)
    right = json.dumps(incoming, sort_keys=True, ensure_ascii=True)
    return current if left <= right else incoming


def merge_item_objects(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in incoming.items():
        if key == "evidence":
            out["evidence"] = normalize_evidence(list(out.get("evidence", [])) + list(value if isinstance(value, list) else []))
            continue
        current = out.get(key)
        if isinstance(current, list) and isinstance(value, list):
            merged = current + value
            dedup = sorted(
                {
                    json.dumps(v, sort_keys=True, ensure_ascii=True): v
                    for v in merged
                }.values(),
                key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=True),
            )
            out[key] = dedup
            continue
        if isinstance(current, dict) and isinstance(value, dict):
            out[key] = merge_item_objects(current, value)
            continue
        out[key] = merge_scalar(current, value)
    return out


def merge_item_list_payloads(payloads: List[Any], merge_key: str = "id") -> Dict[str, Any]:
    merged_by_id: Dict[str, Dict[str, Any]] = {}
    conflicts: List[Dict[str, Any]] = []
    for payload in payloads:
        rows = payload if isinstance(payload, list) else payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            rid = str(row.get(merge_key, "")).strip()
            if not rid:
                rid = "sha256:" + hashlib.sha256(
                    json.dumps(row, sort_keys=True, ensure_ascii=True).encode("utf-8")
                ).hexdigest()
            if rid in merged_by_id:
                before = json.dumps(merged_by_id[rid], sort_keys=True, ensure_ascii=True)
                merged_by_id[rid] = merge_item_objects(merged_by_id[rid], row)
                after = json.dumps(merged_by_id[rid], sort_keys=True, ensure_ascii=True)
                if before != after:
                    conflicts.append({"id": rid, "conflict": "merged_duplicate"})
            else:
                merged_by_id[rid] = dict(row)
    items = sorted(merged_by_id.values(), key=stable_item_key)
    return {"items": items, "_merge_conflicts": conflicts}


def merge_payloads(payloads: List[Any], rule: ArtifactRule) -> Tuple[Any, List[Dict[str, Any]]]:
    if not payloads:
        return {"items": []}, []
    if len(payloads) == 1:
        only = payloads[0]
        if isinstance(only, dict):
            return only, []
        if isinstance(only, list):
            return {"items": only}, []
        return {"items": [only]}, []
    if rule.merge_strategy in {"itemlist_by_service_id", "itemlist_by_id"}:
        key = "service_id" if rule.merge_strategy == "itemlist_by_service_id" else "id"
        merged = merge_item_list_payloads(payloads, merge_key=key)
        conflicts = list(merged.pop("_merge_conflicts", []))
        return merged, conflicts
    # fallback deterministic merge
    return merge_item_list_payloads(payloads), []


def parse_raw_artifacts(raw_payload: Any, expected_outputs: Sequence[str]) -> List[Tuple[str, Any]]:
    expected = set(expected_outputs)
    out: List[Tuple[str, Any]] = []
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("artifacts"), list):
        for row in raw_payload["artifacts"]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("artifact_name", "")).strip()
            if name in expected:
                out.append((name, row.get("payload")))
        if out:
            return out
    if isinstance(raw_payload, dict):
        for name in expected_outputs:
            if name in raw_payload:
                out.append((name, raw_payload[name]))
    return out


def extract_step_partition_payloads(raw_dir: Path, step_id: str, expected_outputs: Sequence[str]) -> Dict[str, List[Tuple[str, Any]]]:
    buckets: Dict[str, List[Tuple[str, Any]]] = {name: [] for name in expected_outputs}
    pattern = f"{step_id}__*.json"
    for raw_file in sorted(raw_dir.glob(pattern)):
        match = RAW_STEP_FILE_RE.match(raw_file.name)
        if not match:
            continue
        partition = match.group("partition")
        parsed = read_json(raw_file)
        if parsed is None:
            continue
        for artifact_name, payload in parse_raw_artifacts(parsed, expected_outputs):
            buckets.setdefault(artifact_name, []).append((partition, payload))
    return buckets


def ensure_phase_dirs(dst_phase_dir: Path) -> None:
    ensure_dir(dst_phase_dir / "inputs")
    ensure_dir(dst_phase_dir / "raw")
    ensure_dir(dst_phase_dir / "qa")
    ensure_dir(dst_phase_dir / "norm")
    ensure_dir(dst_phase_dir / "norm" / "by_step")


def copy_phase_inputs_raw(src_phase_dir: Path, dst_phase_dir: Path) -> None:
    ensure_phase_dirs(dst_phase_dir)
    for bucket in ("inputs", "raw"):
        src = src_phase_dir / bucket
        dst = dst_phase_dir / bucket
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)


from lib.service_catalog import build_service_catalog


def build_service_coverage_payload(service_catalog: Dict[str, Any]) -> Dict[str, Any]:
    registry = read_yaml(SERVICES_REGISTRY)
    expected_services = sorted(
        str(row.get("name", "")).strip()
        for row in registry.get("services", [])
        if isinstance(row, dict) and str(row.get("name", "")).strip()
    )
    expected_set = set(expected_services)
    rows = service_catalog.get("items", []) if isinstance(service_catalog, dict) else []
    observed = [str(row.get("service_id", "")).strip() for row in rows if isinstance(row, dict)]
    observed_set = set(v for v in observed if v)
    duplicates = sorted({sid for sid in observed if sid and observed.count(sid) > 1})
    missing = sorted(expected_set - observed_set)
    required_fields = [
        "service_id",
        "category",
        "description",
        "ports",
        "health",
        "repo_locations",
        "entrypoints",
        "interfaces",
        "dependencies",
        "config",
    ]
    missing_fields: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("service_id", "")).strip()
        absent: List[str] = []
        for field in required_fields:
            if field not in row:
                absent.append(field)
                continue
            value = row.get(field)
            if value is None:
                absent.append(field)
                continue
            if field in {"service_id", "category", "description"} and not str(value).strip():
                absent.append(field)
        if absent:
            missing_fields.append({"service_id": sid, "missing_fields": absent})
    status = "PASS" if not missing and not duplicates and not missing_fields else "FAIL"
    return {
        "generated_at": now_iso(),
        "required_fields": required_fields,
        "service_count_expected": len(expected_services),
        "service_count_observed": len(observed_set),
        "status": status,
        "missing_services": missing,
        "duplicate_services": duplicates,
        "missing_required_fields": missing_fields,
    }


def sync_phase_from_v3(
    *,
    run_id: str,
    phase: str,
    promptset: Dict[str, Any],
    artifact_rules: Dict[Tuple[str, str], ArtifactRule],
    forbidden_norm_keys: Sequence[str],
) -> None:
    if phase not in PHASE_DIR_NAMES:
        return
    src_phase_dir = V3_RUNS_ROOT / run_id / PHASE_DIR_NAMES[phase]
    dst_phase_dir = V4_RUNS_ROOT / run_id / PHASE_DIR_NAMES[phase]
    ensure_phase_dirs(dst_phase_dir)
    if src_phase_dir.exists():
        copy_phase_inputs_raw(src_phase_dir, dst_phase_dir)

    raw_dir = dst_phase_dir / "raw"
    steps = phase_steps(promptset, phase)
    phase_collisions: List[Dict[str, Any]] = []
    canonical_index: List[Dict[str, Any]] = []
    producer_map: Dict[str, List[str]] = {}
    merge_conflicts: Dict[str, List[Dict[str, Any]]] = {}

    for step in steps:
        step_id = str(step.get("step_id", "")).strip()
        outputs = list(step.get("outputs", []))
        for artifact_name in outputs:
            producer_map.setdefault(artifact_name, []).append(step_id)
        by_step_dir = dst_phase_dir / "norm" / "by_step" / step_id
        ensure_dir(by_step_dir)

        buckets = extract_step_partition_payloads(raw_dir, step_id, outputs)
        for artifact_name in outputs:
            values = buckets.get(artifact_name, [])
            rule = artifact_rules.get(
                (phase, artifact_name),
                ArtifactRule(
                    phase=phase,
                    artifact_name=artifact_name,
                    canonical_writer_step_id=step_id,
                    kind="json_item_list",
                    norm_artifact=True,
                    allow_timestamp_keys=False,
                    merge_strategy="itemlist_by_id",
                    required_fields=tuple(),
                ),
            )
            if ".partX." in artifact_name:
                for idx, (_partition_id, payload) in enumerate(values, start=1):
                    part_name = artifact_name.replace(".partX.", f".part{idx:04d}.")
                    out_payload = strip_forbidden_keys(payload, forbidden_norm_keys) if rule.norm_artifact else payload
                    if part_name.endswith(".json"):
                        if isinstance(out_payload, list):
                            out_payload = {"items": out_payload}
                        if not isinstance(out_payload, dict):
                            out_payload = {"items": [out_payload]}
                        write_json(by_step_dir / part_name, out_payload)
                    else:
                        ensure_dir((by_step_dir / part_name).parent)
                        text = out_payload if isinstance(out_payload, str) else json.dumps(out_payload, indent=2, sort_keys=True)
                        (by_step_dir / part_name).write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")
                continue

            payloads = [payload for _partition_id, payload in values]
            merged, conflicts = merge_payloads(payloads, rule)
            if conflicts:
                merge_conflicts[artifact_name] = conflicts
            if rule.norm_artifact and not rule.allow_timestamp_keys:
                merged = strip_forbidden_keys(merged, forbidden_norm_keys)
            if artifact_name.endswith(".json"):
                write_json(by_step_dir / artifact_name, merged)
            else:
                text = merged if isinstance(merged, str) else json.dumps(merged, indent=2, sort_keys=True)
                (by_step_dir / artifact_name).write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")

    # v4-specific enrichment: build all-services deep catalog deterministically.
    if phase == "C":
        c10_dir = dst_phase_dir / "norm" / "by_step" / "C10"
        c9_dir = dst_phase_dir / "norm" / "by_step" / "C9"
        ensure_dir(c10_dir)
        ensure_dir(c9_dir)
        service_catalog = build_service_catalog()
        write_json(c10_dir / "SERVICE_CATALOG.part0001.json", service_catalog)
        write_json(c9_dir / "SERVICE_CATALOG.json", service_catalog)

    # Promote canonical artifacts.
    for artifact_name, _producers in sorted(producer_map.items()):
        rule = artifact_rules.get((phase, artifact_name))
        if rule is None:
            continue
        if ".partX." in artifact_name:
            continue
        canonical_step = rule.canonical_writer_step_id
        canonical_path = dst_phase_dir / "norm" / "by_step" / canonical_step / artifact_name
        if canonical_path.exists():
            promoted_path = dst_phase_dir / "norm" / artifact_name
            ensure_dir(promoted_path.parent)
            shutil.copy2(canonical_path, promoted_path)
            canonical_index.append(
                {
                    "artifact_name": artifact_name,
                    "canonical_step": canonical_step,
                    "sha256": hashlib.sha256(promoted_path.read_bytes()).hexdigest(),
                }
            )
        # by_step can legitimately contain multiple producers; policy violation
        # would be a non-canonical write to phase norm root, which this runner
        # never performs. Keep collision ledger for explicit violations only.

    write_json(
        dst_phase_dir / "qa" / f"PHASE_{phase}_CANONICAL_INDEX.json",
        {
            "generated_at": now_iso(),
            "phase": phase,
            "canonical_index": canonical_index,
        },
    )
    write_json(
        dst_phase_dir / "qa" / f"PHASE_{phase}_COLLISIONS.json",
        {
            "generated_at": now_iso(),
            "phase": phase,
            "status": "FAIL" if phase_collisions else "PASS",
            "collisions": phase_collisions,
        },
    )
    for artifact_name, conflicts in merge_conflicts.items():
        write_json(
            dst_phase_dir / "qa" / f"{artifact_name}.MERGE_CONFLICTS.json",
            {"generated_at": now_iso(), "artifact_name": artifact_name, "conflicts": conflicts},
        )


def sync_service_coverage(run_id: str) -> None:
    c_phase = V4_RUNS_ROOT / run_id / PHASE_DIR_NAMES["C"]
    q_phase = V4_RUNS_ROOT / run_id / PHASE_DIR_NAMES["Q"]
    catalog_path = c_phase / "norm" / "SERVICE_CATALOG.json"
    if not catalog_path.exists():
        return
    payload = read_json(catalog_path)
    if not isinstance(payload, dict):
        return
    qa = build_service_coverage_payload(payload)
    ensure_phase_dirs(q_phase)
    write_json(q_phase / "qa" / "QA_SERVICE_COVERAGE.json", qa)
    q9_dir = q_phase / "norm" / "by_step" / "Q9"
    ensure_dir(q9_dir)
    write_json(q9_dir / "QA_SERVICE_COVERAGE.json", qa)


def mirror_doctor_outputs() -> None:
    if not V3_DOCTOR_ROOT.exists():
        return
    ensure_dir(V4_DOCTOR_ROOT)
    for file in sorted(V3_DOCTOR_ROOT.glob("*")):
        if file.is_file():
            shutil.copy2(file, V4_DOCTOR_ROOT / file.name)


def latest_v4_run_id() -> Optional[str]:
    if V4_LATEST_FILE.exists():
        value = V4_LATEST_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    if not V4_RUNS_ROOT.exists():
        return None
    candidates = [path for path in V4_RUNS_ROOT.iterdir() if path.is_dir()]
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0].name


def _count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for candidate in path.rglob(pattern) if candidate.is_file())


def build_v4_status_payload(run_id: str) -> Dict[str, Any]:
    promptset = load_promptset()
    run_dir = V4_RUNS_ROOT / run_id
    phase_status: Dict[str, Any] = {}
    summary = {"NOT_STARTED": 0, "IN_PROGRESS": 0, "PASS": 0, "FAIL": 0}

    for phase in expected_phase_order(promptset):
        phase_dir = run_dir / PHASE_DIR_NAMES[phase]
        inputs_count = _count_files(phase_dir / "inputs")
        raw_total = _count_files(phase_dir / "raw", "*.json")
        raw_failed_sidecars = _count_files(phase_dir / "raw", "*.FAILED.txt")
        norm_count = _count_files(phase_dir / "norm", "*.json")
        qa_count = _count_files(phase_dir / "qa")
        last_modified = (
            datetime.fromtimestamp(phase_dir.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
            if phase_dir.exists()
            else None
        )

        issues: List[str] = []
        if not phase_dir.exists():
            status = "NOT_STARTED"
            issues.append("phase directory missing.")
        elif raw_total == 0 and norm_count == 0 and qa_count == 0:
            status = "NOT_STARTED"
            issues.append("phase has no raw/norm/qa artifacts.")
        elif raw_failed_sidecars > 0:
            status = "FAIL"
            issues.append("phase has failed partition sidecars.")
        else:
            status = "PASS"
            collision_file = phase_dir / "qa" / f"PHASE_{phase}_COLLISIONS.json"
            collisions = read_json(collision_file) if collision_file.exists() else None
            if isinstance(collisions, dict) and collisions.get("status") == "FAIL":
                status = "FAIL"
                issues.append("canonical collision policy failed.")

        summary[status] += 1
        phase_status[phase] = {
            "phase": phase,
            "phase_dir": str(phase_dir),
            "phase_dir_exists": phase_dir.exists(),
            "inputs_count": inputs_count,
            "raw_total": raw_total,
            "raw_ok": max(0, raw_total - raw_failed_sidecars),
            "raw_failed_sidecars": raw_failed_sidecars,
            "norm_count": norm_count,
            "qa_count": qa_count,
            "last_modified": last_modified,
            "status": status,
            "issues": issues,
        }

    return {
        "generated_at": now_iso(),
        "pipeline_version": "v4",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "phases": phase_status,
        "summary": summary,
    }


def print_v4_status(payload: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(f"Repo Truth Extractor v4 status :: run_id={payload.get('run_id')}")
    for phase in payload.get("phases", {}).values():
        print(
            " - {phase}: {status} (raw={raw_total}, norm={norm_count}, qa={qa_count})".format(
                phase=phase.get("phase", "?"),
                status=phase.get("status", "UNKNOWN"),
                raw_total=phase.get("raw_total", 0),
                norm_count=phase.get("norm_count", 0),
                qa_count=phase.get("qa_count", 0),
            )
        )
    summary = payload.get("summary", {})
    print(
        "Summary: PASS={PASS} FAIL={FAIL} IN_PROGRESS={IN_PROGRESS} NOT_STARTED={NOT_STARTED}".format(
            PASS=summary.get("PASS", 0),
            FAIL=summary.get("FAIL", 0),
            IN_PROGRESS=summary.get("IN_PROGRESS", 0),
            NOT_STARTED=summary.get("NOT_STARTED", 0),
        )
    )


def write_v4_latest(run_id: str) -> None:
    ensure_dir(V4_LATEST_FILE.parent)
    V4_LATEST_FILE.write_text(run_id + "\n", encoding="utf-8")


def sync_run_to_v4(run_id: str, phases: Sequence[str]) -> None:
    promptset = load_promptset()
    artifact_rules, forbidden_norm_keys = load_artifacts()
    for phase in phases:
        if phase in SUPPORTED_V3_PHASES:
            sync_phase_from_v3(
                run_id=run_id,
                phase=phase,
                promptset=promptset,
                artifact_rules=artifact_rules,
                forbidden_norm_keys=forbidden_norm_keys,
            )
        elif phase in {"M", "S"}:
            dst_phase = V4_RUNS_ROOT / run_id / PHASE_DIR_NAMES[phase]
            ensure_phase_dirs(dst_phase)
            write_json(
                dst_phase / "qa" / f"PHASE_{phase}_STATUS.json",
                {
                    "generated_at": now_iso(),
                    "phase": phase,
                    "status": "SKIPPED",
                    "note": "Optional v4-only phase placeholder",
                },
            )
    sync_service_coverage(run_id)
    write_v4_latest(run_id)


def resolved_run_id(input_run_id: Optional[str]) -> str:
    if input_run_id and input_run_id.strip():
        return input_run_id.strip()
    return datetime.now(timezone.utc).strftime("v4_%Y%m%d_%H%M%S")


def resolved_existing_or_new_run_id(input_run_id: Optional[str]) -> str:
    if input_run_id and input_run_id.strip():
        return input_run_id.strip()
    existing = latest_v4_run_id()
    if existing:
        return existing
    return resolved_run_id(None)


def run_pipeline(
    *,
    phase: Optional[str],
    run_id: str,
    dry_run: bool,
    resume: bool,
    partition_workers: int,
    executor: str,
    doctor: bool,
    doctor_auto_reprocess: bool,
    doctor_reprocess_dry_run: bool,
    doctor_reprocess_phases: str,
    status: bool,
    status_json: bool,
    doctor_auth: bool,
    preflight_providers: bool,
    coverage_report: bool,
    sync: bool,
    routing_policy: str,
    disable_escalation: bool,
    escalation_max_hops: int,
    batch_mode: bool,
    batch_provider: str,
    batch_poll_seconds: int,
    batch_wait_timeout_seconds: int,
    batch_max_requests_per_job: int,
    step: Optional[str] = None,
    s_prompts: Optional[str] = None,
    s_steps: Optional[str] = None,
    d0_max_files: Optional[int] = None,
    d1_max_files: Optional[int] = None,
    ui: str,
    pretty: bool,
    quiet: bool,
    jsonl_events: bool,
) -> int:
    promptset = load_promptset()
    all_phases = expected_phase_order(promptset)
    selected_phases = all_phases if (phase is None or phase == "ALL") else [phase]
    v3_phases = [p for p in selected_phases if p in (SUPPORTED_V3_PHASES | SUPPORTED_V3_SPECIAL_PHASES)]

    if status or status_json:
        if sync and run_id and (V3_RUNS_ROOT / run_id).exists() and not (V4_RUNS_ROOT / run_id).exists():
            sync_run_to_v4(run_id, all_phases)
        payload = build_v4_status_payload(run_id)
        print_v4_status(payload, as_json=status_json)
        return 0

    if v3_phases or doctor or doctor_auth or preflight_providers or coverage_report:
        # v3 accepts only one phase at a time except ALL; use ALL for canonical sweep.
        v3_phase_arg = None
        if phase == "ALL" or phase is None:
            v3_phase_arg = "ALL"
        elif phase in (SUPPORTED_V3_PHASES | SUPPORTED_V3_SPECIAL_PHASES):
            v3_phase_arg = phase
        cmd = build_v3_cmd(
            phase=v3_phase_arg,
            run_id=run_id,
            dry_run=dry_run,
            resume=resume,
            partition_workers=partition_workers,
            executor=executor,
            doctor=doctor,
            doctor_auto_reprocess=doctor_auto_reprocess,
            doctor_reprocess_dry_run=doctor_reprocess_dry_run,
            doctor_reprocess_phases=doctor_reprocess_phases,
            status=False,
            status_json=False,
            doctor_auth=doctor_auth,
            preflight_providers=preflight_providers,
            coverage_report=coverage_report,
            routing_policy=routing_policy,
            disable_escalation=disable_escalation,
            escalation_max_hops=escalation_max_hops,
            batch_mode=batch_mode,
            batch_provider=batch_provider,
            batch_poll_seconds=batch_poll_seconds,
            batch_wait_timeout_seconds=batch_wait_timeout_seconds,
            batch_max_requests_per_job=batch_max_requests_per_job,
            step=step,
            s_prompts=s_prompts,
            s_steps=s_steps,
            d0_max_files=d0_max_files,
            d1_max_files=d1_max_files,
            ui=ui,
            pretty=pretty,
            quiet=quiet,
            jsonl_events=jsonl_events,
        )
        shim_prompt_root = None if any(p in {"S", "S_INT"} for p in selected_phases) else V4_PROMPT_ROOT
        rc = call_v3_runner(cmd, prompt_root=shim_prompt_root)
        if rc != 0:
            return rc
        if not any([doctor, doctor_auth, preflight_providers, coverage_report, status, status_json]) and not any(
            p in {"S", "S_INT"} for p in selected_phases
        ):
            verify_resume_proof_prompt_paths(run_id, V4_PROMPT_ROOT)

    if doctor or doctor_auth or preflight_providers:
        mirror_doctor_outputs()

    sync_phases = [p for p in selected_phases if p != "S_INT"]
    if sync and (sync_phases or phase in {"M"} or phase == "ALL" or phase is None):
        sync_run_to_v4(run_id, sync_phases)
    return 0


@APP.callback(invoke_without_command=True)
def cli(
    phase: Optional[str] = typer.Option(None, "--phase", help="Phase code or ALL"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Run ID"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Dry-run mode"),
    execute: bool = typer.Option(False, "--execute", help="Execute providers (overrides dry-run)"),
    resume: bool = typer.Option(False, "--resume", help="Resume mode"),
    partition_workers: int = typer.Option(1, "--partition-workers"),
    executor: str = typer.Option("thread", "--executor", help="Executor type: thread or process"),
    doctor: bool = typer.Option(False, "--doctor"),
    doctor_auto_reprocess: bool = typer.Option(False, "--doctor-auto-reprocess"),
    doctor_reprocess_dry_run: bool = typer.Option(False, "--doctor-reprocess-dry-run"),
    doctor_reprocess_phases: str = typer.Option("", "--doctor-reprocess-phases"),
    status: bool = typer.Option(False, "--status"),
    status_json: bool = typer.Option(False, "--status-json"),
    doctor_auth: bool = typer.Option(False, "--doctor-auth"),
    preflight_providers: bool = typer.Option(False, "--preflight-providers"),
    coverage_report: bool = typer.Option(False, "--coverage-report"),
    promptset_audit: bool = typer.Option(False, "--promptset-audit"),
    strict_audit: bool = typer.Option(True, "--strict-audit/--no-strict-audit"),
    routing_policy: str = typer.Option(DEFAULT_ROUTING_POLICY, "--routing-policy"),
    step: Optional[str] = typer.Option(None, "--step"),
    s_prompts: Optional[str] = typer.Option(None, "--s-prompts"),
    s_steps: Optional[str] = typer.Option(None, "--s-steps"),
    d0_max_files: Optional[int] = typer.Option(None, "--d0-max-files"),
    d1_max_files: Optional[int] = typer.Option(None, "--d1-max-files"),
    disable_escalation: bool = typer.Option(False, "--disable-escalation"),
    escalation_max_hops: int = typer.Option(2, "--escalation-max-hops"),
    batch_mode: bool = typer.Option(False, "--batch-mode"),
    batch_provider: str = typer.Option("auto", "--batch-provider"),
    batch_poll_seconds: int = typer.Option(30, "--batch-poll-seconds"),
    batch_wait_timeout_seconds: int = typer.Option(86400, "--batch-wait-timeout-seconds"),
    batch_max_requests_per_job: int = typer.Option(2000, "--batch-max-requests-per-job"),
    ui: str = typer.Option("auto", "--ui"),
    pretty: bool = typer.Option(False, "--pretty"),
    quiet: bool = typer.Option(False, "--quiet"),
    jsonl_events: bool = typer.Option(False, "--jsonl-events"),
    sync: bool = typer.Option(
        True,
        "--sync/--no-sync",
        help="Sync v3 run outputs into extraction/repo-truth-extractor/v4",
    ),
) -> None:
    if status or status_json or doctor or doctor_auth or preflight_providers:
        run_id_resolved = resolved_existing_or_new_run_id(run_id)
    else:
        run_id_resolved = resolved_run_id(run_id)
    if execute:
        dry_run = False
    if phase is not None:
        phase = phase.strip().upper()

    # Run promptset lint before mutating operations unless explicitly disabled.
    if promptset_audit or (phase in SUPPORTED_V3_PHASES or phase in {"ALL", "M", None}):
        try:
            run_promptset_audit(strict=strict_audit)
        except RuntimeError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        if promptset_audit and not any(
            [phase, doctor, status, status_json, doctor_auth, preflight_providers, coverage_report]
        ):
            raise typer.Exit(code=0)

    rc = run_pipeline(
        phase=phase,
        run_id=run_id_resolved,
        dry_run=dry_run,
        resume=resume,
        partition_workers=partition_workers,
        executor=executor,
        doctor=doctor,
        doctor_auto_reprocess=doctor_auto_reprocess,
        doctor_reprocess_dry_run=doctor_reprocess_dry_run,
        doctor_reprocess_phases=doctor_reprocess_phases,
        status=status,
        status_json=status_json,
        doctor_auth=doctor_auth,
        preflight_providers=preflight_providers,
        coverage_report=coverage_report,
        sync=sync,
        routing_policy=routing_policy,
        disable_escalation=disable_escalation,
        escalation_max_hops=escalation_max_hops,
        batch_mode=batch_mode,
        batch_provider=batch_provider,
        batch_poll_seconds=batch_poll_seconds,
        batch_wait_timeout_seconds=batch_wait_timeout_seconds,
        batch_max_requests_per_job=batch_max_requests_per_job,
        step=step,
        s_prompts=s_prompts,
        s_steps=s_steps,
        d0_max_files=d0_max_files,
        d1_max_files=d1_max_files,
        ui=ui,
        pretty=pretty,
        quiet=quiet,
        jsonl_events=jsonl_events,
    )
    raise typer.Exit(code=rc)


def main() -> None:
    APP()


if __name__ == "__main__":
    main()
