from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .extractor_commands import _extractor_runner_path, _resolve_extractor_root


DEFAULT_REPORT_ROOT = Path("reports/repo-truth-extractor/validation")
DEFAULT_CANARY_PHASES = ("D", "C", "R")
DEFAULT_DOCS_GOV_PHASES = ("A", "H", "D", "W", "B", "G")
DEFAULT_CODE_QA_PHASES = ("C", "E", "Q")
DEFAULT_SYNTHESIS_PHASES = ("R", "X", "T", "Z", "S")
DEFAULT_PROVIDER_ENV_VARS = (
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "XAI_API_KEY",
    "OPENROUTER_API_KEY",
)
DEFAULT_SECURITY_COMMANDS: Dict[str, Sequence[str]] = {
    "pip_audit": ("pip-audit",),
    "bandit": ("bandit", "-r", "src", "services/repo-truth-extractor"),
    "semgrep": ("semgrep", "--config", "auto", "src", "services/repo-truth-extractor"),
    "gitleaks": ("gitleaks", "detect", "--no-git", "--source", "."),
}
NORMALIZED_EPHEMERAL_KEYS = {
    "generated_at",
    "updated_at",
    "started_at",
    "finished_at",
    "created_at",
    "ts",
    "run_id",
    "run_root",
    "phase_dir",
    "coverage_rollup",
    "doctor_auth",
    "doctor_full",
    "latest_run_id_file",
    "last_modified",
    "proof_path",
}


class ValidationFailure(RuntimeError):
    """Raised when a validation gate fails in fail-closed mode."""


@dataclass
class ValidationConfig:
    promptset_root: Path
    stage: str = "preflight"
    run_id: Optional[str] = None
    report_root: Path = DEFAULT_REPORT_ROOT
    routing_policy: str = "balanced_openrouter"
    canary_phases: Sequence[str] = DEFAULT_CANARY_PHASES
    docs_governance_phases: Sequence[str] = DEFAULT_DOCS_GOV_PHASES
    code_qa_phases: Sequence[str] = DEFAULT_CODE_QA_PHASES
    synthesis_phases: Sequence[str] = DEFAULT_SYNTHESIS_PHASES
    canary_max_usd: float = 15.0
    canary_max_minutes: float = 45.0
    full_max_usd: float = 75.0
    full_max_minutes: float = 240.0
    tp008_map: Optional[Path] = None
    pricing_manifest: Optional[Path] = None


@dataclass
class StepRecord:
    name: str
    kind: str
    status: str
    detail: str
    command: List[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    elapsed_seconds: float = 0.0
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_validation_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"rte_v5_validation_{stamp}"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: Dict[str, Any] = {}
        for key in sorted(value):
            if key in NORMALIZED_EPHEMERAL_KEYS:
                continue
            normalized[key] = _normalize_payload(value[key])
        return normalized
    if isinstance(value, list):
        return [_normalize_payload(item) for item in value]
    if isinstance(value, str):
        if "T" in value and value.endswith("Z"):
            return "<timestamp>"
        return value
    return value


def _collect_phase_file_map(phase_dir: Path, bucket: str) -> Dict[str, str]:
    bucket_dir = phase_dir / bucket
    if not bucket_dir.exists():
        return {}
    out: Dict[str, str] = {}
    for file_path in sorted(bucket_dir.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(bucket_dir).as_posix()
        if file_path.suffix.lower() == ".json":
            out[rel] = hashlib.sha256(
                json.dumps(_normalize_payload(_load_json(file_path)), sort_keys=True, ensure_ascii=True).encode("utf-8")
            ).hexdigest()
        else:
            out[rel] = _sha256_file(file_path)
    return out


def _load_pricing_manifest(path: Optional[Path]) -> Dict[str, float]:
    if path is None:
        return {}
    payload = _load_json(path)
    raw_bounds = payload.get("route_call_upper_bounds")
    if not isinstance(raw_bounds, dict):
        raise ValidationFailure(
            f"Pricing manifest must contain route_call_upper_bounds: {path}"
        )
    parsed: Dict[str, float] = {}
    for key, value in raw_bounds.items():
        try:
            parsed[str(key)] = float(value)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValidationFailure(f"Invalid pricing manifest entry for {key}: {value}") from exc
    return parsed


def _phase_missing_required_artifacts(coverage_rollup: Dict[str, Any], phase: str) -> List[str]:
    phases = coverage_rollup.get("phases")
    if not isinstance(phases, dict):
        return [f"{phase}:missing_coverage_rollup"]
    row = phases.get(phase)
    if not isinstance(row, dict):
        return [f"{phase}:missing_phase_row"]
    if str(row.get("status") or "").upper() != "PASS":
        return [f"{phase}:status={row.get('status')}"]
    return []


def _estimate_upper_bound_spend(
    usage_payload: Dict[str, Any],
    route_call_upper_bounds: Dict[str, float],
) -> Dict[str, Any]:
    counts = usage_payload.get("step_done_route_counts")
    if not isinstance(counts, dict) or not counts:
        counts = usage_payload.get("step_start_counts")
    if not isinstance(counts, dict) or not counts:
        return {"estimated_upper_bound_usd": 0.0, "missing_routes": [], "matched_routes": {}}

    total = 0.0
    missing_routes: List[str] = []
    matched_routes: Dict[str, Dict[str, Any]] = {}
    for route, raw_count in sorted(counts.items()):
        try:
            count = int(raw_count)
        except Exception:
            continue
        if route not in route_call_upper_bounds:
            missing_routes.append(str(route))
            continue
        unit_cost = float(route_call_upper_bounds[route])
        subtotal = unit_cost * float(count)
        total += subtotal
        matched_routes[str(route)] = {
            "count": count,
            "upper_bound_per_call_usd": unit_cost,
            "upper_bound_total_usd": round(subtotal, 6),
        }
    return {
        "estimated_upper_bound_usd": round(total, 6),
        "missing_routes": missing_routes,
        "matched_routes": matched_routes,
    }


def _compare_prompt_step_sets(
    *,
    required_steps: Iterable[str],
    observed_steps: Iterable[str],
) -> Dict[str, Any]:
    required = {str(step).strip().upper() for step in required_steps if str(step).strip()}
    observed = {str(step).strip().upper() for step in observed_steps if str(step).strip()}
    return {
        "required_steps": sorted(required),
        "observed_steps": sorted(observed),
        "missing_steps": sorted(required - observed),
        "extra_steps": sorted(observed - required),
        "matches": required == observed,
    }


class LiveValidationRunner:
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.repo_root = _resolve_extractor_root(Path.cwd())
        if self.repo_root is None:
            raise ValidationFailure("Cannot find repo-truth-extractor from the current workspace.")
        self.service_root = self.repo_root / "services" / "repo-truth-extractor"
        self.run_id = config.run_id or default_validation_run_id()
        self.report_dir = (self.repo_root / config.report_root / self.run_id).resolve()
        self.log_dir = self.report_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.steps: List[StepRecord] = []
        self.blockers: List[str] = []
        self.started_at = time.monotonic()
        self.pricing_manifest = _load_pricing_manifest(config.pricing_manifest)

    def run(self) -> Dict[str, Any]:
        self._record_baseline()
        try:
            self._run_preflight_stages()
            if self.config.stage in {"canary", "full"}:
                self._ensure_pricing_manifest_for_paid_stage()
                self._run_paid_canary()
            if self.config.stage == "full":
                self._run_paid_full()
        except ValidationFailure as exc:
            self.blockers.append(str(exc))

        payload = self._build_report_payload()
        _write_json(self.report_dir / "VALIDATION_REPORT.json", payload)
        _write_text(self.report_dir / "VALIDATION_REPORT.md", self._render_markdown_report(payload))
        return payload

    def _record_step(self, record: StepRecord) -> None:
        self.steps.append(record)
        if record.status == "fail":
            self.blockers.append(f"{record.name}: {record.detail}")

    def _record_baseline(self) -> None:
        provider_env = {
            key: {"present": bool(os.environ.get(key)), "source": "env"}
            for key in DEFAULT_PROVIDER_ENV_VARS
        }
        baseline = {
            "generated_at": now_iso(),
            "run_id": self.run_id,
            "repo_root": str(self.repo_root),
            "git_sha": self._git_sha(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "promptset_root": str(self.config.promptset_root.resolve()),
            "routing_policy": self.config.routing_policy,
            "stage": self.config.stage,
            "caps": {
                "canary_max_usd": self.config.canary_max_usd,
                "canary_max_minutes": self.config.canary_max_minutes,
                "full_max_usd": self.config.full_max_usd,
                "full_max_minutes": self.config.full_max_minutes,
            },
            "provider_env": provider_env,
            "tp008_map": str(self.config.tp008_map.resolve()) if self.config.tp008_map else None,
            "pricing_manifest": str(self.config.pricing_manifest.resolve()) if self.config.pricing_manifest else None,
        }
        _write_json(self.report_dir / "RUN_BASELINE.json", baseline)

    def _git_sha(self) -> str:
        proc = subprocess.run(
            ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return "UNKNOWN"
        return proc.stdout.strip() or "UNKNOWN"

    def _python_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        repo_src = str((self.repo_root / "src").resolve())
        if existing:
            env["PYTHONPATH"] = f"{repo_src}{os.pathsep}{existing}"
        else:
            env["PYTHONPATH"] = repo_src
        return env

    def _dopemux_cli(self, *args: str) -> List[str]:
        return [sys.executable, "-m", "dopemux.cli", *args]

    def _runner_cli(self, *args: str) -> List[str]:
        runner = _extractor_runner_path(self.repo_root, "v5")
        return [sys.executable, str(runner), *args]

    def _load_v5_runner_module(self):
        runner_path = _extractor_runner_path(self.repo_root, "v5")
        spec = importlib.util.spec_from_file_location(
            "run_extraction_v5_validation",
            runner_path,
        )
        if spec is None or spec.loader is None:
            raise ValidationFailure(f"Unable to load runner module: {runner_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _run_command(
        self,
        name: str,
        command: Sequence[str],
        *,
        timeout_seconds: Optional[float] = None,
        env: Optional[Dict[str, str]] = None,
        kind: str = "command",
    ) -> StepRecord:
        safe_name = name.replace("/", "_").replace(" ", "_")
        stdout_path = self.log_dir / f"{safe_name}.stdout.txt"
        stderr_path = self.log_dir / f"{safe_name}.stderr.txt"
        started = time.monotonic()
        try:
            proc = subprocess.run(
                list(command),
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env or self._python_env(),
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - started
            stdout_text = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
            stderr_text = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
            _write_text(stdout_path, stdout_text)
            _write_text(stderr_path, stderr_text)
            return StepRecord(
                name=name,
                kind=kind,
                status="fail",
                detail=f"timed out after {timeout_seconds:.1f}s" if timeout_seconds else "timed out",
                command=list(command),
                exit_code=None,
                elapsed_seconds=round(elapsed, 3),
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
            )
        elapsed = time.monotonic() - started
        _write_text(stdout_path, proc.stdout)
        _write_text(stderr_path, proc.stderr)
        return StepRecord(
            name=name,
            kind=kind,
            status="pass" if proc.returncode == 0 else "fail",
            detail="ok" if proc.returncode == 0 else f"exit code {proc.returncode}",
            command=list(command),
            exit_code=proc.returncode,
            elapsed_seconds=round(elapsed, 3),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
        )

    def _run_preflight_stages(self) -> None:
        self._validate_prompt_sources()
        self._run_reliability_tests()
        self._run_security_gates()
        self._run_non_paid_execution_gates()

    def _validate_prompt_sources(self) -> None:
        promptset_root = self.config.promptset_root.resolve()
        required = ["promptset.yaml", "artifacts.yaml", "model_map.yaml"]
        missing = [name for name in required if not (promptset_root / name).exists()]
        if missing:
            raise ValidationFailure(
                f"Promptset root is missing required files: {', '.join(missing)}"
            )

        sys.path.insert(0, str(self.service_root))
        from lib.promptgen.integrity_validator import validate_from_files

        result = validate_from_files(
            promptset_path=promptset_root / "promptset.yaml",
            artifacts_path=promptset_root / "artifacts.yaml",
            model_map_path=promptset_root / "model_map.yaml",
        )
        _write_json(self.report_dir / "PROMPTSET_VALIDATE_RESULT.json", result)
        promptset_step = StepRecord(
            name="promptset_validate_external",
            kind="python",
            status="pass" if bool(result.get("passed")) else "fail",
            detail="ok" if bool(result.get("passed")) else f"errors={result.get('error_count', 0)}",
            artifacts={"result_path": str((self.report_dir / 'PROMPTSET_VALIDATE_RESULT.json').resolve())},
        )
        self._record_step(promptset_step)
        if not result.get("passed"):
            raise ValidationFailure("External promptset validation failed.")

        self._record_step(
            self._run_command(
                "v5_prompt_truth_tests",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--no-cov",
                    "services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py",
                ],
            )
        )
        self._record_step(
            self._run_command(
                "v4_promptset_audit",
                self._dopemux_cli(
                    "upgrades",
                    "promptset",
                    "audit",
                    "--pipeline-version",
                    "v4",
                    "--strict",
                ),
            )
        )
        self._record_prompt_discovery_contract()
        if self.blockers:
            raise ValidationFailure("Prompt source validation gates failed.")

    def _record_prompt_discovery_contract(self) -> None:
        runner = self._load_v5_runner_module()
        phase_results: Dict[str, Any] = {}
        drift: Dict[str, Any] = {}
        for phase, required_steps in sorted(runner.REQUIRED_PROMPT_STEP_IDS.items()):
            try:
                specs = runner.get_phase_prompts(phase)
                observed_steps = [spec.step_id for spec in specs]
                phase_result = _compare_prompt_step_sets(
                    required_steps=required_steps,
                    observed_steps=observed_steps,
                )
                phase_result["prompt_paths_exist"] = all(spec.prompt_path.exists() for spec in specs)
            except Exception as exc:
                phase_result = {
                    "required_steps": sorted(str(step) for step in required_steps),
                    "observed_steps": [],
                    "missing_steps": sorted(str(step) for step in required_steps),
                    "extra_steps": [],
                    "matches": False,
                    "prompt_paths_exist": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            phase_results[phase] = phase_result
            if (
                not phase_result.get("matches")
                or not bool(phase_result.get("prompt_paths_exist"))
            ):
                drift[phase] = phase_result

        artifact_path = self.report_dir / "PROMPT_DISCOVERY_CONTRACT.json"
        _write_json(
            artifact_path,
            {
                "generated_at": now_iso(),
                "phase_results": phase_results,
                "drift": drift,
            },
        )
        self._record_step(
            StepRecord(
                name="v5_prompt_discovery_contract",
                kind="python",
                status="pass" if not drift else "fail",
                detail="ok" if not drift else f"drift phases={','.join(sorted(drift))}",
                artifacts={"result_path": str(artifact_path.resolve())},
            )
        )

    def _run_reliability_tests(self) -> None:
        self._record_step(
            self._run_command(
                "extractor_test_suite",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--no-cov",
                    "services/repo-truth-extractor/tests",
                ],
            )
        )
        focused_tests = [
            "services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_concurrency.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_rollup_reports.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_soft_gate_logging.py",
            "services/repo-truth-extractor/tests/test_run_extraction_v5_ui_events.py",
        ]
        self._record_step(
            self._run_command(
                "focused_v5_tests",
                [sys.executable, "-m", "pytest", "--no-cov", *focused_tests],
            )
        )
        if self.config.tp008_map:
            out_dir = self.report_dir / "tp008"
            self._record_step(
                self._run_command(
                    "tp008_drift_audit",
                    [
                        sys.executable,
                        str((self.service_root / "audit_tp008.py").resolve()),
                        "--tp008-map",
                        str(self.config.tp008_map.resolve()),
                        "--out-dir",
                        str(out_dir),
                    ],
                )
            )
        if self.blockers:
            raise ValidationFailure("Code and reliability gates failed.")

    def _run_security_gates(self) -> None:
        pal_health = self._run_command(
            "pal_health",
            [sys.executable, "-c", "import urllib.request; urllib.request.urlopen('http://localhost:3003/health', timeout=5).read()"],
        )
        self._record_step(pal_health)

        for name, command in DEFAULT_SECURITY_COMMANDS.items():
            binary = command[0]
            if shutil.which(binary) is None:
                self._record_step(
                    StepRecord(
                        name=name,
                        kind="security",
                        status="fail",
                        detail=f"required tool not installed: {binary}",
                        command=list(command),
                    )
                )
                continue
            self._record_step(self._run_command(name, command, kind="security"))

        if self.blockers:
            raise ValidationFailure("Security or supply-chain gates failed.")

    def _run_non_paid_execution_gates(self) -> None:
        promptset_root = str(self.config.promptset_root.resolve())
        self._record_step(
            self._run_command(
                "provider_preflight",
                self._dopemux_cli(
                    "upgrades",
                    "preflight",
                    "--pipeline-version",
                    "v5",
                    "--auth-doctor",
                    "--promptset-root",
                    promptset_root,
                ),
            )
        )
        self._record_step(
            self._run_command(
                "print_run_order",
                self._runner_cli("--print-run-order", "--promptset-root", promptset_root),
            )
        )
        self._record_step(
            self._run_command(
                "print_phase_routing",
                self._runner_cli(
                    "--print-phase-routing",
                    "--phase",
                    "ALL",
                    "--promptset-root",
                    promptset_root,
                ),
            )
        )
        self._record_step(
            self._run_command(
                "print_phase_prompts",
                self._runner_cli(
                    "--print-phase-prompts",
                    "ALL",
                    "--promptset-root",
                    promptset_root,
                ),
            )
        )
        for phase in ("D", "C"):
            self._run_determinism_gate(phase)
        if self.blockers:
            raise ValidationFailure("Non-paid execution gates failed.")

    def _run_determinism_gate(self, phase: str) -> None:
        promptset_root = str(self.config.promptset_root.resolve())
        snapshots: Dict[int, Dict[str, Any]] = {}
        for workers in (1, 4):
            run_id = f"{self.run_id}_{phase.lower()}_dry_w{workers}"
            execute = self._run_command(
                f"dry_run_{phase}_w{workers}",
                self._dopemux_cli(
                    "upgrades",
                    "run",
                    "--pipeline-version",
                    "v5",
                    "--phase",
                    phase,
                    "--run-id",
                    run_id,
                    "--dry-run",
                    "--resume",
                    "--partition-workers",
                    str(workers),
                    "--routing-policy",
                    self.config.routing_policy,
                    "--jsonl-events",
                    "--ui",
                    "plain",
                    "--promptset-root",
                    promptset_root,
                ),
            )
            self._record_step(execute)
            verify = self._run_command(
                f"verify_{phase}_w{workers}",
                self._runner_cli(
                    "--run-id",
                    run_id,
                    "--verify-phase-output",
                    phase,
                    "--promptset-root",
                    promptset_root,
                ),
            )
            self._record_step(verify)
            snapshots[workers] = self._phase_snapshot(run_id, phase)

        if snapshots[1] != snapshots[4]:
            diff_path = self.report_dir / f"DETERMINISM_DIFF_{phase}.json"
            _write_json(
                diff_path,
                {"phase": phase, "workers_1": snapshots[1], "workers_4": snapshots[4]},
            )
            self._record_step(
                StepRecord(
                    name=f"determinism_compare_{phase}",
                    kind="comparison",
                    status="fail",
                    detail="normalized dry-run snapshots differ between workers=1 and workers=4",
                    artifacts={"diff_path": str(diff_path)},
                )
            )
            raise ValidationFailure(f"Determinism check failed for phase {phase}.")

        self._record_step(
            StepRecord(
                name=f"determinism_compare_{phase}",
                kind="comparison",
                status="pass",
                detail="normalized dry-run snapshots match for workers=1 and workers=4",
            )
        )

    def _phase_snapshot(self, run_id: str, phase: str) -> Dict[str, Any]:
        run_root = self.repo_root / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id
        phase_dir_name = {
            "A": "A_repo_control_plane",
            "H": "H_home_control_plane",
            "D": "D_docs_pipeline",
            "C": "C_code_surfaces",
            "E": "E_execution_plane",
            "W": "W_workflow_plane",
            "B": "B_boundary_plane",
            "G": "G_governance_plane",
            "Q": "Q_quality_assurance",
            "R": "R_arbitration",
            "X": "X_feature_index",
            "T": "T_task_packets",
            "Z": "Z_handoff_freeze",
            "S": "S_synthesis",
        }[phase]
        phase_dir = run_root / phase_dir_name
        telemetry_dir = run_root / "telemetry"
        snapshot = {
            "coverage_rollup": _normalize_payload(_load_json(run_root / "COVERAGE_ROLLUP.json")),
            "step_metrics": _normalize_payload(_load_json(telemetry_dir / "STEP_METRICS.json")),
            "failure_index": _normalize_payload(_load_json(telemetry_dir / "FAILURE_INDEX.json")),
            "phase_norm": _collect_phase_file_map(phase_dir, "norm"),
            "phase_qa": _collect_phase_file_map(phase_dir, "qa"),
        }
        return snapshot

    def _ensure_pricing_manifest_for_paid_stage(self) -> None:
        if not self.pricing_manifest:
            raise ValidationFailure(
                "Paid validation stages require --pricing-manifest so spend caps can be enforced."
            )

    def _run_paid_canary(self) -> None:
        started = time.monotonic()
        spend_total = 0.0
        for phase in self.config.canary_phases:
            spend_total += self._run_paid_phase(
                phase=phase,
                run_id=f"{self.run_id}_canary",
                elapsed_started=started,
                max_minutes=self.config.canary_max_minutes,
                max_usd=self.config.canary_max_usd,
            )
            if spend_total > self.config.canary_max_usd:
                raise ValidationFailure(
                    f"Canary upper-bound spend exceeded cap: {spend_total:.2f} > {self.config.canary_max_usd:.2f}"
                )

        self._record_step(
            StepRecord(
                name="canary_budget_review",
                kind="budget",
                status="pass",
                detail=f"canary completed within caps (estimated_upper_bound_usd={spend_total:.2f})",
            )
        )

    def _run_paid_full(self) -> None:
        started = time.monotonic()
        spend_total = 0.0
        groups = (
            ("docs_governance", self.config.docs_governance_phases),
            ("code_qa", self.config.code_qa_phases),
            ("synthesis", self.config.synthesis_phases),
        )
        for group_name, phases in groups:
            for phase in phases:
                spend_total += self._run_paid_phase(
                    phase=phase,
                    run_id=f"{self.run_id}_full",
                    elapsed_started=started,
                    max_minutes=self.config.full_max_minutes,
                    max_usd=self.config.full_max_usd,
                )
            checkpoint = self._full_checkpoint(group_name, spend_total)
            self._record_step(checkpoint)
            if checkpoint.status != "pass":
                raise ValidationFailure(checkpoint.detail)

    def _run_paid_phase(
        self,
        *,
        phase: str,
        run_id: str,
        elapsed_started: float,
        max_minutes: float,
        max_usd: float,
    ) -> float:
        elapsed_minutes = (time.monotonic() - elapsed_started) / 60.0
        if elapsed_minutes > max_minutes:
            raise ValidationFailure(
                f"Time cap exceeded before phase {phase}: {elapsed_minutes:.2f} minutes > {max_minutes:.2f}"
            )
        promptset_root = str(self.config.promptset_root.resolve())
        execute = self._run_command(
            f"execute_phase_{phase}",
            self._dopemux_cli(
                "upgrades",
                "run",
                "--pipeline-version",
                "v5",
                "--phase",
                phase,
                "--run-id",
                run_id,
                "--execute",
                "--resume",
                "--routing-policy",
                self.config.routing_policy,
                "--jsonl-events",
                "--ui",
                "plain",
                "--promptset-root",
                promptset_root,
            ),
            timeout_seconds=max_minutes * 60.0,
        )
        self._record_step(execute)
        if execute.status != "pass":
            raise ValidationFailure(f"Paid phase {phase} execution failed.")

        verify = self._run_command(
            f"verify_paid_phase_{phase}",
            self._runner_cli(
                "--run-id",
                run_id,
                "--verify-phase-output",
                phase,
                "--promptset-root",
                promptset_root,
            ),
        )
        self._record_step(verify)
        if verify.status != "pass":
            raise ValidationFailure(f"Phase {phase} verification failed.")

        doctor = self._run_command(
            f"doctor_phase_{phase}",
            self._dopemux_cli(
                "upgrades",
                "doctor",
                "--pipeline-version",
                "v5",
                "--run-id",
                run_id,
            ),
        )
        self._record_step(doctor)
        if doctor.status != "pass":
            raise ValidationFailure(f"Doctor failed after phase {phase}.")

        usage = self._run_command(
            f"provider_usage_{phase}",
            self._runner_cli(
                "--run-id",
                run_id,
                "--show-provider-usage",
                "--phase",
                phase,
                "--promptset-root",
                promptset_root,
            ),
        )
        self._record_step(usage)
        usage_payload = _load_json(Path(usage.stdout_path)) if usage.stdout_path else {}
        spend = _estimate_upper_bound_spend(usage_payload, self.pricing_manifest)
        spend_path = self.report_dir / f"SPEND_ESTIMATE_{run_id}_{phase}.json"
        _write_json(spend_path, spend)
        if spend.get("missing_routes"):
            raise ValidationFailure(
                f"Spend cap cannot be enforced for phase {phase}; pricing manifest is missing routes: {', '.join(spend['missing_routes'])}"
            )
        estimated_upper_bound = float(spend.get("estimated_upper_bound_usd", 0.0))
        if estimated_upper_bound > max_usd:
            raise ValidationFailure(
                f"Phase {phase} exceeded stage spend cap upper bound: {estimated_upper_bound:.2f} > {max_usd:.2f}"
            )

        monitor = self._evaluate_phase_outputs(run_id, phase, max_usd=max_usd)
        self._record_step(monitor)
        if monitor.status != "pass":
            raise ValidationFailure(monitor.detail)
        return estimated_upper_bound

    def _evaluate_phase_outputs(self, run_id: str, phase: str, *, max_usd: float) -> StepRecord:
        run_root = self.repo_root / "extraction" / "repo-truth-extractor" / "v3" / "runs" / run_id
        telemetry_dir = run_root / "telemetry"
        events_path = run_root / "events.jsonl"
        dashboard = _load_json(telemetry_dir / "RUN_DASHBOARD.json")
        failure_index = _load_json(telemetry_dir / "FAILURE_INDEX.json")
        step_metrics = _load_json(telemetry_dir / "STEP_METRICS.json")
        coverage_rollup = _load_json(run_root / "COVERAGE_ROLLUP.json")

        soft_gate_breach = self._soft_gate_breach(events_path, phase)
        missing_artifacts = _phase_missing_required_artifacts(coverage_rollup, phase)
        failure_hist = (
            failure_index.get("global_failure_histogram")
            if isinstance(failure_index.get("global_failure_histogram"), dict)
            else {}
        )
        detail = {
            "phase": phase,
            "soft_gate_breach": soft_gate_breach,
            "missing_required_artifacts": missing_artifacts,
            "failure_histogram": failure_hist,
            "dashboard_summary": dashboard.get("summary", {}),
            "step_metrics_keys": sorted((step_metrics.get("steps") or {}).keys()) if isinstance(step_metrics.get("steps"), dict) else [],
            "coverage_status": ((coverage_rollup.get("phases") or {}).get(phase) or {}).get("status"),
        }
        detail_path = self.report_dir / f"PHASE_MONITOR_{run_id}_{phase}.json"
        _write_json(detail_path, detail)

        if soft_gate_breach is not None and soft_gate_breach > 0.2:
            return StepRecord(
                name=f"monitor_phase_{phase}",
                kind="monitor",
                status="fail",
                detail=f"soft-gate fail_rate exceeded threshold for phase {phase}: {soft_gate_breach:.4f}",
                artifacts={"detail_path": str(detail_path), "max_usd": max_usd},
            )
        if missing_artifacts:
            return StepRecord(
                name=f"monitor_phase_{phase}",
                kind="monitor",
                status="fail",
                detail=f"required artifacts missing for phase {phase}: {', '.join(missing_artifacts)}",
                artifacts={"detail_path": str(detail_path)},
            )
        return StepRecord(
            name=f"monitor_phase_{phase}",
            kind="monitor",
            status="pass",
            detail=f"phase {phase} telemetry and required artifacts are within policy",
            artifacts={"detail_path": str(detail_path)},
        )

    def _soft_gate_breach(self, events_path: Path, phase: str) -> Optional[float]:
        if not events_path.exists():
            return None
        max_fail_rate: Optional[float] = None
        for line in events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            if str(row.get("phase") or "").upper() != phase:
                continue
            if str(row.get("type") or "") != "soft_gate_triggered":
                continue
            try:
                fail_rate = float(row.get("fail_rate"))
            except Exception:
                continue
            if max_fail_rate is None or fail_rate > max_fail_rate:
                max_fail_rate = fail_rate
        return max_fail_rate

    def _full_checkpoint(self, group_name: str, spend_total: float) -> StepRecord:
        if spend_total <= (self.config.full_max_usd * 0.6):
            return StepRecord(
                name=f"checkpoint_{group_name}",
                kind="checkpoint",
                status="pass",
                detail=f"group {group_name} within spend progression threshold",
            )

        status_payload = self._latest_status_snapshot(f"{self.run_id}_full")
        summary = status_payload.get("summary", {}) if isinstance(status_payload, dict) else {}
        pass_count = int(summary.get("PASS", 0))
        fail_count = int(summary.get("FAIL", 0))
        in_progress = int(summary.get("IN_PROGRESS", 0))
        total_evaluated = max(1, pass_count + fail_count + in_progress)
        pass_ratio = float(pass_count) / float(total_evaluated)
        if pass_ratio < 0.5:
            return StepRecord(
                name=f"checkpoint_{group_name}",
                kind="checkpoint",
                status="fail",
                detail=(
                    f"cumulative spend crossed 60% of full budget before 50% PASS ratio "
                    f"(spend={spend_total:.2f}, pass_ratio={pass_ratio:.2%})"
                ),
            )
        return StepRecord(
            name=f"checkpoint_{group_name}",
            kind="checkpoint",
            status="pass",
            detail=f"group {group_name} passed checkpoint review",
        )

    def _latest_status_snapshot(self, run_id: str) -> Dict[str, Any]:
        record = self._run_command(
            f"status_{run_id}",
            self._dopemux_cli(
                "upgrades",
                "status",
                "--pipeline-version",
                "v5",
                "--run-id",
                run_id,
                "--json",
            ),
        )
        self._record_step(record)
        if not record.stdout_path:
            return {}
        return _load_json(Path(record.stdout_path))

    def _build_report_payload(self) -> Dict[str, Any]:
        elapsed = time.monotonic() - self.started_at
        status = "pass" if not self.blockers else "fail"
        return {
            "generated_at": now_iso(),
            "run_id": self.run_id,
            "stage": self.config.stage,
            "status": status,
            "elapsed_seconds": round(elapsed, 3),
            "repo_root": str(self.repo_root),
            "promptset_root": str(self.config.promptset_root.resolve()),
            "routing_policy": self.config.routing_policy,
            "blockers": self.blockers,
            "steps": [asdict(step) for step in self.steps],
        }

    def _render_markdown_report(self, payload: Dict[str, Any]) -> str:
        lines = [
            "# Repo Truth Extractor v5 Validation Report",
            "",
            f"- status: `{payload.get('status')}`",
            f"- run_id: `{payload.get('run_id')}`",
            f"- stage: `{payload.get('stage')}`",
            f"- routing_policy: `{payload.get('routing_policy')}`",
            f"- promptset_root: `{payload.get('promptset_root')}`",
            f"- elapsed_seconds: `{payload.get('elapsed_seconds')}`",
            "",
            "## Blockers",
        ]
        blockers = payload.get("blockers") or []
        if blockers:
            lines.extend(f"- {blocker}" for blocker in blockers)
        else:
            lines.append("- none")
        lines.extend(["", "## Steps"])
        for step in payload.get("steps", []):
            lines.append(
                f"- `{step.get('name')}` `{step.get('status')}` "
                f"(exit={step.get('exit_code')}, elapsed={step.get('elapsed_seconds')}) "
                f"{step.get('detail')}"
            )
        return "\n".join(lines) + "\n"


def run_live_validation(config: ValidationConfig) -> Dict[str, Any]:
    return LiveValidationRunner(config).run()
