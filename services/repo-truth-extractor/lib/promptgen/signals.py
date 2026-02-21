from __future__ import annotations

from typing import Any, Dict


def _bool_as_float(value: Any) -> float:
    return 1.0 if bool(value) else 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _cap01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def compute_signals(repo_fingerprint: Dict[str, Any], archetypes_payload: Dict[str, Any]) -> Dict[str, float]:
    archetypes = archetypes_payload.get("archetypes") if isinstance(archetypes_payload.get("archetypes"), dict) else {}
    surface = archetypes_payload.get("surface_areas") if isinstance(archetypes_payload.get("surface_areas"), dict) else {}
    contracts = archetypes_payload.get("contracts_present") if isinstance(archetypes_payload.get("contracts_present"), dict) else {}

    filetype_counts = repo_fingerprint.get("filetype_counts") if isinstance(repo_fingerprint.get("filetype_counts"), dict) else {}
    language_counts = repo_fingerprint.get("language_counts") if isinstance(repo_fingerprint.get("language_counts"), dict) else {}

    docs_count = _safe_float(surface.get("docs_file_count", 0.0))
    code_count = _safe_float(surface.get("code_file_count", 0.0))
    docs_to_code = docs_count / code_count if code_count > 0 else 0.0

    signals: Dict[str, float] = {
        "is_monorepo": _bool_as_float((archetypes.get("monorepo") or {}).get("value")),
        "is_microservices": _bool_as_float((archetypes.get("microservices") or {}).get("value")),
        "is_single_service": _bool_as_float((archetypes.get("single_service_app") or {}).get("value")),
        "is_event_driven": _bool_as_float((archetypes.get("event_driven_likely") or {}).get("value")),
        "is_db_heavy": _bool_as_float((archetypes.get("db_heavy") or {}).get("value")),
        "is_plugin_system": _bool_as_float((archetypes.get("plugin_system_likely") or {}).get("value")),
        "is_node_ts_monorepo": _bool_as_float((archetypes.get("node_typescript_monorepo") or {}).get("value")),
        "is_docs_first": _bool_as_float((archetypes.get("docs_first_spec_driven") or {}).get("value")),
        "has_event_contracts": _bool_as_float(contracts.get("event_taxonomy")),
        "has_db_contracts": _bool_as_float(contracts.get("db_schema")),
        "has_api_specs": _bool_as_float(contracts.get("api_specs")),
        "has_adrs": _bool_as_float(contracts.get("adrs")),
        "services_root_count_norm": _cap01(_safe_float(surface.get("services_root_count", 0.0)) / 10.0),
        "dockerfile_count_norm": _cap01(_safe_float(surface.get("dockerfile_count", 0.0)) / 10.0),
        "docs_to_code_ratio_norm": _cap01(docs_to_code / 4.0),
        "python_present": _cap01(_safe_float(language_counts.get("python", 0.0))),
        "node_present": _cap01(_safe_float(language_counts.get("javascript", 0.0) + language_counts.get("typescript", 0.0))),
        "has_pyproject": 1.0 if "python" in language_counts and filetype_counts.get(".toml") else 0.0,
    }

    # collapse presence signals to 0/1
    for key in ["python_present", "node_present"]:
        signals[key] = 1.0 if signals[key] > 0 else 0.0
    return dict(sorted(signals.items()))
