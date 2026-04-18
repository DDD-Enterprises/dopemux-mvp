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
    """Raised when all candidates in a route ladder fail."""
    pass

@dataclass(init=False)
class ExecutionAttempt:
    provider: str
    model_id: str
    api_key_env: str
    status: str  # success|failed|skipped
    latency_ms: float = 0.0
    error: str | None = None
    limiter_wait_ms: float = 0.0
    tokens_prompt: int = 0
    tokens_completion: int = 0

    def __init__(
        self,
        provider: str,
        model_id: str | None = None,
        api_key_env: str = "",
        status: str = "pending",
        latency_ms: float = 0.0,
        error: str | None = None,
        limiter_wait_ms: float = 0.0,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        *,
        model: str | None = None,
    ) -> None:
        resolved_model_id = model_id if model_id is not None else model
        if resolved_model_id is None:
            raise TypeError("ExecutionAttempt requires model_id")
        self.provider = provider
        self.model_id = resolved_model_id
        self.api_key_env = api_key_env
        self.status = status
        self.latency_ms = latency_ms
        self.error = error
        self.limiter_wait_ms = limiter_wait_ms
        self.tokens_prompt = tokens_prompt
        self.tokens_completion = tokens_completion

    @property
    def model(self) -> str:
        return self.model_id

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

    def _online_authorized(self) -> bool:
        override = getattr(self.config, "online_authorized", None)
        if override is not None:
            return bool(override)
        return bool(self.config.allow_online_llm)

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

        if not self._online_authorized():
            logger.warning("🚫 Online prescan passes (batched) NOT authorized.")
            return {}

        for pass_id in passes:
            if pass_id not in PASS_IDS: continue
            plan = batch_plans.get(pass_id)
            if not plan or not plan.batches: continue

            for i, batch in enumerate(plan.batches):
                evidence = ExecutionEvidence(
                    pass_id=pass_id,
                    batch_id=batch.batch_id,
                    planned_candidates=(routing_plan or {}).get("candidate_routes", {}).get(pass_id, []),
                    online_authorized=self._online_authorized()
                )
                result = self._call_grok_validated(pass_id, "payload", routing_plan, evidence, est_tokens=batch.estimated_tokens)
                self.evidence_log.append(evidence)
                if result: all_results[f"{pass_id}_{i}"] = result

        self.save_attempts()
        return all_results

    def _normalize_routing_plan(self, routing_plan: dict[str, Any] | None) -> dict[str, Any] | None:
        if routing_plan is None:
            return None
        if "candidate_routes" in routing_plan:
            return routing_plan
        selected_routes = routing_plan.get("selected_routes")
        if not isinstance(selected_routes, dict):
            return routing_plan
        candidate_routes: dict[str, list[dict[str, Any]]] = {}
        for pass_id, route in selected_routes.items():
            if isinstance(route, list):
                candidate_routes[pass_id] = [item for item in route if isinstance(item, dict)]
            elif isinstance(route, dict):
                candidate_routes[pass_id] = [route]
        return {
            **routing_plan,
            "candidate_routes": candidate_routes,
        }

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
                    model_id=candidate["model_id"],
                    api_key_env=candidate["api_key_env"],
                    status="pending"
                )
                evidence.attempts.append(attempt_record)
                try:
                    if est_tokens:
                        result = self._call_grok(pass_id, payload, candidate, attempt_record, est_tokens)
                    else:
                        result = self._call_grok(pass_id, payload, candidate, attempt_record)
                    if result is not None:
                        attempt_record.status = "success"
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
        if not self._online_authorized():
            return {}

        routing_plan = self._normalize_routing_plan(routing_plan)
        results: dict[str, Any] = {}
        for pass_id in passes:
            if pass_id not in PASS_IDS:
                continue
            evidence = ExecutionEvidence(
                pass_id=pass_id,
                batch_id=None,
                planned_candidates=(routing_plan or {}).get("candidate_routes", {}).get(pass_id, []),
                online_authorized=self._online_authorized(),
            )
            result = self._call_grok_validated(
                pass_id,
                "payload",
                routing_plan,
                evidence,
            )
            self.evidence_log.append(evidence)
            if result is not None:
                results[pass_id] = result
        self.save_attempts()
        return results

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
        model_id = candidate["model_id"]
        api_key = os.environ.get(candidate["api_key_env"])
        transport = str(candidate.get("execution_transport") or "openai_sdk")

        if not self._online_authorized() and provider != "mock":
             raise SecurityViolation("Spend gate blocked call")
        if transport != "openai_sdk":
            raise ValueError(f"Unsupported prescan route transport: {transport}")
        if not api_key:
            raise ValueError("API key not found for selected route")

        if self.limiter:
            attempt_record.limiter_wait_ms = self.limiter.acquire(est_tokens) * 1000

        import openai

        base_url = None
        if provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
        elif provider not in {"openai", "mock"}:
            base_url = self.config.xai_base_url

        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "user",
                    "content": payload,
                }
            ],
            temperature=self.config.temperature,
        )
        content = getattr(response.choices[0].message, "content", "") or "{}"
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("LLM response must decode to a JSON object")

        usage = getattr(response, "usage", None)
        if usage is not None:
            attempt_record.tokens_prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
            attempt_record.tokens_completion = int(getattr(usage, "completion_tokens", 0) or 0)
        attempt_record.status = "success"
        return data

    def save_attempts(self) -> Path:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.config.output_dir / "prescan_llm_attempts.json"
        flattened_attempts: list[dict[str, Any]] = []
        success_count = 0
        for evidence in self.evidence_log:
            for attempt in evidence.attempts:
                success = attempt.status == "success"
                if success:
                    success_count += 1
                flattened_attempts.append(
                    {
                        "pass_id": evidence.pass_id,
                        "batch_id": evidence.batch_id,
                        "provider": attempt.provider,
                        "model_id": attempt.model_id,
                        "api_key_env": attempt.api_key_env,
                        "status": attempt.status,
                        "success": success,
                        "latency_ms": attempt.latency_ms,
                        "error": attempt.error,
                        "limiter_wait_ms": attempt.limiter_wait_ms,
                        "tokens_prompt": attempt.tokens_prompt,
                        "tokens_completion": attempt.tokens_completion,
                    }
                )
        payload = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "total_attempts": len(flattened_attempts),
            "success_count": success_count,
            "attempts": flattened_attempts,
            "evidence": [e.to_dict() for e in self.evidence_log],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path
