#!/usr/bin/env python3
"""Audit and lint the Repo Truth Extractor v4 promptset contracts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import yaml

OUTPUT_RE = re.compile(r"\b[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)\b")
STEP_RE = re.compile(r"^[A-Z]\d+$")
HEADING_RE = re.compile(r"^\s*##\s+(.+?)\s*$", re.MULTILINE)
REQUIRED_SECTIONS_DEFAULT = [
    "Goal",
    "Inputs",
    "Outputs",
    "Schema",
    "Extraction Procedure",
    "Evidence Rules",
    "Determinism Rules",
    "Anti-Fabrication Rules",
    "Failure Modes",
]

MIN_SECTION_BODY_CHARS = {
    "Goal": 40,
    "Inputs": 220,
    "Outputs": 10,
    "Schema": 280,
    "Extraction Procedure": 180,
    "Evidence Rules": 180,
    "Determinism Rules": 180,
    "Anti-Fabrication Rules": 160,
    "Failure Modes": 160,
}


@dataclass(frozen=True)
class PromptAuditRow:
    phase: str
    step_id: str
    prompt_file: str
    outputs: Tuple[str, ...]
    rating: str
    missing_sections: Tuple[str, ...]
    missing_outputs_in_registry: Tuple[str, ...]
    notes: Tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Repo Truth Extractor v4 prompts")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--promptset",
        type=Path,
        default=Path("services/repo-truth-extractor/promptsets/v4/promptset.yaml"),
        help="Path to promptset yaml relative to repo root",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=Path("services/repo-truth-extractor/promptsets/v4/artifacts.yaml"),
        help="Path to artifacts yaml relative to repo root",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=None,
        help="Write markdown report to this path",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write JSON payload to this path",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any lint failure",
    )
    parser.add_argument(
        "--model-map",
        type=Path,
        default=Path("services/repo-truth-extractor/promptsets/v4/model_map.yaml"),
        help="Path to model_map yaml relative to repo root",
    )
    return parser.parse_args()


def _read_yaml(path: Path) -> Dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} did not decode to an object")
    return raw


def _parse_step_key(step_id: str) -> Tuple[str, int]:
    if not STEP_RE.match(step_id):
        raise ValueError(f"Invalid step id format: {step_id}")
    return (step_id[0], int(step_id[1:]))


def _extract_prompt_outputs(text: str) -> List[str]:
    seen = set()
    outputs: List[str] = []
    for match in OUTPUT_RE.findall(text):
        if "_" not in match:
            continue
        if match in seen:
            continue
        seen.add(match)
        outputs.append(match)
    return outputs


def _section_bodies(text: str) -> Dict[str, str]:
    matches = list(HEADING_RE.finditer(text))
    sections: Dict[str, str] = {}
    for idx, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[name] = body
    return sections


def _rating_for_sections(required: Sequence[str], sections: Dict[str, str]) -> str:
    present = 0
    non_empty = 0
    for req in required:
        if req in sections:
            present += 1
            if sections[req]:
                non_empty += 1
    if present == len(required) and non_empty == len(required):
        return "complete"
    if present >= max(1, len(required) // 2):
        return "partial"
    return "stub"


def _collect_artifact_index(artifacts_payload: Dict[str, Any]) -> Tuple[Dict[Tuple[str, str], Dict[str, Any]], List[str]]:
    rows = artifacts_payload.get("artifacts", [])
    if not isinstance(rows, list):
        raise ValueError("artifacts.yaml 'artifacts' must be a list")
    index: Dict[Tuple[str, str], Dict[str, Any]] = {}
    issues: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            issues.append("artifact row is not an object")
            continue
        phase = str(row.get("phase", "")).strip()
        artifact_name = str(row.get("artifact_name", "")).strip()
        if not phase or not artifact_name:
            issues.append(f"artifact row missing phase/artifact_name: {row}")
            continue
        key = (phase, artifact_name)
        if key in index:
            issues.append(f"duplicate artifact registry entry: {phase}:{artifact_name}")
            continue
        index[key] = row
    return index, issues


def _canonical_uniqueness_issues(artifacts_payload: Dict[str, Any]) -> List[str]:
    rows = artifacts_payload.get("artifacts", [])
    seen: Dict[Tuple[str, str], str] = {}
    issues: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase", "")).strip()
        artifact_name = str(row.get("artifact_name", "")).strip()
        writer = str(row.get("canonical_writer_step_id", "")).strip()
        if not phase or not artifact_name or not writer:
            issues.append(f"canonical metadata missing for {phase}:{artifact_name}")
            continue
        key = (phase, artifact_name)
        previous = seen.get(key)
        if previous is None:
            seen[key] = writer
            continue
        if previous != writer:
            issues.append(
                f"conflicting canonical writer for {phase}:{artifact_name}: {previous} vs {writer}"
            )
    return issues


def _forbidden_norm_key_issues(artifacts_payload: Dict[str, Any]) -> List[str]:
    forbidden_raw = artifacts_payload.get("forbidden_norm_keys", [])
    forbidden = {
        str(item).strip() for item in forbidden_raw if isinstance(item, (str, int, float))
    }
    if not forbidden:
        return []
    issues: List[str] = []
    for row in artifacts_payload.get("artifacts", []):
        if not isinstance(row, dict):
            continue
        if not bool(row.get("norm_artifact", False)):
            continue
        phase = str(row.get("phase", "")).strip()
        artifact_name = str(row.get("artifact_name", "")).strip()
        required_fields = row.get("required_fields", [])
        if not isinstance(required_fields, list):
            continue
        bad = sorted(forbidden.intersection({str(field).strip() for field in required_fields}))
        if bad:
            issues.append(
                f"norm artifact {phase}:{artifact_name} required_fields contains forbidden keys: {bad}"
            )
    return issues


def _phase_step_order_issues(promptset_payload: Dict[str, Any]) -> List[str]:
    phases = promptset_payload.get("phases", {})
    if not isinstance(phases, dict):
        return ["promptset phases must be an object"]
    issues: List[str] = []
    for phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            issues.append(f"phase {phase} payload is not an object")
            continue
        steps = phase_payload.get("steps", [])
        if not isinstance(steps, list):
            issues.append(f"phase {phase} steps must be a list")
            continue
        observed_ids: List[str] = []
        for row in steps:
            if not isinstance(row, dict):
                issues.append(f"phase {phase} step row is not an object")
                continue
            step_id = str(row.get("step_id", "")).strip()
            if not step_id:
                issues.append(f"phase {phase} missing step_id")
                continue
            observed_ids.append(step_id)
        parsed = []
        for step_id in observed_ids:
            try:
                parsed.append(_parse_step_key(step_id))
            except ValueError as exc:
                issues.append(str(exc))
        if parsed:
            sorted_ids = [f"{letter}{number}" for letter, number in sorted(parsed, key=lambda x: (x[0], x[1]))]
            if observed_ids != sorted_ids:
                issues.append(
                    f"phase {phase} step ordering is not numeric deterministic: {observed_ids} vs {sorted_ids}"
                )
        if len(set(observed_ids)) != len(observed_ids):
            issues.append(f"phase {phase} has duplicate step IDs")
        required_steps = phase_payload.get("required_steps", [])
        if isinstance(required_steps, list):
            required_set = {str(value).strip() for value in required_steps}
            observed_set = set(observed_ids)
            missing_required = sorted(required_set - observed_set)
            if missing_required:
                issues.append(f"phase {phase} missing required step IDs: {missing_required}")
    return issues


def _model_map_cross_check(
    promptset_payload: Dict[str, Any],
    model_map_payload: Dict[str, Any],
) -> List[str]:
    """Every step_id in promptset.yaml must have a matching entry in model_map.yaml.

    Steps in optional_phases with exclude_from_validation are skipped.
    """
    issues: List[str] = []
    optional_phases = set(promptset_payload.get("optional_phases", []))
    phases = promptset_payload.get("phases", {})

    # Collect model_map step_ids
    mm_step_ids: set = set()
    for entry in model_map_payload.get("steps", []):
        if isinstance(entry, dict):
            sid = str(entry.get("step_id", "")).strip()
            if sid:
                mm_step_ids.add(sid)

    for phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            continue
        # Skip optional phases if explicitly excluded
        if phase in optional_phases and phase_payload.get("exclude_from_validation", False):
            continue
        steps = phase_payload.get("steps", [])
        if not isinstance(steps, list):
            continue
        for row in steps:
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id", "")).strip()
            if step_id and step_id not in mm_step_ids:
                issues.append(f"step_id {step_id} in promptset.yaml has no model_map entry")
    return issues


def _artifact_output_cross_check(
    promptset_payload: Dict[str, Any],
    artifact_index: Dict[Tuple[str, str], Dict[str, Any]],
) -> List[str]:
    """Every output in a promptset step must have an artifacts.yaml entry."""
    issues: List[str] = []
    phases = promptset_payload.get("phases", {})
    for phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            continue
        steps = phase_payload.get("steps", [])
        if not isinstance(steps, list):
            continue
        for row in steps:
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id", "")).strip()
            for output in row.get("outputs", []):
                output_name = str(output).strip()
                if not output_name:
                    continue
                # Check across all phases for the artifact
                found = False
                for p in phases:
                    if (p, output_name) in artifact_index:
                        found = True
                        break
                if not found:
                    issues.append(
                        f"step {step_id} output {output_name} has no artifacts.yaml entry"
                    )
    return issues


def _prompt_file_existence_check(
    repo_root: Path,
    promptset_payload: Dict[str, Any],
) -> List[str]:
    """Verify all prompt_file paths in promptset resolve to real files."""
    issues: List[str] = []
    phases = promptset_payload.get("phases", {})
    for _phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            continue
        steps = phase_payload.get("steps", [])
        if not isinstance(steps, list):
            continue
        for row in steps:
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id", "")).strip()
            prompt_file = str(row.get("prompt_file", "")).strip()
            if prompt_file and not (repo_root / prompt_file).exists():
                issues.append(
                    f"step {step_id} prompt_file does not exist: {prompt_file}"
                )
    return issues


def _prompt_file_coverage_issues(repo_root: Path, promptset_payload: Dict[str, Any]) -> List[str]:
    phases = promptset_payload.get("phases", {})
    if not isinstance(phases, dict):
        return []

    declared: Dict[str, str] = {}
    issues: List[str] = []
    for _phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            continue
        steps = phase_payload.get("steps", [])
        if not isinstance(steps, list):
            continue
        for row in steps:
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id", "")).strip()
            prompt_file = str(row.get("prompt_file", "")).strip()
            if not prompt_file:
                continue
            if prompt_file in declared and declared[prompt_file] != step_id:
                issues.append(
                    f"prompt file mapped by multiple steps: {prompt_file} ({declared[prompt_file]} vs {step_id})"
                )
            declared[prompt_file] = step_id

    prompts_root = repo_root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "prompts"
    discovered = {
        path.relative_to(repo_root).as_posix()
        for path in prompts_root.glob("PROMPT_*.md")
        if path.is_file()
    }
    declared_set = set(declared.keys())

    unmapped = sorted(discovered - declared_set)
    if unmapped:
        preview = ", ".join(unmapped[:5])
        issues.append(
            f"promptset is missing mappings for {len(unmapped)} prompt files (examples: {preview})"
        )

    missing_files = sorted(declared_set - discovered)
    if missing_files:
        preview = ", ".join(missing_files[:5])
        issues.append(
            f"promptset references {len(missing_files)} prompt files that do not exist (examples: {preview})"
        )

    return issues


def _audit_rows(
    repo_root: Path,
    promptset_payload: Dict[str, Any],
    artifact_index: Dict[Tuple[str, str], Dict[str, Any]],
) -> List[PromptAuditRow]:
    phases = promptset_payload.get("phases", {})
    required_sections = promptset_payload.get("required_prompt_sections") or REQUIRED_SECTIONS_DEFAULT
    rows: List[PromptAuditRow] = []
    for phase, phase_payload in sorted(phases.items()):
        steps = phase_payload.get("steps", [])
        for step_row in steps:
            step_id = str(step_row.get("step_id", "")).strip()
            prompt_file = str(step_row.get("prompt_file", "")).strip()
            prompt_path = repo_root / prompt_file
            notes: List[str] = []
            if not prompt_path.exists():
                rows.append(
                    PromptAuditRow(
                        phase=phase,
                        step_id=step_id or "UNKNOWN",
                        prompt_file=prompt_file or "<missing>",
                        outputs=tuple(),
                        rating="stub",
                        missing_sections=tuple(required_sections),
                        missing_outputs_in_registry=tuple(),
                        notes=("missing_prompt_file",),
                    )
                )
                continue

            text = prompt_path.read_text(encoding="utf-8", errors="replace")
            sections = _section_bodies(text)
            missing_sections = [name for name in required_sections if not sections.get(name, "").strip()]
            rating = _rating_for_sections(required_sections, sections)
            outputs_body = sections.get("Outputs", "")
            prompt_outputs = _extract_prompt_outputs(outputs_body)
            declared_outputs = list(step_row.get("outputs", []))

            if sorted(prompt_outputs) != sorted(declared_outputs):
                notes.append("lint:outputs_differ_from_promptset")

            for section_name in required_sections:
                body = sections.get(section_name, "").strip()
                if not body:
                    continue
                min_chars = MIN_SECTION_BODY_CHARS.get(section_name, 80)
                if len(body) < min_chars:
                    notes.append(f"lint:section_too_short:{section_name}")

            missing_registry: List[str] = []
            for artifact_name in declared_outputs:
                if (phase, artifact_name) not in artifact_index:
                    missing_registry.append(artifact_name)

            schema_body = sections.get("Schema", "")
            for artifact_name in declared_outputs:
                if artifact_name not in schema_body:
                    notes.append(f"lint:schema_missing_output:{artifact_name}")

            evidence_body = sections.get("Evidence Rules", "")
            # Skip source-code evidence check for synthesis prompts (Phase S) as they use artifact#section format
            if phase != "S":
                for required_key in ("path", "line_range", "excerpt"):
                    if required_key not in evidence_body:
                        notes.append(f"lint:evidence_missing_key:{required_key}")

            determinism_body = sections.get("Determinism Rules", "")
            if not any(token in determinism_body for token in ("generated_at", "run_id", "timestamp")):
                notes.append("lint:determinism_forbidden_keys_unspecified")

            if not prompt_outputs:
                notes.append("lint:no_outputs_found")
            if missing_sections:
                notes.append("lint:missing_required_sections")
            if missing_registry:
                notes.append("lint:missing_artifact_registry_entries")

            rows.append(
                PromptAuditRow(
                    phase=phase,
                    step_id=step_id,
                    prompt_file=prompt_file,
                    outputs=tuple(declared_outputs),
                    rating=rating,
                    missing_sections=tuple(missing_sections),
                    missing_outputs_in_registry=tuple(missing_registry),
                    notes=tuple(notes),
                )
            )
    return rows


def _summary(rows: Sequence[PromptAuditRow], global_issues: Sequence[str]) -> Dict[str, Any]:
    rating_counts: Dict[str, int] = {"complete": 0, "partial": 0, "stub": 0}
    per_phase: Dict[str, Dict[str, int]] = {}
    lint_failures = 0
    for row in rows:
        rating_counts[row.rating] = rating_counts.get(row.rating, 0) + 1
        phase_counts = per_phase.setdefault(row.phase, {"complete": 0, "partial": 0, "stub": 0})
        phase_counts[row.rating] = phase_counts.get(row.rating, 0) + 1
        if row.missing_sections or row.missing_outputs_in_registry or any(note.startswith("lint:") for note in row.notes):
            lint_failures += 1
    lint_failures += len(global_issues)
    return {
        "prompt_count": len(rows),
        "rating_counts": rating_counts,
        "phase_rating_counts": per_phase,
        "global_issues_count": len(global_issues),
        "global_issues": list(global_issues),
        "lint_failures": lint_failures,
        "status": "PASS" if lint_failures == 0 else "FAIL",
    }


def _rows_to_json(rows: Sequence[PromptAuditRow]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "phase": row.phase,
                "step_id": row.step_id,
                "prompt_file": row.prompt_file,
                "outputs": list(row.outputs),
                "rating": row.rating,
                "missing_sections": list(row.missing_sections),
                "missing_outputs_in_registry": list(row.missing_outputs_in_registry),
                "notes": list(row.notes),
            }
        )
    return out


def _report_markdown(summary: Dict[str, Any], rows: Sequence[PromptAuditRow]) -> str:
    today = dt.date.today().isoformat()
    lines: List[str] = []
    lines.append("---")
    lines.append(f"id: RTE_V4_PROMPTSET_AUDIT_{today}")
    lines.append("title: Repo Truth Extractor v4 Promptset Audit")
    lines.append("type: reference")
    lines.append("owner: '@hu3mann'")
    lines.append("author: '@codex'")
    lines.append(f"date: '{today}'")
    lines.append(f"last_review: '{today}'")
    lines.append("next_review: '2026-05-21'")
    lines.append("prelude: Deterministic lint report for Repo Truth Extractor v4 prompt contracts.")
    lines.append("---")
    lines.append(f"# Repo Truth Extractor v4 Promptset Audit ({today})")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- status: **{summary['status']}**")
    lines.append(f"- prompt_count: {summary['prompt_count']}")
    lines.append(
        "- rating_counts: complete={complete}, partial={partial}, stub={stub}".format(
            **summary["rating_counts"]
        )
    )
    lines.append(f"- lint_failures: {summary['lint_failures']}")
    lines.append("")
    if summary["global_issues"]:
        lines.append("## Global Issues")
        for issue in summary["global_issues"]:
            lines.append(f"- {issue}")
        lines.append("")
    lines.append("## Per-Prompt Table")
    lines.append("")
    lines.append("| Phase | Step | Prompt | Outputs | Rating | Missing | Notes |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        missing_bits = []
        if row.missing_sections:
            missing_bits.append("sections:" + ",".join(row.missing_sections))
        if row.missing_outputs_in_registry:
            missing_bits.append("registry:" + ",".join(row.missing_outputs_in_registry))
        missing = "<br>".join(missing_bits) if missing_bits else "-"
        notes = ",".join(row.notes) if row.notes else "-"
        outputs = ", ".join(row.outputs) if row.outputs else "-"
        lines.append(
            f"| {row.phase} | {row.step_id} | {row.prompt_file} | {outputs} | {row.rating} | {missing} | {notes} |"
        )
    return "\n".join(lines) + "\n"


def run_audit(
    repo_root: Path,
    promptset_path: Path,
    artifacts_path: Path,
    model_map_path: Path | None = None,
) -> Dict[str, Any]:
    promptset_payload = _read_yaml(promptset_path)
    artifacts_payload = _read_yaml(artifacts_path)
    artifact_index, artifact_issues = _collect_artifact_index(artifacts_payload)

    global_issues = []
    global_issues.extend(artifact_issues)
    global_issues.extend(_canonical_uniqueness_issues(artifacts_payload))
    global_issues.extend(_forbidden_norm_key_issues(artifacts_payload))
    global_issues.extend(_phase_step_order_issues(promptset_payload))
    global_issues.extend(_prompt_file_coverage_issues(repo_root, promptset_payload))
    global_issues.extend(_prompt_file_existence_check(repo_root, promptset_payload))
    global_issues.extend(_artifact_output_cross_check(promptset_payload, artifact_index))

    if model_map_path and model_map_path.exists():
        model_map_payload = _read_yaml(model_map_path)
        global_issues.extend(_model_map_cross_check(promptset_payload, model_map_payload))

    rows = _audit_rows(repo_root, promptset_payload, artifact_index)
    summary = _summary(rows, global_issues)
    return {
        "summary": summary,
        "rows": _rows_to_json(rows),
        "required_prompt_sections": promptset_payload.get(
            "required_prompt_sections", REQUIRED_SECTIONS_DEFAULT
        ),
        "forbidden_norm_keys": artifacts_payload.get("forbidden_norm_keys", []),
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    promptset_path = (repo_root / args.promptset).resolve()
    artifacts_path = (repo_root / args.artifacts).resolve()
    model_map_path = (repo_root / args.model_map).resolve()

    payload = run_audit(repo_root, promptset_path, artifacts_path, model_map_path)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if args.report_out:
        rows = [
            PromptAuditRow(
                phase=str(row["phase"]),
                step_id=str(row["step_id"]),
                prompt_file=str(row["prompt_file"]),
                outputs=tuple(row["outputs"]),
                rating=str(row["rating"]),
                missing_sections=tuple(row["missing_sections"]),
                missing_outputs_in_registry=tuple(row["missing_outputs_in_registry"]),
                notes=tuple(row["notes"]),
            )
            for row in payload["rows"]
        ]
        md = _report_markdown(payload["summary"], rows)
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(md, encoding="utf-8")

    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
