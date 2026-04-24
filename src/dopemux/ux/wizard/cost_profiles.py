"""Stage 5: Cost profile selection sourced from canonical repo truth.

This module intentionally avoids importing ``run_extraction_v5.py`` directly.
The runner has heavyweight runtime dependencies, so the wizard reads the
canonical ladder literal from source and pricing from ``config/pricing.yaml``.
"""

from __future__ import annotations

import ast
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from dopemux.console import console

from ..questionary_support import MissingInteractiveDependencyError, require_questionary
from .display import render_cost_table, render_educational_panel, render_policy_detail
from .stages import StageResult, StageStatus, WizardState

_REPO_ROOT = Path(__file__).resolve().parents[4]
_RUNNER_PATH = _REPO_ROOT / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
_PRICING_PATH = _REPO_ROOT / "config" / "pricing.yaml"

POLICY_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "cost": {"label": "Budget", "emoji": "💚", "tier": "low", "desc": "Lowest-spend ladder for exploratory and validator-first runs."},
    "balanced": {"label": "Balanced", "emoji": "💛", "tier": "mid", "desc": "General mixed-provider ladder without preset overrides."},
    "balanced_openrouter": {"label": "Balanced OR", "emoji": "💛", "tier": "mid", "desc": "Canonical v5 general default outside preset rewrites."},
    "balanced_grok_openrouter": {"label": "Grok+OR", "emoji": "🟠", "tier": "high", "desc": "xAI/OpenRouter-biased ladder with premium synthesis risk."},
    "quality": {"label": "Quality", "emoji": "🟠", "tier": "high", "desc": "Higher-quality ladder with moderate premium exposure."},
    "openrouter": {"label": "OpenRouter", "emoji": "💙", "tier": "high", "desc": "OpenRouter-heavy ladder with wider premium variance."},
    "gemini_primary": {"label": "Gemini", "emoji": "💙", "tier": "mid", "desc": "Gemini-first non-code routing with premium escape hatches."},
    "optimal": {"label": "Optimal", "emoji": "🔴", "tier": "max", "desc": "Highest-cost quality-biased ladder, not budget-safe by default."},
}

TIER_WEIGHTS = {"bulk": 0.50, "extract": 0.30, "synthesis": 0.15, "qa": 0.05}


def _extract_assignment_literal(path: Path, target_name: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == target_name:
                    return ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == target_name:
                return ast.literal_eval(node.value)
    raise RuntimeError(f"{target_name} not found in {path}")


@lru_cache(maxsize=1)
def _routing_ladders() -> Dict[str, Dict[str, List[Tuple[str, str, str]]]]:
    payload = _extract_assignment_literal(_RUNNER_PATH, "ROUTING_LADDERS")
    if not isinstance(payload, dict):
        raise RuntimeError("ROUTING_LADDERS must decode to a dict")
    return payload


@lru_cache(maxsize=1)
def _pricing_registry() -> Dict[str, Tuple[float, float]]:
    payload = yaml.safe_load(_PRICING_PATH.read_text(encoding="utf-8"))
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, dict):
        return {}
    registry: Dict[str, Tuple[float, float]] = {}
    for key, row in models.items():
        if not isinstance(row, dict):
            continue
        in_cost = row.get("input_cost_per_m")
        out_cost = row.get("output_cost_per_m")
        if in_cost is None or out_cost is None:
            continue
        try:
            registry[str(key).strip().lower()] = (float(in_cost), float(out_cost))
        except (TypeError, ValueError):
            continue
    return registry


def _model_price(provider: str, model_id: str) -> Tuple[float, float]:
    registry = _pricing_registry()
    provider_key = f"{provider}/{model_id}".strip().lower()
    if provider_key in registry:
        return registry[provider_key]
    bare = model_id.split("/")[-1].strip().lower()
    if bare in registry:
        return registry[bare]
    for key, price in registry.items():
        if key.endswith(f"/{bare}") or key == bare:
            return price
    return (1.00, 4.00)


def get_required_keys(policy: str, overrides: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
    ladder = _routing_ladders().get(policy, {})
    keys: Dict[str, bool] = {}
    override_map = overrides or {}
    for tier_routes in ladder.values():
        for _provider, _model, env_var in tier_routes:
            if env_var in keys:
                continue
            keys[env_var] = bool(
                override_map.get(env_var, "").strip()
                or os.environ.get(env_var, "").strip()
            )
    return keys


def estimate_cost(policy: str, corpus_size_bytes: int) -> Tuple[float, float]:
    corpus_chars = corpus_size_bytes
    input_tokens = corpus_chars / 4.0
    output_tokens = input_tokens * 0.3

    ladder = _routing_ladders().get(policy, _routing_ladders()["balanced_openrouter"])
    total_low = 0.0
    total_high = 0.0

    for tier, weight in TIER_WEIGHTS.items():
        routes = ladder.get(tier, [])
        if not routes:
            continue
        prices = [_model_price(provider, model) for provider, model, _env in routes]
        tier_low_input = min(p[0] for p in prices)
        tier_low_output = min(p[1] for p in prices)
        tier_high_input = max(p[0] for p in prices)
        tier_high_output = max(p[1] for p in prices)
        tier_tokens_in = input_tokens * weight
        tier_tokens_out = output_tokens * weight
        total_low += (tier_tokens_in * tier_low_input + tier_tokens_out * tier_low_output) / 1_000_000
        total_high += (tier_tokens_in * tier_high_input + tier_tokens_out * tier_high_output) / 1_000_000

    phase_factor = 14 * 0.3
    return (round(total_low * phase_factor, 2), round(total_high * phase_factor, 2))


def _build_policy_rows(corpus_size: int) -> List[Dict[str, Any]]:
    rows = []
    for policy_name, ladder in _routing_ladders().items():
        meta = POLICY_DESCRIPTIONS.get(policy_name, {"label": policy_name, "emoji": "💛", "desc": ""})
        keys = get_required_keys(policy_name)
        keys_set = sum(1 for v in keys.values() if v)
        low, high = estimate_cost(policy_name, corpus_size)
        rows.append(
            {
                "name": policy_name,
                "label": meta.get("label", policy_name),
                "emoji": meta.get("emoji", "💛"),
                "desc": meta.get("desc", ""),
                "tier": meta.get("tier", "mid"),
                "low_cost": low,
                "high_cost": high,
                "keys_ok": keys_set == len(keys),
                "keys_status": f"{keys_set}/{len(keys)}",
                "keys_detail": keys,
                "tier_routes": ladder,
                "authority": str(_RUNNER_PATH),
                "pricing_authority": str(_PRICING_PATH),
            }
        )
    return rows


def run_cost_selection(state: WizardState) -> StageResult:
    """Stage 5 — display routing policies and let the operator pick one."""
    corpus_size = state.corpus_total_size or 50_000_000
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

    if state.educate_mode:
        render_educational_panel(
            "How routing policies work",
            "These rows are read from the canonical v5 runner and repo pricing catalog.\n\n"
            "  • Bulk    — high-volume, lower-complexity scanning (50%)\n"
            "  • Extract — targeted extraction (30%)\n"
            "  • Synthesis — cross-reference and merge work (15%)\n"
            "  • QA      — validation and checks (5%)\n\n"
            "Displayed prices are bounded estimates from repo pricing authority, not live provider quotes.",
        )

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
    keys = get_required_keys(policy_name, overrides=state.provider_key_overrides)
    missing = [key for key, present in keys.items() if not present]
    if missing:
        console.print(f"\n  [yellow]⚠  Missing API keys: {', '.join(missing)}[/yellow]")
        console.print("  [dim]Set these environment variables or add session overrides before running extraction.[/dim]\n")

    low, high = estimate_cost(policy_name, corpus_size)
    console.print(f"\n  [green]✓  Selected: {policy_name}  •  Estimated ${low:.0f}–${high:.0f}[/green]\n")
    return StageResult(
        status=StageStatus.COMPLETED,
        message=f"{policy_name} (~${low:.0f}–${high:.0f})",
        data={
            "policy": policy_name,
            "low": low,
            "high": high,
            "missing_keys": missing,
            "routing_authority": str(_RUNNER_PATH),
            "pricing_authority": str(_PRICING_PATH),
        },
    )
