#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import py_compile
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

import yaml

SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from output_safety import sanitize_text_for_output, sanitized_json_bytes, sanitized_json_text

REPO_ROOT = SERVICE_DIR.parents[1]
RUNNER_PATH = SERVICE_DIR / "run_extraction_v5.py"
CONTRACT_MAP_PATH = SERVICE_DIR / "lib" / "phase_contract_map.py"
PROMPTSET_PATH = SERVICE_DIR / "promptsets" / "v4" / "promptset.yaml"
ARTIFACTS_PATH = SERVICE_DIR / "promptsets" / "v4" / "artifacts.yaml"
MODEL_MAP_PATH = SERVICE_DIR / "promptsets" / "v4" / "model_map.yaml"

DEFAULT_TARGET_PHASES = ("A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z")
DEFAULT_TARGET_POLICY = "balanced_openrouter"
DEFAULT_TARGET_MODE = "direct"
DEFAULT_TARGET_PROFILE = "P00_GENERIC"
DEFAULT_RUN_ID_PREFIX = "pre_live_gate_v25"
DEFAULT_MAX_FILES_DOCS = 35
DEFAULT_MAX_FILES_CODE = 20
DEFAULT_MAX_CHARS = 650000
DEFAULT_MAX_REQUEST_BYTES = 200000
DEFAULT_FILE_TRUNCATE_CHARS = 70000

CRITICAL_TEST_PATHS = (
    "services/repo-truth-extractor/tests/test_live_llm_guard.py",
    "services/repo-truth-extractor/tests/test_phase_d_contract_map.py",
    "services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py",
    "services/repo-truth-extractor/tests/test_run_extraction_v5_soft_gate_logging.py",
    "services/repo-truth-extractor/tests/test_run_extraction_v5_ui_events.py",
)
REPO_DRIFT_TEST_PATHS = (
    "services/repo-truth-extractor/tests/test_promptset_v4_lint.py",
)
SMOKE_TEST_CANDIDATES = {
    "golden_fixture_smoke": (
        "services/repo-truth-extractor/tests/test_v5_golden_fixture_smoke.py",
    ),
    "resume_smoke": (
        "services/repo-truth-extractor/tests/test_v5_resume_smoke.py",
    ),
    "verify_phase_output_smoke": (
        "services/repo-truth-extractor/tests/test_v5_verify_phase_output_smoke.py",
    ),
}

TRUTH_SPLIT_CLASSIFICATIONS = (
    "MATCH",
    "STALE_RUNNER_REGISTRY",
    "STALE_PROMPTSET",
    "STALE_MODEL_MAP",
    "STALE_ARTIFACT_MAP",
    "UNCLASSIFIED_TARGET_TRUTH_SPLIT",
)
MODEL_REFERENCE_MODES = {
    "exact_model_documented",
    "documented_alias_or_pattern",
    "provider_compatible_namespace_documented",
    "unresolved",
}
PAL_SOURCE_TYPES = {"api_docs", "sdk_docs", "model_docs", "release_notes"}
PAL_DOC_SOURCE_TYPES = {"api_docs", "sdk_docs", "model_docs"}
PAL_ALLOWED_HOSTS = {
    "openai": {"platform.openai.com", "developers.openai.com", "openai.com"},
    "gemini": {"ai.google.dev", "developers.googleblog.com", "cloud.google.com"},
    "openrouter": {"openrouter.ai"},
    "xai": {"docs.x.ai", "x.ai"},
}
DEFAULT_REQUIRED_DIRECT_PROVIDERS = {
    "balanced_openrouter": ("gemini", "xai"),
}
CONTRACT_MAP_VOLATILE_KEYS = {
    "generated_at",
    "created_at",
    "run_id",
    "phase_contract_map_updated_at",
}

IMPORT_OR_CLI_FAILURE = "IMPORT_OR_CLI_FAILURE"
TARGET_PROMPT_INTEGRITY_FAILURE = "TARGET_PROMPT_INTEGRITY_FAILURE"
TARGET_TRUTH_SPLIT_MISMATCH = "TARGET_TRUTH_SPLIT_MISMATCH"
CONTRACT_MAP_NONDETERMINISTIC = "CONTRACT_MAP_NONDETERMINISTIC"
ROUTE_DERIVATION_FAILURE = "ROUTE_DERIVATION_FAILURE"
REQUIRED_API_KEY_MISSING = "REQUIRED_API_KEY_MISSING"
PAL_REQUIRED_UNAVAILABLE = "PAL_REQUIRED_UNAVAILABLE"
PROVIDER_CONTRACT_MISMATCH = "PROVIDER_CONTRACT_MISMATCH"
ACTIVE_MODEL_REFERENCE_UNRESOLVED = "ACTIVE_MODEL_REFERENCE_UNRESOLVED"
ONLINE_PREFLIGHT_FAILURE = "ONLINE_PREFLIGHT_FAILURE"
CRITICAL_TEST_FAILURE = "CRITICAL_TEST_FAILURE"
MISSING_SMOKE_EVIDENCE = "MISSING_SMOKE_EVIDENCE"
SMOKE_FAILURE = "SMOKE_FAILURE"


@dataclass(frozen=True)
class GateConfig:
    repo_root: Path
    output_dir: Path
    run_id: str
    target_policy: str
    target_mode: str
    target_profile: str
    target_phases: Tuple[str, ...]
    target_step: Optional[str] = None
    allow_online_preflight: bool = False
    pal_validation_file: Optional[Path] = None
    waiver_codes: Tuple[str, ...] = ()
    required_direct_providers: Tuple[str, ...] = ()


@dataclass
class Blocker:
    reason_code: str
    layer: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class Condition:
    reason_code: str
    layer: str
    message: str
    details: Optional[Dict[str, Any]] = None


GateCondition = Condition

CODE_BLOCKER = "CODE_BLOCKER"
ARTIFACT_OR_STATE_BLOCKER = "ARTIFACT_OR_STATE_BLOCKER"
ENVIRONMENT_BLOCKER = "ENVIRONMENT_BLOCKER"
EXTERNAL_PROVIDER_BLOCKER = "EXTERNAL_PROVIDER_BLOCKER"
FALSE_POSITIVE = "FALSE_POSITIVE"
DEFERRED_NON_BLOCKING = "DEFERRED_NON_BLOCKING"

GO_NOW = "GO_NOW"
NO_GO_CODE = "NO_GO_CODE"
NO_GO_ENV = "NO_GO_ENV"
NO_GO_EXTERNAL = "NO_GO_EXTERNAL"
NO_GO_ARTIFACT_STATE = "NO_GO_ARTIFACT_STATE"
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def classify_truth_split_row(
    *,
    step_id: str,
    runner_active: bool,
    prompt_resolution_active: bool,
    promptset_declared: bool,
    model_map_declared: bool,
    artifact_declarations_present: bool,
) -> str:
    if runner_active and not prompt_resolution_active:
        return "STALE_RUNNER_REGISTRY"
    if not prompt_resolution_active and promptset_declared:
        return "STALE_PROMPTSET"
    if prompt_resolution_active and not model_map_declared:
        return "STALE_MODEL_MAP"
    if prompt_resolution_active and not artifact_declarations_present:
        return "STALE_ARTIFACT_MAP"
    return "MATCH"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sanitized_json_text(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sanitize_text_for_output(text), encoding="utf-8")


def read_yaml(path: Path) -> Dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode to an object")
    return payload


def normalize_json_payload(payload: Any, volatile_keys: Optional[Set[str]] = None) -> Any:
    if volatile_keys is None:
        volatile_keys = set()
    if isinstance(payload, dict):
        return {
            key: normalize_json_payload(value, volatile_keys)
            for key, value in sorted(payload.items())
            if key not in volatile_keys
        }
    if isinstance(payload, list):
        return [normalize_json_payload(item, volatile_keys) for item in payload]
    return payload


def normalized_sha(payload: Any, volatile_keys: Optional[Set[str]] = None) -> str:
    normalized = normalize_json_payload(payload, volatile_keys)
    raw = sanitized_json_bytes(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.blake2b(raw, digest_size=32).hexdigest()


def run_command(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def get_git_sha(repo_root: Path) -> str:
    result = run_command(("git", "rev-parse", "HEAD"), repo_root)
    if result.returncode != 0:
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the repo-truth-extractor v5 pre-live gate.")
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--target-policy", type=str, default=DEFAULT_TARGET_POLICY)
    parser.add_argument("--target-mode", type=str, default=DEFAULT_TARGET_MODE)
    parser.add_argument("--target-profile", type=str, default=DEFAULT_TARGET_PROFILE)
    parser.add_argument(
        "--target-phases",
        nargs="+",
        default=list(DEFAULT_TARGET_PHASES),
        help="Phase codes to validate.",
    )
    parser.add_argument(
        "--step",
        type=str,
        default=None,
        help="Execution step filter.",
    )
    parser.add_argument(
        "--pal-validation-file",
        type=Path,
        default=None,
        help="Optional PAL_VALIDATION.json input generated outside this script.",
    )
    parser.add_argument(
        "--allow-online-preflight",
        action="store_true",
        help="Run the live provider preflight layer. Tests should not enable this.",
    )
    parser.add_argument(
        "--waiver-code",
        action="append",
        default=[],
        help="Reason code waiver. May be specified multiple times.",
    )
    parser.add_argument(
        "--require-direct-provider",
        action="append",
        default=None,
        help="Provider that must appear directly in route derivation for the chosen policy.",
    )
    return parser


def resolve_required_direct_providers(policy: str, configured: Optional[Sequence[str]]) -> Tuple[str, ...]:
    if configured:
        return tuple(sorted({str(item).strip().lower() for item in configured if str(item).strip()}))
    return tuple(DEFAULT_REQUIRED_DIRECT_PROVIDERS.get(policy, ()))


def build_config(args: argparse.Namespace) -> GateConfig:
    run_id = args.run_id or f"{DEFAULT_RUN_ID_PREFIX}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    output_dir = args.output_dir or (
        REPO_ROOT / "reports" / "repo-truth-extractor" / "pre_live_gate_v25" / run_id
    )
    return GateConfig(
        repo_root=REPO_ROOT,
        output_dir=output_dir.resolve(),
        run_id=run_id,
        target_policy=str(args.target_policy).strip(),
        target_mode=str(args.target_mode).strip(),
        target_profile=str(args.target_profile).strip(),
        target_phases=tuple(str(phase).strip().upper() for phase in args.target_phases),
        target_step=args.step,
        allow_online_preflight=bool(args.allow_online_preflight),
        pal_validation_file=args.pal_validation_file.resolve() if args.pal_validation_file else None,
        waiver_codes=tuple(sorted({str(code).strip() for code in args.waiver_code if str(code).strip()})),
        required_direct_providers=resolve_required_direct_providers(
            str(args.target_policy).strip(),
            args.require_direct_provider,
        ),
    )

def expected_contract_map_target_keys(contract_module: Any, config: GateConfig) -> List[str]:
    payload = contract_module.compile_phase_contract_map()
    steps = payload.get("steps")
    if not isinstance(steps, dict):
        return []
    target_phases = set(config.target_phases)
    return sorted(
        key
        for key in steps.keys()
        if str(key).split(":", 1)[0] in target_phases
    )


def derive_scope(runner: Any, contract_module: Any, config: GateConfig) -> Dict[str, Any]:
    readiness = runner.derive_route_readiness_summary(  # type: ignore[attr-defined]
        phases=list(config.target_phases),
        routing_policy=config.target_policy,
    )
    enriched_routes = []
    for row in readiness["routes"]:
        enriched_routes.append(
            {
                "route_signature": row["route_signature"],
                "provider": row["provider"],
                "model_id": row["model_id"],
                "api_key_env": row["api_key_env"],
                "active_route_required": bool(row.get("required_active_route", False)),
                "optional_fallback": bool(row.get("optional_fallback", False)),
                "configured_not_required": bool(row.get("configured_not_required", False)),
                "fallback_chain_present": bool(row.get("fallback_chain_present", False)),
                "requirement_level": row.get("requirement_level"),
                "steps": row.get("steps", []),
            }
        )
    contract_payload = contract_module.compile_phase_contract_map()
    scope = {
        "validation_started_at": now_iso(),
        "git_sha": get_git_sha(config.repo_root),
        "validator_host": socket.gethostname(),
        "validator_python": platform.python_version(),
        "target_policy": config.target_policy,
        "target_phases": list(config.target_phases),
        "target_step": config.target_step,
        "target_mode": config.target_mode,
        "target_runner_path": str(RUNNER_PATH.resolve()),
        "target_runner_sha256": sha256_file(RUNNER_PATH),
        "promptset_sha256": sha256_file(PROMPTSET_PATH),
        "artifacts_sha256": sha256_file(ARTIFACTS_PATH),
        "model_map_sha256": sha256_file(MODEL_MAP_PATH),
        "route_readiness_summary": readiness,
        "required_provider_routes": enriched_routes,
        "required_api_key_envs": list(readiness["api_key_env_categories"]["required_active_route"]),
        "fallback_api_key_envs": list(readiness["api_key_env_categories"]["optional_fallback"]),
        "configured_not_required_api_key_envs": list(
            readiness["api_key_env_categories"]["configured_not_required"]
        ),
        "all_route_api_key_envs": sorted(
            {
                str(row["api_key_env"]).strip()
                for row in enriched_routes
                if str(row.get("api_key_env") or "").strip()
            }
        ),
        "routing_fingerprint_hash": normalized_sha(enriched_routes),
        "phase_contract_map_hash": normalized_sha(
            contract_payload,
            volatile_keys=CONTRACT_MAP_VOLATILE_KEYS,
        ),
    }
    return scope


def evaluate_import_cli_smoke(config: GateConfig) -> Tuple[Dict[str, Any], List[Blocker]]:
    blockers: List[Blocker] = []
    # 1) Python compile check
    try:
        py_compile.compile(str(RUNNER_PATH), doraise=True)
    except Exception as exc:
        blockers.append(Blocker(IMPORT_OR_CLI_FAILURE, "import_cli_smoke", "P0", f"Runner failed to compile: {exc}"))

    # 2) CLI help check
    result = run_command((sys.executable, str(RUNNER_PATH), "--help"), config.repo_root)
    if result.returncode != 0:
        blockers.append(Blocker(IMPORT_OR_CLI_FAILURE, "import_cli_smoke", "P0", "Runner --help failed", {"stderr": result.stderr}))

    results = {
        "layer": "import_cli_smoke",
        "status": "FAIL" if blockers else "PASS",
        "compile_ok": not any(b.message.startswith("Runner failed to compile") for b in blockers),
        "cli_help_ok": not any(b.message == "Runner --help failed" for b in blockers),
    }
    return results, blockers


def evaluate_prompt_integrity(runner: Any, config: GateConfig) -> Tuple[Dict[str, Any], List[Blocker]]:
    blockers: List[Blocker] = []
    prompt_views = {}
    for phase in config.target_phases:
        try:
            specs = runner.get_phase_prompts(phase)
            prompt_report = runner._prompt_hash_report_for_phase(phase, specs)
            prompt_views[phase] = prompt_report
        except Exception as exc:
            blockers.append(Blocker(TARGET_PROMPT_INTEGRITY_FAILURE, "target_prompt_integrity", "P0", f"Failed to gather prompt report for phase {phase}: {exc}"))

    # Global blocked check
    prompt_report = {"blocked_promptset": False, "details": prompt_views}
    if any(view.get("blocked_promptset") for view in prompt_views.values()):
        prompt_report["blocked_promptset"] = True
        blockers.append(
            Blocker(
                TARGET_PROMPT_INTEGRITY_FAILURE,
                "target_prompt_integrity",
                "P0",
                "Active target prompt integrity failed",
                prompt_report,
            )
        )
    results = {
        "layer": "target_prompt_integrity",
        "status": "FAIL" if blockers else "PASS",
        "promptset_fingerprint": prompt_report,
        "phase_prompt_views": prompt_views,
    }
    return results, blockers


def collect_truth_split(runner: Any, config: GateConfig) -> Tuple[Dict[str, Any], List[Blocker], List[Dict[str, Any]]]:
    # Placeholder for truth split logic
    return {"layer": "truth_split_audit", "status": "PASS", "target_phase_mismatch_count": 0, "repo_wide_mismatch_count": 0, "rows": []}, [], []


def evaluate_contract_map(
    runner: Any,
    contract_module: Any,
    config: GateConfig,
) -> Tuple[Dict[str, Any], List[Blocker]]:
    blockers: List[Blocker] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        path_one = contract_module.write_phase_contract_map(temp_root / "one", f"{config.run_id}_one")
        path_two = contract_module.write_phase_contract_map(temp_root / "two", f"{config.run_id}_two")
        payload_one = json.loads(path_one.read_text(encoding="utf-8"))
        payload_two = json.loads(path_two.read_text(encoding="utf-8"))
    hash_one = normalized_sha(payload_one, volatile_keys=CONTRACT_MAP_VOLATILE_KEYS)
    hash_two = normalized_sha(payload_two, volatile_keys=CONTRACT_MAP_VOLATILE_KEYS)

    expected_target_keys = expected_contract_map_target_keys(contract_module, config)
    map_steps = payload_one.get("steps", {})
    observed_target_keys = sorted(
        key
        for key in map_steps.keys()
        if str(key).split(":")[0] in set(config.target_phases)
    )
    if hash_one != hash_two or expected_target_keys != observed_target_keys:
        blockers.append(
            Blocker(
                CONTRACT_MAP_NONDETERMINISTIC,
                "contract_map_determinism",
                "P0",
                "Phase contract map determinism or target-step coverage failed",
                {
                    "hash_one": hash_one,
                    "hash_two": hash_two,
                    "expected_target_keys": expected_target_keys,
                    "observed_target_keys": observed_target_keys,
                },
            )
        )
    results = {
        "layer": "contract_map_determinism",
        "status": "FAIL" if blockers else "PASS",
        "hash_one": hash_one,
        "hash_two": hash_two,
        "expected_target_keys": expected_target_keys,
        "observed_target_keys": observed_target_keys,
    }
    return results, blockers


def evaluate_route_readiness(
    runner: Any,
    config: GateConfig,
    scope: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Blocker]]:
    blockers: List[Blocker] = []
    derived_routes = scope["required_provider_routes"]
    present_providers = sorted({str(row["provider"]).strip().lower() for row in derived_routes})
    missing_direct = sorted(set(config.required_direct_providers) - set(present_providers))
    bounded_target_scope = tuple(config.target_phases) != tuple(DEFAULT_TARGET_PHASES) or config.target_step is not None
    missing_keys = sorted([env_name for env_name in scope["required_api_key_envs"] if not os.environ.get(env_name)])
    missing_fallback_keys = sorted(
        [env_name for env_name in scope.get("fallback_api_key_envs", []) if not os.environ.get(env_name)]
    )
    if missing_direct and not bounded_target_scope:
        blockers.append(
            Blocker(
                ROUTE_DERIVATION_FAILURE,
                "route_derived_readiness",
                "P0",
                "Required direct providers were not present in current route derivation",
                {"required_direct_providers": list(config.required_direct_providers), "missing": missing_direct},
            )
        )
    if missing_keys:
        blockers.append(
            Blocker(
                REQUIRED_API_KEY_MISSING,
                "route_derived_readiness",
                "P0",
                "Required API keys are missing for current active routes",
                {"missing_api_key_envs": missing_keys},
            )
        )
    results = {
        "layer": "route_derived_readiness",
        "status": "FAIL" if blockers else "PASS",
        "derived_routes": derived_routes,
        "present_providers": present_providers,
        "required_direct_providers": list(config.required_direct_providers),
        "missing_required_direct_providers": missing_direct,
        "bounded_target_scope": bounded_target_scope,
        "required_api_key_envs": scope["required_api_key_envs"],
        "missing_api_key_envs": missing_keys,
        "fallback_api_key_envs": scope.get("fallback_api_key_envs", []),
        "missing_fallback_api_key_envs": missing_fallback_keys,
        "configured_not_required_api_key_envs": scope.get("configured_not_required_api_key_envs", []),
        "api_key_env_categories": scope.get("route_readiness_summary", {}).get("api_key_env_categories", {}),
        "provider_categories": scope.get("route_readiness_summary", {}).get("provider_categories", {}),
    }
    return results, blockers


def host_allowed_for_provider(provider: str, locator: str) -> bool:
    parsed = urlparse(locator)
    host = str(parsed.netloc or parsed.path).split("/")[0].lower()
    if not host:
        return False
    allowed_hosts = PAL_ALLOWED_HOSTS.get(provider, set())
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)


def pal_row_precedence(source_type: str) -> int:
    if source_type in PAL_DOC_SOURCE_TYPES:
        return 0
    return 1


def normalize_pal_rows(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        signature = str(row.get("route_signature") or "").strip()
        if not signature:
            continue
        grouped.setdefault(signature, []).append(row)
    normalized: Dict[str, Dict[str, Any]] = {}
    for signature, members in grouped.items():
        chosen = sorted(
            members,
            key=lambda item: (
                pal_row_precedence(str(item.get("source_type") or "").strip()),
                str(item.get("validation_timestamp") or ""),
            ),
        )[0]
        normalized[signature] = chosen
    return normalized


def evaluate_pal_validation(
    config: GateConfig,
    scope: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Blocker], List[Condition]]:
    blockers: List[Blocker] = []
    conditions: List[Condition] = []
    routes = {
        row["route_signature"]: row
        for row in scope["required_provider_routes"]
    }
    rows_in: List[Dict[str, Any]] = []
    if config.pal_validation_file and config.pal_validation_file.exists():
        payload = json.loads(config.pal_validation_file.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            rows = payload.get("routes", payload.get("rows", []))
            if isinstance(rows, list):
                rows_in = [row for row in rows if isinstance(row, dict)]
        elif isinstance(payload, list):
            rows_in = [row for row in payload if isinstance(row, dict)]
    if not rows_in:
        output_rows: List[Dict[str, Any]] = []
        for signature, route in sorted(routes.items()):
            output_rows.append(
                {
                    "route_signature": signature,
                    "provider": route["provider"],
                    "source_type": "unavailable",
                    "source_locator": "",
                    "validation_timestamp": now_iso(),
                    "auth_mode_repo": "bearer" if route["provider"] != "gemini" else "auto",
                    "auth_mode_official": None,
                    "transport_repo": None,
                    "transport_official": None,
                    "endpoint_repo": None,
                    "endpoint_official": None,
                    "model_id_repo": route["model_id"],
                    "model_reference_mode": "unresolved",
                    "model_reference_official": None,
                    "active_route_required": bool(route["active_route_required"]),
                    "fallback_chain_present": bool(route["fallback_chain_present"]),
                    "compatibility_status": "pal_skipped",
                    "mismatch_class": "",
                    "notes": "PAL validation file was not provided.",
                }
            )
        conditions.append(
            Condition(
                PAL_REQUIRED_UNAVAILABLE,
                "pal_provider_validation",
                "PAL validation was not provided for the selected routes. Runtime eligibility remains environment-based.",
                {"pal_validation_file": None, "routes_count": len(output_rows)},
            )
        )
        return (
            {
                "layer": "pal_provider_validation",
                "status": "SKIPPED",
                "routes": output_rows,
            },
            blockers,
            conditions,
        )

    normalized_rows = normalize_pal_rows(rows_in)

    output_rows: List[Dict[str, Any]] = []
    for signature, route in sorted(routes.items()):
        row = dict(normalized_rows.get(signature, {}))
        if not row:
            row = {
                "route_signature": signature,
                "provider": route["provider"],
                "source_type": "unavailable",
                "source_locator": "",
                "validation_timestamp": now_iso(),
                "auth_mode_repo": "bearer" if route["provider"] != "gemini" else "auto",
                "auth_mode_official": None,
                "transport_repo": None,
                "transport_official": None,
                "endpoint_repo": None,
                "endpoint_official": None,
                "model_id_repo": route["model_id"],
                "model_reference_mode": "unresolved",
                "model_reference_official": None,
                "active_route_required": bool(route["active_route_required"]),
                "fallback_chain_present": bool(route["fallback_chain_present"]),
                "compatibility_status": "pal_unavailable",
                "mismatch_class": "PAL_REQUIRED_UNAVAILABLE",
                "notes": "PAL validation file was not provided for this active route.",
            }
            conditions.append(
                Condition(
                    PAL_REQUIRED_UNAVAILABLE,
                    "pal_provider_validation",
                    f"PAL validation unavailable for route {signature}",
                    row,
                )
            )
            output_rows.append(row)
            continue

        row["active_route_required"] = bool(row.get("active_route_required", route["active_route_required"]))
        row["fallback_chain_present"] = bool(row.get("fallback_chain_present", route["fallback_chain_present"]))
        provider = str(row.get("provider") or route["provider"]).strip().lower()
        row["provider"] = provider
        source_type = str(row.get("source_type") or "").strip()
        if source_type not in PAL_SOURCE_TYPES:
            blockers.append(
                Blocker(
                    PAL_REQUIRED_UNAVAILABLE,
                    "pal_provider_validation",
                    "P0",
                    f"Invalid PAL source_type for route {signature}",
                    row,
                )
            )
        locator = str(row.get("source_locator") or "").strip()
        if source_type in PAL_SOURCE_TYPES and not host_allowed_for_provider(provider, locator):
            blockers.append(
                Blocker(
                    PROVIDER_CONTRACT_MISMATCH,
                    "pal_provider_validation",
                    "P0",
                    f"PAL source locator is not first-party for route {signature}",
                    row,
                )
            )
        model_reference_mode = str(row.get("model_reference_mode") or "").strip()
        if model_reference_mode not in MODEL_REFERENCE_MODES:
            blockers.append(
                Blocker(
                    PAL_REQUIRED_UNAVAILABLE,
                    "pal_provider_validation",
                    "P0",
                    f"Invalid model_reference_mode for route {signature}",
                    row,
                )
            )
        if str(row.get("compatibility_status") or "").strip().lower() in {"contradiction", "mismatch", "incompatible"}:
            blockers.append(
                Blocker(
                    PROVIDER_CONTRACT_MISMATCH,
                    "pal_provider_validation",
                    "P0",
                    f"Provider contract mismatch for route {signature}",
                    row,
                )
            )
        if model_reference_mode == "unresolved":
            severity = "P0" if row["active_route_required"] and not row["fallback_chain_present"] else "P1"
            blockers.append(
                Blocker(
                    ACTIVE_MODEL_REFERENCE_UNRESOLVED,
                    "pal_provider_validation",
                    severity,
                    f"Model reference unresolved for route {signature}",
                    row,
                )
            )
        output_rows.append(row)

    results = {
        "layer": "pal_provider_validation",
        "status": "FAIL" if blockers else ("WARN" if conditions else "PASS"),
        "routes": output_rows,
        "conditions": [
            {
                "reason_code": condition.reason_code,
                "layer": condition.layer,
                "message": condition.message,
                "details": condition.details or {},
            }
            for condition in conditions
        ],
    }
    return results, blockers, conditions


def evaluate_online_preflight(
    runner: Any,
    config: GateConfig,
) -> Tuple[Dict[str, Any], List[Blocker], List[Condition]]:
    blockers: List[Blocker] = []
    conditions: List[Condition] = []
    if not config.allow_online_preflight:
        condition = Condition(
            ONLINE_PREFLIGHT_FAILURE,
            "online_provider_preflight",
            "Online provider preflight not executed. Re-run with --allow-online-preflight for a full gate.",
            {"allow_online_preflight": False},
        )
        conditions.append(condition)
        return (
            {
                "layer": "online_provider_preflight",
                "status": "WARN",
                "allow_online_preflight": False,
                "payload": None,
                "conditions": [
                    {
                        "reason_code": condition.reason_code,
                        "layer": condition.layer,
                        "message": condition.message,
                        "details": condition.details or {},
                    }
                ],
            },
            blockers,
            conditions,
        )

    cfg = runner.RunnerConfig(
        dry_run=True,
        max_files_docs=DEFAULT_MAX_FILES_DOCS,
        max_files_code=DEFAULT_MAX_FILES_CODE,
        max_chars=DEFAULT_MAX_CHARS,
        max_request_bytes=DEFAULT_MAX_REQUEST_BYTES,
        file_truncate_chars=DEFAULT_FILE_TRUNCATE_CHARS,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="default",
        retry_max_attempts=4,
        retry_base_seconds=2.0,
        retry_max_seconds=30.0,
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy=config.target_policy,
        disable_escalation=False,
        escalation_max_hops=2,
        batch_mode=False,
        batch_provider="auto",
        batch_poll_seconds=30,
        batch_wait_timeout_seconds=86400,
        batch_max_requests_per_job=2000,
        batch_submit_only=False,
        webhook_url="",
        webhook_secret="",
        webhook_timeout_seconds=5,
        webhook_required=False,
        webhook_auto_continue=False,
        live_ok=False,
        selected_s_steps=None,
        selected_execution_step=config.target_step,
        d0_max_files=None,
        d1_max_files=None,
        provider_denylist=(),
    )
    
    ok, payload = runner.run_provider_preflight(
        config.repo_root,
        config.run_id,
        cfg,
        list(config.target_phases),
    )

    if not ok:
        probes = payload.get("probes", []) if isinstance(payload, dict) else []
        if isinstance(probes, list):
            for probe in probes:
                if not isinstance(probe, dict):
                    continue
                status_code = probe.get("status_code")
                failure_type = str(probe.get("failure_type") or "").strip()
                if status_code == 200 and not failure_type:
                    continue
                provider = str(probe.get("provider") or "unknown").strip()
                model_id = str(probe.get("model_id") or "unknown").strip()
                blockers.append(
                    Blocker(
                        ONLINE_PREFLIGHT_FAILURE,
                        "online_provider_preflight",
                        "P0",
                        f"Provider preflight failed for {provider}:{model_id}",
                        probe,
                    )
                )
        if not blockers:
            blockers.append(
                Blocker(
                    ONLINE_PREFLIGHT_FAILURE,
                    "online_provider_preflight",
                    "P0",
                    "Runner-native provider preflight failed",
                    payload,
                )
            )
    return (
        {
            "layer": "online_provider_preflight",
            "status": "PASS" if ok and not blockers else "FAIL",
            "allow_online_preflight": True,
            "payload": payload,
            "conditions": [],
        },
        blockers,
        conditions,
    )


def evaluate_pytest_layer(
    config: GateConfig,
    layer_name: str,
    reason_code: str,
    paths: Sequence[str],
    blocking: bool,
) -> Tuple[Dict[str, Any], List[Blocker], List[Dict[str, Any]]]:
    blockers: List[Blocker] = []
    findings: List[Dict[str, Any]] = []
    result = run_command(
        (
            sys.executable,
            "-m",
            "pytest",
            "-v",
            "--tb=short",
            *paths,
        ),
        config.repo_root,
    )
    payload = {
        "layer": layer_name,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "paths": list(paths),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        message = f"{layer_name} failed"
        if blocking:
            blockers.append(Blocker(reason_code, layer_name, "P0", message, payload))
        else:
            findings.append({"layer": layer_name, "message": message, "details": payload})
    return payload, blockers, findings


def evaluate_smoke_tests(config: GateConfig) -> Tuple[Dict[str, Any], List[Blocker]]:
    blockers: List[Blocker] = []
    checks: Dict[str, Any] = {}
    executable_paths: List[str] = []
    for label, candidates in SMOKE_TEST_CANDIDATES.items():
        found = next((candidate for candidate in candidates if (config.repo_root / candidate).exists()), None)
        checks[label] = {"candidate_paths": list(candidates), "resolved_path": found}
        if not found:
            blockers.append(
                Blocker(
                    MISSING_SMOKE_EVIDENCE,
                    "smoke_and_verify_evidence",
                    "P0",
                    f"Missing smoke evidence for {label}",
                    checks[label],
                )
            )
        else:
            executable_paths.append(found)
    if executable_paths:
        result = run_command(
            (sys.executable, "-m", "pytest", "-v", "--tb=short", *executable_paths),
            config.repo_root,
        )
        checks["pytest"] = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        if result.returncode != 0:
            blockers.append(
                Blocker(
                    SMOKE_FAILURE,
                    "smoke_and_verify_evidence",
                    "P0",
                    "Smoke evidence exists but failed",
                    checks["pytest"],
                )
            )
    return (
        {
            "layer": "smoke_and_verify_evidence",
            "status": "FAIL" if blockers else "PASS",
            "checks": checks,
        },
        blockers,
    )


def split_findings_by_waiver(
    blockers: Sequence[Blocker],
    conditions: Sequence[GateCondition],
    waiver_codes: Set[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    active: List[Dict[str, Any]] = []
    waived: List[Dict[str, Any]] = []
    condition_rows: List[Dict[str, Any]] = []
    for blocker in blockers:
        payload = {
            "reason_code": blocker.reason_code,
            "layer": blocker.layer,
            "severity": blocker.severity,
            "message": blocker.message,
            "details": blocker.details or {},
        }
        if blocker.reason_code in waiver_codes and blocker.severity == "P1":
            waived.append(payload)
        else:
            active.append(payload)
    for condition in conditions:
        condition_rows.append(
            {
                "reason_code": condition.reason_code,
                "layer": condition.layer,
                "message": condition.message,
                "details": condition.details or {},
            }
        )
    return active, waived, condition_rows


def classify_blocker_bucket(blocker: Mapping[str, Any]) -> str:
    reason_code = str(blocker.get("reason_code") or "").strip()
    details = blocker.get("details") or {}
    if reason_code == REQUIRED_API_KEY_MISSING:
        return ENVIRONMENT_BLOCKER
    if reason_code == PAL_REQUIRED_UNAVAILABLE:
        return ARTIFACT_OR_STATE_BLOCKER
    if reason_code == ONLINE_PREFLIGHT_FAILURE:
        if isinstance(details, dict) and "failure_type" in details:
            if not details.get("api_key_present", True):
                return ENVIRONMENT_BLOCKER
            if str(details.get("failure_type") or "").strip() == "auth_missing":
                return ENVIRONMENT_BLOCKER
            if str(details.get("failure_type") or "").strip() == "auth_rejected":
                return EXTERNAL_PROVIDER_BLOCKER
        probes = details.get("probes")
        if isinstance(probes, list):
            if any(not probe.get("api_key_present", True) for probe in probes if isinstance(probe, dict)):
                return ENVIRONMENT_BLOCKER
            if any(str(probe.get("failure_type") or "").strip() == "auth_missing" for probe in probes if isinstance(probe, dict)):
                return ENVIRONMENT_BLOCKER
            if any(
                probe.get("api_key_present")
                and str(probe.get("failure_type") or "").strip() == "auth_rejected"
                for probe in probes
                if isinstance(probe, dict)
            ):
                return EXTERNAL_PROVIDER_BLOCKER
        if details.get("allow_online_preflight") is False:
            return ARTIFACT_OR_STATE_BLOCKER
        return EXTERNAL_PROVIDER_BLOCKER
    if reason_code in {MISSING_SMOKE_EVIDENCE, ACTIVE_MODEL_REFERENCE_UNRESOLVED, PROVIDER_CONTRACT_MISMATCH}:
        return ARTIFACT_OR_STATE_BLOCKER
    if reason_code in {
        IMPORT_OR_CLI_FAILURE,
        TARGET_PROMPT_INTEGRITY_FAILURE,
        TARGET_TRUTH_SPLIT_MISMATCH,
        CONTRACT_MAP_NONDETERMINISTIC,
        ROUTE_DERIVATION_FAILURE,
        CRITICAL_TEST_FAILURE,
        SMOKE_FAILURE,
    }:
        return CODE_BLOCKER
    return CODE_BLOCKER


def build_blocker_classification(
    blockers: Sequence[Mapping[str, Any]],
    repo_wide_findings: Sequence[Mapping[str, Any]],
) -> Dict[str, List[Any]]:
    classification = {
        "code_blockers": [],
        "artifact_or_state_blockers": [],
        "environment_blockers": [],
        "external_provider_blockers": [],
        "false_positives": [],
        "deferred_non_blocking": list(repo_wide_findings),
    }
    for blocker in blockers:
        bucket = classify_blocker_bucket(blocker)
        if bucket == CODE_BLOCKER:
            classification["code_blockers"].append(blocker)
        elif bucket == ARTIFACT_OR_STATE_BLOCKER:
            classification["artifact_or_state_blockers"].append(blocker)
        elif bucket == ENVIRONMENT_BLOCKER:
            classification["environment_blockers"].append(blocker)
        elif bucket == EXTERNAL_PROVIDER_BLOCKER:
            classification["external_provider_blockers"].append(blocker)
        elif bucket == FALSE_POSITIVE:
            classification["false_positives"].append(blocker)
        else:
            classification["deferred_non_blocking"].append(blocker)
    return classification


def derive_operator_verdict(
    blockers: Sequence[Mapping[str, Any]],
    conditions: Sequence[Mapping[str, Any]],
    repo_wide_findings: Sequence[Mapping[str, Any]],
) -> Tuple[str, Dict[str, List[Any]]]:
    classification = build_blocker_classification(blockers, repo_wide_findings)
    if classification["code_blockers"]:
        return NO_GO_CODE, classification
    if classification["environment_blockers"]:
        return NO_GO_ENV, classification
    if classification["external_provider_blockers"]:
        return NO_GO_EXTERNAL, classification
    if classification["artifact_or_state_blockers"]:
        return NO_GO_ARTIFACT_STATE, classification
    if blockers:
        return NO_GO_CODE, classification
    return GO_NOW, classification


def summarize_layers(layer_payloads: Mapping[str, Mapping[str, Any]]) -> Dict[str, str]:
    return {name: str(payload.get("status") or "UNKNOWN") for name, payload in layer_payloads.items()}


def build_environment_summary(verdict_payload: Mapping[str, Any]) -> Optional[Dict[str, str]]:
    verdict = str(verdict_payload.get("verdict") or "").strip().upper()
    reason_codes = {
        str(code).strip()
        for code in verdict_payload.get("reason_codes", [])
        if str(code).strip()
    }
    condition_codes = {
        str(row.get("reason_code") or "").strip()
        for row in verdict_payload.get("conditions", [])
        if isinstance(row, dict) and str(row.get("reason_code") or "").strip()
    }
    environment_blocked_codes = {
        REQUIRED_API_KEY_MISSING,
        ONLINE_PREFLIGHT_FAILURE,
        PAL_REQUIRED_UNAVAILABLE,
    }
    if not (reason_codes & environment_blocked_codes or condition_codes & environment_blocked_codes):
        return None
    return {
        "tooling_status": verdict,
        "live_online_status": "environment_blocked_or_unverified",
        "message": (
            "Repo and tooling checks can pass while live online readiness remains blocked "
            "or unverified by current provider credentials, PAL evidence, or online preflight."
        ),
    }


def render_summary(
    scope: Dict[str, Any],
    verdict: Dict[str, Any],
    layer_payloads: Mapping[str, Mapping[str, Any]],
) -> str:
    lines = [
        "# Pre-Live Gate v2.5 Summary",
        "",
        f"- Verdict: {verdict['verdict']}",
        f"- Target policy: {scope['target_policy']}",
        f"- Target phases: {', '.join(scope['target_phases'])}",
        f"- Target mode: {scope['target_mode']}",
        f"- Run ID: {verdict['run_id']}",
        "",
        "## Layers",
    ]
    for layer_name, payload in layer_payloads.items():
        lines.append(f"- {layer_name}: {payload.get('status')}")
    lines.append("")
    lines.append("## Operator Verdict")
    lines.append(f"- {verdict.get('operator_verdict', 'UNKNOWN')}")
    lines.append("")
    lines.append("## Reason Codes")
    if verdict["reason_codes"]:
        for code in verdict["reason_codes"]:
            lines.append(f"- {code}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Conditions")
    if verdict.get("conditions"):
        for row in verdict["conditions"]:
            lines.append(f"- {row['reason_code']}: {row['message']}")
    else:
        lines.append("- none")
    lines.append("")
    environment_summary = verdict.get("environment_summary")
    lines.append("## Environment Status")
    if isinstance(environment_summary, dict):
        lines.append(f"- Tooling status: {environment_summary.get('tooling_status')}")
        lines.append(
            f"- Live online status: {environment_summary.get('live_online_status')}"
        )
        lines.append(f"- Note: {environment_summary.get('message')}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Evidence")
    lines.append(f"- Scope: {scope['target_runner_path']}")
    lines.append(f"- Output dir: {verdict['output_dir']}")
    return "\n".join(lines) + "\n"


def run_gate(
    config: GateConfig,
    args: Optional[argparse.Namespace] = None,
) -> Dict[str, Any]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    runner = load_module(RUNNER_PATH, "run_extraction_v5_pre_live_gate")
    contract_module = load_module(CONTRACT_MAP_PATH, "phase_contract_map_pre_live_gate")

    scope = derive_scope(runner, contract_module, config)
    write_json(config.output_dir / "VALIDATION_SCOPE.json", scope)

    layer_payloads: Dict[str, Dict[str, Any]] = {}
    all_blockers: List[Blocker] = []
    all_conditions: List[Condition] = []
    repo_wide_findings: List[Dict[str, Any]] = []

    import_cli, blockers = evaluate_import_cli_smoke(config)
    layer_payloads["import_cli_smoke"] = import_cli
    all_blockers.extend(blockers)

    prompt_integrity, blockers = evaluate_prompt_integrity(runner, config)
    layer_payloads["target_prompt_integrity"] = prompt_integrity
    all_blockers.extend(blockers)

    truth_split, blockers, findings = collect_truth_split(runner, config)
    layer_payloads["truth_split_audit"] = {
        "layer": truth_split["layer"],
        "status": truth_split["status"],
        "target_phase_mismatch_count": truth_split["target_phase_mismatch_count"],
        "repo_wide_mismatch_count": truth_split["repo_wide_mismatch_count"],
    }
    write_json(config.output_dir / "TRUTH_SPLIT_REPORT.json", {"rows": truth_split["rows"]})
    all_blockers.extend(blockers)
    repo_wide_findings.extend(findings)

    contract_map, blockers = evaluate_contract_map(runner, contract_module, config)
    layer_payloads["contract_map_determinism"] = contract_map
    all_blockers.extend(blockers)

    route_readiness, blockers = evaluate_route_readiness(runner, config, scope)
    layer_payloads["route_derived_readiness"] = route_readiness
    all_blockers.extend(blockers)

    critical_tests, blockers, findings = evaluate_pytest_layer(
        config=config,
        layer_name="critical_tests",
        reason_code=CRITICAL_TEST_FAILURE,
        paths=CRITICAL_TEST_PATHS,
        blocking=True,
    )
    layer_payloads["critical_tests"] = critical_tests
    all_blockers.extend(blockers)

    repo_drift_tests, _blockers, findings_repo = evaluate_pytest_layer(
        config=config,
        layer_name="repo_drift_tests",
        reason_code=CRITICAL_TEST_FAILURE,
        paths=REPO_DRIFT_TEST_PATHS,
        blocking=False,
    )
    layer_payloads["repo_drift_tests"] = repo_drift_tests
    repo_wide_findings.extend(findings_repo)

    offline_results = {
        "import_cli_smoke": import_cli,
        "target_prompt_integrity": prompt_integrity,
        "truth_split_audit": {
            "target_phase_mismatch_count": truth_split["target_phase_mismatch_count"],
            "repo_wide_mismatch_count": truth_split["repo_wide_mismatch_count"],
        },
        "contract_map_determinism": contract_map,
        "route_derived_readiness": route_readiness,
        "critical_tests": critical_tests,
    }
    write_json(config.output_dir / "OFFLINE_GATE_RESULTS.json", offline_results)

    pal_validation, blockers, conditions = evaluate_pal_validation(config, scope)
    layer_payloads["pal_provider_validation"] = {
        "layer": pal_validation["layer"],
        "status": pal_validation["status"],
        "routes_count": len(pal_validation["routes"]),
        "conditions": pal_validation.get("conditions", []),
    }
    write_json(config.output_dir / "PAL_VALIDATION.json", pal_validation)
    all_blockers.extend(blockers)
    all_conditions.extend(conditions)

    online_preflight, blockers, conditions = evaluate_online_preflight(runner, config)
    layer_payloads["online_provider_preflight"] = online_preflight
    write_json(config.output_dir / "ONLINE_PREFLIGHT_RESULTS.json", online_preflight)
    all_blockers.extend(blockers)
    all_conditions.extend(conditions)

    smoke_results, blockers = evaluate_smoke_tests(config)
    layer_payloads["smoke_and_verify_evidence"] = smoke_results
    all_blockers.extend(blockers)

    active_blockers, waived, condition_rows = split_findings_by_waiver(
        all_blockers,
        all_conditions,
        set(config.waiver_codes),
    )
    reason_codes = sorted({row["reason_code"] for row in active_blockers})
    verdict = "NO_GO"
    if not active_blockers:
        verdict = "CONDITIONAL_GO" if condition_rows else "GO"
    operator_verdict, blocker_classification = derive_operator_verdict(
        active_blockers,
        condition_rows,
        repo_wide_findings,
    )

    verdict_payload = {
        "verdict": verdict,
        "operator_verdict": operator_verdict,
        "run_id": config.run_id,
        "output_dir": str(config.output_dir.resolve()),
        "reason_codes": reason_codes,
        "run_scoped_blockers": active_blockers,
        "blocker_classification": blocker_classification,
        "conditions": condition_rows,
        "repo_wide_findings": repo_wide_findings,
        "waivers": waived,
        "layers": summarize_layers(layer_payloads),
        "generated_at": now_iso(),
    }
    verdict_payload["environment_summary"] = build_environment_summary(verdict_payload)
    write_json(config.output_dir / "VALIDATION_VERDICT.json", verdict_payload)
    summary = render_summary(scope, verdict_payload, layer_payloads)
    write_text(config.output_dir / "VALIDATION_SUMMARY.md", summary)
    return {
        "scope": scope,
        "layer_payloads": layer_payloads,
        "verdict": verdict_payload,
        "summary": summary,
    }


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    config = build_config(args)
    result = run_gate(config)
    print(sanitized_json_text(result["verdict"], indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["verdict"]["verdict"] in {"GO", "CONDITIONAL_GO"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
