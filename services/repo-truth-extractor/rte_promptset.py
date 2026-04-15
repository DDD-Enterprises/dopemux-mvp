from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple


def prompt_root(
    *,
    prompt_root_env_value: str,
    legacy_prompt_root_env_value: str,
    extractor_service_dir: Path,
) -> Path:
    configured = str(prompt_root_env_value or "").strip()
    if not configured:
        configured = str(legacy_prompt_root_env_value or "").strip()
    if configured:
        return Path(configured)
    v4_path = extractor_service_dir / "promptsets" / "v4" / "prompts"
    if v4_path.exists():
        return v4_path
    return extractor_service_dir / "prompts" / "v3"


def set_active_s_prompts_mode(
    mode: Optional[str],
    *,
    legacy_mode: str,
    allowed_modes: Set[str],
    logger: Any,
) -> str:
    normalized = str(mode or "").strip().lower() or legacy_mode
    if normalized not in allowed_modes:
        allowed = ", ".join(sorted(allowed_modes))
        raise RuntimeError(
            f"Unsupported S prompts mode {mode!r}. Expected one of: {allowed}"
        )
    if normalized != legacy_mode:
        logger.warning(
            "Ignoring S prompts mode=%s; phase S always uses legacy prompts. Use phase SP for registry-backed pipeline prompts.",
            normalized,
        )
        normalized = legacy_mode
    return normalized


def get_active_s_prompts_mode(
    *,
    active_mode: str,
    env_mode_value: str,
    env_var_name: str,
    legacy_mode: str,
    allowed_modes: Set[str],
    logger: Any,
) -> str:
    current = str(active_mode or "").strip().lower()
    if current in allowed_modes:
        return current
    env_mode = str(env_mode_value or "").strip().lower()
    if not env_mode:
        return legacy_mode
    if env_mode not in allowed_modes:
        allowed = ", ".join(sorted(allowed_modes))
        raise RuntimeError(
            f"{env_var_name} must be one of {allowed}. Got: {env_mode}"
        )
    if env_mode != legacy_mode:
        logger.warning(
            "Ignoring %s=%s; phase S always uses legacy prompts. Use phase SP for registry-backed pipeline prompts.",
            env_var_name,
            env_mode,
        )
        return legacy_mode
    return env_mode


def phase_s_registry_dir(
    *,
    prompt_root_env_value: str,
    legacy_prompt_root_env_value: str,
    extractor_service_dir: Path,
) -> Path:
    configured = str(prompt_root_env_value or "").strip()
    if not configured:
        configured = str(legacy_prompt_root_env_value or "").strip()
    if configured:
        return Path(configured) / "phase_s"
    return extractor_service_dir / "prompts" / "phase_s"


def phase_s_registry_path(
    *,
    prompt_root_env_value: str,
    legacy_prompt_root_env_value: str,
    extractor_service_dir: Path,
) -> Path:
    return phase_s_registry_dir(
        prompt_root_env_value=prompt_root_env_value,
        legacy_prompt_root_env_value=legacy_prompt_root_env_value,
        extractor_service_dir=extractor_service_dir,
    ) / "registry.json"


def step_sort_key(step_id: str) -> Tuple[str, int]:
    match = re.match(r"^([A-Z]+)(\d+)$", step_id)
    if not match:
        return (step_id[:1], 999999)
    return (match.group(1), int(match.group(2)))


def _parse_step_csv(raw: str) -> List[str]:
    tokens: List[str] = []
    seen: Set[str] = set()
    for token in str(raw or "").split(","):
        normalized = token.strip().upper()
        if not normalized:
            raise RuntimeError("Step selection contains an empty token.")
        if normalized in seen:
            raise RuntimeError(
                f"Step selection contains a duplicate step: {normalized}"
            )
        seen.add(normalized)
        tokens.append(normalized)
    if not tokens:
        raise RuntimeError("Step selection is empty.")
    return tokens


def _normalize_s_steps(selected: List[str]) -> List[str]:
    return sorted(list(selected), key=step_sort_key)


def _validate_s_steps(selected: List[str], *, phase_s_base_step_set: Set[str]) -> None:
    unknown = [step_id for step_id in selected if step_id not in phase_s_base_step_set]
    if unknown:
        raise RuntimeError(
            "Phase S step selection only allows S0-S12. "
            f"Unsupported steps: {', '.join(sorted(unknown, key=step_sort_key))}"
        )


def get_s_step_controls(
    args: Any,
    *,
    env_steps_value: str,
    phase_s_base_step_set: Set[str],
) -> Optional[List[str]]:
    raw = getattr(args, "s_steps", None)
    if raw is None:
        raw = env_steps_value
    if not str(raw or "").strip():
        return None
    selected = _parse_step_csv(str(raw))
    _validate_s_steps(selected, phase_s_base_step_set=phase_s_base_step_set)
    return _normalize_s_steps(selected)


def legacy_phase_prompt_specs(
    phase: str,
    *,
    required_prompt_step_ids: Dict[str, Set[str]],
    resolve_prompt_root: Callable[[], Path],
    extractor_service_dir: Path,
    prompt_spec_factory: Callable[..., Any],
    safe_read: Callable[[Path], str],
    extract_output_artifacts: Callable[[str, str], Sequence[str]],
    step_contract_for: Callable[[str, str], Optional[Dict[str, Any]]],
    logger: Any,
) -> List[Any]:
    grouped: Dict[str, List[Path]] = {}
    expected_steps = required_prompt_step_ids.get(phase, set())
    primary_root = resolve_prompt_root()
    for prompt_path in sorted(primary_root.glob(f"PROMPT_{phase}*_*.md")):
        match = re.match(r"PROMPT_([A-Z]+\d+)", prompt_path.name)
        if not match:
            continue
        step_id = match.group(1)
        grouped.setdefault(step_id, []).append(prompt_path)

    if str(phase or "").upper() == "S":
        missing_steps = set(expected_steps) - set(grouped.keys())
        if missing_steps:
            v4_prompt_root = extractor_service_dir / "promptsets" / "v4" / "prompts"
            for prompt_path in sorted(v4_prompt_root.glob("PROMPT_S*_*.md")):
                match = re.match(r"PROMPT_([A-Z]+\d+)", prompt_path.name)
                if not match:
                    continue
                step_id = match.group(1)
                if step_id not in missing_steps:
                    continue
                grouped.setdefault(step_id, []).append(prompt_path)

    specs: List[Any] = []
    for step_id in sorted(grouped.keys(), key=step_sort_key):
        candidates = sorted(grouped[step_id], key=str)
        if len(candidates) > 1:
            raise RuntimeError(
                f"Duplicate prompts for {step_id}: {[str(path) for path in candidates]}. "
                "Resolve duplicates before running the pipeline."
            )
        prompt_path = candidates[0]
        prompt_text = safe_read(prompt_path)
        output_artifacts = tuple(extract_output_artifacts(prompt_text, step_id))
        if not output_artifacts:
            logger.warning(
                "Prompt %s (%s) does not declare explicit output artifacts. Falling back to %s.json.",
                prompt_path.name,
                step_id,
                step_id,
            )
            output_artifacts = (f"{step_id}.json",)
        specs.append(
            prompt_spec_factory(
                step_id=step_id,
                prompt_path=prompt_path,
                output_artifacts=tuple(output_artifacts),
                source="legacy",
                contract=step_contract_for(phase, step_id),
            )
        )
    return specs


def validate_phase_s_registry(
    payload: Dict[str, Any],
    *,
    required_prompt_step_ids: Dict[str, Set[str]],
    phase_s_root: Path,
    valid_prompt_tiers: Set[str],
    is_within: Callable[[Path, Path], bool],
) -> Dict[str, Dict[str, str]]:
    if not isinstance(payload, dict):
        raise ValueError("Phase SP registry must be a JSON object.")
    if int(payload.get("version", 0)) != 1:
        raise ValueError("Phase SP registry must declare version=1.")
    if str(payload.get("phase", "")).strip().upper() != "SP":
        raise ValueError("Phase SP registry must declare phase='SP'.")
    steps = payload.get("steps")
    if not isinstance(steps, dict):
        raise ValueError("Phase SP registry must contain an object 'steps'.")
    expected = set(required_prompt_step_ids.get("SP", set()))
    observed = {str(key).strip().upper() for key in steps.keys()}
    if observed != expected:
        raise ValueError(
            "Phase SP registry must declare exactly steps "
            f"{sorted(expected)}. Observed: {sorted(observed)}"
        )

    validated: Dict[str, Dict[str, str]] = {}
    for step_id in sorted(expected, key=step_sort_key):
        entry = steps.get(step_id)
        if not isinstance(entry, dict):
            raise ValueError(f"Phase SP registry step {step_id} must be an object.")
        prompt_path = str(entry.get("prompt_path", "")).strip()
        tier = str(
            entry.get("routing_tier", entry.get("tier", "synthesis"))
        ).strip().lower() or "synthesis"
        outputs = entry.get("outputs")
        if not prompt_path or Path(prompt_path).is_absolute():
            raise ValueError(
                f"Phase SP registry step {step_id} prompt_path must be a relative path."
            )
        if tier not in valid_prompt_tiers:
            raise ValueError(
                f"Phase SP registry step {step_id} routing_tier must be one of {sorted(valid_prompt_tiers)}."
            )
        if not isinstance(outputs, list) or not outputs:
            raise ValueError(
                f"Phase SP registry step {step_id} outputs must be a non-empty list."
            )
        resolved = (phase_s_root / prompt_path).resolve()
        if not is_within(resolved, phase_s_root):
            raise ValueError(
                f"Phase SP registry step {step_id} prompt_path escapes {phase_s_root}."
            )
        if not resolved.exists() or not resolved.is_file():
            raise ValueError(
                f"Phase SP registry step {step_id} prompt file does not exist: {resolved}"
            )
        validated[step_id] = {
            "prompt_path": prompt_path,
            "tier": tier,
        }
    return validated


def load_phase_s_registry(
    *,
    registry_path: Path,
    validate_phase_s_registry: Callable[[Dict[str, Any]], Dict[str, Dict[str, str]]],
) -> Dict[str, Dict[str, str]]:
    if not registry_path.exists():
        raise FileNotFoundError(f"Phase S registry not found: {registry_path}")
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(
            f"Failed to parse Phase S registry {registry_path}: {exc}"
        ) from exc
    return validate_phase_s_registry(payload)


def resolve_phase_s_prompts(
    mode: str,
    *,
    legacy_mode: str,
    allowed_modes: Set[str],
    load_phase_s_registry: Callable[[], Dict[str, Dict[str, str]]],
    legacy_phase_prompt_specs: Callable[[str], List[Any]],
    resolve_phase_s_registry_dir: Callable[[], Path],
    prompt_spec_factory: Callable[..., Any],
    safe_read: Callable[[Path], str],
    extract_output_artifacts: Callable[[str, str], Sequence[str]],
    step_contract_for: Callable[[str, str], Optional[Dict[str, Any]]],
    logger: Any,
) -> List[Any]:
    normalized_mode = str(mode or legacy_mode).strip().lower() or legacy_mode
    if normalized_mode not in allowed_modes:
        allowed = ", ".join(sorted(allowed_modes))
        raise RuntimeError(
            f"Unsupported S prompts mode {mode!r}. Expected one of: {allowed}"
        )
    if normalized_mode == legacy_mode:
        return legacy_phase_prompt_specs("S")

    try:
        registry = load_phase_s_registry()
    except Exception as exc:
        if normalized_mode == "registry":
            raise RuntimeError(f"Phase S registry mode failed: {exc}") from exc
        logger.warning(
            "Phase S registry unavailable; falling back to legacy prompts. reason=%s",
            exc,
        )
        return legacy_phase_prompt_specs("S")

    base = resolve_phase_s_registry_dir().resolve()
    specs: List[Any] = []
    for step_id in sorted(registry.keys(), key=step_sort_key):
        prompt_path = (base / registry[step_id]["prompt_path"]).resolve()
        prompt_text = safe_read(prompt_path)
        output_artifacts = tuple(extract_output_artifacts(prompt_text, step_id))
        if not output_artifacts:
            logger.warning(
                "Prompt %s (%s) does not declare explicit output artifacts. Falling back to %s.json.",
                prompt_path.name,
                step_id,
                step_id,
            )
            output_artifacts = (f"{step_id}.json",)
        specs.append(
            prompt_spec_factory(
                step_id=step_id,
                prompt_path=prompt_path,
                output_artifacts=tuple(output_artifacts),
                tier_override=registry[step_id]["tier"],
                source="registry",
                contract=step_contract_for(
                    "SP" if str(step_id).strip().upper().startswith("SP") else "S",
                    step_id,
                ),
            )
        )
    return specs


def resolve_phase_sp_prompts(
    *,
    load_phase_s_registry: Callable[[], Dict[str, Dict[str, str]]],
    resolve_phase_s_registry_dir: Callable[[], Path],
    prompt_spec_factory: Callable[..., Any],
    safe_read: Callable[[Path], str],
    extract_output_artifacts: Callable[[str, str], Sequence[str]],
    step_contract_for: Callable[[str, str], Optional[Dict[str, Any]]],
) -> List[Any]:
    registry = load_phase_s_registry()
    base = resolve_phase_s_registry_dir().resolve()
    specs: List[Any] = []
    for step_id in sorted(registry.keys(), key=step_sort_key):
        prompt_path = (base / registry[step_id]["prompt_path"]).resolve()
        prompt_text = safe_read(prompt_path)
        output_artifacts = tuple(extract_output_artifacts(prompt_text, step_id))
        if not output_artifacts:
            output_artifacts = (f"{step_id}.json",)
        specs.append(
            prompt_spec_factory(
                step_id=step_id,
                prompt_path=prompt_path,
                output_artifacts=tuple(output_artifacts),
                tier_override=registry[step_id]["tier"],
                source="registry",
                contract=step_contract_for("SP", step_id),
            )
        )
    return specs


def blocked_promptset_payload(
    prompt_report: Dict[str, Any],
    at: str,
    *,
    promptset_blocked_reason: str,
) -> Dict[str, Any]:
    return {
        "reason": promptset_blocked_reason,
        "at": at,
        "promptset": {
            "status": "blocked",
            "failures": prompt_report.get("prompt_failures", []),
        },
    }


def resume_blocked_payload(
    prompt_report: Dict[str, Any],
    *,
    promptset_blocked_reason: str,
) -> Dict[str, Any]:
    return {
        "reason": promptset_blocked_reason,
        "promptset_hash": None,
        "promptset_status": "blocked",
        "prompt_failures": prompt_report.get("prompt_failures", []),
    }


def prompt_hash_report_for_phase(
    phase: str,
    specs: List[Any],
    *,
    required_prompt_step_ids: Dict[str, Set[str]],
    required_step_ids: Optional[Set[str]],
    prompt_hash_mode: str,
    missing_prompt_glob: Callable[[str], str],
    prompt_failure_entry: Callable[..., Dict[str, str]],
    truncate_exception_message: Callable[[str], str],
    sha256_bytes: Callable[[bytes], str],
) -> Dict[str, Any]:
    prompt_hashes: List[Dict[str, str]] = []
    prompt_missing: List[str] = []
    prompt_unreadable: List[Dict[str, str]] = []
    prompt_hash_errors: List[str] = []
    prompt_failures: List[Dict[str, str]] = []

    expected_steps = (
        set(required_step_ids)
        if required_step_ids is not None
        else required_prompt_step_ids.get(phase, set())
    )
    observed_steps = {spec.step_id for spec in specs}
    target_required_steps = set(expected_steps)
    for step_id in sorted(target_required_steps - observed_steps):
        missing_pattern = missing_prompt_glob(step_id)
        prompt_missing.append(missing_pattern)
        prompt_hash_errors.append(f"prompt_missing: {missing_pattern}")
        prompt_failures.append(
            prompt_failure_entry(
                kind="MISSING_PROMPT",
                prompt_id=step_id,
                path=Path(missing_pattern),
                exception_type="FileNotFoundError",
                exception_message=f"No prompt file found for required step '{step_id}'.",
            )
        )

    for spec in sorted(specs, key=lambda row: (row.step_id, str(row.prompt_path))):
        path = spec.prompt_path.resolve()
        if not path.exists():
            prompt_missing.append(str(path))
            prompt_hash_errors.append(f"prompt_missing: {path}")
            prompt_failures.append(
                prompt_failure_entry(
                    kind="MISSING_PROMPT",
                    prompt_id=spec.step_id,
                    path=path,
                    exception_type="FileNotFoundError",
                    exception_message=f"Prompt file does not exist: {path}",
                )
            )
            continue
        try:
            digest = sha256_bytes(path.read_bytes())
        except Exception as exc:
            error_message = truncate_exception_message(str(exc))
            prompt_unreadable.append(
                {
                    "prompt_id": spec.step_id,
                    "path": str(path),
                    "error": f"{type(exc).__name__}: {error_message}",
                }
            )
            prompt_hash_errors.append(
                f"prompt_unreadable: {path} :: {type(exc).__name__}: {error_message}"
            )
            prompt_failures.append(
                prompt_failure_entry(
                    kind="UNREADABLE_PROMPT",
                    prompt_id=spec.step_id,
                    path=path,
                    exception_type=type(exc).__name__,
                    exception_message=error_message,
                )
            )
            continue
        prompt_hashes.append(
            {"prompt_id": spec.step_id, "path": str(path), "sha256": digest}
        )

    prompt_failures = sorted(
        prompt_failures,
        key=lambda row: (row["prompt_id"], row["path"], row["kind"]),
    )
    blocked = bool(prompt_failures)
    promptset_sha256: Optional[str] = None
    if not blocked:
        normalized = json.dumps(
            sorted(prompt_hashes, key=lambda row: row["path"]),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        promptset_sha256 = sha256_bytes(normalized)

    return {
        "phase": phase,
        "prompt_hash_mode": prompt_hash_mode,
        "promptset_sha256": promptset_sha256,
        "prompt_hashes": sorted(prompt_hashes, key=lambda row: row["path"]),
        "prompt_missing": sorted(set(prompt_missing)),
        "prompt_unreadable": sorted(prompt_unreadable, key=lambda row: row["path"]),
        "prompt_hash_errors": prompt_hash_errors,
        "prompt_failures": prompt_failures,
        "blocked_promptset": blocked,
        "missing_prompts_count": len(set(prompt_missing)),
        "unreadable_prompts_count": len(prompt_unreadable),
        "prompt_failures_count": len(prompt_failures),
    }


def promptset_fingerprint(
    phases: Iterable[str],
    *,
    prompt_hash_mode: str,
    get_phase_prompts: Callable[[str], List[Any]],
    prompt_hash_report_for_phase: Callable[[str, List[Any]], Dict[str, Any]],
    sha256_bytes: Callable[[bytes], str],
) -> Dict[str, Any]:
    active_phases = sorted(set(phases))
    prompt_hashes: List[Dict[str, str]] = []
    prompt_missing: List[str] = []
    prompt_unreadable: List[Dict[str, str]] = []
    prompt_hash_errors: List[str] = []
    prompt_failures: List[Dict[str, str]] = []

    for phase in active_phases:
        report = prompt_hash_report_for_phase(phase, get_phase_prompts(phase))
        prompt_hashes.extend(report["prompt_hashes"])
        prompt_missing.extend(report["prompt_missing"])
        prompt_unreadable.extend(report["prompt_unreadable"])
        prompt_hash_errors.extend(report["prompt_hash_errors"])
        prompt_failures.extend(report.get("prompt_failures", []))

    prompt_failures = sorted(
        prompt_failures,
        key=lambda row: (row["prompt_id"], row["path"], row["kind"]),
    )
    blocked = bool(prompt_failures)
    promptset_sha256: Optional[str] = None
    if not blocked:
        normalized = json.dumps(
            sorted(prompt_hashes, key=lambda row: row["path"]),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        promptset_sha256 = sha256_bytes(normalized)

    return {
        "active_phases": active_phases,
        "prompt_hash_mode": prompt_hash_mode,
        "promptset_sha256": promptset_sha256,
        "prompt_hashes": sorted(prompt_hashes, key=lambda row: row["path"]),
        "prompt_missing": sorted(set(prompt_missing)),
        "prompt_unreadable": sorted(prompt_unreadable, key=lambda row: row["path"]),
        "prompt_hash_errors": prompt_hash_errors,
        "prompt_failures": prompt_failures,
        "blocked_promptset": blocked,
        "missing_prompts_count": len(set(prompt_missing)),
        "unreadable_prompts_count": len(prompt_unreadable),
        "prompt_failures_count": len(prompt_failures),
    }
