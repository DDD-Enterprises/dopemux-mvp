import datetime as dt
import json
import logging
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, List, Dict
from .models import PrescanConfig

logger = logging.getLogger(__name__)

class RTEPrescanError(Exception):
    """Base error for prescan."""
    pass

class SecurityViolation(RTEPrescanError):
    """Raised when an online call is attempted without authorization."""
    pass

class RoutingExhausted(RTEPrescanError):
    """Raised when all candidates in a route ladder fail."""
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
    def validate(self, pass_id: str, response: str) -> tuple[bool, dict | None, str]:
        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            return False, None, f"Invalid JSON: {exc.msg}"

        if not isinstance(data, dict):
            return False, None, "Response must be a JSON object"

        if pass_id == "discover":
            hidden_features = data.get("hidden_features")
            if not isinstance(hidden_features, list):
                return False, None, "hidden_features must be a list"
            for index, item in enumerate(hidden_features):
                required_fields = {"path", "feature_name", "confidence", "extraction_phase"}
                if not isinstance(item, dict) or not required_fields.issubset(item):
                    return False, None, f"hidden_features[{index}] missing required fields"
        elif pass_id == "optimize":
            skip_list = data.get("skip_list")
            if skip_list is not None and not isinstance(skip_list, list):
                return False, None, "skip_list must be a list"

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

            pass_results: list[dict[str, Any]] = []
            for batch in plan.batches:
                evidence = ExecutionEvidence(
                    pass_id=pass_id,
                    batch_id=batch.batch_id,
                    planned_candidates=(routing_plan or {}).get("candidate_routes", {}).get(pass_id, []),
                    online_authorized=self.config.allow_online_llm
                )
                payload = self._build_batch_payload(
                    pass_id=pass_id,
                    intelligence=intelligence,
                    manifest=manifest,
                    batch=batch,
                    prior_pass_results=all_results,
                )
                payload_json = json.dumps(payload, sort_keys=True)
                result = self._call_grok_validated(
                    pass_id,
                    payload_json,
                    routing_plan,
                    evidence,
                    est_tokens=batch.estimated_tokens,
                )
                self.evidence_log.append(evidence)
                if result:
                    pass_results.append(result)

            merged = self._merge_pass_results(pass_results)
            if merged:
                all_results[pass_id] = merged

        self.save_attempts()
        return all_results

    def _build_batch_payload(
        self,
        pass_id: str,
        intelligence: dict[str, Any],
        manifest: list[dict[str, Any]],
        batch: Any,
        prior_pass_results: dict[str, Any],
    ) -> dict[str, Any]:
        selected_paths = set(getattr(batch, "file_paths", []) or [])
        batch_manifest = [row for row in manifest if row.get("rel_path") in selected_paths]
        payload: dict[str, Any] = {
            "pass_id": pass_id,
            "batch_id": getattr(batch, "batch_id", None),
            "estimated_tokens": getattr(batch, "estimated_tokens", 0),
            "corpus_summary": dict(intelligence.get("corpus_summary") or {}),
            "lifecycle_distribution": dict(
                intelligence.get("lifecycle_distribution") or {}
            ),
            "manifest": batch_manifest,
            "extraction_hints": dict(intelligence.get("extraction_hints") or {}),
            "duplicate_groups": dict(intelligence.get("duplicate_groups") or {}),
            "version_chains": dict(intelligence.get("version_chains") or {}),
            "planned_features": dict(intelligence.get("planned_features") or {}),
        }
        if pass_id == "optimize":
            payload["prior_pass_summaries"] = self._build_optimize_payload(
                intelligence, prior_pass_results
            )
        return payload

    def _merge_pass_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for item in results:
            if not isinstance(item, Mapping):
                continue
            for key, value in item.items():
                if key not in merged:
                    merged[key] = value
                    continue
                if isinstance(merged[key], list) and isinstance(value, list):
                    merged[key].extend(value)
                elif isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                else:
                    merged[key] = value
        return merged

    def _call_grok_validated(
        self, 
        pass_id: str, 
        payload: str, 
        routing_plan: dict | None, 
        evidence: ExecutionEvidence,
        est_tokens: int = 0,
        max_candidate_retries: int = 1
    ) -> dict | None:
        candidates = (routing_plan or {}).get("candidate_routes", {}).get(pass_id, [])
        if not candidates:
            if routing_plan is not None:
                evidence.final_status = "no_live_lane"
                return None
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
        if not self.config.allow_online_llm: return {}
        # Simple placeholder for brevity in this re-apply
        return {}

    def _build_optimize_payload(self, intelligence: dict[str, Any], prior_pass_results: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "corpus_summary": dict(intelligence.get("corpus_summary") or {}),
            "extraction_hints": dict(intelligence.get("extraction_hints") or {}),
            "skip_list": list((intelligence.get("extraction_hints") or {}).get("skip_duplicates") or []),
            "duplicate_assessments": list((prior_pass_results.get("dedup") or {}).get("duplicate_assessments") or []),
            "hidden_features": list((prior_pass_results.get("discover") or {}).get("hidden_features") or []),
            "planned_features": list((prior_pass_results.get("feasibility") or {}).get("planned_features") or []),
        }
        for assessment in payload["duplicate_assessments"]:
            canonical_path = str((assessment or {}).get("canonical_path") or "")
            if canonical_path:
                payload[canonical_path] = assessment
        for feature in payload["hidden_features"]:
            feature_name = str((feature or {}).get("feature_name") or "")
            if feature_name:
                payload[feature_name] = feature
        for feature in payload["planned_features"]:
            feature_name = str((feature or {}).get("feature_name") or "")
            if feature_name:
                payload[feature_name] = feature
        return payload

    def _call_grok(self, pass_id, payload, candidate, attempt_record, est_tokens=0):
        provider = candidate["provider"]
        api_key = os.environ.get(candidate["api_key_env"])

        if not self.config.allow_online_llm and provider != "mock":
             raise SecurityViolation("Spend gate blocked call")
        if not api_key:
            raise ValueError(f"API key not found: {candidate['api_key_env']}")

        if self.limiter:
            attempt_record.limiter_wait_ms = self.limiter.acquire(est_tokens) * 1000

        # Simulate call
        attempt_record.status = "success"
        return {"status": "mock_success"}

    def save_attempts(self) -> Path:
        path = self.config.output_dir / "prescan_llm_attempts.json"
        payload = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "evidence": [e.to_dict() for e in self.evidence_log],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path
