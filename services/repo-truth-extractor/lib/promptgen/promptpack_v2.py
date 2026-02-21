from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .hashing import sha256_file, sha256_text
from .io import read_json, write_json

PROMPTPACK_V2_FILENAME = "PROMPTPACK.v2.json"
PROMPTPACK_V2_HASH_FILENAME = "PROMPTPACK.v2.sha256.json"
PROMPTPACK_V2_DIRNAME = "PROMPTPACK.v2"
PROMPT_ADJUSTMENTS_FILENAME = "PROMPT_ADJUSTMENTS.json"
PROMPTPACK_DIFF_FILENAME = "PROMPTPACK_DIFF.md"

RULE_SPLIT_STEP_ON_MISSING_ARTIFACTS = "RULE_SPLIT_STEP_ON_MISSING_ARTIFACTS"
RULE_SHRINK_BUDGET_ON_PAYLOAD_UNSHRINKABLE = "RULE_SHRINK_BUDGET_ON_PAYLOAD_UNSHRINKABLE"
RULE_REDUCE_MAX_FILES_ON_PARSE_OR_EMPTY = "RULE_REDUCE_MAX_FILES_ON_PARSE_OR_EMPTY"
RULE_ENABLE_STRICT_ENVELOPE_ON_PARSE = "RULE_ENABLE_STRICT_ENVELOPE_ON_PARSE"
RULE_TARGET_REORDER_ON_THIN_COVERAGE = "RULE_TARGET_REORDER_ON_THIN_COVERAGE"


def _phase_dir_map(run_root: Path) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for entry in sorted(run_root.iterdir()):
        if not entry.is_dir():
            continue
        phase = entry.name.split("_", 1)[0]
        if len(phase) == 1 and phase.isalpha() and phase.isupper():
            out[phase] = entry
    return out


def _load_step_qa(run_root: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    rows: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for phase, phase_dir in _phase_dir_map(run_root).items():
        qa_dir = phase_dir / "qa"
        if not qa_dir.exists():
            continue
        for path in sorted(qa_dir.glob("*_QA.json")):
            payload = read_json(path)
            if not payload:
                continue
            step_id = str(payload.get("step_id") or "")
            if not step_id:
                continue
            rows[(phase, step_id)] = payload
    return rows


def _load_coverage(run_root: Path) -> Dict[str, Any]:
    return read_json(run_root / "COVERAGE_REPORT.json")


def _load_routing(run_root: Path) -> Dict[str, Any]:
    payload = read_json(run_root / "RUN_ROUTING_FINGERPRINT.json")
    phases = payload.get("phases") if isinstance(payload.get("phases"), dict) else {}
    rows: Dict[str, Dict[str, Any]] = {}
    for phase, entries in phases.items():
        if not isinstance(entries, list):
            continue
        for row in entries:
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id") or "")
            if step_id:
                rows[f"{phase}:{step_id}"] = row
    return rows


def _hist_for_phase(coverage: Dict[str, Any], phase: str) -> Dict[str, int]:
    phases = coverage.get("phases") if isinstance(coverage.get("phases"), dict) else {}
    row = phases.get(phase) if isinstance(phases, dict) else None
    hist = row.get("failure_type_histogram") if isinstance(row, dict) and isinstance(row.get("failure_type_histogram"), dict) else {}
    return {str(k): int(v) for k, v in sorted(hist.items())}


def _partitions_ratio(coverage: Dict[str, Any], phase: str) -> float:
    phases = coverage.get("phases") if isinstance(coverage.get("phases"), dict) else {}
    row = phases.get(phase) if isinstance(phases, dict) else None
    if not isinstance(row, dict):
        return 1.0
    total = int(row.get("partitions_attempted", 0) or 0)
    ok = int(row.get("partitions_ok", 0) or 0)
    if total <= 0:
        return 1.0
    return ok / total


def _split_outputs(outputs: List[str]) -> List[List[str]]:
    ordered = sorted(outputs)
    if len(ordered) < 2:
        return [ordered]
    pivot = max(1, len(ordered) // 2)
    left = ordered[:pivot]
    right = ordered[pivot:]
    return [left, right]


def _rule_enabled(profile_payload: Dict[str, Any], rule_name: str) -> Dict[str, Any]:
    rules = profile_payload.get("v2_rules") if isinstance(profile_payload.get("v2_rules"), dict) else {}
    row = rules.get(rule_name)
    if isinstance(row, dict):
        return row
    return {"enabled": False}


def adjust_promptpack_v2(
    *,
    run_id: str,
    run_root: Path,
    promptpack_root: Path,
    promptpack_v1_payload: Dict[str, Any],
    profile_payload: Dict[str, Any],
) -> Dict[str, Any]:
    coverage = _load_coverage(run_root)
    step_qa = _load_step_qa(run_root)
    routing_index = _load_routing(run_root)

    v2_payload = copy.deepcopy(promptpack_v1_payload)
    v2_payload["version"] = "PROMPTPACK_V2"
    v2_payload["source_promptpack_version"] = str(promptpack_v1_payload.get("version", "PROMPTPACK_V1"))

    adjustments: List[Dict[str, Any]] = []
    rendered_root = promptpack_root / PROMPTPACK_V2_DIRNAME
    rendered_root.mkdir(parents=True, exist_ok=True)
    rendered_hashes: List[Dict[str, str]] = []

    for phase in sorted(v2_payload.get("phases", {}).keys()):
        phase_steps = v2_payload["phases"][phase]
        if not isinstance(phase_steps, list):
            continue
        hist = _hist_for_phase(coverage, phase)
        parse_failures = int(hist.get("parse_or_empty", 0))
        payload_unshrinkable = int(hist.get("payload_unshrinkable", 0))

        parse_budget_rule = _rule_enabled(profile_payload, RULE_REDUCE_MAX_FILES_ON_PARSE_OR_EMPTY)
        shrink_budget_rule = _rule_enabled(profile_payload, RULE_SHRINK_BUDGET_ON_PAYLOAD_UNSHRINKABLE)
        strict_envelope_rule = _rule_enabled(profile_payload, RULE_ENABLE_STRICT_ENVELOPE_ON_PARSE)
        split_rule = _rule_enabled(profile_payload, RULE_SPLIT_STEP_ON_MISSING_ARTIFACTS)
        reorder_rule = _rule_enabled(profile_payload, RULE_TARGET_REORDER_ON_THIN_COVERAGE)

        phase_ratio = _partitions_ratio(coverage, phase)
        should_reorder = bool(reorder_rule.get("enabled")) and phase_ratio < float(reorder_rule.get("threshold", 0.7))

        for step in sorted(phase_steps, key=lambda row: str(row.get("step_id", ""))):
            step_id = str(step.get("step_id") or "")
            if not step_id:
                continue
            budgets = step.get("budgets") if isinstance(step.get("budgets"), dict) else {}
            targets = list(step.get("targets") or []) if isinstance(step.get("targets"), list) else []
            declared_outputs = list(step.get("declared_outputs") or []) if isinstance(step.get("declared_outputs"), list) else []
            overlays: List[str] = []

            if payload_unshrinkable >= int(shrink_budget_rule.get("threshold", 1)) and bool(shrink_budget_rule.get("enabled")):
                old = int(budgets.get("max_chars", 650000))
                factor = float(shrink_budget_rule.get("factor", 0.8))
                new = max(32_000, int(old * factor))
                if new != old:
                    budgets["max_chars"] = new
                    adjustments.append(
                        {
                            "rule": RULE_SHRINK_BUDGET_ON_PAYLOAD_UNSHRINKABLE,
                            "phase": phase,
                            "step_id": step_id,
                            "old_max_chars": old,
                            "new_max_chars": new,
                            "reason": f"payload_unshrinkable={payload_unshrinkable}",
                        }
                    )

            if parse_failures >= int(parse_budget_rule.get("threshold", 1)) and bool(parse_budget_rule.get("enabled")):
                old_files = int(budgets.get("max_files", 20))
                dec = int(parse_budget_rule.get("decrement", 2))
                new_files = max(4, old_files - dec)
                if new_files != old_files:
                    budgets["max_files"] = new_files
                    adjustments.append(
                        {
                            "rule": RULE_REDUCE_MAX_FILES_ON_PARSE_OR_EMPTY,
                            "phase": phase,
                            "step_id": step_id,
                            "old_max_files": old_files,
                            "new_max_files": new_files,
                            "reason": f"parse_or_empty={parse_failures}",
                        }
                    )

            if should_reorder and targets:
                reordered = targets[-1:] + targets[:-1]
                if reordered != targets:
                    step["targets"] = reordered
                    adjustments.append(
                        {
                            "rule": RULE_TARGET_REORDER_ON_THIN_COVERAGE,
                            "phase": phase,
                            "step_id": step_id,
                            "old_targets": targets,
                            "new_targets": reordered,
                            "reason": f"ok_ratio={phase_ratio:.3f}",
                        }
                    )
                    targets = reordered

            qa_payload = step_qa.get((phase, step_id), {})
            missing_expected = qa_payload.get("missing_expected_artifacts") if isinstance(qa_payload, dict) and isinstance(qa_payload.get("missing_expected_artifacts"), list) else []
            if bool(split_rule.get("enabled")) and declared_outputs:
                missing_ratio = len(missing_expected) / max(1, len(declared_outputs))
                threshold = float(split_rule.get("threshold", 0.34))
                if missing_ratio >= threshold and len(declared_outputs) >= 2:
                    split_groups = _split_outputs(declared_outputs)
                    step["virtual_split"] = split_groups
                    overlays.append(
                        "Deterministic virtual split enabled. If output pressure is high, emit artifacts in group order: "
                        + json.dumps(split_groups, ensure_ascii=True)
                    )
                    adjustments.append(
                        {
                            "rule": RULE_SPLIT_STEP_ON_MISSING_ARTIFACTS,
                            "phase": phase,
                            "step_id": step_id,
                            "missing_expected_artifacts": sorted(str(x) for x in missing_expected),
                            "missing_ratio": round(missing_ratio, 6),
                            "threshold": threshold,
                            "split_groups": split_groups,
                        }
                    )

            if bool(strict_envelope_rule.get("enabled")) and parse_failures > 0:
                route = routing_index.get(f"{phase}:{step_id}", {})
                provider = str(route.get("provider") or "unknown")
                model = str(route.get("model_id") or "unknown")
                overlays.append(
                    "STRICT ENVELOPE: Output JSON only. NO MARKDOWN FENCES."
                    f" Provider={provider} Model={model}."
                )
                adjustments.append(
                    {
                        "rule": RULE_ENABLE_STRICT_ENVELOPE_ON_PARSE,
                        "phase": phase,
                        "step_id": step_id,
                        "provider": provider,
                        "model_id": model,
                        "reason": f"parse_or_empty={parse_failures}",
                    }
                )

            step["budgets"] = budgets
            if overlays:
                previous = str(step.get("v2_overlay") or "").strip()
                overlay_text = "\n".join(overlays)
                step["v2_overlay"] = (previous + "\n" + overlay_text).strip() if previous else overlay_text

            src_path = Path(str(step.get("rendered_prompt") or ""))
            if not src_path.exists():
                src_path = Path(str(step.get("source_prompt") or ""))
            prompt_text = src_path.read_text(encoding="utf-8", errors="ignore") if src_path.exists() else ""
            v2_overlay = str(step.get("v2_overlay") or "").strip()
            rendered_text = prompt_text.rstrip() + ("\n\n## PROMPTGEN_V2_ADJUSTMENTS\n" + v2_overlay + "\n" if v2_overlay else "\n")
            dst_path = rendered_root / str(step.get("prompt_file") or f"PROMPT_{step_id}.md")
            dst_path.write_text(rendered_text, encoding="utf-8")
            step["rendered_prompt"] = str(dst_path.resolve())
            step["sha256"] = sha256_file(dst_path)
            rendered_hashes.append({"file": str(dst_path.resolve()), "sha256": step["sha256"]})

    adjustments.sort(
        key=lambda row: (
            str(row.get("phase", "")),
            str(row.get("step_id", "")),
            str(row.get("rule", "")),
            json.dumps(row, sort_keys=True, ensure_ascii=True),
        )
    )

    v2_payload["adjustments_count"] = len(adjustments)
    v2_payload["adjustments"] = adjustments

    v2_json_path = promptpack_root / PROMPTPACK_V2_FILENAME
    write_json(v2_json_path, v2_payload)

    hash_payload = {
        "version": "PROMPTPACK_V2_SHA256",
        "run_id": run_id,
        "pack_sha256": sha256_text(v2_json_path.read_text(encoding="utf-8")),
        "rendered_hashes": sorted(rendered_hashes, key=lambda row: row["file"]),
    }
    write_json(promptpack_root / PROMPTPACK_V2_HASH_FILENAME, hash_payload)
    write_json(promptpack_root / PROMPT_ADJUSTMENTS_FILENAME, {"version": "PROMPT_ADJUSTMENTS_V1", "rows": adjustments})

    diff_lines = [
        "# PromptPack v1 -> v2 Diff",
        "",
        f"- run_id: {run_id}",
        f"- adjustments: {len(adjustments)}",
        "",
    ]
    for row in adjustments:
        diff_lines.append(
            "- "
            + f"[{row.get('rule')}] phase={row.get('phase')} step={row.get('step_id')} reason={row.get('reason', 'n/a')}"
        )
    (promptpack_root / PROMPTPACK_DIFF_FILENAME).write_text("\n".join(diff_lines).rstrip() + "\n", encoding="utf-8")

    return {
        "payload": v2_payload,
        "hash_payload": hash_payload,
        "adjustments": adjustments,
        "promptpack_json": str(v2_json_path.resolve()),
        "prompt_root": str((promptpack_root / PROMPTPACK_V2_DIRNAME).resolve()),
    }
