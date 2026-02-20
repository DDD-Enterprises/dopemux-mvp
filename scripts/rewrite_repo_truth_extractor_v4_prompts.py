#!/usr/bin/env python3
"""Rewrite Repo Truth Extractor v4 prompts into schema-first contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROMPTSET_PATH = ROOT / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "promptset.yaml"
ARTIFACTS_PATH = ROOT / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "artifacts.yaml"
LEGACY_ROOT = ROOT / "services" / "repo-truth-extractor" / "prompts" / "v3"


PHASE_SCOPE_HINTS: Dict[str, List[str]] = {
    "A": [
        ".claude/**",
        ".github/**",
        ".taskx/**",
        "config/**",
        "scripts/**",
        "docker/**",
        "compose.yml",
        "docker-compose*.yml",
        "README.md",
        "AGENTS.md",
    ],
    "H": [
        "$HOME/.claude/**",
        "$HOME/.codex/**",
        "$HOME/.taskx/**",
        "$HOME/.config/**",
        "$HOME/.tmux.conf*",
    ],
    "D": ["docs/**", "README.md", "CHANGELOG.md", "docs/docs_index.yaml"],
    "C": ["src/**", "services/**", "docker/**", "compose.yml", "docker-compose*.yml", "services/registry.yaml"],
    "E": ["scripts/**", "compose.yml", "docker-compose*.yml", "Makefile", "src/**"],
    "W": ["scripts/**", "services/**", "docs/02-how-to/**", "docs/03-reference/**", "compose.yml"],
    "B": ["src/**", "services/**", "docs/90-adr/**", ".claude/**", "AGENTS.md"],
    "G": [".github/workflows/**", "pyproject.toml", "scripts/**", "config/**", "docs/90-adr/**"],
    "Q": ["extraction/**", "services/repo-truth-extractor/**", "services/registry.yaml", "compose.yml", "docker-compose*.yml"],
    "R": ["extraction/**/norm/**", "docs/**", "services/repo-truth-extractor/**"],
    "X": ["src/**", "services/**", "docs/**", "README.md"],
    "T": ["services/repo-truth-extractor/**", "docs/90-adr/**", "docs/05-audit-reports/**"],
    "Z": ["extraction/**", "docs/**", "services/repo-truth-extractor/**"],
    "M": ["services/**", "docker/**", "extraction/**"],
    "S": ["extraction/**/norm/**", "docs/**", "services/repo-truth-extractor/**"],
}


def read_yaml(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not decode to object")
    return payload


def phase_step_sort(step_id: str) -> Tuple[str, int]:
    phase = step_id[:1]
    number = step_id[1:]
    try:
        return (phase, int(number))
    except ValueError:
        return (phase, 999999)


def artifact_index(artifacts_payload: Dict[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in artifacts_payload.get("artifacts", []):
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase", "")).strip()
        artifact_name = str(row.get("artifact_name", "")).strip()
        if not phase or not artifact_name:
            continue
        out[(phase, artifact_name)] = row
    return out


def find_legacy_prompt(step_id: str) -> str:
    matches = sorted(LEGACY_ROOT.glob(f"PROMPT_{step_id}_*.md"))
    if not matches:
        return ""
    text = matches[0].read_text(encoding="utf-8", errors="replace").strip()
    return text[:1600].rstrip()


def id_rule_for_artifact(name: str) -> str:
    stem = name.replace(".partX", "").replace(".json", "").replace(".md", "")
    prefix = stem[:32]
    return f"{prefix}:<stable-hash(path|symbol|name)>"


def contract_fields_for_artifact(name: str, required_fields: List[str]) -> List[str]:
    upper = name.upper()
    if upper.startswith("SERVICE_CATALOG"):
        return [
            "id",
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
            "evidence",
        ]
    if "GRAPH" in upper:
        return ["nodes", "edges", "schema"]
    if "PARTITIONS" in upper:
        return ["id", "partition_id", "files", "reason", "evidence"]
    if "INVENTORY" in upper:
        return ["id", "path", "kind", "summary", "evidence"]
    if "QA" in upper or upper.startswith("QA_"):
        return ["id", "status", "checks", "issues", "evidence"]
    if "MANIFEST" in upper:
        return ["id", "artifact_name", "sha256", "writer_step_id", "evidence"]
    if "COVERAGE" in upper:
        return ["id", "status", "missing", "extra", "evidence"]
    if "RISK" in upper:
        return ["id", "risk", "severity", "location", "evidence"]
    if "INDEX" in upper:
        return ["id", "name", "path", "kind", "evidence"]
    if "SURFACE" in upper:
        return ["id", "component", "symbol", "path", "line_range", "evidence"]
    if "ENTRYPOINT" in upper:
        return ["id", "service_id", "type", "value", "path", "line_range", "evidence"]
    fields = ["id", "evidence"]
    for field in required_fields:
        if field not in fields:
            fields.append(field)
    return fields


def phase_focus_hint(phase: str) -> str:
    if phase == "C":
        return "Focus on service runtime truths, interfaces, dependencies, and code-level ownership."
    if phase == "W":
        return "Focus on executable workflows, runbooks, and multi-service coordination boundaries."
    if phase == "B":
        return "Focus on boundary enforcement points, refusal rails, and concrete bypass evidence."
    if phase == "G":
        return "Focus on CI gates, policy enforcement, and governance drift risks."
    if phase == "Q":
        return "Focus on coverage, collisions, determinism drift, and recovery actions."
    return "Focus on concrete, machine-verifiable implementation facts."


def upstream_outputs(steps: List[Dict[str, Any]], step_id: str) -> List[str]:
    collected: List[str] = []
    for row in sorted(steps, key=lambda item: phase_step_sort(str(item.get("step_id", "")))):
        current = str(row.get("step_id", "")).strip()
        if current == step_id:
            break
        for output in row.get("outputs", []):
            output_name = str(output)
            if output_name not in collected:
                collected.append(output_name)
    return collected


def render_schema_block(
    phase: str,
    outputs: List[str],
    idx: Dict[Tuple[str, str], Dict[str, Any]],
) -> str:
    lines: List[str] = []
    lines.append("- Use deterministic containers only:")
    lines.append('  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`')
    lines.append('  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`')
    lines.append("- Output contracts:")
    for output in outputs:
        rule = idx.get((phase, output), {})
        kind = str(rule.get("kind", "json_item_list"))
        merge_strategy = str(rule.get("merge_strategy", "itemlist_by_id"))
        required_fields = [str(value) for value in rule.get("required_fields", []) if isinstance(value, str)]
        canonical_writer = str(rule.get("canonical_writer_step_id", ""))
        fields = contract_fields_for_artifact(output, required_fields)
        lines.append(f"  - `{output}`")
        lines.append(f"    - `kind`: `{kind}`")
        lines.append(f"    - `merge_strategy`: `{merge_strategy}`")
        lines.append(f"    - `canonical_writer_step_id`: `{canonical_writer}`")
        lines.append(f"    - `id_rule`: `{id_rule_for_artifact(output)}`")
        lines.append(f"    - `required_item_fields`: `{', '.join(fields)}`")
        if required_fields:
            lines.append(f"    - `required_registry_fields`: `{', '.join(required_fields)}`")
    return "\n".join(lines)


def render_prompt(
    *,
    phase: str,
    step_id: str,
    outputs: List[str],
    steps_in_phase: List[Dict[str, Any]],
    idx: Dict[Tuple[str, str], Dict[str, Any]],
) -> str:
    scope_hints = PHASE_SCOPE_HINTS.get(phase, ["src/**", "services/**", "docs/**"])
    upstream = upstream_outputs(steps_in_phase, step_id)
    legacy = find_legacy_prompt(step_id)

    outputs_block = "\n".join(f"- `{name}`" for name in outputs)
    scope_block = "\n".join(f"- `{value}`" for value in scope_hints)
    upstream_block = (
        "\n".join(f"- `{value}`" for value in upstream[:24])
        if upstream
        else "- None; this step can rely on phase inventory inputs."
    )

    schema_block = render_schema_block(phase, outputs, idx)
    evidence_object = """```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```"""

    prompt_lines: List[str] = []
    prompt_lines.append(f"# PROMPT_{step_id}")
    prompt_lines.append("")
    prompt_lines.append("## Goal")
    prompt_lines.append(
        f"Produce `{step_id}` outputs for phase `{phase}` with strict schema, explicit evidence, and deterministic normalization."
    )
    prompt_lines.append(phase_focus_hint(phase))
    prompt_lines.append("")
    prompt_lines.append("## Inputs")
    prompt_lines.append("- Source scope (scan these roots first):")
    prompt_lines.append(scope_block)
    prompt_lines.append("- Upstream normalized artifacts available to this step:")
    prompt_lines.append(upstream_block)
    prompt_lines.append("- Runner context artifacts:")
    prompt_lines.append("  - `extraction/*/inputs/INVENTORY.json`")
    prompt_lines.append("  - `extraction/*/inputs/PARTITIONS.json`")
    prompt_lines.append("  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`")
    prompt_lines.append("  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`")
    prompt_lines.append("- When relevant, use `services/registry.yaml` as canonical service list.")
    prompt_lines.append("")
    prompt_lines.append("## Outputs")
    prompt_lines.append(outputs_block)
    prompt_lines.append("")
    prompt_lines.append("## Schema")
    prompt_lines.append(schema_block)
    prompt_lines.append("")
    prompt_lines.append("## Extraction Procedure")
    prompt_lines.append("1. Enumerate candidate facts only from in-scope inputs and upstream artifacts.")
    prompt_lines.append("2. Build deterministic IDs using stable content keys (path/symbol/name/service_id).")
    prompt_lines.append("3. Attach evidence to every non-derived field and every relationship edge.")
    prompt_lines.append("4. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).")
    prompt_lines.append("5. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.")
    prompt_lines.append("6. Emit exactly the declared outputs and no additional files.")
    prompt_lines.append("")
    prompt_lines.append("## Evidence Rules")
    prompt_lines.append("- Every load-bearing value must carry at least one evidence object:")
    prompt_lines.append(evidence_object)
    prompt_lines.append("- `path` must be repo-relative (never absolute in norm artifacts).")
    prompt_lines.append("- `excerpt` must be exact (no paraphrase) and <= 200 chars.")
    prompt_lines.append("- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.")
    prompt_lines.append("")
    prompt_lines.append("## Determinism Rules")
    prompt_lines.append("- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.")
    prompt_lines.append("- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.")
    prompt_lines.append("- Merge duplicates deterministically:")
    prompt_lines.append("  - union evidence by `(path,line_range,excerpt)`")
    prompt_lines.append("  - union arrays with stable sort")
    prompt_lines.append("  - choose scalar conflicts by non-empty, else lexicographically smallest stable value")
    prompt_lines.append("- Output byte content must be reproducible for same commit + same configuration.")
    prompt_lines.append("")
    prompt_lines.append("## Anti-Fabrication Rules")
    prompt_lines.append("- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.")
    prompt_lines.append("- Do not infer intent from filenames alone; require direct textual/code evidence.")
    prompt_lines.append("- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.")
    prompt_lines.append("- Never copy unsupported keys from upstream QA artifacts into norm artifacts.")
    prompt_lines.append("")
    prompt_lines.append("## Failure Modes")
    prompt_lines.append("- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.")
    prompt_lines.append("- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.")
    prompt_lines.append("- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.")
    prompt_lines.append("- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.")
    if legacy:
        prompt_lines.append("")
        prompt_lines.append("## Legacy Context (for intent only; never as evidence)")
        prompt_lines.append("```markdown")
        prompt_lines.append(legacy)
        prompt_lines.append("```")

    prompt_lines.append("")
    return "\n".join(prompt_lines)


def main() -> int:
    promptset = read_yaml(PROMPTSET_PATH)
    artifacts = read_yaml(ARTIFACTS_PATH)
    idx = artifact_index(artifacts)

    phases = promptset.get("phases", {})
    for phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            continue
        steps = phase_payload.get("steps", [])
        if not isinstance(steps, list):
            continue
        ordered_steps = sorted(steps, key=lambda row: phase_step_sort(str(row.get("step_id", ""))))
        for step in ordered_steps:
            step_id = str(step.get("step_id", "")).strip()
            prompt_file = str(step.get("prompt_file", "")).strip()
            outputs = [str(value) for value in step.get("outputs", []) if str(value).strip()]
            if not step_id or not prompt_file:
                continue
            prompt_path = ROOT / prompt_file
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            body = render_prompt(
                phase=phase,
                step_id=step_id,
                outputs=outputs,
                steps_in_phase=ordered_steps,
                idx=idx,
            )
            prompt_path.write_text(body, encoding="utf-8")

    coverage_map = {
        "generated_by": "scripts/rewrite_repo_truth_extractor_v4_prompts.py",
        "generated_at_utc": "DETERMINISTIC",
        "prompt_count": sum(
            len(payload.get("steps", []))
            for payload in phases.values()
            if isinstance(payload, dict)
        ),
        "phases": {},
    }
    for phase, phase_payload in phases.items():
        if not isinstance(phase_payload, dict):
            continue
        rows = []
        for step in sorted(
            phase_payload.get("steps", []),
            key=lambda row: phase_step_sort(str(row.get("step_id", ""))),
        ):
            if not isinstance(step, dict):
                continue
            prompt_file = str(step.get("prompt_file", ""))
            step_id = str(step.get("step_id", ""))
            outputs = [str(value) for value in step.get("outputs", [])]
            digest = hashlib.sha256((ROOT / prompt_file).read_bytes()).hexdigest() if prompt_file else ""
            rows.append(
                {
                    "step_id": step_id,
                    "prompt_file": prompt_file,
                    "prompt_sha256": digest,
                    "outputs": outputs,
                }
            )
        coverage_map["phases"][phase] = rows

    coverage_path = ROOT / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "prompt_artifact_coverage_map.json"
    coverage_path.write_text(json.dumps(coverage_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
