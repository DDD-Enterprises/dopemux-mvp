#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from typing import List, Optional

SERVICE_ROOT = Path(__file__).resolve().parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # type: ignore[import-not-found]
from fl_int.models import FLIntStep, ladder_for_step
from fl_int.run_fl_int import normalize_step_payload, run_fl_int as run_fl_int_pipeline
from s_int.schema_validate import validate_payload


def _build_cfg(args: argparse.Namespace) -> runner.RunnerConfig:
    return runner.RunnerConfig(
        dry_run=bool(args.dry_run),
        max_files_docs=35,
        max_files_code=20,
        max_chars=650000,
        max_request_bytes=200000,
        file_truncate_chars=70000,
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
        executor="thread",
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy=str(args.routing_policy),
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
        max_cost_usd=None,
        selected_s_steps=None,
        selected_execution_step=None,
        d0_max_files=None,
        d1_max_files=None,
        provider_denylist=(),
        fl_int_provider_timeout_seconds=int(args.fl_int_provider_timeout_seconds),
        fl_int_f0_batch_timeout_seconds=int(args.fl_int_f0_batch_timeout_seconds),
    )


def _prompt_executor(cfg: runner.RunnerConfig):
    def _execute(step: FLIntStep, rendered_prompt: str, schema: dict, _prior_outputs: dict) -> dict:
        step_cfg = replace(cfg, escalation_max_hops=max(0, int(step.max_hops) - 1))
        ladder = ladder_for_step(step)
        observer = _prior_outputs.get("__fl_int_diag_observer__")
        if not callable(observer):
            observer = None

        def _execute_attempt(route, _hop_index):  # type: ignore[no-untyped-def]
            provider, model_id, api_key_env = route
            if observer is not None:
                observer(
                    "provider_call_start",
                    {
                        "route": route,
                        "request_meta": {
                            "provider": provider,
                            "model_id": model_id,
                            "api_key_env_requested": api_key_env,
                        },
                    },
                )
            result = runner.call_llm(
                provider=provider,
                model_id=model_id,
                api_key_env=api_key_env,
                system_prompt="Return JSON only.",
                user_content=rendered_prompt,
                cfg=step_cfg,
                timeout_seconds=step_cfg.fl_int_provider_timeout_seconds,
            )
            meta = dict(result.get("meta") or {})
            response_text = str(result.get("text") or "")
            if observer is not None:
                observer(
                    "provider_call_return",
                    {
                        "route": route,
                        "request_meta": meta,
                        "response_received": bool(meta.get("response_received") or response_text),
                        "response_text_chars": len(response_text),
                    },
                )
            payload = None
            schema_errors: List[str] = []
            escalation_trigger = str(meta.get("failure_type") or "").strip() or None
            if not escalation_trigger:
                if observer is not None:
                    observer(
                        "normalize_start",
                        {
                            "route": route,
                            "request_meta": meta,
                            "response_received": bool(response_text),
                            "response_text_chars": len(response_text),
                        },
                    )
                try:
                    payload = json.loads(response_text)
                except Exception:
                    meta["failure_type"] = "invalid_json"
                    escalation_trigger = "invalid_json"
                else:
                    payload = normalize_step_payload(step.step_id, payload, _prior_outputs)
                    if observer is not None:
                        observer(
                            "normalize_return",
                            {
                                "route": route,
                                "request_meta": meta,
                                "response_received": bool(response_text),
                                "response_text_chars": len(response_text),
                            },
                        )
                    schema_errors = validate_payload(payload, schema)
                    if schema_errors:
                        meta["failure_type"] = "schema_invalid"
                        meta["schema_errors"] = list(schema_errors)
                        if any("missing required key" in row for row in schema_errors):
                            escalation_trigger = "schema_missing_key"
                        else:
                            escalation_trigger = "format_violation"
            return {
                "response_text": response_text,
                "request_meta": meta,
                "artifacts": [payload] if isinstance(payload, dict) else [],
                "route": route,
                "artifacts_ok": isinstance(payload, dict) and not schema_errors,
                "escalation_trigger": escalation_trigger,
            }

        ladder_result = runner.call_llm_with_ladder(
            phase="FL_INT",
            step_id=step.step_id,
            partition_id=step.step_id,
            routing_policy=cfg.routing_policy,
            routing_tier=step.routing_tier,
            ladder=ladder,
            cfg=step_cfg,
            execute_attempt=_execute_attempt,
            ui=None,
        )
        payload = None
        request_meta = (
            dict(ladder_result.get("request_meta") or {})
            if isinstance(ladder_result.get("request_meta"), dict)
            else {}
        )
        response_text = str(ladder_result.get("response_text") or "")
        route = ladder_result.get("route")
        artifacts = ladder_result.get("artifacts")
        if isinstance(artifacts, list) and artifacts:
            candidate = artifacts[0]
            if isinstance(candidate, dict):
                payload = candidate
        if payload is None and response_text:
            try:
                payload = json.loads(response_text)
            except Exception:
                request_meta.setdefault("failure_type", "invalid_json")
        if isinstance(payload, dict):
            payload = normalize_step_payload(step.step_id, payload, _prior_outputs)
            errors = validate_payload(payload, schema)
            if errors:
                request_meta["failure_type"] = "schema_invalid"
                request_meta["schema_errors"] = list(errors)
                payload = None
        return {
            "payload": payload,
            "request_meta": request_meta,
            "response_text": response_text,
            "route": route,
        }

    return _execute


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser("FL_INT standalone post-processor")
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--out-root", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--routing-policy", default="cost")
    parser.add_argument("--fl-int-provider-timeout-seconds", type=int, default=180)
    parser.add_argument("--fl-int-f0-batch-timeout-seconds", type=int, default=210)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    run_root = Path(args.run_root).resolve()
    out_root = Path(args.out_root).resolve() if str(args.out_root).strip() else None
    cfg = _build_cfg(args)
    try:
        summary = run_fl_int_pipeline(
            run_root,
            dry_run=bool(args.dry_run),
            out_root=out_root,
            prompt_executor=None if args.dry_run else _prompt_executor(cfg),
            f0_batch_timeout_seconds=cfg.fl_int_f0_batch_timeout_seconds,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
