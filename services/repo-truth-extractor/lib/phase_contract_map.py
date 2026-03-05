from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

SERVICE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVICE_DIR.parents[1]
PROMPTSET_PATH = SERVICE_DIR / "promptsets" / "v4" / "promptset.yaml"
ARTIFACTS_PATH = SERVICE_DIR / "promptsets" / "v4" / "artifacts.yaml"
MODEL_MAP_PATH = SERVICE_DIR / "promptsets" / "v4" / "model_map.yaml"
REPO_TRUTH_MAP_PATH = REPO_ROOT / "repo_truth_map.json"

CONTRACT_MAP_FILENAME = "PHASE_CONTRACT_MAP.json"
RUNNER_MINIMUM_REQUIRED_KEYS = ("id", "path", "line_range")

_ARTIFACT_NAME_RE = re.compile(r"`([A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md))`")
_REQUIRED_FIELDS_RE = re.compile(r"`required_item_fields`:\s*`([^`]+)`")
_PART_SUFFIX_RE = re.compile(r"\.part(?:X|\d+)")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_yaml(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode to an object")
    return payload


def _read_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode to an object")
    return payload


def _split_csv_fields(value: str) -> List[str]:
    out: List[str] = []
    for part in value.split(","):
        token = str(part).strip()
        if token:
            out.append(token)
    return out


def canonical_schema_name_for_artifact(artifact_name: str) -> str:
    name = str(artifact_name or "").strip()
    if name.endswith(".json"):
        name = name[:-5]
    if name.endswith(".md"):
        name = name[:-3]
    name = _PART_SUFFIX_RE.sub("", name)
    return name


def canonical_schema_id_for_artifact(artifact_name: str) -> str:
    return f"{canonical_schema_name_for_artifact(artifact_name)}@v1"


def schema_aliases_for_artifact(artifact_name: str) -> List[str]:
    canonical = canonical_schema_id_for_artifact(artifact_name)
    lowered = canonical.lower()
    uppered = canonical.upper()
    values = {canonical, lowered, uppered}
    return sorted(values)


def _artifact_rules_by_key() -> Dict[Tuple[str, str], Dict[str, Any]]:
    payload = _read_yaml(ARTIFACTS_PATH)
    rules: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in payload.get("artifacts", []):
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "").strip().upper()
        artifact_name = str(row.get("artifact_name") or "").strip()
        if not phase or not artifact_name:
            continue
        rules[(phase, artifact_name)] = {
            "phase": phase,
            "artifact_name": artifact_name,
            "canonical_writer_step_id": str(row.get("canonical_writer_step_id") or "").strip().upper(),
            "kind": str(row.get("kind") or "json_item_list").strip(),
            "norm_artifact": bool(row.get("norm_artifact", True)),
            "merge_strategy": str(row.get("merge_strategy") or "itemlist_by_id").strip(),
            "required_fields": [
                str(value).strip()
                for value in row.get("required_fields", [])
                if str(value).strip()
            ],
        }
    return rules


def _normalize_route(route: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": str(route.get("provider") or "").strip().lower(),
        "model_id": str(route.get("model_id") or "").strip(),
        "api_key_env": str(route.get("api_key_env") or "").strip(),
        "strict_json_schema": bool(route.get("strict_json_schema", False)),
        "strict_passthrough_verified": bool(route.get("strict_passthrough_verified", False)),
    }


def _normalize_routes(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: List[Dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        parsed = _normalize_route(row)
        if parsed["provider"] and parsed["model_id"] and parsed["api_key_env"]:
            rows.append(parsed)
    return rows


def _model_map_payload() -> Dict[str, Any]:
    payload = _read_yaml(MODEL_MAP_PATH)
    rows = payload.get("steps")
    if not isinstance(rows, list):
        raise ValueError(f"{MODEL_MAP_PATH} must contain a list at steps")
    return payload


def _model_map_by_key() -> Dict[Tuple[str, str], Dict[str, Any]]:
    payload = _model_map_payload()
    mapping: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in payload.get("steps", []):
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "").strip().upper()
        step_id = str(row.get("step_id") or "").strip().upper()
        if not phase or not step_id:
            continue
        mapping[(phase, step_id)] = {
            "phase": phase,
            "step_id": step_id,
            "lane_class": str(row.get("lane_class") or "").strip().upper(),
            "strict_schema_required_primary": bool(row.get("strict_schema_required_primary", False)),
            "sidefill_enabled": bool(row.get("sidefill_enabled", False)),
            "repair_mode": str(row.get("repair_mode") or "").strip(),
            "primary_routes": _normalize_routes(row.get("primary_routes")),
            "repair_routes": _normalize_routes(row.get("repair_routes")),
            "sidefill_routes": _normalize_routes(row.get("sidefill_routes")),
        }
    return mapping


def _required_item_fields_by_artifact(prompt_text: str, expected_artifacts: Iterable[str]) -> Dict[str, List[str]]:
    expected = set(expected_artifacts)
    rows: Dict[str, List[str]] = {}
    in_schema = False
    current_artifact: Optional[str] = None
    for raw_line in prompt_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            in_schema = stripped == "## Schema"
            current_artifact = None
            continue
        if not in_schema:
            continue
        artifact_match = _ARTIFACT_NAME_RE.search(stripped)
        if artifact_match:
            candidate = artifact_match.group(1)
            current_artifact = candidate if candidate in expected else None
        if current_artifact is None:
            continue
        fields_match = _REQUIRED_FIELDS_RE.search(stripped)
        if fields_match:
            rows[current_artifact] = _split_csv_fields(fields_match.group(1))
    return rows


def _prompt_path_by_step() -> Dict[Tuple[str, str], Path]:
    payload = _read_yaml(PROMPTSET_PATH)
    out: Dict[Tuple[str, str], Path] = {}
    phases = payload.get("phases")
    if not isinstance(phases, dict):
        raise ValueError(f"{PROMPTSET_PATH} must contain phases object")
    for phase, phase_payload in phases.items():
        phase_code = str(phase or "").strip().upper()
        steps = phase_payload.get("steps") if isinstance(phase_payload, dict) else None
        if not isinstance(steps, list):
            continue
        for row in steps:
            if not isinstance(row, dict):
                continue
            step_id = str(row.get("step_id") or "").strip().upper()
            prompt_file = str(row.get("prompt_file") or "").strip()
            if not step_id or not prompt_file:
                continue
            out[(phase_code, step_id)] = (REPO_ROOT / prompt_file).resolve()
    return out


def _repo_truth_scope_by_key() -> Dict[Tuple[str, str], Dict[str, Any]]:
    payload = _read_json(REPO_TRUTH_MAP_PATH)
    steps = payload.get("steps")
    if not isinstance(steps, list):
        raise ValueError(f"{REPO_TRUTH_MAP_PATH} must contain a list at steps")
    scope: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in steps:
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "").strip().upper()
        step_id = str(row.get("step") or row.get("step_id") or "").strip().upper()
        prompt_declared = row.get("prompt_declared") if isinstance(row.get("prompt_declared"), dict) else {}
        expected = prompt_declared.get("expected_artifacts")
        if not isinstance(expected, list):
            continue
        expected_tokens = [str(value).strip() for value in expected if str(value).strip()]
        json_artifacts = [token for token in expected_tokens if token.endswith(".json")]
        markdown_artifacts = [token for token in expected_tokens if token.endswith(".md")]
        if not phase or not step_id or not json_artifacts:
            continue
        prompt_required = prompt_declared.get("required_item_keys")
        scope[(phase, step_id)] = {
            "phase": phase,
            "step_id": step_id,
            "json_artifacts": list(json_artifacts),
            "markdown_artifacts": list(markdown_artifacts),
            "all_declared_artifacts": expected_tokens,
            "mixed_step": bool(markdown_artifacts),
            "prompt_required_item_keys": [
                str(value).strip()
                for value in (prompt_required if isinstance(prompt_required, list) else [])
                if str(value).strip()
            ],
        }
    return scope


def _assert_lane_map_matches_scope(
    lane_map: Dict[Tuple[str, str], Dict[str, Any]],
    scope_map: Dict[Tuple[str, str], Dict[str, Any]],
) -> None:
    unknown_lane_steps = sorted(set(lane_map.keys()) - set(scope_map.keys()))
    if unknown_lane_steps:
        formatted = ", ".join(f"{phase}:{step}" for phase, step in unknown_lane_steps)
        raise ValueError(
            f"model_map.yaml contains steps outside repo_truth_map JSON scope: {formatted}"
        )
    missing_lane_steps = sorted(set(scope_map.keys()) - set(lane_map.keys()))
    if missing_lane_steps:
        formatted = ", ".join(f"{phase}:{step}" for phase, step in missing_lane_steps)
        raise ValueError(
            f"repo_truth_map JSON-managed steps missing from model_map.yaml: {formatted}"
        )


@lru_cache(maxsize=1)
def compile_phase_contract_map() -> Dict[str, Any]:
    artifact_rules = _artifact_rules_by_key()
    lane_map = _model_map_by_key()
    prompt_paths = _prompt_path_by_step()
    scope_map = _repo_truth_scope_by_key()
    _assert_lane_map_matches_scope(lane_map, scope_map)

    steps_payload: Dict[str, Dict[str, Any]] = {}
    for (phase_code, step_id), scope in sorted(scope_map.items()):
        lane = lane_map[(phase_code, step_id)]
        expected_artifacts = list(scope["json_artifacts"])
        markdown_artifacts = list(scope.get("markdown_artifacts") or [])
        prompt_path = prompt_paths.get((phase_code, step_id))
        prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path and prompt_path.exists() else ""
        prompt_required_map = _required_item_fields_by_artifact(prompt_text, expected_artifacts)

        artifacts_payload: Dict[str, Dict[str, Any]] = {}
        for artifact_name in expected_artifacts:
            artifact_rule = artifact_rules.get((phase_code, artifact_name), {})
            required_fields = [
                str(value).strip()
                for value in (artifact_rule.get("required_fields") or RUNNER_MINIMUM_REQUIRED_KEYS)
                if str(value).strip()
            ]
            prompt_required = prompt_required_map.get(artifact_name)
            if not prompt_required:
                prompt_required = list(scope.get("prompt_required_item_keys") or [])
            artifacts_payload[artifact_name] = {
                "artifact_name": artifact_name,
                "canonical_schema_name": canonical_schema_name_for_artifact(artifact_name),
                "canonical_schema_id": canonical_schema_id_for_artifact(artifact_name),
                "schema_version": "v1",
                "schema_aliases": schema_aliases_for_artifact(artifact_name),
                "required_fields": required_fields,
                "prompt_required_item_fields": prompt_required,
                "merge_strategy": str(artifact_rule.get("merge_strategy") or "itemlist_by_id"),
                "kind": str(artifact_rule.get("kind") or "json_item_list"),
                "canonical_writer_step_id": str(artifact_rule.get("canonical_writer_step_id") or step_id),
                "norm_artifact": bool(artifact_rule.get("norm_artifact", True)),
            }

        steps_payload[f"{phase_code}:{step_id}"] = {
            "phase": phase_code,
            "step_id": step_id,
            "scope_source": "repo_truth_map",
            "scope": {
                "json_managed": True,
                "mixed_step": bool(scope.get("mixed_step")),
                "markdown_bypassed": bool(markdown_artifacts),
            },
            "expected_artifacts": expected_artifacts,
            "expected_markdown_artifacts": markdown_artifacts,
            "artifact_order": expected_artifacts,
            "plural_expected_json_artifacts": len(expected_artifacts) >= 2,
            "runner_minimum_required_keys": list(RUNNER_MINIMUM_REQUIRED_KEYS),
            "prompt_path": str(prompt_path) if prompt_path else None,
            "lane": {
                "lane": str(lane.get("lane_class") or ""),
                "lane_class": str(lane.get("lane_class") or ""),
                "strict_schema_required": bool(lane.get("strict_schema_required_primary", False)),
                "strict_schema_required_primary": bool(lane.get("strict_schema_required_primary", False)),
                "sidefill_enabled": bool(lane.get("sidefill_enabled", False)),
                "repair_mode": str(lane.get("repair_mode") or ""),
                "primary_routes": list(lane.get("primary_routes") or []),
                "repair_routes": list(lane.get("repair_routes") or []),
                "sidefill_routes": list(lane.get("sidefill_routes") or []),
            },
            "artifacts": artifacts_payload,
        }

    model_map_policy = _model_map_payload().get("policy")
    return {
        "version": "PHASE_CONTRACT_MAP_V2",
        "scope": "json_managed_only",
        "source_files": {
            "repo_truth_map": str(REPO_TRUTH_MAP_PATH.resolve()),
            "promptset": str(PROMPTSET_PATH.resolve()),
            "artifacts": str(ARTIFACTS_PATH.resolve()),
            "model_map": str(MODEL_MAP_PATH.resolve()),
        },
        "policy": model_map_policy if isinstance(model_map_policy, dict) else {},
        "steps": steps_payload,
    }


def get_step_contract(phase: str, step_id: str) -> Optional[Dict[str, Any]]:
    payload = compile_phase_contract_map()
    steps = payload.get("steps") if isinstance(payload.get("steps"), dict) else {}
    key = f"{str(phase or '').strip().upper()}:{str(step_id or '').strip().upper()}"
    row = steps.get(key)
    return dict(row) if isinstance(row, dict) else None


def write_phase_contract_map(run_root: Path, run_id: str) -> Path:
    payload = dict(compile_phase_contract_map())
    payload["generated_at"] = now_iso()
    payload["run_id"] = run_id
    out_path = run_root / CONTRACT_MAP_FILENAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path

