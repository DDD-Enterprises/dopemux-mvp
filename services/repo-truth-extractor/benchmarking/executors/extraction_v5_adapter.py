from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .base import ExecutionResult, ExecutorAdapter

SCRIPT = Path(__file__).resolve().parents[2] / "run_extraction_v5.py"
FIXTURE_REPO = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden_repo_min"


class ExtractionV5Adapter(ExecutorAdapter):
    adapter_name = "runtime_v5_extraction"

    def _execution_config(self, case: dict[str, Any], work_root: Path) -> dict[str, Any]:
        campaign = dict(case.get("campaign_execution") or {})
        if campaign:
            return {
                "run_id": str(campaign.get("run_id") or "benchmark_v5_case"),
                "phase": str(campaign.get("phase") or "A"),
                "output_root": Path(str(campaign.get("output_root") or (work_root / "v5_run"))),
                "repo_root": Path(str(campaign.get("repo_root") or FIXTURE_REPO)),
                "live_execution": bool(campaign.get("live_execution", False)),
                "routing_override_model": str(campaign.get("routing_override_model") or ""),
                "route_id": str(campaign.get("route_id") or ""),
                "surface_class": str(campaign.get("surface_class") or ""),
                "provider_name": str(campaign.get("provider_name") or ""),
            }
        return {
            "run_id": "benchmark_v5_case",
            "phase": "A",
            "output_root": work_root / "v5_run",
            "repo_root": FIXTURE_REPO,
            "live_execution": False,
            "routing_override_model": "",
            "route_id": "",
            "surface_class": "openrouter_routed",
            "provider_name": "openrouter",
        }

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _load_json_if_present(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def execute(self, case: dict[str, Any], work_root: Path) -> ExecutionResult:
        self.validate_case(case)
        config = self._execution_config(case, work_root)
        run_id = str(config["run_id"])
        output_root = Path(config["output_root"])
        phase = str(config["phase"])
        repo_root = Path(config["repo_root"])
        live_execution = bool(config["live_execution"])
        routing_override_model = str(config["routing_override_model"])
        command = [
            sys.executable,
            str(SCRIPT),
            "--phase",
            phase,
            "--run-id",
            run_id,
            "--output-root",
            str(output_root),
            "--ui",
            "plain",
            "--no-batch",
            "--partition-workers",
            "1",
        ]
        env = dict(os.environ)
        if live_execution:
            command.append("--execute")
            env["DPMX_LIVE_OK"] = "1"
            if routing_override_model:
                env["DPMX_ROUTING_ENABLE"] = "1"
                for step_type_env in ("DPMX_MODEL_INVENTORY", "DPMX_MODEL_EXTRACT", "DPMX_MODEL_QA", "DPMX_MODEL_SYNTHESIS"):
                    env[step_type_env] = routing_override_model
        else:
            command.append("--dry-run")
        result = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        run_root = output_root / "runs" / run_id
        if not run_root.exists():
            raise subprocess.CalledProcessError(
                returncode=result.returncode,
                cmd=command,
                output=result.stdout,
                stderr=result.stderr,
            )
        phase_root = run_root / "A_repo_control_plane"
        if phase != "A":
            phase_root = run_root / f"{phase}_phase"
        routing_fingerprint = self._load_json_if_present(run_root / "RUN_ROUTING_FINGERPRINT.json")
        step_metrics = self._load_json_if_present(run_root / "telemetry" / "STEP_METRICS.json")
        run_dashboard = self._load_json_if_present(run_root / "telemetry" / "RUN_DASHBOARD.json")
        failure_index = self._load_json_if_present(run_root / "telemetry" / "FAILURE_INDEX.json")
        qa_payload = self._load_json_if_present(phase_root / "qa" / "A0_QA.json")
        qa_merge_payload = self._load_json_if_present(phase_root / "qa" / "A99_QA.json")
        raw_payload = self._load_json_if_present(phase_root / "raw" / "A0__A_P0001.json")
        output_payload = self._load_json_if_present(phase_root / "norm" / "REPOCTRL_INVENTORY.json")
        repoctrl_qa = self._load_json_if_present(phase_root / "norm" / "REPOCTRL_QA.json")
        effective_route = (
            routing_fingerprint.get("effective_model_routing", {}).get("A")
            or routing_fingerprint.get("effective_model_routing", {}).get(phase)
            or str(config["route_id"])
        )
        step_rows = step_metrics.get("steps", {})
        total_latency_ms = round(
            sum(float(payload.get("elapsed_ms", 0.0)) for payload in step_rows.values()),
            6,
        )
        total_retry_cost = round(
            sum(float(payload.get("retry_extra_cost_estimate_usd", 0.0)) for payload in step_rows.values()),
            6,
        )
        total_tokens_input = sum(int(payload.get("prompt_tokens", 0) or 0) for payload in step_rows.values())
        total_tokens_output = sum(int(payload.get("completion_tokens", 0) or 0) for payload in step_rows.values())
        route_hops = []
        step_route_counts: dict[str, list[str]] = {}
        for payload in step_rows.values():
            final_routes = payload.get("final_route_counts", {})
            if isinstance(final_routes, dict):
                route_hops.extend(sorted(str(item) for item in final_routes.keys()))
        for step_key, payload in sorted(step_rows.items()):
            final_routes = payload.get("final_route_counts", {})
            if isinstance(final_routes, dict) and final_routes:
                step_route_counts[str(step_key)] = sorted(str(item) for item in final_routes.keys())
        phase_status = run_dashboard.get("payload", {}).get("phases", {}).get("A", {}).get("status")
        missing_artifacts = list(qa_payload.get("missing_expected_artifacts") or [])
        missing_merge_artifacts = list(qa_merge_payload.get("missing_expected_artifacts") or [])
        contract_gate_pass = (
            result.returncode == 0
            and not missing_artifacts
            and not missing_merge_artifacts
            and phase_status in {"PASS", "", None}
        )
        fail_reasons = []
        if result.returncode != 0:
            fail_reasons.append(f"runtime_exit_{result.returncode}")
        if missing_artifacts:
            fail_reasons.append("missing_expected_artifacts")
        if missing_merge_artifacts:
            fail_reasons.append("missing_merge_artifacts")
        if phase_status and phase_status != "PASS":
            fail_reasons.append(f"phase_status_{phase_status.lower()}")
        if failure_index:
            fail_reasons.append("failure_index_present")
        return ExecutionResult(
            adapter_name=self.adapter_name,
            case_id=str(case["case_id"]),
            succeeded=result.returncode == 0,
            contract_gate_pass=contract_gate_pass,
            contract_gate_strength="strong",
            contract_fail_reason=";".join(fail_reasons) if fail_reasons else None,
            output_artifact_ref="outputs/REPOCTRL_INVENTORY.json",
            outputs={
                "REPOCTRL_INVENTORY.json": output_payload,
                "A0_QA.json": qa_payload,
                "A99_QA.json": qa_merge_payload,
                "REPOCTRL_QA.json": repoctrl_qa,
                "A0__A_P0001.json": raw_payload,
                "STEP_METRICS.json": step_metrics,
                "RUN_DASHBOARD.json": run_dashboard,
                "FAILURE_INDEX.json": failure_index,
            },
            route_trace={
                "surface_class": str(config["surface_class"]),
                "execution_mode": "live_execute" if live_execution else "dry_run",
                "phase": phase,
                "logical_route_id": str(config["route_id"]),
                "provider_name": str(config["provider_name"]),
                "route_hops": route_hops or [effective_route],
                "step_route_counts": step_route_counts,
                "routing_fingerprint_path": str(run_root / "RUN_ROUTING_FINGERPRINT.json"),
                "run_root": str(run_root),
            },
            task_eval={
                "status": "captured",
                "task_success_score": 1.0,
                "latency_ms": total_latency_ms,
                "tokens_input": total_tokens_input,
                "tokens_output": total_tokens_output,
                "cost_estimate_usd": total_retry_cost,
                "phase_status": run_dashboard.get("payload", {}).get("phases", {}).get("A", {}).get("status"),
            },
            executor_links={
                "script": str(SCRIPT),
                "cwd": str(repo_root),
                "run_root": str(run_root),
                "phase_root": str(phase_root),
                "output_root": str(output_root),
                "return_code": result.returncode,
                "stdout_excerpt": result.stdout.splitlines()[-1] if result.stdout.splitlines() else "",
                "stderr_excerpt": result.stderr.splitlines()[-1] if result.stderr.splitlines() else "",
            },
            validator_inputs={
                "qa_path": str(phase_root / "qa" / "A0_QA.json"),
                "qa_merge_path": str(phase_root / "qa" / "A99_QA.json"),
                "routing_fingerprint_path": str(run_root / "RUN_ROUTING_FINGERPRINT.json"),
                "phase_root": str(phase_root),
            },
            repair_invocations=int(qa_payload.get("repair_invocations", 0)),
            sidefill_invocations=int(qa_payload.get("sidefill_invocations", 0)),
            route_hop_total=len(route_hops) or 1,
            work_root=str(run_root),
        )
