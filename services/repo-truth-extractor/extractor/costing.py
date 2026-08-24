from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import yaml

from extractor._spend_tracker_registry import get_registry

logger = logging.getLogger(__name__)

# extractor/costing.py is THE single pricing authority (TP-RTE-TRUTH-R2-001,
# fixing F-10/F-11). Every dollar figure this service prints or enforces —
# preview, preventive cap check, and post-response accounting — is priced
# from config/pricing.yaml through load_pricing_registry()/resolve_model_rate()
# below. This module deliberately does NOT import from lib.spend_ledger;
# lib/spend_ledger.py imports FROM here instead, so there is exactly one
# direction of dependency and exactly one place a catalog-load failure could
# be silently swallowed — and it isn't: load_pricing_registry() always raises
# on failure (missing file, bad YAML, missing/invalid rows). No caller of the
# pricing authority may catch that and substitute a baseline/guessed rate.
PRICING_VERSION = "baseline_v1"
UNKNOWN_MODEL_POLICY = "baseline_v1_fallback"

# Legacy constants retained ONLY for a peripheral, non-authoritative retry-cost
# hotspot reporting helper in run_extraction_v5.py (_pricing_preview_record)
# that is exercised only when no SpendLedger instance exists at all (never
# true in a normal run — the ledger is constructed unconditionally at
# startup, before Stage 0 even runs). They MUST NOT be used anywhere in the
# pricing authority below (load_pricing_registry / resolve_model_rate /
# compute_optimized_cost / estimate_usage_cost_usd).
BASELINE_INPUT_COST_PER_1M_USD = 0.15
BASELINE_OUTPUT_COST_PER_1M_USD = 0.60


# ---------------------------------------------------------------------------
# Shared token estimation (TP-RTE-TRUTH-R2-002, F-12).
#
# Before this fix the service computed "how many tokens is this text" three
# incompatible ways: lib/prescan/cost_estimator.py hardcoded chars/3.5;
# run_extraction_v5.py's runtime/preview fallback hardcoded chars//4 (a ~14%
# disagreement on the SAME corpus before any model even runs); and
# lib/prescan/token_counter.py (a separate, batch-planning-only concern) uses
# tiktoken cl100k_base with its own chars/3.5 fallback. None printed which
# method produced the number (A2 §1.3).
#
# estimate_tokens() below is the ONE function this packet's allowlisted
# caller (lib/prescan/cost_estimator.py) uses for its dollar estimate. It
# tries a real tokenizer (tiktoken o200k_base -- the current
# OpenAI/OpenRouter-OpenAI-compatible encoding) when both the library is
# importable AND the route is OpenAI-family; every other route (Gemini, xAI,
# unknown) falls back to a chars/4 heuristic, explicitly labeled so a caller
# can never mistake a heuristic estimate for a measured one.
#
# Scope note: this does NOT change run_extraction_v5.py's separate runtime
# tokenizer/output-ratio functions (_estimate_text_tokens /
# _project_output_tokens / _project_preview_output_tokens in
# run_extraction_v5.py, cited in the task packet as v5:11066,11071,11083) or
# lib/prescan/token_counter.py's batch-planning estimator. Neither file is in
# this packet's commit allowlist (services/repo-truth-extractor/extractor/
# costing.py, lib/prescan/cost_estimator.py, tests/ only); consolidating them
# onto this function is flagged as an OUT-OF-BOUNDARY finding for a follow-up
# packet rather than done here.
# ---------------------------------------------------------------------------

HEURISTIC_CHARS_PER_TOKEN = 4.0
_TIKTOKEN_ENCODING_NAME = "o200k_base"
_TIKTOKEN_ENCODING: Any = None
_TIKTOKEN_LOAD_ATTEMPTED = False


def _get_tiktoken_encoding() -> Any:
    """Lazily import + cache a tiktoken encoding. Never raises: any failure
    (library not installed, encoding fetch failure) is logged at debug level
    and this returns None so callers always have a working heuristic
    fallback. tiktoken is an optional, not a declared/pinned, dependency of
    this service -- exactly like the existing lib/prescan/token_counter.py
    pattern this mirrors."""
    global _TIKTOKEN_ENCODING, _TIKTOKEN_LOAD_ATTEMPTED
    if _TIKTOKEN_LOAD_ATTEMPTED:
        return _TIKTOKEN_ENCODING
    _TIKTOKEN_LOAD_ATTEMPTED = True
    try:
        import tiktoken  # type: ignore

        _TIKTOKEN_ENCODING = tiktoken.get_encoding(_TIKTOKEN_ENCODING_NAME)
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.debug(
            "estimate_tokens: tiktoken unavailable (%s); using heuristic chars/%s fallback.",
            exc,
            HEURISTIC_CHARS_PER_TOKEN,
        )
        _TIKTOKEN_ENCODING = None
    return _TIKTOKEN_ENCODING


def reset_tokenizer_cache() -> None:
    """Test-only: force the next estimate_tokens()/_get_tiktoken_encoding()
    call to re-probe tiktoken instead of reusing the cached result."""
    global _TIKTOKEN_ENCODING, _TIKTOKEN_LOAD_ATTEMPTED
    _TIKTOKEN_ENCODING = None
    _TIKTOKEN_LOAD_ATTEMPTED = False


def _is_openai_family(provider: str, model_id: str) -> bool:
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip().lower()
    if provider_token == "openai":
        return True
    if provider_token in ("openrouter", "or") and "openai" in model_token:
        return True
    return False


def estimate_tokens(*texts: str, provider: str = "", model_id: str = "") -> Dict[str, Any]:
    """THE single token-estimation function for text this service actually
    holds in memory (F-12 fix).

    Returns a dict -- never a bare int -- so every call site is forced to
    carry (and can print) which method produced the number::

        {"tokens": int, "tokenizer": str, "confidence": "measured"|"heuristic"}

    ``tokenizer`` is one of:
      - ``"tiktoken_o200k_base"`` -- a real tokenizer ran (confidence
        "measured"); only reachable for OpenAI-family routes with tiktoken
        importable.
      - ``"heuristic_chars4"`` -- chars/4 fallback (confidence "heuristic"),
        used for every non-OpenAI-family route, or when tiktoken is not
        importable.
    """
    chunks = [str(t or "") for t in texts]
    if _is_openai_family(provider, model_id):
        encoding = _get_tiktoken_encoding()
        if encoding is not None:
            total_tokens = 0
            for chunk in chunks:
                if chunk:
                    total_tokens += len(encoding.encode(chunk))
            return {
                "tokens": total_tokens,
                "tokenizer": f"tiktoken_{_TIKTOKEN_ENCODING_NAME}",
                "confidence": "measured",
            }
    total_chars = sum(len(chunk) for chunk in chunks)
    return {
        "tokens": max(0, int(total_chars / HEURISTIC_CHARS_PER_TOKEN)),
        "tokenizer": "heuristic_chars4",
        "confidence": "heuristic",
    }


def estimate_tokens_from_char_count(
    total_chars: int,
    *,
    provider: str = "",
    model_id: str = "",
) -> Dict[str, Any]:
    """Heuristic-only variant of estimate_tokens() for callers that have a
    character/byte COUNT but not the actual text -- e.g.
    lib/prescan/cost_estimator.py's CostEstimator, which estimates from
    FileEntry.size_bytes without reading file contents.

    tiktoken needs real text to encode, so this path can never reach
    "measured" confidence: it always returns the heuristic chars/4 result,
    using the SAME HEURISTIC_CHARS_PER_TOKEN constant as estimate_tokens()'s
    own fallback branch, so there is exactly one heuristic divisor value
    shared by both entry points (F-12 fix: this replaces
    lib/prescan/cost_estimator.py's independent chars/3.5 constant, which
    also disagreed with run_extraction_v5.py's separate chars/4 heuristic).
    ``provider``/``model_id`` are accepted for signature symmetry with
    estimate_tokens() and future extension; they do not affect the result.
    """
    del provider, model_id  # unused: no text available to route to tiktoken
    return {
        "tokens": max(0, int(max(0, int(total_chars)) / HEURISTIC_CHARS_PER_TOKEN)),
        "tokenizer": "heuristic_chars4_count_only",
        "confidence": "heuristic",
    }


# ---------------------------------------------------------------------------
# Per-lane, per-model-family output-token ratio table (TP-RTE-TRUTH-R2-002,
# F-12). Replaces cost_estimator.py's flat 15%-of-input heuristic -- the only
# output projection this packet's allowlist can touch; run_extraction_v5.py's
# separate 10%/2% runtime heuristics are the same documented OUT-OF-BOUNDARY
# finding as the tokenizer split above.
#
# Every row carries an implicit ratio_source="assumed" (see
# resolve_output_ratio): no calibration job exists yet that recomputes ratios
# from telemetry/spend_ledger.json run history (A2 DESIGN item 2 / §5.2
# describes that job; it is not part of this packet). "assumed" is printed on
# every estimate specifically so a reader never mistakes these numbers for
# measured ones.
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_LANE = "BULK_DOCS"
_MODEL_FAMILY_GENERIC = "generic"
_MIN_PROJECTED_OUTPUT_TOKENS = 1

OUTPUT_RATIO_TABLE: Dict[str, Dict[str, float]] = {
    # Bulk documentation/inventory phases (A-style bulk extraction): modest
    # narrative output relative to input.
    "BULK_DOCS": {
        "gpt_mini": 0.08,
        "gpt": 0.12,
        "codex": 0.10,
        "gemini": 0.10,
        "grok": 0.10,
        "reasoning": 1.00,
        _MODEL_FAMILY_GENERIC: 0.15,
    },
    # Bulk code-analysis phases: slightly higher than docs (structured
    # findings, code excerpts echoed back).
    "BULK_CODE": {
        "gpt_mini": 0.10,
        "gpt": 0.15,
        "codex": 0.12,
        "gemini": 0.12,
        "grok": 0.12,
        "reasoning": 1.00,
        _MODEL_FAMILY_GENERIC: 0.15,
    },
    # Contract-extraction / JSON-managed steps: compact structured output,
    # small relative to input by design (previously the runtime's flat 2%
    # heuristic).
    "CE": {
        "gpt_mini": 0.03,
        "gpt": 0.03,
        "codex": 0.03,
        "gemini": 0.03,
        "grok": 0.03,
        "reasoning": 0.50,
        _MODEL_FAMILY_GENERIC: 0.05,
    },
    # Synthesis/aggregation phases (R/S-style): A2 §2.3's dominant error
    # term -- output can approach or exceed input on reasoning models.
    "SYNTH": {
        "gpt_mini": 0.25,
        "gpt": 0.35,
        "codex": 0.30,
        "gemini": 0.30,
        "grok": 0.30,
        "reasoning": 1.50,
        _MODEL_FAMILY_GENERIC: 0.35,
    },
}


_REASONING_TOKEN_RE = re.compile(r"(?:^|[^a-z0-9])o[0-9](?:[^a-z0-9]|$)")


def classify_model_family(provider: str, model_id: str) -> str:
    """Coarse model-family classifier used as the output_ratio table's
    second key. Reasoning-labeled models are called out explicitly because
    A2 §2.3 identifies unmodeled reasoning output as the single biggest
    source of estimate error (~4-6x under on synthesis phases).

    Matches the literal substring "reasoning" (e.g. xAI's
    "grok-4.20-beta-0309-reasoning" catalog entries) OR an OpenAI
    reasoning-line model id token like "o1", "o1-mini", "o3", "o3-pro"
    delimited by non-alphanumeric characters or string boundaries (so
    "gpt-4o-mini" does NOT match: "o" there is not its own token).
    """
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip().lower()
    if "reasoning" in model_token or _REASONING_TOKEN_RE.search(model_token):
        return "reasoning"
    if _is_openai_family(provider_token, model_token):
        if "codex" in model_token:
            return "codex"
        if "mini" in model_token:
            return "gpt_mini"
        return "gpt"
    if provider_token == "gemini":
        return "gemini"
    if provider_token == "xai":
        return "grok"
    return _MODEL_FAMILY_GENERIC


def resolve_output_ratio(lane: Optional[str], provider: str, model_id: str) -> Dict[str, Any]:
    """Look up the output_ratio[lane][model_family] table. Never raises: an
    unrecognized lane falls back to DEFAULT_OUTPUT_LANE; an unrecognized
    family falls back to that lane's "generic" row -- both fallbacks are
    reported in the return value so a caller can print them rather than
    silently substitute."""
    requested_lane = str(lane or DEFAULT_OUTPUT_LANE).strip().upper()
    lane_key = requested_lane if requested_lane in OUTPUT_RATIO_TABLE else DEFAULT_OUTPUT_LANE
    family = classify_model_family(provider, model_id)
    lane_table = OUTPUT_RATIO_TABLE[lane_key]
    ratio = lane_table.get(family)
    family_key = family
    if ratio is None:
        family_key = _MODEL_FAMILY_GENERIC
        ratio = lane_table[_MODEL_FAMILY_GENERIC]
    return {
        "lane": lane_key,
        "lane_requested": requested_lane,
        "model_family": family_key,
        "output_ratio": float(ratio),
        "ratio_source": "assumed",
    }


def project_output_tokens(
    input_tokens: int,
    *,
    lane: Optional[str] = None,
    provider: str = "",
    model_id: str = "",
    min_tokens: int = _MIN_PROJECTED_OUTPUT_TOKENS,
) -> Dict[str, Any]:
    """Project output tokens from input tokens using the shared
    output_ratio[lane][family] table (F-12 fix). Replaces
    lib/prescan/cost_estimator.py's flat 15%-of-input heuristic."""
    resolved = resolve_output_ratio(lane, provider, model_id)
    net_input = max(0, int(input_tokens or 0))
    projected = max(int(min_tokens), int(net_input * resolved["output_ratio"]))
    return {
        **resolved,
        "input_tokens": net_input,
        "output_tokens": projected,
    }


@dataclass
class SpendTrackerState:
    run_root: Path
    run_id: str
    max_cost_usd: Decimal
    pricing_source: str
    pricing_sha256: str
    pricing_registry: Dict[str, Dict[str, Decimal]]
    total_cost_usd: Decimal
    cost_abort_triggered: bool
    abort_reason: Optional[str]
    entries: List[Dict[str, Any]]
    # TP-RTE-TRUTH-R2-003 (F-13 wiring): "preventive" (default; every shipped
    # cost profile declares it) refuses to commit a call's spend to
    # total_cost_usd when doing so would breach max_cost_usd -- see
    # record_request_cost. "post_hoc" reproduces the pre-fix legacy
    # record-then-compare behavior (opt-in only; no shipped profile uses it).
    # Any other/missing value fails closed to "preventive".
    cost_cap_mode: str = "preventive"


class CostLimitExceededError(RuntimeError):
    def __init__(self, message: str, details: Dict[str, Any]) -> None:
        super().__init__(message)
        self.details = dict(details)


@dataclass(frozen=True)
class CostingDeps:
    selected_execution_step_ids_for_phase: Callable[[Any, str], Optional[list[str]]]
    collect_provider_routes: Callable[..., Dict[str, Dict[str, Any]]]
    load_pricing_registry: Callable[[], Tuple[Dict[str, Dict[str, Decimal]], str]]
    pricing_config_path: Path
    write_json: Callable[[Path, Dict[str, Any]], None]
    telemetry_path: Callable[[Path, str], Path]
    now_iso: Callable[[], str]
    pricing_surface_metadata: Callable[..., Dict[str, Any]]
    spend_ledger_filename: str


def _quantize_usd(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _pricing_key(provider: str, model_id: str) -> str:
    return f"{str(provider).strip().lower()}/{str(model_id).strip()}"


# ---------------------------------------------------------------------------
# Provider/model normalization + candidate resolution (moved verbatim from
# lib/spend_ledger.py so both the preview/preventive path (SpendLedger) and
# the accounting path (SpendTrackerState, below) resolve a route to a pricing
# row identically — same candidate order, same match semantics).
# ---------------------------------------------------------------------------


def _normalize_provider_model(
    provider: Optional[str],
    model_id: Optional[str],
    route: Optional[str] = None,
) -> Tuple[str, str]:
    route_token = str(route or "").strip()
    if route_token and (not provider or not model_id):
        if "/" in route_token:
            route_provider, route_model_id = route_token.split("/", 1)
            provider = provider or route_provider
            model_id = model_id or route_model_id
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip()
    if not provider_token and "/" in model_token:
        first, rest = model_token.split("/", 1)
        if first:
            return first.strip().lower(), rest.strip()
    return provider_token, model_token


def _pricing_candidates(provider: str, model_id: str) -> list[str]:
    provider_token, model_token = _normalize_provider_model(provider, model_id)
    lower_model = model_token.lower()
    candidates: list[str] = []

    def _push(token: str) -> None:
        normalized = str(token or "").strip().lower()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    if provider_token and lower_model:
        _push(f"{provider_token}/{lower_model}")
    _push(lower_model)
    if "/" in lower_model:
        _push(lower_model.split("/", 1)[1])
        parts = lower_model.split("/")
        if len(parts) >= 2:
            _push("/".join(parts[-2:]))
    return candidates


# Optimizer fields (May 2026 pricing.yaml schema extension) carried on every
# registry row so preview/preventive/accounting can apply the SAME
# service_tier / batch / cache multipliers via compute_optimized_cost below.
_OPTIMIZER_PASSTHROUGH_KEYS = (
    "cached_input_cost_per_1m_usd",
    "batch_discount",
    "service_tier_flex_multiplier",
    "service_tier_priority_multiplier",
    "cache_read_multiplier",
    "cache_write_5m_multiplier",
    "cache_write_1h_multiplier",
    "prompt_cache_min_tokens",
    "auto_cache_enabled",
    "tiered_input_threshold_tokens",
    "tiered_input_above_cost_per_1m_usd",
    "tiered_output_above_cost_per_1m_usd",
    "tiered_cached_input_above_cost_per_1m_usd",
    "data_residency_us_multiplier",
    "context_window",
    "supports_json_schema_strict",
    "supports_reasoning_toggle",
    "alias_of",
    "specialization",
)


def _opt_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_pricing_registry(path: Path) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """THE single pricing authority (F-10 fix).

    Reads config/pricing.yaml directly and FAILS CLOSED: a missing file, an
    unparsable YAML document, a missing/empty ``models`` map, a malformed
    row, or a negative rate all raise RuntimeError immediately. There is no
    fallback branch here that returns a partial or degraded registry — a
    catalog load failure must block every costed operation, never silently
    reprice every model at a $0.15/$0.60 baseline while still reporting
    "priced" (the exact defect this task packet closes).

    Each returned row carries both the legacy Decimal ``input_cost_per_m`` /
    ``output_cost_per_m`` keys (consumed by estimate_usage_cost_usd's Decimal
    math below) AND the float ``*_cost_per_1m_usd`` + optimizer keys consumed
    by compute_optimized_cost / resolve_model_rate — so E2 (SpendLedger) and
    E3 (SpendTrackerState) price the exact same row through the exact same
    optimizer math when given the same usage + context.
    """
    if not path.exists():
        raise RuntimeError(f"Pricing config missing: {path}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Pricing config is not valid YAML: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Pricing config must decode to an object: {path}")
    models = payload.get("models")
    if not isinstance(models, dict) or not models:
        raise RuntimeError(f"Pricing config missing models map: {path}")
    registry: Dict[str, Dict[str, Any]] = {}
    for key, row in models.items():
        if not isinstance(row, dict):
            raise RuntimeError(f"Pricing entry must be an object for {key}")
        input_cost_raw = row.get("input_cost_per_m")
        output_cost_raw = row.get("output_cost_per_m")
        if input_cost_raw is None or output_cost_raw is None:
            # Explicit UNPRICED row (vendor data still null in the catalog).
            # Skipped from the registry so a lookup treats it exactly like
            # "no entry" — never invents a rate for it. See resolve_model_rate.
            continue
        try:
            input_cost = Decimal(str(input_cost_raw))
            output_cost = Decimal(str(output_cost_raw))
        except Exception as exc:
            raise RuntimeError(f"Invalid pricing entry for {key}") from exc
        if input_cost < 0 or output_cost < 0:
            raise RuntimeError(f"Negative pricing entry for {key}")
        registry[str(key).strip().lower()] = {
            "input_cost_per_m": input_cost,
            "output_cost_per_m": output_cost,
            "input_cost_per_1m_usd": float(input_cost),
            "output_cost_per_1m_usd": float(output_cost),
            "pricing_source_type": row.get("pricing_source_type"),
            "pricing_source_ref": row.get("pricing_source_ref"),
            "pricing_status": row.get("pricing_status"),
            "pricing_confidence": row.get("pricing_confidence"),
            "pricing_currency": row.get("pricing_currency"),
            "surface_scope": row.get("surface_scope"),
            "cached_input_cost_per_1m_usd": _opt_float(row.get("cached_input_cost")),
            "batch_discount": _opt_float(row.get("batch_discount")),
            "service_tier_flex_multiplier": _opt_float(row.get("service_tier_flex_multiplier")),
            "service_tier_priority_multiplier": _opt_float(row.get("service_tier_priority_multiplier")),
            "cache_read_multiplier": _opt_float(row.get("cache_read_multiplier")),
            "cache_write_5m_multiplier": _opt_float(row.get("cache_write_5m_multiplier")),
            "cache_write_1h_multiplier": _opt_float(row.get("cache_write_1h_multiplier")),
            "prompt_cache_min_tokens": _opt_int(row.get("prompt_cache_min_tokens")),
            "auto_cache_enabled": (
                bool(row["auto_cache_enabled"]) if row.get("auto_cache_enabled") is not None else None
            ),
            "tiered_input_threshold_tokens": _opt_int(row.get("tiered_input_threshold_tokens")),
            "tiered_input_above_cost_per_1m_usd": _opt_float(row.get("tiered_input_above_cost_per_m")),
            "tiered_output_above_cost_per_1m_usd": _opt_float(row.get("tiered_output_above_cost_per_m")),
            "tiered_cached_input_above_cost_per_1m_usd": _opt_float(
                row.get("tiered_cached_input_above_cost_per_m")
            ),
            "data_residency_us_multiplier": _opt_float(row.get("data_residency_us_multiplier")),
            "context_window": _opt_int(row.get("context_window")),
            "supports_json_schema_strict": (
                bool(row["supports_json_schema_strict"])
                if row.get("supports_json_schema_strict") is not None
                else None
            ),
            "supports_reasoning_toggle": (
                bool(row["supports_reasoning_toggle"])
                if row.get("supports_reasoning_toggle") is not None
                else None
            ),
            "alias_of": row.get("alias_of"),
            "specialization": row.get("specialization"),
        }
    from lib.promptgen.hashing import sha256_text

    return registry, sha256_text(path.read_text(encoding="utf-8"))


# mtime-keyed cache so repeated per-call lookups (thousands over a run) don't
# re-read + re-parse pricing.yaml every time. A load FAILURE is never cached —
# every call re-attempts the load and re-raises, so a transiently broken
# catalog stays fail-closed rather than latching a stale success or a cached
# "it's fine" that masks a later corruption.
_PRICING_REGISTRY_CACHE: Dict[str, Tuple[Dict[str, Dict[str, Any]], str, float]] = {}


def load_pricing_registry_cached(path: Path) -> Tuple[Dict[str, Dict[str, Any]], str]:
    key = str(path)
    try:
        mtime = path.stat().st_mtime
    except OSError as exc:
        raise RuntimeError(f"Pricing config missing: {path}") from exc
    cached = _PRICING_REGISTRY_CACHE.get(key)
    if cached is not None and cached[2] == mtime:
        return cached[0], cached[1]
    registry, sha = load_pricing_registry(path)
    _PRICING_REGISTRY_CACHE[key] = (registry, sha, mtime)
    return registry, sha


def reset_pricing_registry_cache() -> None:
    """Test/teardown hook — clears the mtime-keyed cache above."""
    _PRICING_REGISTRY_CACHE.clear()


def resolve_model_rate(
    pricing_registry: Dict[str, Dict[str, Any]],
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    route: Optional[str] = None,
) -> Dict[str, Any]:
    """Pure pricing-table lookup against an already-loaded registry.

    Never raises for an unknown model: this is the "does a priced row exist"
    layer. Catalog LOAD failure is handled entirely by load_pricing_registry /
    load_pricing_registry_cached above (raise, fail closed) before this is
    ever reached. Whether an unknown MODEL should raise (cap set) or be
    marked UNPRICED (no cap) is a cap-aware policy decision made by the
    caller (SpendLedger.price_usage / accumulate) — this function only ever
    reports the plain fact "priced" or "not priced", with no fabricated
    dollar figure in the "not priced" case (F-10: a model this function
    cannot price returns $0.00, never a baseline or max-of-registry guess).
    """
    provider_token, model_token = _normalize_provider_model(provider, model_id, route)
    for index, candidate in enumerate(_pricing_candidates(provider_token, model_token)):
        row = pricing_registry.get(candidate)
        if not row:
            continue
        input_rate = row.get("input_cost_per_1m_usd")
        output_rate = row.get("output_cost_per_1m_usd")
        if input_rate is None and row.get("input_cost_per_m") is not None:
            input_rate = float(row["input_cost_per_m"])
        if output_rate is None and row.get("output_cost_per_m") is not None:
            output_rate = float(row["output_cost_per_m"])
        if input_rate is None or output_rate is None:
            # Row present but still carries no numeric rate — treat exactly
            # like "no entry" rather than inventing one.
            continue
        return {
            "provider": provider_token,
            "model_id": model_token,
            "pricing_key": candidate,
            "pricing_version": PRICING_VERSION,
            "pricing_source": str(
                row.get("pricing_source_ref") or row.get("pricing_source_type") or "config/pricing.yaml"
            ),
            "pricing_source_type": str(row.get("pricing_source_type") or "unknown"),
            "pricing_status": str(row.get("pricing_status") or "PRICED_WITH_CAVEAT"),
            "pricing_confidence": str(row.get("pricing_confidence") or "UNKNOWN"),
            "pricing_currency": str(row.get("pricing_currency") or "USD"),
            "surface_scope": str(row.get("surface_scope") or "unknown"),
            "match_type": "exact" if index == 0 else "fuzzy",
            "unknown_model": False,
            "input_cost_per_1m_usd": float(input_rate),
            "output_cost_per_1m_usd": float(output_rate),
            **{k: row.get(k) for k in _OPTIMIZER_PASSTHROUGH_KEYS},
        }

    fallback_key = (
        f"{provider_token}/{model_token}".lower()
        if provider_token and model_token
        else (model_token.lower() if model_token else "unknown")
    )
    return {
        "provider": provider_token,
        "model_id": model_token,
        "pricing_key": fallback_key,
        "pricing_version": PRICING_VERSION,
        "pricing_source": f"unknown_model:{UNKNOWN_MODEL_POLICY}",
        "pricing_source_type": "unpriced_no_catalog_entry",
        "pricing_status": "UNPRICED_UNKNOWN",
        "pricing_confidence": "UNKNOWN",
        "pricing_currency": "USD",
        "surface_scope": "unknown",
        "match_type": "fallback",
        "unknown_model": True,
        # No fabricated dollar figure (F-10 fix): an unpriced model prices at
        # exactly $0.00 here, never a baseline or max-of-registry guess
        # dressed up as a confident number. Callers must render "UNPRICED",
        # not a dollar amount, whenever unknown_model is True.
        "input_cost_per_1m_usd": 0.0,
        "output_cost_per_1m_usd": 0.0,
        **{k: None for k in _OPTIMIZER_PASSTHROUGH_KEYS},
    }


_VALID_SERVICE_TIERS = ("default", "flex", "priority", "auto", None)


def _resolve_per_token_input_rate(rate: Dict[str, Any], prompt_token_count: Optional[int]) -> float:
    """Pick base input rate; honor tiered_input_above_cost_per_1m_usd if prompt
    crosses the model's tier threshold (Gemini Pro >200K, grok-4-fast >128K)."""
    base = float(rate.get("input_cost_per_1m_usd") or 0.0)
    threshold = rate.get("tiered_input_threshold_tokens")
    if prompt_token_count is not None and threshold is not None and prompt_token_count > int(threshold):
        above = rate.get("tiered_input_above_cost_per_1m_usd")
        if above is not None:
            return float(above)
    return base


def _resolve_per_token_output_rate(rate: Dict[str, Any], prompt_token_count: Optional[int]) -> float:
    base = float(rate.get("output_cost_per_1m_usd") or 0.0)
    threshold = rate.get("tiered_input_threshold_tokens")
    if prompt_token_count is not None and threshold is not None and prompt_token_count > int(threshold):
        above = rate.get("tiered_output_above_cost_per_1m_usd")
        if above is not None:
            return float(above)
    return base


def _resolve_cached_input_rate(rate: Dict[str, Any]) -> float:
    """Cached input rate per million tokens.

    Resolution order: explicit cached_input_cost_per_1m_usd -> cache_read_multiplier
    x input rate -> 10% of input rate (industry-standard 90% discount fallback).
    """
    explicit = rate.get("cached_input_cost_per_1m_usd")
    if explicit is not None:
        return float(explicit)
    input_rate = float(rate.get("input_cost_per_1m_usd") or 0.0)
    multiplier = rate.get("cache_read_multiplier")
    if multiplier is not None:
        return input_rate * float(multiplier)
    return input_rate * 0.10


def _tier_multiplier(rate: Dict[str, Any], service_tier: Optional[str]) -> Tuple[float, str]:
    if service_tier is None or service_tier in ("default", "auto"):
        return 1.0, service_tier or "default"
    if service_tier == "flex":
        m = rate.get("service_tier_flex_multiplier")
        return (float(m) if m is not None else 1.0), "flex"
    if service_tier == "priority":
        m = rate.get("service_tier_priority_multiplier")
        return (float(m) if m is not None else 1.0), "priority"
    return 1.0, service_tier or "default"


def _batch_multiplier(rate: Dict[str, Any], is_batch: bool) -> float:
    if not is_batch:
        return 1.0
    discount = rate.get("batch_discount")
    if discount is None:
        return 1.0
    return float(discount)


def compute_optimized_cost(
    rate: Dict[str, Any],
    *,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0,
    service_tier: Optional[str] = None,
    is_batch: bool = False,
    prompt_token_count: Optional[int] = None,
    data_residency: str = "global",
) -> Dict[str, Any]:
    """Compute a cost breakdown with optimizer multipliers.

    THE money-math function: preview, preventive check, and E2 accounting all
    call this (via SpendLedger.price_usage/accumulate); E3 accounting
    (estimate_usage_cost_usd below) applies the identical tier/batch/cache
    semantics when given the same optimizer context, so all three paths
    produce the same number for the same usage (F-11 fix).
    """
    input_tokens = max(0, int(input_tokens or 0))
    output_tokens = max(0, int(output_tokens or 0))
    cached_input_tokens = max(0, min(int(cached_input_tokens or 0), input_tokens))
    uncached_input_tokens = input_tokens - cached_input_tokens

    input_rate = _resolve_per_token_input_rate(rate, prompt_token_count)
    output_rate = _resolve_per_token_output_rate(rate, prompt_token_count)
    cached_rate = _resolve_cached_input_rate(rate)

    base_input_cost = (uncached_input_tokens / 1_000_000.0) * input_rate
    cached_input_cost = (cached_input_tokens / 1_000_000.0) * cached_rate
    base_output_cost = (output_tokens / 1_000_000.0) * output_rate
    base_cost = base_input_cost + cached_input_cost + base_output_cost
    no_cache_input_cost = (input_tokens / 1_000_000.0) * input_rate
    cache_discount = max(0.0, no_cache_input_cost - (base_input_cost + cached_input_cost))

    tier_mult, tier_label = _tier_multiplier(rate, service_tier)
    batch_mult = _batch_multiplier(rate, is_batch)

    residency_mult = 1.0
    if data_residency == "us":
        rd = rate.get("data_residency_us_multiplier")
        if rd is not None:
            residency_mult = float(rd)

    combined_mult = tier_mult * batch_mult * residency_mult
    final_cost = base_cost * combined_mult

    applied: list = []
    if tier_label != "default":
        applied.append(f"service_tier:{tier_label}({tier_mult:.2f}x)")
    if is_batch and batch_mult != 1.0:
        applied.append(f"batch({batch_mult:.2f}x)")
    if cached_input_tokens > 0:
        applied.append(f"cache({cached_input_tokens}/{input_tokens}tok)")
    if residency_mult != 1.0:
        applied.append(f"residency:us({residency_mult:.2f}x)")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_input_tokens,
        "uncached_input_tokens": uncached_input_tokens,
        "input_rate_per_1m_usd": input_rate,
        "output_rate_per_1m_usd": output_rate,
        "cached_input_rate_per_1m_usd": cached_rate,
        "base_input_cost_usd": base_input_cost,
        "cached_input_cost_usd": cached_input_cost,
        "base_output_cost_usd": base_output_cost,
        "base_cost_usd": base_cost,
        "no_cache_input_cost_usd": no_cache_input_cost,
        "cache_discount_usd": cache_discount,
        "service_tier": tier_label,
        "tier_multiplier": tier_mult,
        "is_batch": bool(is_batch),
        "batch_multiplier": batch_mult,
        "data_residency": data_residency,
        "data_residency_multiplier": residency_mult,
        "combined_multiplier": combined_mult,
        "final_cost_usd": final_cost,
        "applied_optimizers": applied,
    }


def make_projected_cost_check(
    *,
    rate: Dict[str, Any],
    current_total_cost_usd: float,
    max_cost_usd: Optional[float],
) -> Callable[..., bool]:
    """Return a callable that previews whether one more LLM call would breach
    the spend cap, BEFORE the call is made (the preventive-cap helper)."""
    if max_cost_usd is None:
        def _always_ok(**_kwargs: Any) -> bool:
            return True
        return _always_ok

    def _check(
        *,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
        service_tier: Optional[str] = None,
        is_batch: bool = False,
        prompt_token_count: Optional[int] = None,
        data_residency: str = "global",
    ) -> bool:
        priced = compute_optimized_cost(
            rate,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            service_tier=service_tier,
            is_batch=is_batch,
            prompt_token_count=prompt_token_count,
            data_residency=data_residency,
        )
        return current_total_cost_usd + priced["final_cost_usd"] <= max_cost_usd

    return _check


def _decimal_tier_multiplier(rate: Dict[str, Any], service_tier: Optional[str]) -> Decimal:
    if service_tier is None or service_tier in ("default", "auto"):
        return Decimal("1")
    if service_tier == "flex":
        m = rate.get("service_tier_flex_multiplier")
        return Decimal(str(m)) if m is not None else Decimal("1")
    if service_tier == "priority":
        m = rate.get("service_tier_priority_multiplier")
        return Decimal(str(m)) if m is not None else Decimal("1")
    return Decimal("1")


def _decimal_cached_rate(rate: Dict[str, Any], input_rate: Decimal) -> Decimal:
    explicit = rate.get("cached_input_cost_per_1m_usd")
    if explicit is not None:
        return Decimal(str(explicit))
    multiplier = rate.get("cache_read_multiplier")
    if multiplier is not None:
        return input_rate * Decimal(str(multiplier))
    return input_rate * Decimal("0.10")


def extract_usage_summary(
    provider: str,
    response_obj: Any,
    response_json: Optional[Dict[str, Any]],
) -> Optional[Dict[str, int]]:
    if provider == "gemini":
        usage = getattr(response_obj, "usage_metadata", None)
        if usage is None and isinstance(response_json, dict):
            usage = response_json.get("usage_metadata")
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        completion_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_token_count", prompt_tokens)
            completion_tokens = usage.get("candidates_token_count", completion_tokens)
            total_tokens = usage.get("total_token_count", total_tokens)
    else:
        usage = (
            response_json.get("usage")
            if isinstance(response_json, dict)
            else getattr(response_obj, "usage", None)
        )
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
            completion_tokens = usage.get("completion_tokens", completion_tokens)
            total_tokens = usage.get("total_tokens", total_tokens)

    def _to_int(value: Any) -> Optional[int]:
        try:
            if value is None or value == "":
                return None
            return int(value)
        except Exception:
            return None

    prompt_value = _to_int(prompt_tokens)
    completion_value = _to_int(completion_tokens)
    total_value = _to_int(total_tokens)
    if prompt_value is None and completion_value is None and total_value is None:
        return None
    if total_value is None and prompt_value is not None and completion_value is not None:
        total_value = prompt_value + completion_value
    return {
        "prompt_tokens": int(prompt_value or 0),
        "completion_tokens": int(completion_value or 0),
        "total_tokens": int(total_value or 0),
    }


def estimate_usage_cost_usd(
    *,
    provider: str,
    model_id: str,
    usage: Dict[str, int],
    pricing_registry: Dict[str, Dict[str, Decimal]],
    service_tier: Optional[str] = None,
    is_batch: bool = False,
    cached_input_tokens: int = 0,
) -> Decimal:
    """E3 accounting math. Backward compatible: with no optimizer context
    (the default) this is byte-for-byte the original flat-rate computation.
    When given the SAME service_tier / is_batch / cached_input_tokens context
    that E2's preview/preventive path used for this call (see
    compute_optimized_cost in this module), it applies the identical
    multipliers so E2 and E3 price identical usage identically (F-11 fix) —
    see the fixture table in tests/test_pricing_authority_unification.py.
    """
    key = _pricing_key(provider, model_id)
    pricing = pricing_registry.get(key)
    if pricing is None:
        raise RuntimeError(f"Missing pricing for route {key}")
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    cached_tokens = max(0, min(int(cached_input_tokens or 0), prompt_tokens))
    uncached_tokens = prompt_tokens - cached_tokens

    input_rate = pricing["input_cost_per_m"]
    output_rate = pricing["output_cost_per_m"]

    input_cost = (Decimal(uncached_tokens) / Decimal(1_000_000)) * input_rate
    if cached_tokens:
        cached_rate = _decimal_cached_rate(pricing, input_rate)
        input_cost += (Decimal(cached_tokens) / Decimal(1_000_000)) * cached_rate
    output_cost = (Decimal(completion_tokens) / Decimal(1_000_000)) * output_rate
    base_cost = input_cost + output_cost

    multiplier = _decimal_tier_multiplier(pricing, service_tier)
    if is_batch:
        batch_discount = pricing.get("batch_discount")
        if batch_discount is not None:
            multiplier *= Decimal(str(batch_discount))

    return _quantize_usd(base_cost * multiplier)


def get_active_spend_tracker() -> Optional[SpendTrackerState]:
    """Get the currently active spend tracker state.

    Returns:
        SpendTrackerState or None: The active tracker state, if initialized.
    """
    registry = get_registry()
    return registry.get()


def is_spend_tracker_aborted() -> bool:
    state = get_active_spend_tracker()
    return bool(state is not None and state.cost_abort_triggered)


def _write_spend_ledger_snapshot(
    deps: CostingDeps,
    state: SpendTrackerState,
) -> Dict[str, Any]:
    totals_by_provider: Dict[str, Decimal] = {}
    totals_by_model: Dict[str, Decimal] = {}
    totals_by_phase: Dict[str, Decimal] = {}
    totals_by_step: Dict[str, Decimal] = {}
    for row in state.entries:
        cost = Decimal(str(row.get("cost_usd", "0")))
        provider = str(row.get("provider") or "")
        model_id = str(row.get("model_id") or "")
        phase = str(row.get("phase") or "")
        step_id = str(row.get("step_id") or "")
        if provider:
            totals_by_provider[provider] = totals_by_provider.get(provider, Decimal("0")) + cost
        if provider and model_id:
            model_key = f"{provider}/{model_id}"
            totals_by_model[model_key] = totals_by_model.get(model_key, Decimal("0")) + cost
        if phase:
            totals_by_phase[phase] = totals_by_phase.get(phase, Decimal("0")) + cost
        if phase and step_id:
            step_key = f"{phase}:{step_id}"
            totals_by_step[step_key] = totals_by_step.get(step_key, Decimal("0")) + cost
    payload = {
        "generated_at": deps.now_iso(),
        "run_id": state.run_id,
        "pricing_source": state.pricing_source,
        "pricing_sha256": state.pricing_sha256,
        "max_cost_usd": float(state.max_cost_usd),
        "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
        "cost_abort_triggered": state.cost_abort_triggered,
        "abort_reason": state.abort_reason,
        "entries_total": len(state.entries),
        "totals_by_provider_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_provider.items())
        },
        "totals_by_model_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_model.items())
        },
        "totals_by_phase_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_phase.items())
        },
        "totals_by_step_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_step.items())
        },
        "entries": list(state.entries),
    }
    deps.write_json(deps.telemetry_path(state.run_root, deps.spend_ledger_filename), payload)
    return payload


def reset_spend_tracker() -> None:
    """Reset the active spend tracker to None.

    This is typically used in test teardown to clean state between tests.
    """
    registry = get_registry()
    registry.set(None)


def initialize_spend_tracker(
    *,
    deps: CostingDeps,
    run_root: Path,
    run_id: str,
    cfg: Any,
    phases: Sequence[str],
) -> Optional[Dict[str, Any]]:
    """Initialize the spend tracker with the given configuration.

    Args:
        deps: Costing dependencies.
        run_root: Root path for this run.
        run_id: Unique ID for this run.
        cfg: Configuration object with max_cost_usd, partition_workers, etc.
        phases: List of phases to track.

    Returns:
        Dict with initial spend ledger snapshot, or None if tracking disabled.

    Raises:
        RuntimeError: If configuration is invalid.
    """
    if cfg.max_cost_usd is None:
        reset_spend_tracker()
        return None
    if cfg.partition_workers != 1:
        raise RuntimeError("--max-cost-usd requires --partition-workers 1 for deterministic enforcement.")
    selected_step_ids_by_phase = {
        phase: selected_ids
        for phase in phases
        if (selected_ids := deps.selected_execution_step_ids_for_phase(cfg, phase)) is not None
    }
    pricing_registry, pricing_sha = deps.load_pricing_registry()
    routes = deps.collect_provider_routes(
        phases=phases,
        routing_policy=cfg.routing_policy,
        selected_step_ids_by_phase=selected_step_ids_by_phase or None,
        cost_profile=cfg.cost_profile,
    )
    missing = sorted(
        _pricing_key(route["provider"], route["model_id"])
        for route in routes.values()
        if _pricing_key(route["provider"], route["model_id"]) not in pricing_registry
    )
    if missing:
        raise RuntimeError(
            "Pricing config missing route coverage for active target: "
            + ", ".join(missing)
        )
    cost_cap_mode = str(getattr(cfg, "cost_cap_mode", "preventive") or "preventive")
    if cost_cap_mode not in ("preventive", "post_hoc"):
        # Fail closed to the safe default rather than silently accepting an
        # unrecognized value (F-13 wiring; TP-RTE-TRUTH-R2-003).
        cost_cap_mode = "preventive"
    state = SpendTrackerState(
        run_root=run_root,
        run_id=run_id,
        max_cost_usd=_quantize_usd(Decimal(str(cfg.max_cost_usd))),
        pricing_source=str(deps.pricing_config_path.resolve()),
        pricing_sha256=pricing_sha,
        pricing_registry=pricing_registry,
        total_cost_usd=Decimal("0"),
        cost_abort_triggered=False,
        abort_reason=None,
        entries=[],
        cost_cap_mode=cost_cap_mode,
    )
    registry = get_registry()
    registry.set(state)
    return _write_spend_ledger_snapshot(deps, state)


def record_request_cost(
    *,
    deps: CostingDeps,
    meta: Dict[str, Any],
    phase: str,
    step_id: str,
    partition_id: str,
    provider: str,
    model_id: str,
    service_tier: Optional[str] = None,
    is_batch: bool = False,
    cached_input_tokens: int = 0,
) -> Dict[str, Any]:
    """Record a provider request cost and update the spend tracker.

    Args:
        deps: Costing dependencies.
        meta: Metadata dictionary with response_summary.
        phase: Phase identifier.
        step_id: Step identifier.
        partition_id: Partition identifier.
        provider: Provider name.
        model_id: Model identifier.
        service_tier: Optional service tier ("flex"/"priority"/...) — when
            supplied, priced with the SAME multiplier E2's preview/preventive
            path would apply for the same tier (F-11 fix). Defaults to None
            (no multiplier), which reproduces the historical flat-rate
            behavior byte-for-byte.
        is_batch: Whether this call went through a batch API (batch_discount
            multiplier). Defaults to False (no discount).
        cached_input_tokens: Count of prompt tokens served from cache, priced
            at the model's cached-input rate instead of full input rate.
            Defaults to 0 (no cache split).

    Cap enforcement (TP-RTE-TRUTH-R2-003, F-13): the tracker's
    ``cost_cap_mode`` (set at ``initialize_spend_tracker`` time from
    ``cfg.cost_cap_mode``) decides whether this call's cost is checked
    against ``max_cost_usd`` BEFORE it is added to ``total_cost_usd``
    ("preventive", the default -- the breaching call's cost is never
    committed) or after ("post_hoc", legacy, opt-in only).

    Returns:
        Updated metadata dictionary with cost information.
    """
    if not isinstance(meta, dict):
        return meta
    if meta.get("spend_ledger_recorded"):
        return meta
    if meta.get("failure_type") == "cost_aborted":
        return meta
    if meta.get("dry_run"):
        return meta
    registry = get_registry()
    with registry.with_lock() as state:
        if state is None:
            return meta
        if state.cost_abort_triggered:
            updated = dict(meta)
            updated["spend_ledger_recorded"] = False
            updated["cost_cap"] = {
                "max_cost_usd": float(state.max_cost_usd),
                "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
                "cost_abort_triggered": True,
                "abort_reason": state.abort_reason,
            }
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
            return updated
        response_summary = meta.get("response_summary")
        usage = (
            dict(response_summary.get("usage"))
            if isinstance(response_summary, dict)
            and isinstance(response_summary.get("usage"), dict)
            else None
        )
        if usage is None:
            state.cost_abort_triggered = True
            state.abort_reason = "cost_cap_usage_unavailable"
            _write_spend_ledger_snapshot(deps, state)
            updated = dict(meta)
            updated["spend_ledger_recorded"] = False
            updated["cost_cap"] = {
                "max_cost_usd": float(state.max_cost_usd),
                "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
                "cost_abort_triggered": True,
                "abort_reason": state.abort_reason,
            }
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
            return updated
        cost_usd = estimate_usage_cost_usd(
            provider=provider,
            model_id=model_id,
            usage=usage,
            pricing_registry=state.pricing_registry,
            service_tier=service_tier,
            is_batch=is_batch,
            cached_input_tokens=cached_input_tokens,
        )
        projected_total_cost_usd = _quantize_usd(state.total_cost_usd + cost_usd)
        cap_mode = getattr(state, "cost_cap_mode", "preventive") or "preventive"
        if cap_mode != "post_hoc" and projected_total_cost_usd > state.max_cost_usd:
            # F-13 fix (TP-RTE-TRUTH-R2-003, closes A2-7 one-call overshoot):
            # "preventive" (the default -- every shipped cost profile
            # declares cost_cap_mode="preventive") checks BEFORE the spend is
            # committed. The breaching call's cost is never added to
            # total_cost_usd and no ledger entry is appended for it, so the
            # recorded/durable spend total can never exceed max_cost_usd by
            # way of "commit now, notice later". (The provider call itself
            # already happened -- this closes the *bookkeeping* overshoot,
            # which is what let a run silently blow through its cap in the
            # ledger while still reporting itself as under budget until the
            # very next check.)
            state.cost_abort_triggered = True
            state.abort_reason = (
                f"cost_cap_would_exceed projected_total_cost_usd={float(projected_total_cost_usd)} "
                f"max_cost_usd={float(state.max_cost_usd)}"
            )
            _write_spend_ledger_snapshot(deps, state)
            updated = dict(meta)
            updated["spend_ledger_recorded"] = False
            updated["cost_cap"] = {
                "max_cost_usd": float(state.max_cost_usd),
                "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
                "cost_abort_triggered": True,
                "abort_reason": state.abort_reason,
            }
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
            return updated
        state.total_cost_usd = projected_total_cost_usd
        pricing_meta = deps.pricing_surface_metadata(
            provider=provider,
            model_id=model_id,
            api_key_env=(
                str(
                    meta.get("api_key_env")
                    or meta.get("api_key_env_resolved")
                    or meta.get("api_key_env_requested")
                    or ""
                )
                or None
            ),
            route_identity=meta,
            endpoint_effective=(
                str(meta.get("endpoint_effective"))
                if meta.get("endpoint_effective") is not None
                else None
            ),
            transport=(
                str(meta.get("transport"))
                if meta.get("transport") is not None
                else None
            ),
            provider_signature=(
                str(meta.get("provider_signature"))
                if meta.get("provider_signature") is not None
                else None
            ),
            route_fingerprint_hash=(
                str(meta.get("route_fingerprint_hash"))
                if meta.get("route_fingerprint_hash") is not None
                else None
            ),
        )
        event = {
            "sequence": len(state.entries) + 1,
            "recorded_at": deps.now_iso(),
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
            "provider": provider,
            "model_id": model_id,
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "cost_usd": float(cost_usd),
            "total_cost_usd_after_event": float(_quantize_usd(state.total_cost_usd)),
            **pricing_meta,
        }
        state.entries.append(event)
        if cap_mode == "post_hoc" and state.total_cost_usd > state.max_cost_usd:
            # Legacy record-then-compare behavior, opt-in only via
            # cost_cap_mode="post_hoc" (no shipped profile sets this).
            # Retained so the field has real, testable semantics (F-13
            # wiring) rather than being decorative.
            state.cost_abort_triggered = True
            state.abort_reason = (
                f"cost_cap_exceeded total_cost_usd={float(_quantize_usd(state.total_cost_usd))} "
                f"max_cost_usd={float(state.max_cost_usd)}"
            )
        _write_spend_ledger_snapshot(deps, state)
        updated = dict(meta)
        updated["spend_ledger_recorded"] = True
        updated["cost_event"] = dict(event)
        updated["cost_cap"] = {
            "max_cost_usd": float(state.max_cost_usd),
            "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
            "cost_abort_triggered": state.cost_abort_triggered,
            "abort_reason": state.abort_reason,
        }
        if state.cost_abort_triggered:
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
        return updated
