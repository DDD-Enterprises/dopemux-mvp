import datetime as dt
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, List, Dict
from .models import PrescanConfig
from .token_counter import estimate_tokens
from output_safety import (
    sanitize_payload_for_provider,
    sanitize_text_for_provider_payload,
)

logger = logging.getLogger(__name__)
CACHE_KEY_HMAC_KEY = b"dopemux-rte-prescan-cache-v1"

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

_DEDUP_SYSTEM_PROMPT = """You are a Technical Redundancy Analyst.
Your goal is to analyze provided duplicate groups and version chains to definitively classify redundancy in the codebase.

DIRECTIVES:
1. Differentiate between exact duplicates (identical content hashes) and divergent forks (similar filenames or structure but different content).
2. For version chains (e.g., v1, v2, old), analyze the 'evolution_narrative' by comparing the latest file with its predecessors.
3. Explicitly emit 'superseded_paths' for files that add zero unique information to the extraction target.

OUTPUT CONSTRAINT:
You MUST emit valid JSON strictly conforming to the provided schema.
Include 'confidence' (0.0 to 1.0) and 'reasoning' for every assessment.
"""

_DISCOVER_SYSTEM_PROMPT = """You are a Codebase Archaeology Expert.
Your goal is to identify undocumented capabilities, architectural drift, and valuable 'ghost' files (deleted or archived logic).

DIRECTIVES:
1. Map discovered features to the appropriate extraction phase (A: Control Plane, H: Home, D: Docs, C: Code, E: Logic, W: Webhooks, B: Batch, G: Governance, Q: Quality, R: Arbitration).
2. Compare declared intentions (from READMEs) against actual API surfaces to detect 'drift_signals'.
3. Assess 'ghost_files' to determine if their logic is 'worth_restoring' based on current project goals.

OUTPUT CONSTRAINT:
You MUST emit valid JSON strictly conforming to the provided schema.
Include 'confidence' (0.0 to 1.0) for hidden features.
"""

_FEASIBILITY_SYSTEM_PROMPT = """You are an Implementation Risk Assessor.
Your goal is to evaluate the structural feasibility of planned features against the current codebase architecture.

DIRECTIVES:
1. Assign a 'foundation_score' (0.0 to 1.0) indicating architectural readiness.
2. Identify concrete 'implementation_blockers' (missing deps, conflicting surfaces).
3. Flag 'quick_win' opportunities where the foundation for a planned feature is already robustly present.

OUTPUT CONSTRAINT:
You MUST emit valid JSON strictly conforming to the provided schema.
Include detailed 'reasoning' for foundation scores.
"""

_OPTIMIZE_SYSTEM_PROMPT = """You are an Extraction Token Economics Optimizer.
Your goal is to synthesize prior intelligence into a rigid execution and routing plan to minimize token spend while maximizing truth extraction.

DIRECTIVES:
1. Populate 'skip_list' strictly from confirmed superseded paths and non-restorable ghost files.
2. Generate 'compress_chains' rules for files that should only receive summary hints.
3. Apply 'model_routing_hints': Route high-complexity or high-PageRank paths to premium models; route boilerplate to economy models.
4. Apply 'phase_routing_overrides' for features discovered in unexpected locations.

OUTPUT CONSTRAINT:
You MUST emit valid JSON strictly conforming to the provided schema.
Estimate 'estimated_savings' in terms of files skipped and compressed.
"""

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
        self._cache_dir = self.config.output_dir / ".cache" / "grok_passes"

    def _get_file_preview(self, entry: Any) -> str:
        """Read and truncate file content for LLM preview."""
        path = self.config.repo_root / entry.rel_path
        try:
            # Read only what we need to avoid memory pressure
            with open(path, "rb") as f:
                raw = f.read(MAX_PREVIEW_BYTES)
            text = raw.decode("utf-8", errors="replace")
            lines = text.splitlines()
            if len(lines) > MAX_PREVIEW_LINES:
                text = "\n".join(lines[:MAX_PREVIEW_LINES]) + "\n...[TRUNCATED]"
            return sanitize_text_for_provider_payload(text)
        except Exception as e:
            return sanitize_text_for_provider_payload(f"[Error reading file: {e}]")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens for a given text."""
        return estimate_tokens(text)

    def _cache_digest_default(self, value: Any) -> Any:
        """Return a deterministic JSON-serializable representation for cache keys."""
        if isinstance(value, Path):
            return str(value)
        if hasattr(value, "__dict__"):
            return vars(value)
        return repr(value)

    def _get_cache_path(self, pass_id: str, payload: dict) -> Path:
        """Generate a stable cache path for a pass and its payload."""
        digest_input = {
            "pass_id": pass_id,
            "payload": payload,
        }
        encoded = json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            default=self._cache_digest_default,
        ).encode("utf-8")
        digest = hmac.new(CACHE_KEY_HMAC_KEY, encoded, hashlib.sha256).hexdigest()
        return self._cache_dir / f"{pass_id}_{digest[:16]}.json"

    def _load_cached_pass(self, pass_id: str, payload: dict) -> dict | None:
        """Load pass results from cache if valid."""
        path = self._get_cache_path(pass_id, payload)
        if path.exists():
            try:
                logger.info(f"💾 Loading cached results for pass '{pass_id}'")
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load cache at {path}: {e}")
        return None

    def _save_cached_pass(self, pass_id: str, payload: dict, result: dict) -> None:
        """Save pass results to cache."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            path = self._get_cache_path(pass_id, payload)
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save cache for {pass_id}: {e}")

    def _sanitize_provider_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        sanitized = sanitize_payload_for_provider(payload)
        if isinstance(sanitized, dict):
            return sanitized
        return {"payload": sanitized}

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
        if not self._online_authorized():
            logger.warning("🚫 Online prescan passes (batched) NOT authorized.")
            return {}

        routing_plan = self._normalize_routing_plan(routing_plan)

        for pass_id in passes:
            if pass_id not in PASS_IDS:
                continue
            plan = batch_plans.get(pass_id)
            if not plan or not plan.batches:
                continue

            for i, batch in enumerate(plan.batches):
                result = self._execute_pass(
                    pass_id, 
                    intelligence, 
                    all_results, 
                    routing_plan, 
                    batch_info=batch
                )
                if result:
                    all_results[f"{pass_id}_{i}"] = result

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
            for attempt_index in range(max_candidate_retries + 1):
                attempt_record = ExecutionAttempt(
                    provider=str(candidate["provider"]),
                    model_id=str(candidate["model_id"]),
                    api_key_env=str(candidate["api_key_env"]),
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
                if attempt_index < max_candidate_retries:
                    time.sleep(1)
        evidence.final_status = "exhausted"
        return None

    def _execute_pass(
        self,
        pass_id: str,
        intelligence: dict[str, Any],
        prior_pass_results: dict[str, Any],
        routing_plan: dict[str, Any] | None = None,
        batch_info: Any | None = None
    ) -> dict | None:
        """Execute a single grok pass with caching and validation."""
        # 1. Build provider-bound payload
        payload_data = self._build_provider_payload(
            pass_id, intelligence, prior_pass_results
        )
        if payload_data is None:
            return None

        # 2. Check Cache
        cached = self._load_cached_pass(pass_id, payload_data)
        if cached:
            return cached

        # 3. Call LLM
        payload_str = json.dumps(payload_data, indent=2)
        evidence = ExecutionEvidence(
            pass_id=pass_id,
            batch_id=batch_info.batch_id if batch_info else None,
            planned_candidates=(routing_plan or {}).get("candidate_routes", {}).get(pass_id, []),
            online_authorized=self._online_authorized(),
        )
        
        est_tokens = batch_info.estimated_tokens if batch_info else self._estimate_tokens(payload_str)
        
        result = self._call_grok_validated(
            pass_id,
            payload_str,
            routing_plan,
            evidence,
            est_tokens=est_tokens
        )
        self.evidence_log.append(evidence)

        # 4. Save to Cache if successful
        if result:
            self._save_cached_pass(pass_id, payload_data, result)

        return result

    def _build_provider_payload(
        self,
        pass_id: str,
        intelligence: dict[str, Any],
        prior_pass_results: dict[str, Any],
    ) -> dict[str, Any] | None:
        if pass_id == "dedup":
            payload_data = self._build_dedup_payload(intelligence)
        elif pass_id == "discover":
            payload_data = self._build_discover_payload(intelligence)
        elif pass_id == "feasibility":
            payload_data = self._build_feasibility_payload(intelligence)
        elif pass_id == "optimize":
            payload_data = self._build_optimize_payload(intelligence, prior_pass_results)
        else:
            return None
        return self._sanitize_provider_payload(payload_data)

    def run_passes(self, passes, intel, manifest, routing_plan=None):
        if not self._online_authorized():
            return {}

        routing_plan = self._normalize_routing_plan(routing_plan)
        results: dict[str, Any] = {}
        for pass_id in passes:
            if pass_id not in PASS_IDS:
                continue
            
            result = self._execute_pass(pass_id, intel, results, routing_plan)
            if result is not None:
                results[pass_id] = result
                
        self.save_attempts()
        return results

    def _build_dedup_payload(self, intelligence: dict[str, Any]) -> dict[str, Any]:
        """Build payload for deduplication analysis."""
        return {
            "duplicate_groups": intelligence.get("duplicate_groups", {}),
            "version_chains": intelligence.get("version_chains", {}),
            "corpus_summary": intelligence.get("corpus_summary", {}),
        }

    def _build_discover_payload(self, intelligence: dict[str, Any]) -> dict[str, Any]:
        """Build payload for feature discovery and archaeology."""
        # Include symbols and ghost files if available
        return {
            "corpus_summary": intelligence.get("corpus_summary", {}),
            "symbols_summary": {
                path: {
                    "top_level_symbols": [s["name"] for s in entry.get("symbols", [])[:10]],
                    "complexity": entry.get("complexity_score"),
                }
                for path, entry in intelligence.get("code_intelligence", {}).items()
            },
            "ghost_files": intelligence.get("ghost_files", []),
        }

    def _build_feasibility_payload(self, intelligence: dict[str, Any]) -> dict[str, Any]:
        """Build payload for planned feature feasibility."""
        return {
            "planned_features": intelligence.get("extraction_hints", {}).get("planned_features", []),
            "api_surfaces": {
                path: entry.get("api_surfaces", [])
                for path, entry in intelligence.get("code_intelligence", {}).items()
                if entry.get("api_surfaces")
            },
            "dependency_clusters": intelligence.get("code_intelligence", {}).get("dependency_clusters", []),
        }

    def _build_optimize_payload(self, intelligence: dict[str, Any], prior_pass_results: dict[str, Any]) -> dict[str, Any]:
        """Build payload for final extraction optimization synthesis."""
        payload: dict[str, Any] = {
            "corpus_summary": dict(intelligence.get("corpus_summary") or {}),
            "cost_estimate": dict(intelligence.get("cost_estimate") or {}),
            "dedup_results": prior_pass_results.get("dedup", {}),
            "discovery_results": prior_pass_results.get("discover", {}),
            "feasibility_results": prior_pass_results.get("feasibility", {}),
            "pagerank_hotspots": [
                {"path": h.get("rel_path"), "score": h.get("hotspot_score")}
                for h in intelligence.get("code_intelligence", {}).get("hotspots", [])[:20]
            ]
        }
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
