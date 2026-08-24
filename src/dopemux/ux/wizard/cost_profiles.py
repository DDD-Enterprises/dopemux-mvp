"""Stage 4: Cost profile selection with static routing policy data.

Contains a **static snapshot** of ROUTING_LADDERS from run_extraction_v5.py
(which tier of a policy routes to which provider/model). We do NOT import
run_extraction_v5.py itself here to avoid side effects and expensive
provider probes at wizard-stage-4 time.

Dollar pricing is a different story (TP-RTE-TRUTH-R4-004, F-43): this module
used to *also* hardcode a static MODEL_PRICING $/1M-token table, "last
synced 2026-07-12" -- exactly the kind of drift the RTE-TRUTH programme
exists to kill (TP-RTE-TRUTH-R2-001 established config/pricing.yaml, read
through services/repo-truth-extractor/extractor/costing.py, as THE single
pricing authority for this service; comparing that authority against the
old static table on 2026-07-28 found real, already-manifested drift, e.g.
openai/gpt-5.2 priced here at $2.00/$8.00 vs $2.50/$15.00 in the live
catalog). config/pricing.yaml is a plain data file with no side effects, so
_load_live_pricing_registry() below reads it directly -- no v5-module exec
needed for pricing, unlike the routing-ladder question above.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from dopemux.console import console

from ..questionary_support import MissingInteractiveDependencyError, require_questionary
from .display import render_cost_table, render_educational_panel, render_policy_detail
from .stages import PROVIDER_COLORS, StageResult, StageStatus, WizardState

# ── Static routing ladder snapshot ──────────────────────────────────────────
# Last synced from run_extraction_v5.py's ROUTING_LADDERS on 2026-07-28.
# Each policy maps 4 tiers → list of (provider, model, env_var) tuples.
#
# This mapping (which provider/model serves which tier) is NOT read live --
# only the dollar prices below are (see module docstring). Re-syncing this
# table against run_extraction_v5.py's ROUTING_LADDERS still requires a
# manual diff+copy; a fully dynamic fix would need either a shared data file
# both v5 and the wizard load, or a `--print-routing-ladders-json` v5 flag,
# neither of which exists yet and both are out of this packet's file
# allowlist (services/repo-truth-extractor/run_extraction_v5.py is not
# writable by TP-RTE-TRUTH-R4-004). Flagged as an OUT-OF-BOUNDARY follow-up.

ROUTING_LADDERS: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = {
    "cost": {
        "bulk": [("openai", "gpt-5-nano", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "extract": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "synthesis": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "qa": [("openai", "gpt-5-nano", "OPENAI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("openai", "gpt-5.2", "OPENAI_API_KEY")],
    },
    "balanced": {
        "bulk": [("openai", "gpt-5-nano", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "extract": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "synthesis": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "qa": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("openai", "gpt-5-nano", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")],
    },
    "balanced_openrouter": {
        "bulk": [("openrouter", "openai/gpt-5-nano", "OPENROUTER_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "extract": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "synthesis": [("openrouter", "openai/gpt-5.2-chat", "OPENROUTER_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "qa": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("openrouter", "openai/gpt-5-nano", "OPENROUTER_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")],
    },
    "balanced_grok_openrouter": {
        "bulk": [("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "extract": [("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "synthesis": [("openai", "gpt-5.3-codex", "OPENAI_API_KEY"), ("openai", "gpt-5.5", "OPENAI_API_KEY"), ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY")],
        "qa": [("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
    },
    "quality": {
        "bulk": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "extract": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "synthesis": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "qa": [("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY")],
    },
    "openrouter": {
        "bulk": [("openrouter", "openai/gpt-4.1-nano", "OPENROUTER_API_KEY"), ("openrouter", "openai/gpt-4o-mini", "OPENROUTER_API_KEY"), ("openrouter", "openai/gpt-5-nano", "OPENROUTER_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")],
        "extract": [("openrouter", "openai/gpt-5-nano", "OPENROUTER_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "synthesis": [("openrouter", "openai/gpt-5.2-pro", "OPENROUTER_API_KEY"), ("openrouter", "openai/gpt-5.2-chat", "OPENROUTER_API_KEY"), ("openrouter", "openai/gpt-5-pro", "OPENROUTER_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY")],
        "qa": [("openrouter", "openai/gpt-4.1-nano", "OPENROUTER_API_KEY"), ("openrouter", "openai/gpt-4o-mini", "OPENROUTER_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("openai", "gpt-5-nano", "OPENAI_API_KEY")],
    },
    "gemini_primary": {
        "bulk": [("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "extract": [("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "synthesis": [("gemini", "gemini-3.1-pro-preview", "GEMINI_API_KEY"), ("openai", "gpt-5.5", "OPENAI_API_KEY"), ("openai", "gpt-5.3-codex", "OPENAI_API_KEY")],
        "qa": [("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
    },
    "optimal": {
        "bulk": [("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"), ("xai", "grok-4.3", "XAI_API_KEY")],
        "extract": [("xai", "grok-4.3", "XAI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
        "synthesis": [("xai", "grok-4.3", "XAI_API_KEY"), ("openai", "gpt-5.5", "OPENAI_API_KEY"), ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY")],
        "qa": [("xai", "grok-4.3", "XAI_API_KEY"), ("openai", "gpt-5.4-mini", "OPENAI_API_KEY")],
    },
}

# ── Model pricing (USD per 1M tokens) ──────────────────────────────────────
# Read LIVE from config/pricing.yaml -- the single pricing authority TP-RTE-
# TRUTH-R2-001 established (see services/repo-truth-extractor/extractor/
# costing.py::load_pricing_registry). This is a plain YAML data file with no
# import-time side effects, so it is safe to read directly from the wizard's
# cost-selection stage without executing run_extraction_v5.py.

_PRICING_CONFIG_PATH = Path(__file__).resolve().parents[4] / "config" / "pricing.yaml"

# Last-resort fallback ONLY: used when config/pricing.yaml cannot be read at
# all (missing file, unparsable YAML) or doesn't carry a given model. This
# table is deliberately small and is NOT kept in sync with the live catalog
# -- if you find yourself extending it to "fix" a pricing gap, add the model
# to config/pricing.yaml instead, which is what every other pricing
# consumer in the RTE service reads.
_FALLBACK_MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    "gpt-5-nano": (0.10, 0.40),
    "gpt-5-mini": (0.40, 1.60),
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.2": (2.50, 15.00),
    "gpt-5.4": (2.50, 15.00),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-pro": (1.25, 10.00),
    "grok-code-fast-1": (0.10, 0.40),
    "grok-4-1-fast-non-reasoning": (0.50, 2.00),
    "grok-4.3": (2.00, 8.00),
    "claude-opus-4-6": (15.00, 75.00),
}

_pricing_registry_cache: Optional[Dict[str, Tuple[float, float]]] = None


def _load_live_pricing_registry() -> Dict[str, Tuple[float, float]]:
    """Read {pricing_key: (input_per_1m_usd, output_per_1m_usd)} from
    config/pricing.yaml, keyed exactly as that file's `models` map (e.g.
    "openai/gpt-5.2", "openrouter/anthropic/claude-opus-4-6"). Cached at
    module scope for the lifetime of the process -- see
    reset_pricing_cache() for the test-only invalidation hook. Never raises:
    any load failure (missing file, bad YAML, missing models map) returns an
    empty dict, and callers fall back to _FALLBACK_MODEL_PRICING for that
    model rather than crashing the wizard's cost-preview stage.
    """
    global _pricing_registry_cache
    if _pricing_registry_cache is not None:
        return _pricing_registry_cache
    registry: Dict[str, Tuple[float, float]] = {}
    try:
        payload = yaml.safe_load(_PRICING_CONFIG_PATH.read_text(encoding="utf-8"))
        models = payload.get("models") if isinstance(payload, dict) else None
        if isinstance(models, dict):
            for key, row in models.items():
                if not isinstance(row, dict):
                    continue
                input_cost = row.get("input_cost_per_m")
                output_cost = row.get("output_cost_per_m")
                if input_cost is None or output_cost is None:
                    continue
                try:
                    registry[str(key).strip().lower()] = (
                        float(input_cost),
                        float(output_cost),
                    )
                except (TypeError, ValueError):
                    continue
    except Exception:
        registry = {}
    _pricing_registry_cache = registry
    return registry


def reset_pricing_cache() -> None:
    """Test-only: force the next _load_live_pricing_registry() call to
    re-read config/pricing.yaml instead of reusing the cached result."""
    global _pricing_registry_cache
    _pricing_registry_cache = None

# ── Policy display metadata ────────────────────────────────────────────────

POLICY_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "cost": {"label": "Budget", "emoji": "💚", "tier": "low", "desc": "Cheapest models — nano + flash"},
    "balanced": {"label": "Balanced", "emoji": "💛", "tier": "mid", "desc": "Mixed providers, good quality/cost ratio"},
    "balanced_openrouter": {"label": "Balanced OR", "emoji": "💛", "tier": "mid", "desc": "OpenRouter primary — v5 default"},
    "balanced_grok_openrouter": {"label": "Grok+OR", "emoji": "💛", "tier": "mid", "desc": "Grok primary with OpenRouter fallback"},
    "quality": {"label": "Quality", "emoji": "🟠", "tier": "high", "desc": "Premium models across all providers"},
    "openrouter": {"label": "OpenRouter", "emoji": "💛", "tier": "mid", "desc": "Pure OpenRouter routing"},
    "gemini_primary": {"label": "Gemini", "emoji": "💙", "tier": "mid", "desc": "Gemini 3-series primary"},
    "optimal": {"label": "Optimal", "emoji": "🔴", "tier": "max", "desc": "Best quality — Grok 4.3 + GPT-5.5"},
}

# Tier weight distribution for cost estimation
TIER_WEIGHTS = {"bulk": 0.50, "extract": 0.30, "synthesis": 0.15, "qa": 0.05}


# ── Helper functions ────────────────────────────────────────────────────────

def _model_price(provider: str, model_id: str) -> Tuple[float, float]:
    """Look up (input, output) USD/1M-token price for a routed model.

    Resolution order (F-43 fix — this used to look up ONLY a static,
    already-drifted MODEL_PRICING table by bare model id):
      1. Exact "{provider}/{model_id}" match in the live config/pricing.yaml
         registry (matches that file's key format, including OpenRouter rows
         like "openrouter/openai/gpt-5.2-chat").
      2. Bare model_id match in that same live registry.
      3. The small static _FALLBACK_MODEL_PRICING table (bare-id, then
         prefix-fuzzy match) -- only reached if config/pricing.yaml is
         missing/unreadable or doesn't (yet) carry this model.
      4. A mid-range guess, same as the pre-fix behavior's final fallback.
    """
    registry = _load_live_pricing_registry()
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip()
    bare = model_token.split("/")[-1] if "/" in model_token else model_token

    candidates: List[str] = []

    def _push(token: str) -> None:
        normalized = token.strip().lower()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    if provider_token and model_token:
        _push(f"{provider_token}/{model_token}")
    _push(model_token)
    if bare != model_token:
        _push(bare)

    for candidate in candidates:
        if candidate in registry:
            return registry[candidate]

    if bare in _FALLBACK_MODEL_PRICING:
        return _FALLBACK_MODEL_PRICING[bare]
    for key, price in _FALLBACK_MODEL_PRICING.items():
        if bare.startswith(key.rsplit("-", 1)[0]):
            return price
    # Unknown model — assume mid-range
    return (1.00, 4.00)


def get_required_keys(policy: str, overrides: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
    """Return {env_var: is_set} for all keys needed by this policy."""
    ladder = ROUTING_LADDERS.get(policy, {})
    keys: Dict[str, bool] = {}
    override_map = overrides or {}
    for tier_routes in ladder.values():
        for _provider, _model, env_var in tier_routes:
            if env_var not in keys:
                keys[env_var] = bool(
                    override_map.get(env_var, "").strip()
                    or os.environ.get(env_var, "").strip()
                )
    return keys


def estimate_cost(policy: str, corpus_size_bytes: int) -> Tuple[float, float]:
    """Return (low_estimate, high_estimate) in USD for a full 14-phase extraction.

    Estimation formula:
    - input_tokens ≈ corpus_chars / 4  (rough char-to-token ratio)
    - output_tokens ≈ input_tokens × 0.3
    - Each tier has a weight: bulk=50%, extract=30%, synthesis=15%, qa=5%
    - Low estimate uses cheapest model per tier; high uses most expensive
    - Multiply by 14 phases, divide by 1M for per-1M pricing
    """
    corpus_chars = corpus_size_bytes  # bytes ≈ chars for text
    input_tokens = corpus_chars / 4.0
    output_tokens = input_tokens * 0.3

    ladder = ROUTING_LADDERS.get(policy, ROUTING_LADDERS["balanced_openrouter"])

    total_low = 0.0
    total_high = 0.0

    for tier, weight in TIER_WEIGHTS.items():
        routes = ladder.get(tier, [])
        if not routes:
            continue

        prices = [_model_price(provider, model) for provider, model, _ in routes]
        # Low = cheapest model in tier; High = most expensive
        tier_low_input = min(p[0] for p in prices)
        tier_low_output = min(p[1] for p in prices)
        tier_high_input = max(p[0] for p in prices)
        tier_high_output = max(p[1] for p in prices)

        tier_tokens_in = input_tokens * weight
        tier_tokens_out = output_tokens * weight

        total_low += (tier_tokens_in * tier_low_input + tier_tokens_out * tier_low_output) / 1_000_000
        total_high += (tier_tokens_in * tier_high_input + tier_tokens_out * tier_high_output) / 1_000_000

    # Scale by number of phases (rough — not all phases process full corpus)
    phase_factor = 14 * 0.3  # ~30% of corpus per phase on average
    total_low *= phase_factor
    total_high *= phase_factor

    return (round(total_low, 2), round(total_high, 2))


def _build_policy_rows(corpus_size: int) -> List[Dict[str, Any]]:
    """Build display rows for all policies."""
    rows = []
    for policy_name in ROUTING_LADDERS:
        ladder = ROUTING_LADDERS.get(policy_name, {})
        meta = POLICY_DESCRIPTIONS.get(policy_name, {"label": policy_name, "emoji": "💛", "desc": ""})
        keys = get_required_keys(policy_name, overrides=None)
        keys_set = sum(1 for v in keys.values() if v)
        keys_total = len(keys)
        low, high = estimate_cost(policy_name, corpus_size)

        rows.append({
            "name": policy_name,
            "label": meta.get("label", policy_name),
            "emoji": meta.get("emoji", "💛"),
            "desc": meta.get("desc", ""),
            "tier": meta.get("tier", "mid"),
            "low_cost": low,
            "high_cost": high,
            "keys_ok": keys_set == keys_total,
            "keys_status": f"{keys_set}/{keys_total}",
            "keys_detail": keys,
            "tier_routes": ladder,
        })

    return rows


# ── Stage function ──────────────────────────────────────────────────────────

def run_cost_selection(state: WizardState) -> StageResult:
    """Stage 4 — Display cost profiles and let user select a routing policy."""
    corpus_size = state.corpus_total_size or 50_000_000  # fallback to ~50MB

    # Factor in prescan savings if intelligence router is available
    if state.intelligence_router:
        savings = state.intelligence_router.estimate_token_savings(state.corpus_manifest)
        savings_pct = savings.get("estimated_reduction_pct", 0)
        if savings_pct > 0:
            effective_size = int(corpus_size * (1 - savings_pct / 100))
            console.print(
                f"  [success]Prescan intelligence: ~{savings_pct:.1f}% token reduction "
                f"({corpus_size / (1024*1024):.1f} MB → {effective_size / (1024*1024):.1f} MB effective)[/success]\n"
            )
            corpus_size = effective_size

    rows = _build_policy_rows(corpus_size)
    for row in rows:
        keys = get_required_keys(row["name"], overrides=state.provider_key_overrides)
        keys_set = sum(1 for v in keys.values() if v)
        row["keys_ok"] = keys_set == len(keys)
        row["keys_status"] = f"{keys_set}/{len(keys)}"
        row["keys_detail"] = keys
    render_cost_table(rows, corpus_size, selected=state.selected_policy)

    # Educational content
    if state.educate_mode:
        render_educational_panel(
            "How routing policies work",
            "Each policy defines which LLM models handle the four extraction tiers:\n\n"
            "  • Bulk    — high-volume, low-complexity file scanning (50% of work)\n"
            "  • Extract — targeted content extraction (30%)\n"
            "  • Synthesis — cross-referencing and synthesis (15%)\n"
            "  • QA      — quality assurance validation (5%)\n\n"
            "Cheaper policies use smaller models (nano/flash) for bulk work.\n"
            "Premium policies use larger models for higher extraction quality.\n"
            "Cost estimates are approximate — actual cost depends on file sizes.",
        )

    # Interactive selection
    try:
        questionary = require_questionary()
    except MissingInteractiveDependencyError as exc:
        console.print(f"[red]{exc}[/red]")
        return StageResult(status=StageStatus.FAILED, message=str(exc))

    style = questionary.Style(
        [
            ("selected", "fg:ansiblue bold"),
            ("pointer", "fg:ansicyan"),
        ]
    )

    selected_idx = next(
        (idx for idx, row in enumerate(rows) if row["name"] == state.selected_policy),
        0,
    )

    while True:
        selected_row = rows[selected_idx]
        render_policy_detail(selected_row, index=selected_idx, total=len(rows))
        action = questionary.select(
            "Browse cost profiles:",
            choices=[
                "Select this profile",
                "Previous profile",
                "Next profile",
                "Choose from full list",
                "Cancel",
            ],
            default="Select this profile",
            use_indicator=True,
            style=style,
        ).ask()

        if action is None or action == "Cancel":
            return StageResult(status=StageStatus.SKIPPED, message="User cancelled")
        if action == "Previous profile":
            selected_idx = (selected_idx - 1) % len(rows)
            continue
        if action == "Next profile":
            selected_idx = (selected_idx + 1) % len(rows)
            continue
        if action == "Choose from full list":
            choices = []
            default_choice = None
            for row in rows:
                tag = "✓" if row["keys_ok"] else "✗"
                label = (
                    f"{row['emoji']} {row['label']:16s}  ~${row['low_cost']:.0f}–${row['high_cost']:.0f}  "
                    f"[{tag} {row['keys_status']}]  {row['desc']}"
                )
                choices.append(label)
                if row["name"] == selected_row["name"]:
                    default_choice = label
            selected = questionary.select(
                "Select routing policy:",
                choices=choices,
                default=default_choice or choices[0],
                use_indicator=True,
                style=style,
            ).ask()
            if selected is None:
                return StageResult(status=StageStatus.SKIPPED, message="User cancelled")
            selected_idx = choices.index(selected)
            continue
        break

    policy_name = rows[selected_idx]["name"]
    state.selected_policy = policy_name

    # Warn if keys are missing
    keys = get_required_keys(policy_name)
    missing = [k for k, v in keys.items() if not v]
    if missing:
        console.print(f"\n  [yellow]⚠  Missing API keys: {', '.join(missing)}[/yellow]")
        console.print("  [dim]Set these environment variables before running extraction.[/dim]\n")

    low, high = estimate_cost(policy_name, corpus_size)
    console.print(f"\n  [green]✓  Selected: {policy_name}  •  Estimated ${low:.0f}–${high:.0f}[/green]\n")

    return StageResult(
        status=StageStatus.COMPLETED,
        message=f"{policy_name} (~${low:.0f}–${high:.0f})",
        data={"policy": policy_name, "low": low, "high": high, "missing_keys": missing},
    )
