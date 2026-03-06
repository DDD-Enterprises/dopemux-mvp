#!/usr/bin/env python3
"""
TP-008 audit utilities.

Modes:
1) Legacy contract audit (existing behavior)
2) Drift audit against canonical TP-008 mapping
3) Model-usage audit against expected lane ladders
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

SERVICE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_DIR.parents[1]
MODEL_MAP_PATH = SERVICE_DIR / "promptsets" / "v4" / "model_map.yaml"
REPO_TRUTH_MAP_PATH = REPO_ROOT / "repo_truth_map.json"
DEFAULT_OUT_DIR = REPO_ROOT / "reports" / "strict_closure"
DEFAULT_RUNS_ROOT = REPO_ROOT / "extraction" / "repo-truth-extractor" / "v3" / "runs"

STEP_PART_RE = re.compile(r"^(?P<step>[A-Z]\d+)__?(?P<part>[A-Z]_[Pp]\d{4})\.(?P<ext>.+)$")
STEP_PART_RE2 = re.compile(r"^(?P<step>[A-Z]\d+)__?(?P<part>[A-Z]_P\d{4})\.(?P<ext>.+)$")

FINDING_FAIL_POLICY = "FAIL_POLICY"
FINDING_FAIL_LANE = "FAIL_LANE_CLASS"
FINDING_FAIL_ROUTE_PRIMARY = "FAIL_ROUTE_PRIMARY"
FINDING_FAIL_ROUTE_REPAIR = "FAIL_ROUTE_REPAIR"
FINDING_FAIL_REPAIR_MODE = "FAIL_REPAIR_MODE"
FINDING_FAIL_SIDEFILL = "FAIL_SIDEFILL_POLICY"
FINDING_INFO_SCOPE_EXCLUDED = "INFO_SCOPE_EXCLUDED"
FINDING_INFO_NONEXISTENT = "INFO_NONEXISTENT_STEP"

MODEL_CLASS_MATCH = "MATCH"
MODEL_CLASS_FALLBACK = "LADDER_FALLBACK_MATCH"
MODEL_CLASS_DRIFT = "DRIFT"

BULK_SIDFILL_OPT_IN_REQUIRED = {"D2", "E4", "T2", "T4", "T5"}
PHASE_D_CORRECTIONS = {
    "D2": "CE",
    "D3": "BULK_DOCS_GENERAL",
    "D4": "AGG",
    "D5": "AGG",
}

LANE_ALIAS_MAP = {
    "CE": "CE",
    "AGG": "AGG",
    "BULK": "BULK_DOCS_GENERAL",
    "BULK_DOCS_GENERAL": "BULK_DOCS_GENERAL",
    "BULK_DOCS": "BULK_DOCS_GENERAL",
    "BULK_GENERAL": "BULK_DOCS_GENERAL",
    "BULK_CODE_HEAVY": "BULK_CODE_HEAVY",
    "BULK_CODE": "BULK_CODE_HEAVY",
    "MIXED_JSON_MANAGED": "CE",
    "MIXED_JSON_MANAGED_CE": "CE",
    "AGG_MIXED_JSON_MANAGED": "AGG",
}


@dataclass(frozen=True)
class Failure:
    kind: str
    detail: str
    artifact_name: Optional[str] = None
    item_index: Optional[int] = None
    item_id: Optional[str] = None
    item_path: Optional[str] = None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(_read_text(path))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _read_yaml(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(_read_text(path))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object at {path}")
    return payload


def _route_api_env(provider: str) -> str:
    token = provider.strip().lower()
    if token == "openrouter":
        return "OPENROUTER_API_KEY"
    if token == "xai":
        return "XAI_API_KEY"
    if token == "openai":
        return "OPENAI_API_KEY"
    return "API_KEY"


def _normalize_lane(token: str) -> str:
    key = str(token or "").strip().upper()
    return LANE_ALIAS_MAP.get(key, key)


def _normalize_route(route: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(route.get("provider") or "").strip().lower()
    model_id = str(route.get("model_id") or "").strip()
    strict_json_schema = bool(route.get("strict_json_schema", False))
    strict_passthrough_verified = bool(route.get("strict_passthrough_verified", False))
    return {
        "provider": provider,
        "model_id": model_id,
        "api_key_env": str(route.get("api_key_env") or _route_api_env(provider)).strip(),
        "strict_json_schema": strict_json_schema,
        "strict_passthrough_verified": strict_passthrough_verified,
    }


def _route_signature(route: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": str(route.get("provider") or "").strip().lower(),
        "model_id": str(route.get("model_id") or "").strip(),
        "strict_json_schema": bool(route.get("strict_json_schema", False)),
        "strict_passthrough_verified": bool(route.get("strict_passthrough_verified", False)),
    }


def _normalize_route_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed = _normalize_route(row)
        if parsed["provider"] and parsed["model_id"]:
            out.append(parsed)
    return out


def _parse_route_string(value: str) -> Dict[str, Any]:
    raw = str(value or "").strip()
    strict = "(strict" in raw.lower()
    token = re.sub(r"\s*\(.*?\)\s*", "", raw).strip()
    provider = ""
    model_id = token
    if "/" in token:
        provider, rest = token.split("/", 1)
        provider = provider.strip().lower()
        model_id = rest.strip()
    if not provider:
        provider = "openrouter" if model_id.startswith("openai/") else "xai"
    return {
        "provider": provider,
        "model_id": model_id,
        "api_key_env": _route_api_env(provider),
        "strict_json_schema": strict,
        "strict_passthrough_verified": bool(strict and provider == "openrouter"),
    }


def _normalize_route_list(rows: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if isinstance(row, dict):
            parsed = _normalize_route(row)
        else:
            parsed = _parse_route_string(str(row))
        if parsed["provider"] and parsed["model_id"]:
            out.append(parsed)
    return out


def _canonical_step_key(phase: str, step: str) -> str:
    return f"{str(phase).strip().upper()}:{str(step).strip().upper()}"


def _is_plural_json_step(scope_row: Dict[str, Any]) -> bool:
    return len(scope_row.get("json_artifacts", [])) >= 2


def _is_strict_capable(route: Dict[str, Any]) -> bool:
    provider = str(route.get("provider") or "").strip().lower()
    if not bool(route.get("strict_json_schema", False)):
        return False
    if provider == "openrouter":
        return bool(route.get("strict_passthrough_verified", False))
    return provider in {"openai", "xai"}


def _load_repo_truth_scope(path: Path) -> Dict[str, Any]:
    payload = _read_json(path)
    steps = payload.get("steps")
    if not isinstance(steps, list):
        raise ValueError(f"repo_truth_map.json has invalid steps list: {path}")

    json_scope: Dict[str, Dict[str, Any]] = {}
    markdown_only_keys: set[str] = set()
    all_keys: set[str] = set()

    for row in steps:
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "").strip().upper()
        step = str(row.get("step") or row.get("step_id") or "").strip().upper()
        if not phase or not step:
            continue
        key = _canonical_step_key(phase, step)
        all_keys.add(key)

        prompt_declared = row.get("prompt_declared") if isinstance(row.get("prompt_declared"), dict) else {}
        expected = prompt_declared.get("expected_artifacts")
        if not isinstance(expected, list):
            continue

        json_artifacts = sorted(
            str(a).strip() for a in expected if isinstance(a, str) and str(a).strip().endswith(".json")
        )
        markdown_artifacts = sorted(
            str(a).strip() for a in expected if isinstance(a, str) and str(a).strip().endswith(".md")
        )
        if json_artifacts:
            json_scope[key] = {
                "phase": phase,
                "step": step,
                "json_artifacts": json_artifacts,
                "markdown_artifacts": markdown_artifacts,
                "mixed_step": bool(markdown_artifacts),
                "plural_expected_json_artifacts": len(json_artifacts) >= 2,
            }
        elif markdown_artifacts:
            markdown_only_keys.add(key)

    return {
        "json_scope": json_scope,
        "markdown_only_keys": markdown_only_keys,
        "all_keys": all_keys,
    }


def _load_model_map(path: Path) -> Dict[str, Any]:
    payload = _read_yaml(path)
    steps = payload.get("steps")
    if not isinstance(steps, list):
        raise ValueError(f"model_map has invalid steps list: {path}")

    by_key: Dict[str, Dict[str, Any]] = {}
    for row in steps:
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "").strip().upper()
        step = str(row.get("step_id") or "").strip().upper()
        if not phase or not step:
            continue
        key = _canonical_step_key(phase, step)
        by_key[key] = {
            "phase": phase,
            "step": step,
            "lane_class": _normalize_lane(str(row.get("lane_class") or "")),
            "strict_schema_required_primary": bool(row.get("strict_schema_required_primary", False)),
            "sidefill_enabled": bool(row.get("sidefill_enabled", False)),
            "repair_mode": str(row.get("repair_mode") or "").strip(),
            "primary_routes": _normalize_route_rows(row.get("primary_routes")),
            "repair_routes": _normalize_route_rows(row.get("repair_routes")),
            "sidefill_routes": _normalize_route_rows(row.get("sidefill_routes")),
        }

    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    return {
        "policy": {
            "no_auto_transport_flips": bool(policy.get("no_auto_transport_flips", False)),
            "scope": str(policy.get("scope") or "").strip(),
            "strict_required_behavior": str(policy.get("strict_required_behavior") or "").strip(),
        },
        "steps": by_key,
    }


def _extract_tp008_root(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "tp008" in payload and isinstance(payload.get("tp008"), dict):
        return dict(payload["tp008"])
    return dict(payload)


def _find_lane_def(lanes: Dict[str, Any], lane_token: str) -> Tuple[str, Dict[str, Any]]:
    if lane_token in lanes and isinstance(lanes.get(lane_token), dict):
        return lane_token, dict(lanes[lane_token])

    target = _normalize_lane(lane_token)
    for key, value in lanes.items():
        if not isinstance(value, dict):
            continue
        if _normalize_lane(str(key)) == target:
            return str(key), dict(value)

    if target == "BULK_DOCS_GENERAL":
        for fallback in ("BULK_docs_general", "BULK", "bulk", "BULK_DOCS"):
            if fallback in lanes and isinstance(lanes.get(fallback), dict):
                return fallback, dict(lanes[fallback])

    if target == "BULK_CODE_HEAVY":
        for fallback in ("BULK_code_heavy", "BULK_CODE"):
            if fallback in lanes and isinstance(lanes.get(fallback), dict):
                return fallback, dict(lanes[fallback])

    if target == "AGG":
        for fallback in ("AGG", "AGG_mixed_json_managed"):
            if fallback in lanes and isinstance(lanes.get(fallback), dict):
                return fallback, dict(lanes[fallback])

    if target == "CE":
        for fallback in ("CE", "mixed_json_managed_CE", "mixed_json_managed"):
            if fallback in lanes and isinstance(lanes.get(fallback), dict):
                return fallback, dict(lanes[fallback])

    raise ValueError(f"Could not resolve lane definition for token: {lane_token}")


def _coerce_step_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for value in values:
        token = str(value).strip().upper()
        if token:
            out.append(token)
    return sorted(set(out))


def _load_tp008_map(path: Path, repo_scope: Dict[str, Any]) -> Dict[str, Any]:
    payload = _read_yaml(path) if path.suffix.lower() in {".yaml", ".yml"} else _read_json(path)
    root = _extract_tp008_root(payload)

    lanes = root.get("lanes") if isinstance(root.get("lanes"), dict) else {}
    phases = root.get("phases") if isinstance(root.get("phases"), dict) else {}
    policy = root.get("policy") if isinstance(root.get("policy"), dict) else {}
    bulk_opt_in = set(_coerce_step_list(root.get("bulk_sidefill_opt_in_recommended", [])))

    by_key: Dict[str, Dict[str, Any]] = {}

    for phase, lane_buckets in sorted(phases.items(), key=lambda kv: str(kv[0])):
        phase_code = str(phase).strip().upper()
        if not isinstance(lane_buckets, dict):
            continue
        for bucket_name, step_list in sorted(lane_buckets.items(), key=lambda kv: str(kv[0])):
            if str(bucket_name).strip().lower() == "markdown_only_excluded":
                continue
            steps = _coerce_step_list(step_list)
            for step in steps:
                key = _canonical_step_key(phase_code, step)

                lane_name, lane_def = _find_lane_def(lanes, str(bucket_name))
                lane_class = _normalize_lane(str(bucket_name))

                primary_routes = _normalize_route_list(lane_def.get("primary"))
                repair_routes = _normalize_route_list(lane_def.get("repair"))
                sidefill_routes = _normalize_route_list(lane_def.get("sidefill"))

                strict_required = all(bool(route.get("strict_json_schema", False)) for route in primary_routes) and bool(primary_routes)

                sidefill_default = bool(
                    lane_def.get("sidefill_enabled")
                    if "sidefill_enabled" in lane_def
                    else lane_def.get("sidefill_enabled_default", False)
                )

                scope_row = repo_scope["json_scope"].get(key, {})
                plural_expected = bool(scope_row.get("plural_expected_json_artifacts", False))

                if lane_class in {"BULK_DOCS_GENERAL", "BULK_CODE_HEAVY"}:
                    sidefill_enabled = step in bulk_opt_in
                    if not plural_expected and sidefill_enabled:
                        sidefill_enabled = False
                else:
                    sidefill_enabled = sidefill_default

                by_key[key] = {
                    "phase": phase_code,
                    "step": step,
                    "lane_source": lane_name,
                    "lane_class": lane_class,
                    "strict_schema_required_primary": strict_required,
                    "sidefill_enabled": sidefill_enabled,
                    "repair_mode": str(lane_def.get("repair_mode") or "").strip(),
                    "primary_routes": primary_routes,
                    "repair_routes": repair_routes,
                    "sidefill_routes": sidefill_routes,
                    "json_scope_row": scope_row,
                }

    # Decision-locked D corrections override map-provided lane assignment.
    for step, corrected_lane in PHASE_D_CORRECTIONS.items():
        key = _canonical_step_key("D", step)
        if key not in by_key:
            continue
        lane_name, lane_def = _find_lane_def(lanes, corrected_lane)
        primary_routes = _normalize_route_list(lane_def.get("primary"))
        repair_routes = _normalize_route_list(lane_def.get("repair"))
        sidefill_routes = _normalize_route_list(lane_def.get("sidefill"))
        strict_required = all(bool(route.get("strict_json_schema", False)) for route in primary_routes) and bool(primary_routes)

        scope_row = repo_scope["json_scope"].get(key, {})
        plural_expected = bool(scope_row.get("plural_expected_json_artifacts", False))

        if corrected_lane in {"BULK_DOCS_GENERAL", "BULK_CODE_HEAVY"}:
            sidefill_enabled = step in bulk_opt_in and plural_expected
        else:
            sidefill_enabled = bool(
                lane_def.get("sidefill_enabled")
                if "sidefill_enabled" in lane_def
                else lane_def.get("sidefill_enabled_default", False)
            )

        by_key[key].update(
            {
                "lane_source": lane_name,
                "lane_class": corrected_lane,
                "strict_schema_required_primary": strict_required,
                "sidefill_enabled": sidefill_enabled,
                "repair_mode": str(lane_def.get("repair_mode") or "").strip(),
                "primary_routes": primary_routes,
                "repair_routes": repair_routes,
                "sidefill_routes": sidefill_routes,
            }
        )

    return {
        "policy": {
            "no_auto_transport_flips": bool(policy.get("no_auto_transport_flips", False)),
            "scope": str(policy.get("scope") or "").strip(),
            "strict_required": policy.get("strict_required"),
        },
        "steps": by_key,
        "bulk_sidefill_opt_in_required": sorted(bulk_opt_in),
    }


def _finding(
    *,
    severity: str,
    finding_code: str,
    phase: str,
    step: str,
    expected: Any,
    observed: Any,
    source_paths: Sequence[Path],
    in_scope: bool,
    classification: str,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "severity": severity,
        "finding_code": finding_code,
        "phase": phase,
        "step": step,
        "step_key": _canonical_step_key(phase, step),
        "expected": expected,
        "observed": observed,
        "source_paths": [str(p) for p in source_paths],
        "in_scope": bool(in_scope),
        "classification": classification,
    }
    if note:
        payload["note"] = note
    return payload


def _sorted_signatures(routes: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = [_route_signature(r) for r in routes]
    rows.sort(key=lambda r: (r["provider"], r["model_id"], int(r["strict_json_schema"]), int(r["strict_passthrough_verified"])))
    return rows


def _run_static_drift_audit(
    *,
    tp008_path: Path,
    tp008_map: Dict[str, Any],
    model_map_path: Path,
    model_map: Dict[str, Any],
    repo_truth_path: Path,
    repo_scope: Dict[str, Any],
    scope_excluded_as_info: bool,
) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    src = [tp008_path, model_map_path, repo_truth_path]

    # Global policy checks.
    observed_policy = model_map["policy"]
    expected_policy = {
        "no_auto_transport_flips": True,
        "scope": "json_managed_only",
        "strict_required_behavior": "fail_closed",
    }

    for key, expected_value in expected_policy.items():
        observed_value = observed_policy.get(key)
        if observed_value != expected_value:
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_POLICY,
                    phase="*",
                    step="*",
                    expected={key: expected_value},
                    observed={key: observed_value},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

    tp_steps = tp008_map["steps"]
    model_steps = model_map["steps"]
    json_scope = repo_scope["json_scope"]
    all_repo_steps = repo_scope["all_keys"]

    for step_key in sorted(tp_steps.keys()):
        expected_row = tp_steps[step_key]
        phase = expected_row["phase"]
        step = expected_row["step"]
        in_scope = step_key in json_scope

        if not in_scope:
            if scope_excluded_as_info:
                code = FINDING_INFO_SCOPE_EXCLUDED if step_key in all_repo_steps else FINDING_INFO_NONEXISTENT
                findings.append(
                    _finding(
                        severity="info",
                        finding_code=code,
                        phase=phase,
                        step=step,
                        expected={"scope": "json_managed_only"},
                        observed={
                            "exists_in_repo_truth": step_key in all_repo_steps,
                            "exists_in_json_scope": False,
                        },
                        source_paths=src,
                        in_scope=False,
                        classification="scope_excluded",
                    )
                )
            continue

        observed_row = model_steps.get(step_key)
        if not isinstance(observed_row, dict):
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_LANE,
                    phase=phase,
                    step=step,
                    expected={"lane_class": expected_row["lane_class"]},
                    observed={"lane_class": None, "missing_in_model_map": True},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )
            continue

        if observed_row["lane_class"] != expected_row["lane_class"]:
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_LANE,
                    phase=phase,
                    step=step,
                    expected={"lane_class": expected_row["lane_class"]},
                    observed={"lane_class": observed_row["lane_class"]},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

        # strict-required + strict-capable invariant.
        if bool(observed_row.get("strict_schema_required_primary", False)):
            strict_capable_routes = [r for r in observed_row.get("primary_routes", []) if _is_strict_capable(r)]
            if not strict_capable_routes:
                findings.append(
                    _finding(
                        severity="fail",
                        finding_code=FINDING_FAIL_POLICY,
                        phase=phase,
                        step=step,
                        expected={"strict_capable_primary_route": True},
                        observed={"strict_capable_primary_route": False},
                        source_paths=src,
                        in_scope=True,
                        classification="static_drift",
                    )
                )

        if bool(observed_row.get("strict_schema_required_primary", False)) != bool(
            expected_row.get("strict_schema_required_primary", False)
        ):
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_POLICY,
                    phase=phase,
                    step=step,
                    expected={
                        "strict_schema_required_primary": bool(
                            expected_row.get("strict_schema_required_primary", False)
                        )
                    },
                    observed={
                        "strict_schema_required_primary": bool(
                            observed_row.get("strict_schema_required_primary", False)
                        )
                    },
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

        if str(observed_row.get("repair_mode") or "").strip() != str(expected_row.get("repair_mode") or "").strip():
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_REPAIR_MODE,
                    phase=phase,
                    step=step,
                    expected={"repair_mode": expected_row.get("repair_mode")},
                    observed={"repair_mode": observed_row.get("repair_mode")},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

        if bool(observed_row.get("sidefill_enabled", False)) != bool(expected_row.get("sidefill_enabled", False)):
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_SIDEFILL,
                    phase=phase,
                    step=step,
                    expected={"sidefill_enabled": bool(expected_row.get("sidefill_enabled", False))},
                    observed={"sidefill_enabled": bool(observed_row.get("sidefill_enabled", False))},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

        expected_primary = _sorted_signatures(expected_row.get("primary_routes", []))
        observed_primary = _sorted_signatures(observed_row.get("primary_routes", []))
        if expected_primary != observed_primary:
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_ROUTE_PRIMARY,
                    phase=phase,
                    step=step,
                    expected={"primary_routes": expected_primary},
                    observed={"primary_routes": observed_primary},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

        expected_repair = _sorted_signatures(expected_row.get("repair_routes", []))
        observed_repair = _sorted_signatures(observed_row.get("repair_routes", []))
        if expected_repair != observed_repair:
            findings.append(
                _finding(
                    severity="fail",
                    finding_code=FINDING_FAIL_ROUTE_REPAIR,
                    phase=phase,
                    step=step,
                    expected={"repair_routes": expected_repair},
                    observed={"repair_routes": observed_repair},
                    source_paths=src,
                    in_scope=True,
                    classification="static_drift",
                )
            )

    findings.sort(
        key=lambda f: (
            0 if f["severity"] == "fail" else 1,
            str(f["finding_code"]),
            str(f["phase"]),
            str(f["step"]),
        )
    )

    fail_findings = [f for f in findings if f["severity"] == "fail" and bool(f["in_scope"])]
    by_code: Dict[str, int] = {}
    for row in findings:
        code = str(row.get("finding_code") or "")
        by_code[code] = by_code.get(code, 0) + 1

    recommendations: List[str] = []
    if any(f["finding_code"] == FINDING_FAIL_LANE and f["phase"] == "D" and f["step"] == "D2" for f in findings):
        recommendations.append("Reclassify D2 to CE lane and align strict/sidefill defaults accordingly.")
    if any(f["finding_code"] == FINDING_FAIL_LANE and f["phase"] == "D" and f["step"] == "D4" for f in findings):
        recommendations.append("Reclassify D4 to AGG lane with envelope repair behavior.")
    if any(f["finding_code"] == FINDING_FAIL_LANE and f["phase"] == "D" and f["step"] == "D5" for f in findings):
        recommendations.append("Reclassify D5 to AGG lane; avoid BULK semantics for reducer behavior.")
    if any(f["finding_code"] == FINDING_FAIL_SIDEFILL for f in findings):
        recommendations.append("Align BULK sidefill policy to opt-in only for plural-artifact steps: D2/E4/T2/T4/T5.")

    return {
        "meta": {
            "tp008_map_path": str(tp008_path),
            "model_map_path": str(model_map_path),
            "repo_truth_map_path": str(repo_truth_path),
            "scope_mode": "json-managed-only",
            "scope_excluded_as_info": bool(scope_excluded_as_info),
        },
        "summary": {
            "total_findings": len(findings),
            "in_scope_failures": len(fail_findings),
            "finding_code_histogram": dict(sorted(by_code.items())),
        },
        "invariants": {
            "no_auto_transport_flips": observed_policy.get("no_auto_transport_flips"),
            "strict_required_behavior": observed_policy.get("strict_required_behavior"),
        },
        "recommendations": recommendations,
        "findings": findings,
    }


def _find_latest_run_dir(runs_root: Path) -> Path:
    candidates = [p for p in runs_root.iterdir() if p.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No run directories found under {runs_root}")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _discover_raw_json_files(run_dir: Path) -> List[Path]:
    files: List[Path] = []
    for raw_dir in sorted(p for p in run_dir.rglob("raw") if p.is_dir()):
        for file in sorted(raw_dir.iterdir(), key=lambda p: p.name):
            if file.is_file() and file.suffix.lower() == ".json" and "__" in file.name:
                files.append(file)
    return files


def _parse_step_part(filename: str) -> Optional[Tuple[str, str]]:
    match = STEP_PART_RE.match(filename) or STEP_PART_RE2.match(filename)
    if not match:
        return None
    return (str(match.group("step")).upper(), str(match.group("part")).upper())


def _classify_model_usage(
    *,
    provider: str,
    model_id: str,
    expected_step: Dict[str, Any],
) -> str:
    sig = (provider.strip().lower(), model_id.strip())
    primary = [(r["provider"], r["model_id"]) for r in expected_step.get("primary_routes", [])]
    repair = {(r["provider"], r["model_id"]) for r in expected_step.get("repair_routes", [])}
    sidefill = {(r["provider"], r["model_id"]) for r in expected_step.get("sidefill_routes", [])}

    if primary and sig == primary[0]:
        return MODEL_CLASS_MATCH
    if sig in set(primary[1:]) or sig in repair or sig in sidefill:
        return MODEL_CLASS_FALLBACK
    return MODEL_CLASS_DRIFT


def _run_model_usage_audit(
    *,
    run_dir: Path,
    tp008_map: Dict[str, Any],
    repo_scope: Dict[str, Any],
    scope_excluded_as_info: bool,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    raw_files = _discover_raw_json_files(run_dir)
    for path in raw_files:
        parsed = _parse_step_part(path.name)
        if not parsed:
            continue
        step, partition = parsed

        try:
            payload = _read_json(path)
        except Exception:
            continue

        phase = str(payload.get("phase") or step[:1]).strip().upper()
        step_key = _canonical_step_key(phase, step)
        expected = tp008_map["steps"].get(step_key)
        if not isinstance(expected, dict):
            continue

        in_scope = step_key in repo_scope["json_scope"]
        if not in_scope and scope_excluded_as_info:
            continue

        request_meta = payload.get("request_meta") if isinstance(payload.get("request_meta"), dict) else {}
        provider = str(request_meta.get("provider") or "").strip().lower()
        model_id = str(request_meta.get("model_id") or "").strip()
        classification = _classify_model_usage(provider=provider, model_id=model_id, expected_step=expected)

        rows.append(
            {
                "phase": phase,
                "step": step,
                "partition": partition,
                "file": str(path),
                "lane_class": str(expected.get("lane_class") or ""),
                "provider": provider,
                "model_id": model_id,
                "routing_policy": request_meta.get("routing_policy"),
                "no_auto_transport_flips": request_meta.get("no_auto_transport_flips"),
                "classification": classification,
            }
        )

    rows.sort(key=lambda r: (r["phase"], r["step"], r["partition"], r["file"]))

    def _accumulate(rows_in: List[Dict[str, Any]], key_fn) -> Dict[str, Dict[str, Any]]:
        buckets: Dict[str, Dict[str, Any]] = {}
        for row in rows_in:
            key = str(key_fn(row))
            current = buckets.setdefault(
                key,
                {
                    "total": 0,
                    "match": 0,
                    "ladder_fallback_match": 0,
                    "drift": 0,
                },
            )
            current["total"] += 1
            cls = str(row["classification"])
            if cls == MODEL_CLASS_MATCH:
                current["match"] += 1
            elif cls == MODEL_CLASS_FALLBACK:
                current["ladder_fallback_match"] += 1
            else:
                current["drift"] += 1

        for key, current in buckets.items():
            total = max(1, int(current["total"]))
            current["match_pct"] = round((float(current["match"]) / float(total)) * 100.0, 2)
            current["ladder_fallback_match_pct"] = round(
                (float(current["ladder_fallback_match"]) / float(total)) * 100.0, 2
            )
            current["drift_pct"] = round((float(current["drift"]) / float(total)) * 100.0, 2)
        return dict(sorted(buckets.items(), key=lambda kv: kv[0]))

    by_step = _accumulate(rows, lambda r: _canonical_step_key(r["phase"], r["step"]))
    by_phase = _accumulate(rows, lambda r: r["phase"])
    by_lane = _accumulate(rows, lambda r: r["lane_class"])

    top_drift_steps = sorted(
        (
            {
                "step_key": step_key,
                **values,
            }
            for step_key, values in by_step.items()
        ),
        key=lambda row: (-int(row["drift"]), -float(row["drift_pct"]), row["step_key"]),
    )[:20]

    flips_hist: Dict[str, int] = {}
    for row in rows:
        token = str(row.get("no_auto_transport_flips"))
        flips_hist[token] = flips_hist.get(token, 0) + 1

    return {
        "meta": {
            "run_dir": str(run_dir),
            "rows_scanned": len(rows),
        },
        "summary": {
            "total_rows": len(rows),
            "by_step": by_step,
            "by_phase": by_phase,
            "by_lane": by_lane,
            "top_drift_steps": top_drift_steps,
            "no_auto_transport_flips_histogram": dict(sorted(flips_hist.items())),
        },
        "rows": rows,
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_drift_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    meta = payload.get("meta", {})
    summary = payload.get("summary", {})
    lines.append("# TP-008 Drift Audit")
    lines.append("")
    lines.append(f"- tp008_map: `{meta.get('tp008_map_path')}`")
    lines.append(f"- model_map: `{meta.get('model_map_path')}`")
    lines.append(f"- repo_truth_map: `{meta.get('repo_truth_map_path')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- total_findings: {summary.get('total_findings', 0)}")
    lines.append(f"- in_scope_failures: {summary.get('in_scope_failures', 0)}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for row in payload.get("findings", []):
        lines.append(
            f"- [{row.get('severity')}] {row.get('finding_code')} {row.get('step_key')} "
            f"expected={json.dumps(row.get('expected'), sort_keys=True)} "
            f"observed={json.dumps(row.get('observed'), sort_keys=True)}"
        )
    if payload.get("recommendations"):
        lines.append("")
        lines.append("## Recommendations")
        lines.append("")
        for row in payload.get("recommendations", []):
            lines.append(f"- {row}")
    return "\n".join(lines).strip() + "\n"


def _render_model_usage_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    meta = payload.get("meta", {})
    summary = payload.get("summary", {})
    lines.append("# TP-008 Model Usage Audit")
    lines.append("")
    lines.append(f"- run_dir: `{meta.get('run_dir')}`")
    lines.append(f"- rows_scanned: {meta.get('rows_scanned', 0)}")
    lines.append("")
    lines.append("## By Lane")
    lines.append("")
    by_lane = summary.get("by_lane", {}) if isinstance(summary.get("by_lane"), dict) else {}
    for lane, row in sorted(by_lane.items()):
        lines.append(
            f"- {lane}: total={row.get('total', 0)} match={row.get('match', 0)} "
            f"fallback={row.get('ladder_fallback_match', 0)} drift={row.get('drift', 0)}"
        )
    lines.append("")
    lines.append("## Top Drift Steps")
    lines.append("")
    for row in summary.get("top_drift_steps", [])[:20]:
        lines.append(
            f"- {row.get('step_key')}: total={row.get('total', 0)} drift={row.get('drift', 0)} "
            f"drift_pct={row.get('drift_pct', 0)}"
        )
    return "\n".join(lines).strip() + "\n"


# ---------------- Legacy audit mode (existing behavior) ----------------

def read_json_lenient(p: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        text = _read_text(p)
    except Exception as e:
        return None, f"read_error:{e}"

    text = text.strip()
    if not text:
        return None, "empty_file"

    if p.suffix.lower() == ".txt":
        first_line = text.splitlines()[0].strip()
        try:
            payload = json.loads(first_line)
            if not isinstance(payload, dict):
                return None, "json_first_line_not_object"
            return payload, None
        except Exception as e:
            return None, f"json_parse_error_first_line:{e}"

    try:
        payload = json.loads(text)
        if not isinstance(payload, dict):
            return None, "json_not_object"
        return payload, None
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

    key_candidates = [step_id, f"{step_id[:1]}:{step_id}"]
    sc = None
    for key in key_candidates:
        candidate = steps.get(key)
        if isinstance(candidate, dict):
            sc = candidate
            break
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
        return Failure("schema_missing_key", "missing_key:path", item_id=str(item.get("id")) if "id" in item else None)
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
            return Failure("contract_items_not_list", "payload.items is not a list", artifact_name=name)
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


def audit_partition_file(contract_map: Dict[str, Any], step_id: str, part_id: str, path: Path) -> Dict[str, Any]:
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
        result["failures"].append({"kind": "schema_missing_key", "detail": "missing_or_invalid:artifacts"})
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
            result["failures"].append({"kind": "missing_expected_artifacts", "detail": ",".join(missing)})

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


def write_legacy_outputs(out_dir: Path, results: List[Dict[str, Any]]) -> None:
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
    _write_json(out_dir / "AUDIT_contract_rollup.json", rollup)
    _write_json(out_dir / "AUDIT_partition_results.json", {"results": results})

    lines = [
        "TP-008 AUDIT ROLLUP",
        f"total={total} ok={ok} fail={fail} parse_fail={parse_fail}",
        "",
        "Failure histogram:",
    ]
    for k, v in rollup["failure_histogram"].items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("First failures (up to 50):")
    for ff in rollup["first_failures"]:
        f = ff["failure"] or {}
        lines.append(f"- {ff['step']} {ff['partition']} :: {f.get('kind')} :: {f.get('detail')} :: {ff['file']}")
    (out_dir / "AUDIT_contract_rollup.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_legacy_contract_audit(run_dir: Path, out_dir: Path, only_step: str = "") -> Dict[str, Any]:
    contract_path = find_contract_map(run_dir)
    contract_map = load_contract_map(contract_path)
    raw_files = discover_raw_files(run_dir)
    results: List[Dict[str, Any]] = []
    for p in raw_files:
        sp = parse_step_part(p.name)
        if not sp:
            continue
        step_id, part_id = sp
        if only_step and step_id.upper() != only_step.upper():
            continue
        results.append(audit_partition_file(contract_map, step_id, part_id, p))
    results.sort(key=lambda r: (r["step"], r["partition"], r["file"]))

    meta = {
        "run_dir": str(run_dir),
        "contract_map": str(contract_path),
        "only_step": only_step or None,
        "partitions_scanned": len(results),
    }
    _write_json(out_dir / "AUDIT_meta.json", meta)
    write_legacy_outputs(out_dir, results)
    return {"meta": meta, "results": results}


def main() -> int:
    ap = argparse.ArgumentParser(description="TP-008 contract/drift/model-usage audit")
    ap.add_argument("--run-dir", default="", help="Run root directory for partition/model usage scans")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Directory to write reports")
    ap.add_argument("--only-step", default="", help="Optional single step filter")

    ap.add_argument("--tp008-map", default="", help="Canonical TP-008 mapping file (YAML/JSON)")
    ap.add_argument("--check-model-usage", action="store_true", help="Audit run raw model usage against expected ladder")

    ap.add_argument("--scope-mode", default="json-managed-only", choices=["json-managed-only"])

    scope_group = ap.add_mutually_exclusive_group()
    scope_group.add_argument("--scope-excluded-as-info", action="store_true", default=True)
    scope_group.add_argument("--scope-excluded-as-fail", action="store_true")

    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    scope_excluded_as_info = bool(args.scope_excluded_as_info and not args.scope_excluded_as_fail)

    tp008_map_path = Path(args.tp008_map).expanduser().resolve() if args.tp008_map else None
    run_dir = Path(args.run_dir).expanduser().resolve() if args.run_dir else None

    # Legacy mode (backward compatible): no canonical map provided.
    if tp008_map_path is None:
        if args.check_model_usage:
            raise SystemExit("--check-model-usage requires --tp008-map")
        if run_dir is None:
            raise SystemExit("Legacy mode requires --run-dir")
        _run_legacy_contract_audit(run_dir=run_dir, out_dir=out_dir, only_step=args.only_step)
        return 0

    repo_scope = _load_repo_truth_scope(REPO_TRUTH_MAP_PATH)
    model_map = _load_model_map(MODEL_MAP_PATH)
    tp008_map = _load_tp008_map(tp008_map_path, repo_scope)

    drift_payload = _run_static_drift_audit(
        tp008_path=tp008_map_path,
        tp008_map=tp008_map,
        model_map_path=MODEL_MAP_PATH,
        model_map=model_map,
        repo_truth_path=REPO_TRUTH_MAP_PATH,
        repo_scope=repo_scope,
        scope_excluded_as_info=scope_excluded_as_info,
    )

    _write_json(out_dir / "TP008_DRIFT_AUDIT.json", drift_payload)
    (out_dir / "TP008_DRIFT_AUDIT.md").write_text(_render_drift_markdown(drift_payload), encoding="utf-8")

    if args.check_model_usage:
        if run_dir is None:
            run_dir = _find_latest_run_dir(DEFAULT_RUNS_ROOT)

        usage_payload = _run_model_usage_audit(
            run_dir=run_dir,
            tp008_map=tp008_map,
            repo_scope=repo_scope,
            scope_excluded_as_info=scope_excluded_as_info,
        )
        _write_json(out_dir / "TP008_MODEL_USAGE_AUDIT.json", usage_payload)
        (out_dir / "TP008_MODEL_USAGE_AUDIT.md").write_text(
            _render_model_usage_markdown(usage_payload),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
