"""Stage 4: Cost profile selection with static routing policy data.

Contains a **static snapshot** of ROUTING_LADDERS from run_extraction_v5.py.
We do NOT import from v5 to avoid side effects and expensive provider probes.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import questionary
from rich.table import Table

from dopemux.console import console

from .display import render_cost_table, render_educational_panel
from .stages import PROVIDER_COLORS, StageResult, StageStatus, WizardState

# ── Static routing ladder snapshot ──────────────────────────────────────────
# Last synced from run_extraction_v5.py on 2026-07-12.
# Each policy maps 4 tiers → list of (provider, model, env_var) tuples.

ROUTING_LADDERS: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = {
    "cost": {
        "bulk": [("openai", "gpt-5-nano", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "extract": [("openai", "gpt-5-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "synthesis": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "qa": [("openai", "gpt-5-nano", "OPENAI_API_KEY"), ("openai", "gpt-5-mini", "OPENAI_API_KEY"), ("openai", "gpt-5.2", "OPENAI_API_KEY")],
    },
    "balanced": {
        "bulk": [("openai", "gpt-5-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "extract": [("openai", "gpt-5.1", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("anthropic", "claude-sonnet-4-5", "ANTHROPIC_API_KEY")],
        "synthesis": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("anthropic", "claude-sonnet-4-5", "ANTHROPIC_API_KEY")],
        "qa": [("openai", "gpt-5-mini", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
    },
    "balanced_openrouter": {
        "bulk": [("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"), ("openrouter", "google/gemini-2.5-flash", "OPENROUTER_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "extract": [("openrouter", "openai/gpt-5.1", "OPENROUTER_API_KEY"), ("openrouter", "google/gemini-2.5-pro", "OPENROUTER_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
        "synthesis": [("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"), ("openrouter", "anthropic/claude-sonnet-4-5", "OPENROUTER_API_KEY"), ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY")],
        "qa": [("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"), ("xai", "grok-code-fast-1", "XAI_API_KEY")],
    },
    "balanced_grok_openrouter": {
        "bulk": [("xai", "grok-code-fast-1", "XAI_API_KEY"), ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY")],
        "extract": [("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"), ("openrouter", "openai/gpt-5.1", "OPENROUTER_API_KEY")],
        "synthesis": [("xai", "grok-4.20-beta-0309-non-reasoning", "XAI_API_KEY"), ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY")],
        "qa": [("xai", "grok-code-fast-1", "XAI_API_KEY"), ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY")],
    },
    "quality": {
        "bulk": [("openai", "gpt-5.1", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("anthropic", "claude-sonnet-4-5", "ANTHROPIC_API_KEY")],
        "extract": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("anthropic", "claude-sonnet-4-5", "ANTHROPIC_API_KEY")],
        "synthesis": [("openai", "gpt-5.2", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"), ("anthropic", "claude-sonnet-4-5", "ANTHROPIC_API_KEY")],
        "qa": [("openai", "gpt-5.1", "OPENAI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY")],
    },
    "openrouter": {
        "bulk": [("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"), ("openrouter", "google/gemini-2.5-flash", "OPENROUTER_API_KEY")],
        "extract": [("openrouter", "openai/gpt-5.1", "OPENROUTER_API_KEY"), ("openrouter", "google/gemini-2.5-pro", "OPENROUTER_API_KEY")],
        "synthesis": [("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"), ("openrouter", "anthropic/claude-sonnet-4-5", "OPENROUTER_API_KEY")],
        "qa": [("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"), ("openrouter", "google/gemini-2.5-flash", "OPENROUTER_API_KEY")],
    },
    "gemini_primary": {
        "bulk": [("gemini", "gemini-3-flash", "GEMINI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")],
        "extract": [("gemini", "gemini-3-pro", "GEMINI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY")],
        "synthesis": [("gemini", "gemini-3-pro", "GEMINI_API_KEY"), ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY")],
        "qa": [("gemini", "gemini-3-flash", "GEMINI_API_KEY"), ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY")],
    },
    "optimal": {
        "bulk": [("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"), ("xai", "grok-4.20-beta-0309-non-reasoning", "XAI_API_KEY")],
        "extract": [("xai", "grok-4.20-beta-0309-non-reasoning", "XAI_API_KEY"), ("xai", "grok-4.20-beta-0309-reasoning", "XAI_API_KEY")],
        "synthesis": [("xai", "grok-4.20-beta-0309-reasoning", "XAI_API_KEY"), ("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY"), ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY")],
        "qa": [("xai", "grok-4.20-beta-0309-non-reasoning", "XAI_API_KEY"), ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY")],
    },
}

# ── Model pricing (USD per 1M tokens) ──────────────────────────────────────
# (input_per_1m, output_per_1m) — last updated 2026-07-12

MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    "gpt-5-nano": (0.10, 0.40),
    "gpt-5-mini": (0.40, 1.60),
    "gpt-5.1": (1.00, 4.00),
    "gpt-5.2": (2.00, 8.00),
    "gpt-5.4": (5.00, 20.00),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3-pro": (1.25, 10.00),
    "gemini-3-flash": (0.10, 0.40),
    "grok-code-fast-1": (0.10, 0.40),
    "grok-4-1-fast-non-reasoning": (0.50, 2.00),
    "grok-4.20-beta-0309-non-reasoning": (2.00, 8.00),
    "grok-4.20-beta-0309-reasoning": (3.00, 15.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-opus-4-6": (15.00, 75.00),
}

# ── Policy display metadata ────────────────────────────────────────────────

POLICY_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "cost": {"label": "Budget", "emoji": "💚", "tier": "low", "desc": "Cheapest models — nano + flash"},
    "balanced": {"label": "Balanced", "emoji": "💛", "tier": "mid", "desc": "Mixed providers, good quality/cost ratio"},
    "balanced_openrouter": {"label": "Balanced OR", "emoji": "💛", "tier": "mid", "desc": "OpenRouter primary — v5 default"},
    "balanced_grok_openrouter": {"label": "Grok+OR", "emoji": "💛", "tier": "mid", "desc": "Grok primary with OpenRouter fallback"},
    "quality": {"label": "Quality", "emoji": "🟠", "tier": "high", "desc": "Premium models across all providers"},
    "openrouter": {"label": "OpenRouter", "emoji": "💛", "tier": "mid", "desc": "Pure OpenRouter routing"},
    "gemini_primary": {"label": "Gemini", "emoji": "💙", "tier": "mid", "desc": "Gemini 3-series primary"},
    "optimal": {"label": "Optimal", "emoji": "🔴", "tier": "max", "desc": "Best quality — Grok 4.20 + GPT-5.4"},
}

# Tier weight distribution for cost estimation
TIER_WEIGHTS = {"bulk": 0.50, "extract": 0.30, "synthesis": 0.15, "qa": 0.05}


# ── Helper functions ────────────────────────────────────────────────────────

def _model_price(model_id: str) -> Tuple[float, float]:
    """Look up (input, output) price per 1M tokens. Strips provider prefix."""
    # Strip OpenRouter-style prefixes (openai/gpt-5-mini → gpt-5-mini)
    bare = model_id.split("/")[-1] if "/" in model_id else model_id
    if bare in MODEL_PRICING:
        return MODEL_PRICING[bare]
    # Fuzzy match — try prefix matching
    for key, price in MODEL_PRICING.items():
        if bare.startswith(key.rsplit("-", 1)[0]):
            return price
    # Unknown model — assume mid-range
    return (1.00, 4.00)


def get_required_keys(policy: str) -> Dict[str, bool]:
    """Return {env_var: is_set} for all keys needed by this policy."""
    ladder = ROUTING_LADDERS.get(policy, {})
    keys: Dict[str, bool] = {}
    for tier_routes in ladder.values():
        for _provider, _model, env_var in tier_routes:
            if env_var not in keys:
                keys[env_var] = bool(os.environ.get(env_var, "").strip())
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

        prices = [_model_price(model) for _, model, _ in routes]
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
        meta = POLICY_DESCRIPTIONS.get(policy_name, {"label": policy_name, "emoji": "💛", "desc": ""})
        keys = get_required_keys(policy_name)
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
        })

    return rows


# ── Stage function ──────────────────────────────────────────────────────────

def run_cost_selection(state: WizardState) -> StageResult:
    """Stage 4 — Display cost profiles and let user select a routing policy.

    Enhanced: factors prescan savings into cost estimates when available.
    """
    corpus_size = state.corpus_total_size or 50_000_000  # fallback to ~50MB

    # Factor in prescan savings if intelligence router is available
    savings_pct = 0.0
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
    style = questionary.Style([
        ("selected", "fg:ansiblue bold"),
        ("pointer", "fg:ansicyan"),
    ])

    # Build choices — show cost + key status
    choices = []
    default_choice = None
    for row in rows:
        tag = "✓" if row["keys_ok"] else "✗"
        label = f"{row['emoji']} {row['label']:16s}  ~${row['low_cost']:.0f}–${row['high_cost']:.0f}  [{tag} {row['keys_status']}]  {row['desc']}"
        choices.append(label)
        if row["name"] == state.selected_policy:
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

    # Map selection back to policy name
    selected_idx = choices.index(selected)
    policy_name = rows[selected_idx]["name"]
    state.selected_policy = policy_name

    # Warn if keys are missing
    keys = get_required_keys(policy_name)
    missing = [k for k, v in keys.items() if not v]
    if missing:
        console.print(f"\n  [warning]⚠  Missing API keys: {', '.join(missing)}[/warning]")
        console.print("  [text.dim]Set these environment variables before running extraction.[/text.dim]\n")

    low, high = estimate_cost(policy_name, corpus_size)
    console.print(f"\n  [success]✓  Selected: {policy_name}  •  Estimated ${low:.0f}–${high:.0f}[/success]\n")

    return StageResult(
        status=StageStatus.COMPLETED,
        message=f"{policy_name} (~${low:.0f}–${high:.0f})",
        data={"policy": policy_name, "low": low, "high": high, "missing_keys": missing},
    )
