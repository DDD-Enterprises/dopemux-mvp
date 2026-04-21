import datetime as dt
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, List, Dict
from .models import PrescanConfig

logger = logging.getLogger(__name__)

class RTEPrescanError(Exception):
    """Base error for prescan."""
    pass

class SecurityViolation(RTEPrescanError):
    """Raised when an online call is attempted without authorization."""
    pass

class RoutingExhausted(RTEPrescanError):
    """Represents route-ladder exhaustion when no candidate succeeds.

    Current grok routing may report exhaustion via execution evidence
    (`final_status="exhausted"`) instead of raising this exception.
    """
    pass

@dataclass
class ExecutionAttempt:
    provider: str
    model: str
    api_key_env: str
    status: str  # success|failed|skipped
    latency_ms: float = 0.0
    error: str | None = None
    limiter_wait_ms: float = 0.0
    tokens_prompt: int = 0
    tokens_completion: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class ExecutionEvidence:
    pass_id: str
    batch_id: str | None
    planned_candidates: list[dict]
    attempts: list[ExecutionAttempt] = field(default_factory=list)
    final_status: str = "pending"
    online_authorized: bool = False
    total_latency_ms: float = 0.0
    total_tokens: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["attempts"] = [a.to_dict() for a in self.attempts]
        return d

XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.20-beta-0309-non-reasoning"
MAX_PREVIEW_BYTES = 6144
MAX_PREVIEW_LINES = 150

PASS_IDS = ("dedup", "discover", "feasibility", "optimize")

PASS_DESCRIPTIONS = {
    "dedup": "Near-duplicate detection + version chain compression summaries",
    "discover": "Hidden feature archaeology, drift signals, ghost assessment",
    "feasibility": "Planned feature GSP feasibility analysis",
    "optimize": "Extraction routing, cost, and compression plan",
}

_DEDUP_SYSTEM_PROMPT = "You are a deduplication analyst."
_DISCOVER_SYSTEM_PROMPT = "You are a technical archaeology analyst."
_FEASIBILITY_SYSTEM_PROMPT = "You are a software feasibility analyst."
_OPTIMIZE_SYSTEM_PROMPT = "You are an extraction cost optimizer."

PASS_SYSTEM_PROMPTS = {
    "dedup": _DEDUP_SYSTEM_PROMPT,
    "discover": _DISCOVER_SYSTEM_PROMPT,
    "feasibility": _FEASIBILITY_SYSTEM_PROMPT,
    "optimize": _OPTIMIZE_SYSTEM_PROMPT,
}

class BatchResponseValidator:
    _EXPECTED_TYPES: Dict[str, Dict[str, type]] = {
        "dedup": {
            "duplicate_assessments": list,
            "version_chain_summaries": list,
            "divergent_pairs": list,
        },
        "discover": {
            "hidden_features": list,
            "drift_signals": list,
            "ghost_assessments": list,
            "rediscovery_candidates": list,
        },
        "feasibility": {
            "planned_features": list,
            "implementation_blockers": list,
        },
        "optimize": {
            "skip_list": list,
            "compress_chains": list,
            "phase_routing_overrides": list,
            "model_routing_hints": list,
            "estimated_savings": dict,
        },
    }

    def validate(self, pass_id: str, response: str) -> tuple[bool, dict | None, str]:
        try:
            data = json.loads(response)
        except Exception:
            return False, None, "Invalid JSON"
        if not isinstance(data, dict):
            return False, None, "Response must be a JSON object"
        if pass_id == "discover":
            hidden_features = data.get("hidden_features")
            if hidden_features is not None and not isinstance(hidden_features, list):
                return False, None, "hidden_features must be a list"
            for index, item in enumerate(hidden_features or []):
                required_fields = {"path", "feature_name", "confidence", "extraction_phase"}
                if not isinstance(item, dict) or not required_fields.issubset(item):
                    return False, None, f"hidden_features[{index}] missing required fields"
        elif pass_id == "optimize":
            skip_list = data.get("skip_list")
            if skip_list is not None and not isinstance(skip_list, list):
                return False, None, "skip_list must be a list"
        expected = self._EXPECTED_TYPES.get(pass_id, {})
        for key, expected_type in expected.items():
            if key not in data:
                return False, None, f"Missing required key: {key}"
            if not isinstance(data[key], expected_type):
                return False, None, f"Invalid type for {key}: expected {expected_type.__name__}"
        return True, data, ""

class GrokPassRunner:
    def __init__(self, config: PrescanConfig, limiter: Any | None = None):
        self.config = config
        self.limiter = limiter
        self._validator = BatchResponseValidator()
        self.evidence_log: list[ExecutionEvidence] = []

    def run_passes_batched(
        self,
        passes: list[str],
        intelligence: dict,
        manifest: list[dict],
        batch_plans: dict,
        routing_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        all_results: dict[str, Any] = {}
        output_dir = self.config.output_dir

        if not self.config.allow_online_llm:
            logger.warning("🚫 Online prescan passes (batched) NOT authorized.")
            return {}

        for pass_id in passes:
            if pass_id not in PASS_IDS: continue
            plan = batch_plans.get(pass_id)
            if not plan or not plan.batches: continue

            for i, batch in enumerate(plan.batches):
                payload = self._build_batch_payload(pass_id, intelligence, manifest, batch.file_paths)
                evidence = ExecutionEvidence(
                    pass_id=pass_id,
                    batch_id=batch.batch_id,
                    planned_candidates=(routing_plan or {}).get("candidate_routes", {}).get(pass_id, []),
                    online_authorized=self.config.allow_online_llm
                )
                result = self._call_grok_validated(pass_id, payload, routing_plan, evidence, est_tokens=batch.estimated_tokens)
                self.evidence_log.append(evidence)
                if result: all_results[f"{pass_id}_{i}"] = result

        self.save_attempts()
        return all_results

    def _call_grok_validated(
        self, 
        pass_id: str, 
        payload: str, 
        routing_plan: dict | None, 
        evidence: ExecutionEvidence,
        est_tokens: int = 0,
        max_candidate_retries: int = 1
    ) -> dict | None:
        candidate_routes = (routing_plan or {}).get("candidate_routes")
        if isinstance(candidate_routes, dict) and pass_id in candidate_routes:
            candidates = candidate_routes.get(pass_id) or []
            if not candidates:
                evidence.final_status = "exhausted"
                return None
        else:
            candidates = [{"provider": self.config.provider, "model_id": self.config.model, "api_key_env": self.config.api_key_env}]

        for candidate in candidates:
            for attempt in range(max_candidate_retries + 1):
                attempt_record = ExecutionAttempt(
                    provider=candidate["provider"],
                    model=candidate["model_id"],
                    api_key_env=candidate["api_key_env"],
                    status="pending"
                )
                evidence.attempts.append(attempt_record)
                try:
                    result = self._call_grok(pass_id, payload, candidate, attempt_record, est_tokens)
                    if result:
                        evidence.final_status = "success"
                        return result
                except SecurityViolation:
                    evidence.final_status = "unauthorized"
                    return None
                except Exception as e:
                    attempt_record.status = "failed"
                    attempt_record.error = str(e)
                if attempt < max_candidate_retries:
                    time.sleep(1)
        evidence.final_status = "exhausted"
        return None

    def run_passes(self, passes, intel, manifest, routing_plan=None):
        if not self.config.allow_online_llm:
            return {}

        results: dict[str, Any] = {}
        for pass_id in passes or []:
            if pass_id not in PASS_IDS:
                continue
            payload = self._build_batch_payload(pass_id, intel or {}, manifest or [], [])
            evidence = ExecutionEvidence(
                pass_id=pass_id,
                batch_id=None,
                planned_candidates=(routing_plan or {}).get("candidate_routes", {}).get(pass_id, []),
                online_authorized=self.config.allow_online_llm,
            )
            result = self._call_grok_validated(pass_id, payload, routing_plan, evidence)
            self.evidence_log.append(evidence)
            if result:
                results[pass_id] = result

        self.save_attempts()
        return results

    def _call_grok(self, pass_id, payload, candidate, attempt_record, est_tokens=0):
        provider = candidate["provider"]
        model_id = candidate["model_id"]
        if provider == "mock":
            if self.limiter:
                attempt_record.limiter_wait_ms = self.limiter.acquire(est_tokens) * 1000
            attempt_record.status = "success"
            return {"status": "ok", "pass_id": pass_id}

        if not self.config.allow_online_llm and provider != "mock":
             raise SecurityViolation("Spend gate blocked call")
        api_key = os.environ.get(candidate["api_key_env"])
        if not api_key:
            raise ValueError(f"API key not found: {candidate['api_key_env']}")

        if self.limiter:
            attempt_record.limiter_wait_ms = self.limiter.acquire(est_tokens) * 1000

        try:
            import openai
        except ImportError as exc:
            raise RuntimeError("openai not installed") from exc

        base_url = XAI_BASE_URL if provider == "xai" else None
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": PASS_SYSTEM_PROMPTS[pass_id]},
                {"role": "user", "content": payload},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        valid, data, err = self._validator.validate(pass_id, content)
        if not valid:
            raise ValueError(f"Validation failed: {err}")

        if response.usage:
            attempt_record.tokens_prompt = response.usage.prompt_tokens
            attempt_record.tokens_completion = response.usage.completion_tokens

        attempt_record.status = "success"
        return data

    def _build_batch_payload(
        self,
        pass_id: str,
        intelligence: dict[str, Any],
        manifest: list[dict[str, Any]],
        file_paths: list[str],
    ) -> str:
        selected_paths = set(file_paths)
        selected_manifest = [
            item for item in manifest
            if isinstance(item, dict)
            and item.get("rel_path")
            and (not selected_paths or item.get("rel_path") in selected_paths)
        ]
        payload = {
            "pass_id": pass_id,
            "description": PASS_DESCRIPTIONS.get(pass_id, ""),
            "batch_file_paths": file_paths,
            "manifest_entries": selected_manifest,
            "corpus_summary": intelligence.get("corpus_summary", {}),
            "duplicate_groups": intelligence.get("duplicate_groups", {}),
            "version_chains": intelligence.get("version_chains", {}),
            "planned_features": intelligence.get("planned_features", {}),
            "ghost_files": intelligence.get("ghost_files", []),
            "extraction_hints": intelligence.get("extraction_hints", {}),
        }
        return json.dumps(payload, sort_keys=True)

    def save_attempts(self) -> Path:
        path = self.config.output_dir / "prescan_llm_attempts.json"
        payload = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "evidence": [e.to_dict() for e in self.evidence_log],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path
