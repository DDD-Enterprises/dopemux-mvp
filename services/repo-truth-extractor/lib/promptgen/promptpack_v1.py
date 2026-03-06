from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .fingerprint import deterministic_generated_at
from .hashing import sha256_file, sha256_text
from .io import read_json, write_json

try:
    from lib.phase_contract_map import get_step_contract
except Exception:  # pragma: no cover - fallback for limited import contexts
    get_step_contract = None  # type: ignore[assignment]

PROMPTPACK_V1_FILENAME = "PROMPTPACK.v1.json"
PROMPTPACK_V1_HASH_FILENAME = "PROMPTPACK.v1.sha256.json"
PROMPTPACK_V1_DIRNAME = "PROMPTPACK.v1"

PROMPT_FILE_RE = re.compile(r"^PROMPT_([A-Z][0-9]+)_.+\.md$")
OUTPUT_FILENAME_RE = re.compile(r"\b[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)\b")


def _numeric_step_sort_key(step_id: str) -> Tuple[str, int, str]:
    phase = step_id[:1]
    try:
        number = int(step_id[1:])
    except Exception:
        number = 999999
    return (phase, number, step_id)


def _extract_declared_outputs(prompt_text: str, step_id: str) -> List[str]:
    artifacts = sorted(set(OUTPUT_FILENAME_RE.findall(prompt_text)))
    if artifacts:
        return artifacts
    return [f"{step_id}.json"]


def _phase_from_step(step_id: str) -> str:
    return step_id[:1]


def _profile_phase_targets(profile_payload: Dict[str, Any], phase: str) -> List[str]:
    policy = profile_payload.get("phase_policy") if isinstance(profile_payload.get("phase_policy"), dict) else {}
    targets = (policy.get("targets_by_phase") or {}).get(phase)
    if isinstance(targets, list):
        return [str(x) for x in targets if str(x).strip()]
    return []


def _profile_phase_budget(profile_payload: Dict[str, Any], phase: str) -> Dict[str, int]:
    policy = profile_payload.get("phase_policy") if isinstance(profile_payload.get("phase_policy"), dict) else {}
    row = (policy.get("budgets_by_phase") or {}).get(phase)
    if isinstance(row, dict):
        return {
            "max_files": int(row.get("max_files", 20)),
            "max_chars": int(row.get("max_chars", 650000)),
            "file_truncate_chars": int(row.get("file_truncate_chars", 70000)),
        }
    return {"max_files": 20, "max_chars": 650000, "file_truncate_chars": 70000}


def _profile_step_variant(profile_payload: Dict[str, Any], phase: str, step_id: str) -> str:
    policy = profile_payload.get("phase_policy") if isinstance(profile_payload.get("phase_policy"), dict) else {}
    variant_map = (policy.get("prompt_variants_by_phase_step") or {}).get(phase)
    if isinstance(variant_map, dict):
        value = variant_map.get(step_id)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "default"


def _profile_overlay(profile_payload: Dict[str, Any], key: str) -> str:
    overlays = profile_payload.get("prompt_overlays") if isinstance(profile_payload.get("prompt_overlays"), dict) else {}
    value = overlays.get(key)
    if isinstance(value, str):
        return value.strip()
    return ""


def _collect_prompts(prompt_root: Path, phases: Iterable[str]) -> List[Dict[str, Any]]:
    requested = set(phases)
    rows: List[Dict[str, Any]] = []
    for path in sorted(prompt_root.glob("PROMPT_*.md"), key=lambda p: p.name):
        match = PROMPT_FILE_RE.match(path.name)
        if not match:
            continue
        step_id = match.group(1)
        phase = _phase_from_step(step_id)
        if phase not in requested:
            continue
        prompt_text = path.read_text(encoding="utf-8", errors="ignore")
        rows.append(
            {
                "phase": phase,
                "step_id": step_id,
                "path": path,
                "name": path.name,
                "prompt_text": prompt_text,
                "declared_outputs": _extract_declared_outputs(prompt_text, step_id),
            }
        )
    rows.sort(key=lambda row: (_numeric_step_sort_key(str(row["step_id"])), str(row["name"])))
    return rows


def _render_prompt_text(
    *,
    source_text: str,
    profile_id: str,
    phase: str,
    step_id: str,
    variant: str,
    targets: List[str],
    budgets: Dict[str, int],
    overlay_text: str,
    contracts: Dict[str, Any],
    contract_metadata: Dict[str, Any],
) -> str:
    targets_json = json.dumps(targets, ensure_ascii=True)
    budgets_json = json.dumps(budgets, ensure_ascii=True, sort_keys=True)
    contracts_json = json.dumps(contracts, ensure_ascii=True, sort_keys=True)
    contract_metadata_json = json.dumps(contract_metadata, ensure_ascii=True, sort_keys=True)
    metadata_block = (
        "\n\n## PROMPTGEN_POLICY\n"
        f"- profile_id: {profile_id}\n"
        f"- phase: {phase}\n"
        f"- step_id: {step_id}\n"
        f"- variant: {variant}\n"
        f"- targets: {targets_json}\n"
        f"- budgets: {budgets_json}\n"
        f"- contracts: {contracts_json}\n"
        f"- contract_map: {contract_metadata_json}\n"
        "\n## PROMPTGEN_OVERLAY\n"
        f"{overlay_text or 'NONE'}\n"
    )
    return source_text.rstrip() + metadata_block + "\n"


def _contract_metadata_for_step(phase: str, step_id: str) -> Dict[str, Any]:
    if get_step_contract is None:
        return {}
    try:
        row = get_step_contract(phase, step_id)
    except Exception:
        row = None
    if not isinstance(row, dict):
        return {}
    lane = row.get("lane") if isinstance(row.get("lane"), dict) else {}
    primary_routes = lane.get("primary_routes") if isinstance(lane.get("primary_routes"), list) else []
    primary_route = primary_routes[0] if primary_routes and isinstance(primary_routes[0], dict) else {}
    return {
        "phase": str(row.get("phase") or phase),
        "step_id": str(row.get("step_id") or step_id),
        "expected_artifacts": list(row.get("expected_artifacts") or []),
        "artifact_order": list(row.get("artifact_order") or []),
        "runner_minimum_required_keys": list(row.get("runner_minimum_required_keys") or []),
        "lane": {
            "lane": str(lane.get("lane_class") or lane.get("lane") or ""),
            "lane_class": str(lane.get("lane_class") or lane.get("lane") or ""),
            "provider": str(primary_route.get("provider") or ""),
            "model_id": str(primary_route.get("model_id") or ""),
            "api_key_env": str(primary_route.get("api_key_env") or ""),
            "strict_schema_required": bool(
                lane.get("strict_schema_required_primary")
                if "strict_schema_required_primary" in lane
                else lane.get("strict_schema_required", False)
            ),
            "sidefill_enabled": bool(lane.get("sidefill_enabled", False)),
            "repair_mode": str(lane.get("repair_mode") or ""),
            "primary_routes": list(primary_routes),
            "repair_routes": list(lane.get("repair_routes") or []),
            "sidefill_routes": list(lane.get("sidefill_routes") or []),
        },
    }


def compile_promptpack_v1(
    *,
    run_id: str,
    root: Path,
    prompt_root: Path,
    promptpack_root: Path,
    phases: List[str],
    profile_selection: Dict[str, Any],
    profile_payload: Dict[str, Any],
    archetypes_payload: Dict[str, Any],
) -> Dict[str, Any]:
    rendered_root = promptpack_root / PROMPTPACK_V1_DIRNAME
    rendered_root.mkdir(parents=True, exist_ok=True)

    contracts = archetypes_payload.get("contracts_present") if isinstance(archetypes_payload.get("contracts_present"), dict) else {}
    profile_id = str(profile_selection.get("selected_profile_id") or profile_payload.get("profile_id") or "P00_GENERIC")
    prompts = _collect_prompts(prompt_root, phases)

    phase_entries: Dict[str, List[Dict[str, Any]]] = {phase: [] for phase in phases}
    rendered_hashes: List[Dict[str, str]] = []
    for row in prompts:
        phase = str(row["phase"])
        step_id = str(row["step_id"])
        source_path = Path(str(row["path"]))
        rendered_path = rendered_root / str(row["name"])

        variant = _profile_step_variant(profile_payload, phase, step_id)
        targets = _profile_phase_targets(profile_payload, phase)
        budgets = _profile_phase_budget(profile_payload, phase)
        overlay_parts = [
            _profile_overlay(profile_payload, "base"),
            _profile_overlay(profile_payload, f"phase:{phase}"),
            _profile_overlay(profile_payload, f"step:{step_id}"),
        ]
        overlay_text = "\n".join(part for part in overlay_parts if part)
        contract_metadata = _contract_metadata_for_step(phase, step_id)
        rendered = _render_prompt_text(
            source_text=str(row["prompt_text"]),
            profile_id=profile_id,
            phase=phase,
            step_id=step_id,
            variant=variant,
            targets=targets,
            budgets=budgets,
            overlay_text=overlay_text,
            contracts=contracts,
            contract_metadata=contract_metadata,
        )
        rendered_path.write_text(rendered, encoding="utf-8")

        sha = sha256_file(rendered_path)
        phase_entries.setdefault(phase, []).append(
            {
                "step_id": step_id,
                "prompt_file": rendered_path.name,
                "source_prompt": str(source_path.resolve()),
                "rendered_prompt": str(rendered_path.resolve()),
                "sha256": sha,
                "declared_outputs": list(row["declared_outputs"]),
                "variant": variant,
                "targets": targets,
                "budgets": budgets,
                "contract_metadata": contract_metadata,
                "contract_lane": (
                    (contract_metadata.get("lane") or {}).get("lane")
                    if isinstance(contract_metadata.get("lane"), dict)
                    else None
                ),
                "strict_schema_required": bool(
                    ((contract_metadata.get("lane") or {}).get("strict_schema_required"))
                    if isinstance(contract_metadata.get("lane"), dict)
                    else False
                ),
            }
        )
        rendered_hashes.append({"file": str(rendered_path.resolve()), "sha256": sha})

    for phase in phase_entries:
        phase_entries[phase].sort(key=lambda item: _numeric_step_sort_key(str(item["step_id"])))

    payload = {
        "version": "PROMPTPACK_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "profile_selection": profile_selection,
        "profile_id": profile_id,
        "source_prompt_root": str(prompt_root.resolve()),
        "rendered_prompt_root": str(rendered_root.resolve()),
        "phases": phase_entries,
    }

    pack_json_path = promptpack_root / PROMPTPACK_V1_FILENAME
    write_json(pack_json_path, payload)

    hash_payload = {
        "version": "PROMPTPACK_V1_SHA256",
        "run_id": run_id,
        "pack_sha256": sha256_text(pack_json_path.read_text(encoding="utf-8")),
        "rendered_hashes": sorted(rendered_hashes, key=lambda row: row["file"]),
    }
    write_json(promptpack_root / PROMPTPACK_V1_HASH_FILENAME, hash_payload)

    return {
        "promptpack_json": str(pack_json_path.resolve()),
        "prompt_root": str(rendered_root.resolve()),
        "hash_json": str((promptpack_root / PROMPTPACK_V1_HASH_FILENAME).resolve()),
        "payload": payload,
        "hash_payload": hash_payload,
    }


def load_promptpack(path: Path) -> Dict[str, Any]:
    payload = read_json(path)
    if not payload:
        raise RuntimeError(f"Promptpack not found or invalid: {path}")
    return payload
