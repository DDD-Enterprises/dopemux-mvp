from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


def argv_has_flag(argv: Sequence[str], *flags: str) -> bool:
    return any(flag in argv for flag in flags)


def shared_doctor_advisory_fields(
    artifact_name: str,
    *,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    authority_note = (
        "Shared doctor artifacts are diagnostic only. Launch and certification "
        "authority use run-scoped artifacts under runs/<run_id>/."
    )
    if run_id and artifact_name == "PROVIDER_PREFLIGHT.json":
        authority_note += f" Launch authority for this run is runs/{run_id}/PROVIDER_PREFLIGHT.json."
    return {
        "artifact_name": artifact_name,
        "artifact_origin": "shared_doctor",
        "authority_class": "diagnostic_only",
        "advisory_only": True,
        "launch_authority": False,
        "certification_authority": False,
        "execution_readiness_authority": False,
        "authority_note": authority_note,
    }


def first_live_phase_sequence(
    stage: str,
    *,
    first_live_initial_phases: Sequence[str],
    first_live_post_review_phases: Sequence[str],
) -> List[str]:
    normalized = str(stage or "initial").strip().lower() or "initial"
    if normalized == "post-review":
        return list(first_live_post_review_phases)
    if normalized == "full":
        return list(first_live_initial_phases) + list(first_live_post_review_phases)
    return list(first_live_initial_phases)


def apply_first_live_preset(
    args: argparse.Namespace,
    raw_argv: Sequence[str],
    *,
    first_live_preset_name: str,
    first_live_preset_default_cap_usd: float,
    interactive_safe_batch_wait_seconds: int,
    first_live_initial_phases: Sequence[str],
    first_live_post_review_phases: Sequence[str],
    argv_has_flag: Callable[..., bool],
    first_live_phase_sequence: Callable[[str], List[str]],
) -> Tuple[List[str], Dict[str, Any]]:
    stage = str(getattr(args, "preset_stage", "initial") or "initial").strip().lower()
    selected_phases = first_live_phase_sequence(stage)
    applied_defaults: Dict[str, Any] = {}
    notes = [
        "Validator is step zero for live preset execution unless --skip-pre-live-validator is set.",
        "The initial stage stops after A/H/D/C so operators can review artifacts before synthesis phases.",
        "Strict step-level routes can still override the top-level policy preview for some prompts.",
    ]
    if not argv_has_flag(raw_argv, "--phase"):
        applied_defaults["phase_sequence"] = list(selected_phases)
    if not argv_has_flag(raw_argv, "--routing-policy"):
        args.routing_policy = "cost"
        applied_defaults["routing_policy"] = args.routing_policy
    if not argv_has_flag(raw_argv, "--max-cost-usd"):
        args.max_cost_usd = first_live_preset_default_cap_usd
        applied_defaults["max_cost_usd"] = args.max_cost_usd
    if not argv_has_flag(raw_argv, "--partition-workers"):
        args.partition_workers = 1
        applied_defaults["partition_workers"] = args.partition_workers
    if not argv_has_flag(raw_argv, "--batch-mode", "--no-batch"):
        args.batch_mode = False
        applied_defaults["batch_mode"] = args.batch_mode
    if not argv_has_flag(raw_argv, "--batch-wait-timeout-seconds"):
        args.batch_wait_timeout_seconds = interactive_safe_batch_wait_seconds
        applied_defaults["batch_wait_timeout_seconds"] = args.batch_wait_timeout_seconds
    preview = {
        "preset": first_live_preset_name,
        "stage": stage,
        "selected_phases": list(selected_phases),
        "full_recommended_sequence": list(first_live_initial_phases)
        + ["CHECKPOINT_REVIEW"]
        + list(first_live_post_review_phases),
        "applied_defaults": applied_defaults,
        "compare_mode": getattr(args, "compare_mode", None),
        "output_root": getattr(args, "output_root", None),
        "notes": notes,
    }
    return selected_phases, preview


def apply_staged_safe_preset(
    args: argparse.Namespace,
    raw_argv: Sequence[str],
    *,
    staged_safe_preset_name: str,
    staged_safe_preset_default_cap_usd: float,
    interactive_safe_batch_wait_seconds: int,
    first_live_initial_phases: Sequence[str],
    first_live_post_review_phases: Sequence[str],
    argv_has_flag: Callable[..., bool],
    first_live_phase_sequence: Callable[[str], List[str]],
) -> Tuple[List[str], Dict[str, Any]]:
    stage = str(getattr(args, "preset_stage", "initial") or "initial").strip().lower()
    selected_phases = first_live_phase_sequence(stage)
    applied_defaults: Dict[str, Any] = {}
    notes = [
        "Validator remains step zero unless --skip-pre-live-validator is set.",
        "Staged-safe uses the same phase ladder as first-live but defaults batch execution on for bounded rollout rehearsals.",
        "The initial stage remains A/H/D/C so operators can stop before synthesis phases.",
    ]
    if not argv_has_flag(raw_argv, "--phase"):
        applied_defaults["phase_sequence"] = list(selected_phases)
    if not argv_has_flag(raw_argv, "--routing-policy"):
        args.routing_policy = "cost"
        applied_defaults["routing_policy"] = args.routing_policy
    if not argv_has_flag(raw_argv, "--max-cost-usd"):
        args.max_cost_usd = staged_safe_preset_default_cap_usd
        applied_defaults["max_cost_usd"] = args.max_cost_usd
    if not argv_has_flag(raw_argv, "--partition-workers"):
        args.partition_workers = 1
        applied_defaults["partition_workers"] = args.partition_workers
    if not argv_has_flag(raw_argv, "--batch-mode", "--no-batch"):
        args.batch_mode = True
        applied_defaults["batch_mode"] = args.batch_mode
    if not argv_has_flag(raw_argv, "--batch-wait-timeout-seconds"):
        args.batch_wait_timeout_seconds = interactive_safe_batch_wait_seconds
        applied_defaults["batch_wait_timeout_seconds"] = args.batch_wait_timeout_seconds
    preview = {
        "preset": staged_safe_preset_name,
        "stage": stage,
        "selected_phases": list(selected_phases),
        "full_recommended_sequence": list(first_live_initial_phases)
        + ["CHECKPOINT_REVIEW"]
        + list(first_live_post_review_phases),
        "applied_defaults": applied_defaults,
        "compare_mode": getattr(args, "compare_mode", None),
        "output_root": getattr(args, "output_root", None),
        "notes": notes,
    }
    return selected_phases, preview


def run_pre_live_validator(
    root: Path,
    run_root: Optional[Path] = None,
    *,
    extractor_service_dir: Path,
    python_executable: str,
    target_policy: Optional[str],
    target_phases: Optional[Sequence[str]],
    allow_online_preflight: bool,
    subprocess_run: Callable[..., Any],
    now_iso: Callable[[], str],
    write_json: Callable[[Path, Any], None],
) -> Tuple[bool, Dict[str, Any]]:
    validator_path = extractor_service_dir / "validate_pre_live_gate_v25.py"
    args = [python_executable, str(validator_path)]
    if target_policy:
        args.extend(["--target-policy", str(target_policy)])
    if target_phases:
        normalized_phases = [
            str(phase).strip().upper() for phase in target_phases if str(phase).strip()
        ]
        if normalized_phases:
            args.extend(["--target-phases", *normalized_phases])
    if allow_online_preflight:
        args.append("--allow-online-preflight")
    result = subprocess_run(
        args,
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    payload = {
        "generated_at": now_iso(),
        "validator_path": str(validator_path.resolve()),
        "exit_code": int(result.returncode),
        "status": "pass" if result.returncode == 0 else "fail",
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }
    if run_root is not None:
        write_json(run_root / "PRELIVE_VALIDATOR_RESULT.json", payload)
    return result.returncode == 0, payload


def max_files_for_phase(
    phase: str,
    cfg: Any,
    *,
    code_heavy_phases: Set[str],
) -> int:
    if phase in code_heavy_phases:
        return cfg.max_files_code
    return cfg.max_files_docs


def preview_partition_usage(
    *,
    phase: str,
    step_id: str,
    prompt_text: str,
    output_artifacts: Tuple[str, ...],
    provider: str,
    model_id: str,
    partition: Dict[str, Any],
    cfg: Any,
    max_files: int,
    repo_root: Path,
    build_output_envelope_instructions: Callable[[Tuple[str, ...]], str],
    build_partition_context: Callable[..., Tuple[str, Any]],
    build_chat_payload: Callable[..., Any],
    serialize_payload_body: Callable[[Any], Any],
    measure_payload_bytes_from_body: Callable[[Any], int],
    estimate_text_tokens: Callable[[str, str], int],
    apply_file_cap: Callable[..., Tuple[List[str], Any]],
) -> Dict[str, int]:
    output_instructions = build_output_envelope_instructions(output_artifacts)
    context_brief = str(partition.get("context_brief") or "")
    brief_section = f"\n{context_brief}\n" if context_brief else ""
    prompt_prefix = (
        "Extract from the files below.\n"
        f"{output_instructions}\n"
        f"{brief_section}"
        "\nFILES:\n"
    )
    reserved_chars = len(prompt_prefix)
    current_budget = max(cfg.max_chars - reserved_chars, 2048)
    partition_paths = [str(path) for path in partition.get("paths", [])]
    if phase == "D":
        partition_paths, _ = apply_file_cap(
            step_id=step_id,
            partition_id=str(partition.get("id") or ""),
            files=partition_paths,
            cfg=cfg,
            root=repo_root,
        )

    payload_bytes = 0
    user_prompt = ""
    while True:
        context, _context_stats = build_partition_context(
            phase=phase,
            partition_paths=partition_paths,
            file_truncate_chars=cfg.file_truncate_chars,
            home_scan_mode=cfg.home_scan_mode,
            max_files=max_files,
            max_chars=current_budget,
            router=cfg.router,
        )
        user_prompt = f"{prompt_prefix}{context}"
        payload = build_chat_payload(
            provider,
            model_id,
            prompt_text,
            user_prompt,
            force_json_output=(provider == "gemini"),
        )
        payload_bytes = measure_payload_bytes_from_body(serialize_payload_body(payload))
        if payload_bytes <= cfg.max_request_bytes or current_budget <= 1024:
            break
        next_budget = max(1024, int(current_budget * 0.7))
        if next_budget == current_budget:
            next_budget = current_budget - 1
        current_budget = max(next_budget, 1024)

    return {
        "input_tokens": estimate_text_tokens(prompt_text, user_prompt),
        "payload_bytes": payload_bytes,
    }


def build_phase_cost_preview(
    phase: str,
    cfg: Any,
    prompts: Sequence[Any],
    partitions: List[Dict[str, Any]],
    *,
    now_iso: Callable[[], str],
    pricing_version: str,
    premium_synthesis_phases: Set[str],
    resolve_effective_step_route: Callable[..., Dict[str, Any]],
    safe_read: Callable[[Path], str],
    preview_partition_usage: Callable[..., Dict[str, int]],
    max_files_for_phase: Callable[[str, Any], int],
    pricing_preview_record: Callable[..., Dict[str, Any]],
    project_preview_output_tokens: Callable[..., int],
    is_json_managed_step: Callable[[Any], bool],
    step_sort_key: Callable[[str], Any],
    repo_root: Path,
) -> Dict[str, Any]:
    by_step: List[Dict[str, Any]] = []
    by_model: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0
    unknown_model = False
    route_override_steps: List[str] = []
    input_estimation_mode = "runtime_prompt_projection_v1"
    output_estimation_mode = "response_text_ratio_v1"
    max_preview_payload_bytes = 0

    for spec in prompts:
        route = resolve_effective_step_route(
            phase,
            spec.step_id,
            cfg,
            tier_override=spec.tier_override,
            step_contract=spec.contract,
        )
        reason = str(route.get("reason") or "")
        if reason.startswith("contract_lane") or reason.startswith("env_"):
            route_override_steps.append(spec.step_id)
        prompt_text = safe_read(spec.prompt_path)
        partition_input_tokens = 0
        partition_output_tokens = 0
        max_files = max_files_for_phase(phase, cfg)
        for partition in partitions:
            usage = preview_partition_usage(
                phase=phase,
                step_id=spec.step_id,
                prompt_text=prompt_text,
                output_artifacts=spec.output_artifacts,
                provider=str(route.get("provider") or ""),
                model_id=str(route.get("model_id") or ""),
                partition=partition,
                cfg=cfg,
                max_files=max_files,
                repo_root=repo_root,
            )
            input_tokens = max(128, int(usage.get("input_tokens", 0) or 0))
            output_tokens = project_preview_output_tokens(
                input_tokens,
                step_contract=spec.contract,
            )
            partition_input_tokens += input_tokens
            partition_output_tokens += output_tokens
            max_preview_payload_bytes = max(
                max_preview_payload_bytes,
                int(usage.get("payload_bytes", 0) or 0),
            )
        priced = pricing_preview_record(
            cfg,
            str(route.get("provider") or ""),
            str(route.get("model_id") or ""),
            partition_input_tokens,
            partition_output_tokens,
        )
        total_input_tokens += partition_input_tokens
        total_output_tokens += partition_output_tokens
        total_cost_usd += float(priced.get("estimated_cost_usd", 0.0) or 0.0)
        unknown_model = bool(unknown_model or priced.get("unknown_model"))
        by_step.append(
            {
                "step_id": spec.step_id,
                "step_tier": route.get("step_tier"),
                "routing_reason": reason,
                "provider": route.get("provider"),
                "model_id": route.get("model_id"),
                "partition_count": len(partitions),
                "estimated_input_tokens": partition_input_tokens,
                "estimated_output_tokens": partition_output_tokens,
                "estimated_cost_usd": round(
                    float(priced.get("estimated_cost_usd", 0.0) or 0.0), 6
                ),
                "input_estimation_mode": input_estimation_mode,
                "output_estimation_mode": (
                    "json_managed_ratio_2pct_v1"
                    if is_json_managed_step(spec.contract)
                    else output_estimation_mode
                ),
                "pricing_source": priced.get("pricing_source"),
            }
        )
        model_key = str(priced.get("pricing_key") or "unknown")
        model_row = by_model.setdefault(
            model_key,
            {
                "provider": priced.get("provider"),
                "model_id": priced.get("model_id"),
                "pricing_source": priced.get("pricing_source"),
                "unknown_model": bool(priced.get("unknown_model")),
                "estimated_input_tokens": 0,
                "estimated_output_tokens": 0,
                "estimated_cost_usd": 0.0,
            },
        )
        model_row["estimated_input_tokens"] += partition_input_tokens
        model_row["estimated_output_tokens"] += partition_output_tokens
        model_row["estimated_cost_usd"] += float(
            priced.get("estimated_cost_usd", 0.0) or 0.0
        )

    if route_override_steps:
        warnings.append(
            "Step-level routing overrides are active for this phase; top-level policy alone does not describe the full spend path."
        )
    if unknown_model:
        warnings.append(
            "At least one preview row is using fallback baseline pricing rather than a verified model-specific rate."
        )
    if any(is_json_managed_step(spec.contract) for spec in prompts):
        warnings.append(
            "JSON-managed steps use a compressed output-token preview heuristic; treat this preview as planning guidance, not ledger authority."
        )
    if getattr(cfg, "compare_mode", None):
        warnings.append(
            "Comparison lane is enabled and can add extra spend beyond the canonical route preview."
        )
    confidence = "medium"
    if unknown_model or route_override_steps or not partitions:
        confidence = "low"
    if phase in premium_synthesis_phases:
        warnings.append(
            "This phase is premium-risk: synthesis routes can cost materially more than inventory phases."
        )
    return {
        "generated_at": now_iso(),
        "phase": phase,
        "partition_count": len(partitions),
        "step_count": len(prompts),
        "pricing_version": pricing_version,
        "routing_policy": cfg.routing_policy,
        "confidence": confidence,
        "route_override_steps": sorted(route_override_steps, key=step_sort_key),
        "input_estimation_mode": input_estimation_mode,
        "output_estimation_mode": output_estimation_mode,
        "preview_authority": "heuristic_non_authoritative",
        "ledger_authority": "runtime_provider_usage_when_available",
        "max_preview_request_payload_bytes": max_preview_payload_bytes,
        "estimated_input_tokens": total_input_tokens,
        "estimated_output_tokens": total_output_tokens,
        "estimated_cost_usd": round(total_cost_usd, 6),
        "steps": sorted(by_step, key=lambda row: step_sort_key(str(row["step_id"]))),
        "models": {
            key: {
                **value,
                "estimated_cost_usd": round(
                    float(value.get("estimated_cost_usd", 0.0) or 0.0), 6
                ),
            }
            for key, value in sorted(by_model.items())
        },
        "warnings": warnings,
    }


def derive_route_readiness_summary(
    phases: Sequence[str],
    routing_policy: str,
    *,
    selected_step_ids_by_phase: Optional[Dict[str, Sequence[str]]],
    normalize_routing_policy: Callable[[str], str],
    active_routing_ladders: Dict[str, Dict[str, List[Tuple[str, str, str]]]],
    clone_ladders: Callable[[str], Dict[str, List[Tuple[str, str, str]]]],
    get_phase_prompts: Callable[[str], List[Any]],
    runner_config_factory: Callable[[str], Any],
    resolve_benchmark_owned_stage_route: Callable[..., Tuple[Any, Any, Any]],
    is_strict_contract_step: Callable[[Any], bool],
    resolve_effective_step_tier: Callable[..., str],
    resolve_step_ladder_compat: Callable[..., List[Tuple[str, str, str]]],
    resolve_effective_step_route: Optional[Callable[..., Dict[str, Any]]] = None,
    provider_api_key_env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    route_meta: Dict[str, Dict[str, Any]] = {}
    configured_route_meta: Dict[str, Dict[str, str]] = {}
    selected_policy = normalize_routing_policy(routing_policy)
    tiers = active_routing_ladders.get(selected_policy) or clone_ladders(selected_policy)

    for phase in phases:
        prompts = get_phase_prompts(phase)
        selected_ids = None
        if isinstance(selected_step_ids_by_phase, dict):
            raw_selected = selected_step_ids_by_phase.get(phase)
            if raw_selected is not None:
                selected_ids = {
                    str(step_id).strip().upper()
                    for step_id in raw_selected
                    if str(step_id).strip()
                }
        for prompt in prompts:
            if selected_ids is not None and prompt.step_id not in selected_ids:
                continue
            step_id = str(prompt.step_id)
            tier_override = prompt.tier_override
            cfg = runner_config_factory(selected_policy)
            if resolve_effective_step_route is not None:
                route_info = resolve_effective_step_route(
                    phase,
                    step_id,
                    cfg,
                    tier_override=tier_override,
                    step_contract=prompt.contract,
                )
                step_tier = str(
                    route_info.get("step_tier")
                    or resolve_effective_step_tier(
                        selected_policy,
                        phase,
                        step_id,
                        tier_override=tier_override,
                    )
                )
                configured_ladder = list(tiers.get(step_tier) or tiers.get("extract") or [])
                ladder = [
                    (
                        str(row[0]),
                        str(row[1]),
                        str(row[2])
                        if len(row) > 2
                        else str(
                            route_info.get("api_key_env")
                            or (provider_api_key_env or {}).get(str(row[0]), "")
                        ),
                    )
                    for row in route_info.get("ladder", [])
                ]
            else:
                benchmark_owned_route, _, _ = resolve_benchmark_owned_stage_route(
                    phase,
                    step_id=step_id,
                    cfg=cfg,
                    stage="primary",
                    step_contract=prompt.contract,
                    strict_required=is_strict_contract_step(prompt.contract),
                )
                if benchmark_owned_route is not None:
                    configured_ladder = [
                        (
                            str(benchmark_owned_route["provider"]),
                            str(benchmark_owned_route["model_id"]),
                            str(benchmark_owned_route["api_key_env"]),
                        )
                    ]
                    ladder = configured_ladder
                else:
                    step_tier = resolve_effective_step_tier(
                        selected_policy,
                        phase,
                        step_id,
                        tier_override=tier_override,
                    )
                    configured_ladder = list(tiers.get(step_tier) or tiers.get("extract") or [])
                    ladder = resolve_step_ladder_compat(
                        selected_policy,
                        phase,
                        step_id,
                        tier_override=tier_override,
                    )
            for provider, model_id, api_key_env in configured_ladder:
                signature = f"{provider}:{model_id}:{api_key_env}"
                configured_route_meta.setdefault(
                    signature,
                    {
                        "route_signature": signature,
                        "provider": provider,
                        "model_id": model_id,
                        "api_key_env": api_key_env,
                    },
                )

            for index, (provider, model_id, api_key_env) in enumerate(ladder):
                signature = f"{provider}:{model_id}:{api_key_env}"
                entry = route_meta.setdefault(
                    signature,
                    {
                        "route_signature": signature,
                        "provider": provider,
                        "model_id": model_id,
                        "api_key_env": api_key_env,
                        "required_active_route": False,
                        "optional_fallback": False,
                        "configured_not_required": False,
                        "fallback_chain_present": False,
                        "steps": [],
                    },
                )
                entry["steps"].append(
                    {
                        "phase": phase,
                        "step_id": step_id,
                        "ladder_index": index,
                        "ladder_size": len(ladder),
                    }
                )
                if index == 0:
                    entry["required_active_route"] = True
                    if len(ladder) > 1:
                        entry["fallback_chain_present"] = True
                else:
                    entry["optional_fallback"] = True

    for signature, configured in configured_route_meta.items():
        route_meta.setdefault(
            signature,
            {
                "route_signature": signature,
                "provider": configured["provider"],
                "model_id": configured["model_id"],
                "api_key_env": configured["api_key_env"],
                "required_active_route": False,
                "optional_fallback": False,
                "configured_not_required": True,
                "fallback_chain_present": False,
                "steps": [],
            },
        )

    routes: List[Dict[str, Any]] = []
    for signature in sorted(route_meta):
        entry = dict(route_meta[signature])
        entry["configured_not_required"] = bool(
            not entry["required_active_route"] and not entry["optional_fallback"]
        )
        if entry["required_active_route"]:
            entry["requirement_level"] = "required_active_route"
        elif entry["optional_fallback"]:
            entry["requirement_level"] = "optional_fallback"
        else:
            entry["requirement_level"] = "configured_not_required"
        routes.append(entry)

    def _collect_envs(level: str) -> List[str]:
        return sorted(
            {
                str(row["api_key_env"]).strip()
                for row in routes
                if str(row.get("requirement_level")) == level
                and str(row.get("api_key_env")).strip()
            }
        )

    def _collect_providers(level: str) -> List[str]:
        return sorted(
            {
                str(row["provider"]).strip().lower()
                for row in routes
                if str(row.get("requirement_level")) == level
                and str(row.get("provider")).strip()
            }
        )

    return {
        "target_policy": selected_policy,
        "target_phases": [str(phase).upper() for phase in phases],
        "routes": routes,
        "provider_categories": {
            "required_active_route": _collect_providers("required_active_route"),
            "optional_fallback": _collect_providers("optional_fallback"),
            "configured_not_required": _collect_providers("configured_not_required"),
        },
        "api_key_env_categories": {
            "required_active_route": _collect_envs("required_active_route"),
            "optional_fallback": _collect_envs("optional_fallback"),
            "configured_not_required": _collect_envs("configured_not_required"),
        },
    }


def collect_provider_routes(
    phases: List[str],
    routing_policy: str,
    *,
    selected_step_ids_by_phase: Optional[Dict[str, Sequence[str]]],
    derive_route_readiness_summary: Callable[..., Dict[str, Any]],
) -> Dict[str, Dict[str, str]]:
    summary = derive_route_readiness_summary(
        phases,
        routing_policy,
        selected_step_ids_by_phase=selected_step_ids_by_phase,
    )
    return {
        str(row["route_signature"]): {
            "provider": str(row["provider"]),
            "model_id": str(row["model_id"]),
            "api_key_env": str(row["api_key_env"]),
        }
        for row in summary["routes"]
        if str(row.get("requirement_level")) != "configured_not_required"
    }


def run_provider_preflight(
    root: Path,
    run_id: str,
    cfg: Any,
    phases: List[str],
    *,
    selected_execution_step_ids_for_phase: Callable[[Any, str], Optional[List[str]]],
    collect_provider_routes: Callable[..., Dict[str, Dict[str, str]]],
    run_provider_doctor_probe: Callable[..., Dict[str, Any]],
    resolve_api_key: Callable[[str, str], Tuple[str, str]],
    current_doctor_root: Callable[[Path], Path],
    now_iso: Callable[[], str],
    write_json: Callable[[Path, Any], None],
    routing_policy_version: str,
    scope_kind: str = "launch",
    scope_complete_for_launch: bool = True,
) -> Tuple[bool, Dict[str, Any]]:
    selected_step_ids_by_phase = {
        phase: selected_ids
        for phase in phases
        if (selected_ids := selected_execution_step_ids_for_phase(cfg, phase)) is not None
    }
    provider_routes = collect_provider_routes(
        phases=phases,
        routing_policy=cfg.routing_policy,
        selected_step_ids_by_phase=selected_step_ids_by_phase or None,
    )
    provider_probes = [
        run_provider_doctor_probe(
            provider=route["provider"],
            model_id=route["model_id"],
            api_key_env=route["api_key_env"],
            cfg=cfg,
        )
        for route in provider_routes.values()
    ]
    batch_capability: Dict[str, Any] = {
        "enabled": bool(cfg.batch_mode),
        "provider": cfg.batch_provider,
        "status": "SKIPPED",
        "checks": [],
    }
    if cfg.batch_mode:
        checks: List[Dict[str, Any]] = []
        providers_to_check: Set[str] = set()
        if cfg.batch_provider == "auto":
            providers_to_check = {
                str(route["provider"]) for route in provider_routes.values()
            }
        else:
            providers_to_check = {cfg.batch_provider}
        for provider in sorted(providers_to_check):
            api_key_env = "OPENAI_API_KEY"
            if provider == "gemini":
                api_key_env = "GEMINI_API_KEY"
            elif provider == "xai":
                api_key_env = "XAI_API_KEY"
            api_key, _ = resolve_api_key(provider, api_key_env)
            checks.append(
                {
                    "provider": provider,
                    "api_key_env": api_key_env,
                    "api_key_present": bool(api_key),
                }
            )
        batch_capability = {
            "enabled": True,
            "provider": cfg.batch_provider,
            "status": (
                "PASS" if all(row["api_key_present"] for row in checks) else "FAIL"
            ),
            "checks": checks,
        }
    failures = [probe for probe in provider_probes if not bool(probe.get("ready"))]
    failure_summary: List[Dict[str, Any]] = []
    for probe in failures:
        provider = str(probe.get("provider") or "")
        remediation = None
        if provider == "openrouter" and str(probe.get("failure_type") or "") == "auth_rejected":
            remediation = (
                "Current bounded first-live A/H/D/C routes still require this OpenRouter model "
                "for strict JSON-managed steps. Fix the active OpenRouter credential path "
                f"({probe.get('api_key_env_resolved') or probe.get('api_key_env_name')}) "
                "or the bounded online route remains blocked."
            )
        failure_summary.append(
            {
                "provider": provider,
                "model_id": str(probe.get("model_id") or ""),
                "api_key_env": probe.get("api_key_env_resolved")
                or probe.get("api_key_env_name"),
                "failure_type": probe.get("failure_type"),
                "status_code": probe.get("status_code"),
                "provider_signature": probe.get("provider_signature"),
                "readiness_blocker": probe.get("readiness_blocker"),
                "remediation": remediation,
            }
        )
    blocker_codes = sorted(
        {
            str(blocker.get("blocker_code"))
            for probe in failures
            if isinstance((blocker := probe.get("readiness_blocker")), dict)
            and str(blocker.get("blocker_code"))
        }
    )
    rerun_worthiness = (
        "worth_rerunning_after_fixes"
        if failures
        and all(
            str((probe.get("readiness_blocker") or {}).get("rerun_worthiness", "")).startswith("rerun_after_")
            for probe in failures
        )
        else ("ready_now" if not failures else "not_until_root_caused")
    )
    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "status": "PASS" if not failures else "FAIL",
        "phase_scope": [str(phase).upper() for phase in phases],
        "step_scope": {
            str(phase).upper(): [str(step_id).strip().upper() for step_id in selected_ids]
            for phase, selected_ids in selected_step_ids_by_phase.items()
        },
        "scope_kind": str(scope_kind or "launch"),
        "scope_complete_for_launch": bool(scope_complete_for_launch),
        "routes": provider_routes,
        "probes": provider_probes,
        "failed_providers": [probe.get("provider") for probe in failures],
        "failed_blocker_codes": blocker_codes,
        "failure_summary": failure_summary,
        "rerun_worthiness": rerun_worthiness,
        "routing_policy": cfg.routing_policy,
        "routing_policy_version": routing_policy_version,
        "batch_capability": batch_capability,
    }
    doctor_dir = current_doctor_root(root)
    doctor_dir.mkdir(parents=True, exist_ok=True)
    doctor_payload = dict(payload)
    doctor_payload.update(
        shared_doctor_advisory_fields(
            "PROVIDER_PREFLIGHT.json",
            run_id=run_id,
        )
    )
    write_json(doctor_dir / "PROVIDER_PREFLIGHT.json", doctor_payload)
    return (not failures), payload
