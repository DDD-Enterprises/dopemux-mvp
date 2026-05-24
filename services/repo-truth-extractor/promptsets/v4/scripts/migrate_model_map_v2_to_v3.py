#!/usr/bin/env python3
"""migrate_model_map_v2_to_v3.py — one-shot v2→v3 migration for model_map.yaml.

Architecture (Option B — materialize routes, lane_defaults canonical):
- v3 yaml is a SUPERSET of v2: it ADDS top-level `lane_defaults` (per
  cost_profile × lane_class × capability_tier × stage) and `tag_definitions`
  (the 8-tag bounded enum), and per-step `impact_class` + `capability_tier`
  + optional `tags`/`tag_rationale`, WITHOUT removing the per-step
  `primary_routes`/`repair_routes`/`sidefill_routes` blocks.
- `lane_defaults` is the CANONICAL source of routing intent.
- Per-step `*_routes` for the 130 non-override steps are MATERIALIZED at
  migration time as the resolved expansion of the `(value-default,
  lane_class, capability_tier)` cell in `lane_defaults`.
- Per-step `*_routes` for the 6 override steps {Z0, C10, S12, T0, T1, T3}
  are HAND-CURATED in this script and preserved verbatim across re-runs.

Why materialize instead of resolving at runtime:
- `phase_contract_map.py:_model_map_by_key()` is the actual yaml→step
  contract translator that feeds `route_entries_for_stage()`. It is NOT
  in the E8 commit allowlist. Several other off-allowlist readers
  (run_extraction_v5.py, audit_tp008.py, validate_pre_live_gate_v25.py,
  promptgen/contract_generator.py, promptgen/integrity_validator.py,
  benchmarking/*) likewise consume the v2 shape directly. Materializing
  per-step routes from `lane_defaults` at migration time preserves v2-
  shape backwards compatibility for every off-allowlist reader while
  introducing the new `lane_defaults` canonical source.

Idempotency:
- Re-running the script on the v3 output produces byte-equal yaml.
- The migration reads {step_id, phase, lane_class, strict_schema_required_primary,
  sidefill_enabled, repair_mode} from the input yaml. The structural v3
  fields (lane_class new taxonomy, capability_tier, impact_class, tags,
  tag_rationale, primary/repair/sidefill routes) are derived from this
  script's hardcoded reference tables; the input lane_class is used only
  as a hint for the v2→v3 lane mapping and is overridden by the script
  when LANE_CLASS_EXCEPTIONS applies. Operational flags
  (strict_schema_required_primary, sidefill_enabled, repair_mode) are
  preserved per-step from input — they are NOT derived from the cell
  taxonomy in this packet (a future packet may normalize them).
- Operators who hand-edit per-step routes in v3 yaml will see those edits
  overwritten on the next migration re-run; this is documented in the
  v3 yaml header comment + scripts/README.md.

CLI:
  python migrate_model_map_v2_to_v3.py --input INPUT --output OUTPUT
  python migrate_model_map_v2_to_v3.py --dry-run [--diff]

Default --input is `model_map.v2.yaml.bak`; default --output is
`model_map.yaml` (in the same directory). --dry-run prints a summary
and (with --diff) the unified diff against the on-disk output path.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

# ---------------------------------------------------------------------------
# Phase B.5 reference data (step-complexity classifications)
# Source: claudedocs/research/step-complexity-analysis-2026-05.md §2 table
# ---------------------------------------------------------------------------

# 29 steps with reasoning_depth=high per B.5 pivot 3.1.
# Cross-checked against B.5 §2 rows 138-186 + C10 row 80.
REASONING_DEPTH_HIGH_STEPS: Set[str] = {
    # R-phase synthesis (R0, R2-R11 BULK_DOCS_GENERAL + R1 CE)
    "R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
    # S-phase synthesis (S0-S11 BULK_DOCS_GENERAL + S12 CE)
    "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12",
    # T-phase outliers
    "T0",   # CE high — task packet factory
    "T2",   # BULK_DOCS_GENERAL high — packet schema authority rules (synthesis)
    # Z-phase outlier
    "Z2",   # BULK_DOCS_GENERAL high — opus input bundle (hybrid)
    # C-phase outlier
    "C10",  # BULK_CODE_HEAVY high — service catalog deep (hybrid)
}

# 9 steps with reasoning_depth=low per B.5 pivot 3.1.
REASONING_DEPTH_LOW_STEPS: Set[str] = {
    # M-phase runtime exports
    "M0", "M1", "M2", "M3", "M4", "M5", "M6",
    # CE deterministic freeze
    "Z0",
    # AGG freeze manifest
    "Z9",
}

# All other steps default to reasoning_depth=medium.

# Steps with partition_input_size_class=large per B.5 §2 column.
# Used to auto-infer the `long_context` tag for R/S/T/Z phases.
PARTITION_INPUT_SIZE_LARGE_STEPS: Set[str] = {
    # R-phase (all 12)
    "R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
    # S-phase (all 13)
    "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12",
    # T-phase (all 7)
    "T0", "T1", "T2", "T3", "T4", "T5", "T9",
    # Z-phase (all 4)
    "Z0", "Z1", "Z2", "Z9",
    # Q-phase (all 6 are large per B.5)
    "Q0", "Q1", "Q2", "Q3", "Q9", "Q11",
}

# ---------------------------------------------------------------------------
# Phase D reference data (impact_class + hand-picked critical tier)
# Source: claudedocs/research/routing-consensus-2026-05.md §4 + Change F
# ---------------------------------------------------------------------------

# Phase D Change E: explicit impact_class reclassifications.
IMPACT_CLASS_STRUCTURAL: Set[str] = {"R0", "S0", "T0"}
IMPACT_CLASS_SECURITY_SENSITIVE: Set[str] = {"R11"}
IMPACT_CLASS_IMPORTANT: Set[str] = {"R7", "S2", "Z2"}
# All other steps default to impact_class=routine.

# Phase C cell map shows R7 in (SYNTH, critical) cell even though Phase D
# classifies R7 as impact_class=important. The impact_class→capability_tier
# enforcement rule is one-directional (structural/security_sensitive ⇒
# critical) and does NOT lift `important` to critical. R7 needs a hand-pick
# entry to land at capability_tier=critical.
HAND_PICKED_CRITICAL_TIER: Set[str] = {"R7"}

# Steps that retain hand-curated per-step *_routes in v3. All other steps
# get per-step routes materialized from `lane_defaults` at migration time.
OVERRIDE_STEPS: Set[str] = {"Z0", "C10", "S12", "T0", "T1", "T3"}

# ---------------------------------------------------------------------------
# Phase C reference data (lane_class taxonomy mapping exceptions)
# Source: claudedocs/research/routing-design-2026-05.md Cell map
# ---------------------------------------------------------------------------

# v3 lane_class taxonomy: CE | EXTRACT | SYNTH | AGG (4 values).
# v2 lane_class taxonomy: CE | BULK_DOCS_GENERAL | BULK_CODE_HEAVY | AGG.
# Derivation:
#   v2 CE → v3 CE
#   v2 AGG → v3 AGG
#   v2 BULK_* + R/S phase + reasoning=high → v3 SYNTH
#   v2 BULK_* + step in LANE_CLASS_EXCEPTIONS → use exception value
#   v2 BULK_* + other → v3 EXTRACT
LANE_CLASS_EXCEPTIONS: Dict[str, str] = {
    # Phase C reclassification: SERVICE_CATALOG_DEEP requires reasoning-class.
    "C10": "SYNTH",
    # Phase C explicit: "(EXTRACT, high) — Z2 if reclassified".
    "Z2": "EXTRACT",
    # B.5 row 165 classifies T2 as synthesis; phase C cell map agrees.
    "T2": "SYNTH",
}

# ---------------------------------------------------------------------------
# Phase D reference data (8-tag bounded enum + auto-tag inference rules)
# Source: claudedocs/research/routing-consensus-2026-05.md Change 3, 4, D, E
# ---------------------------------------------------------------------------

# Bounded enum of routing-intent tags. Adding a 9th value requires a new TP
# that explicitly authorizes the change (per packet invariant #6).
TAG_ENUM_ORDER: Tuple[str, ...] = (
    "low_temp",
    "long_context",
    "schema_critical",
    "tooling_heavy",
    "control_plane",
    "security_sensitive",
    "eval_canary",
    "direct_openai_required",
)

LONG_CONTEXT_FALLBACK_ROUTES: List[Dict[str, Any]] = [
    {
        "provider": "openai",
        "model_id": "gpt-5.5",
        "api_key_env": "OPENAI_API_KEY",
        "service_tier": "default",
        "strict_json_schema": True,
        "strict_passthrough_verified": False,
        "cache_strategy": "auto",
        "context_window": 1_050_000,
    },
    {
        "provider": "gemini",
        "model_id": "gemini-3.5-flash",
        "api_key_env": "GEMINI_API_KEY",
        "strict_json_schema": True,
        "strict_passthrough_verified": False,
        "cache_strategy": "auto",
        "context_window": 1_000_000,
    },
]

# Tag definitions (rationale + routing_delta). Each tag deterministically
# maps to a small delta applied to the route ladder at runtime.
TAG_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "low_temp": {
        "rationale": (
            "Deterministic output required; temperature must be 0.0 where "
            "model supports it."
        ),
        "routing_delta": {"temperature_override": 0.0},
    },
    "long_context": {
        "rationale": (
            "Step prompt + inputs exceed 100K tokens routinely; route must "
            "support 1M context."
        ),
        "routing_delta": {
            "filter_route_context_window_min": 1_000_000,
            "fallback_routes": LONG_CONTEXT_FALLBACK_ROUTES,
        },
    },
    "schema_critical": {
        "rationale": (
            "Strict json_schema must be enforced; routes must be verified "
            "strict-capable."
        ),
        "routing_delta": {"filter_supports_json_schema_strict": True},
    },
    "tooling_heavy": {
        "rationale": (
            "Step makes many tool calls; prefer Anthropic tool_use mode in "
            "repair routes."
        ),
        "routing_delta": {"prefer_repair_provider": "anthropic"},
    },
    "control_plane": {
        "rationale": (
            "Step output is a control-plane truth artifact; failure breaks "
            "downstream synthesis."
        ),
        "routing_delta": {
            "require_min_capability_tier": "critical",
            "require_post_step_validator": "control_plane_truth_check",
        },
    },
    "security_sensitive": {
        "rationale": (
            "Step handles security-relevant facts; misclassification has "
            "externality cost."
        ),
        "routing_delta": {
            "require_min_capability_tier": "critical",
            "route_allowlist": [
                "anthropic/claude-opus-*",
                "openai/gpt-5.5*",
                "openai/gpt-5.5-pro",
            ],
        },
    },
    "eval_canary": {
        "rationale": (
            "Step is used to A/B candidate alternate models against current "
            "alias."
        ),
        "routing_delta": {"enable_canary_dual_run": True},
    },
    "direct_openai_required": {
        "rationale": (
            "Step needs OpenAI direct (flex/priority/cache); cannot tolerate "
            "OR aggregator path."
        ),
        "routing_delta": {"filter_provider": "openai"},
    },
}

# Per-step auto-tag rules per Phase D Change E and §3.
# R0/S0/T0 are control_plane truth artifacts.
# R11 is security_sensitive synthesis.
# `long_context` is auto-applied to large-partition R/S/T/Z steps below.
AUTO_TAGS_FIXED: Dict[str, List[str]] = {
    "R0": ["control_plane"],
    "S0": ["control_plane"],
    "T0": ["control_plane"],
    "R11": ["security_sensitive"],
}

# Step-specific tag_rationale, used when auto-applying tags. Falls back to
# the tag definition's rationale when no step-specific text is registered.
STEP_TAG_RATIONALES: Dict[Tuple[str, str], str] = {
    ("R0", "control_plane"): (
        "Control-plane truth map drives the entire downstream synthesis stack."
    ),
    ("S0", "control_plane"): (
        "Opus architecture synthesis is the canonical S/T/Z input."
    ),
    ("T0", "control_plane"): (
        "Task packet factory is the canonical control-plane output."
    ),
    ("R11", "security_sensitive"): (
        "Security risk synthesis feeds compliance / incident response."
    ),
}

# ---------------------------------------------------------------------------
# Phase C reference data (cell ladder map)
# Source: claudedocs/research/routing-design-2026-05.md + Phase D Change A/F
# ---------------------------------------------------------------------------

# Ordered keys for the lane_defaults block. Used for deterministic emission.
COST_PROFILE_ORDER: Tuple[str, ...] = (
    "economy",
    "value-default",
    "quality",
    "experimental",
)
LANE_CLASS_ORDER: Tuple[str, ...] = ("CE", "EXTRACT", "SYNTH", "AGG")
CAPABILITY_TIER_ORDER: Tuple[str, ...] = ("low", "medium", "high", "critical")
STAGE_ORDER: Tuple[str, ...] = ("primary_routes", "repair_routes", "sidefill_routes")
ROUTE_FIELD_ORDER: Tuple[str, ...] = (
    "provider",
    "model_id",
    "api_key_env",
    "service_tier",
    "strict_json_schema",
    "strict_passthrough_verified",
    "cache_strategy",
)


def _route(
    provider: str,
    model_id: str,
    api_key_env: str,
    *,
    service_tier: Optional[str] = None,
    strict_json_schema: bool = False,
    strict_passthrough_verified: Optional[bool] = None,
    cache_strategy: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a canonical route row.

    `strict_passthrough_verified` defaults to True automatically when the
    route is provider=openrouter AND strict_json_schema=True — the v5
    runtime fails closed on strict openrouter routes that lack the
    passthrough-verified flag (see ``run_extraction_v5.py:5367``
    ``openrouter_strict_passthrough_unverified``). Explicit False
    overrides the auto-default.
    """
    row: Dict[str, Any] = {
        "provider": provider,
        "model_id": model_id,
        "api_key_env": api_key_env,
    }
    if service_tier is not None:
        row["service_tier"] = service_tier
    row["strict_json_schema"] = bool(strict_json_schema)
    if strict_passthrough_verified is None:
        # Auto-default: openrouter strict routes are verified by E8 design
        # (they wrap providers that the runtime treats as strict-capable).
        strict_passthrough_verified = (
            provider == "openrouter" and bool(strict_json_schema)
        )
    row["strict_passthrough_verified"] = bool(strict_passthrough_verified)
    if cache_strategy is not None:
        row["cache_strategy"] = cache_strategy
    return row


# Cell ladders. Empty cells (not populated for a given profile) are explicitly
# omitted; the migration audit fails closed if a derived step lands in an
# unpopulated cell. The populated cells per Phase C §6.2 are:
#   (CE, low) — Z0
#   (CE, medium) — A0/A1/A11–A13, B0, CE C-phase, D0/D1, etc. (~39)
#   (CE, high) — R1, S12, T0 (T1, T3 medium/CE per B.5)
#   (EXTRACT, low) — M0-M6
#   (EXTRACT, medium) — A2-A10, B1-B3, D2/D3, E1-E6, G2/G3/G4, H2/H4-H7, T4/T5, W2-W5, X2-X4, Z1
#   (EXTRACT, high) — Z2
#   (SYNTH, high) — R0/R2-R11, S0-S11, T2
#   (SYNTH, critical) — S0/R7/T0 (hand-picked; T0 is overridden via per-step)
#   (AGG, low) — Z9
#   (AGG, medium) — *_merge_qa (~14)
_VALUE_DEFAULT: Dict[Tuple[str, str], Dict[str, List[Dict[str, Any]]]] = {
    ("CE", "low"): {
        "primary_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
        "sidefill_routes": [],
    },
    ("CE", "medium"): {
        # Phase D Change A: OpenRouter primary, direct OpenAI second.
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, cache_strategy="none"),
            _route("openai", "gpt-5.3-codex", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, cache_strategy="none"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openai", "gpt-5.3-codex", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
    },
    ("CE", "high"): {
        # Phase D Change A: same OR-primary pattern as CE/medium.
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, cache_strategy="none"),
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openrouter", "anthropic/claude-opus-4.5",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openrouter", "anthropic/claude-opus-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
    },
    ("EXTRACT", "low"): {
        "primary_routes": [
            _route("openai", "gpt-5-mini", "OPENAI_API_KEY",
                   service_tier="flex", cache_strategy="auto"),
            _route("gemini", "gemini-2.5-flash-lite", "GEMINI_API_KEY",
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5-nano", "OPENAI_API_KEY",
                   service_tier="flex", cache_strategy="auto"),
        ],
    },
    ("EXTRACT", "medium"): {
        "primary_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="flex", cache_strategy="auto"),
            _route("xai", "grok-4-fast", "XAI_API_KEY"),
            _route("gemini", "gemini-3.5-flash", "GEMINI_API_KEY",
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5-mini", "OPENAI_API_KEY",
                   service_tier="flex", cache_strategy="auto"),
        ],
    },
    ("EXTRACT", "high"): {
        # Z2 reclassified to this cell per Phase C.
        "primary_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
            _route("openrouter", "anthropic/claude-sonnet-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
        "repair_routes": [
            _route("openrouter", "anthropic/claude-opus-4.5",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
    },
    ("SYNTH", "high"): {
        # Closes audit finding F2-HIGH-1 (R/S synthesis previously misrouted
        # to bulk tier).
        "primary_routes": [
            _route("openrouter", "anthropic/claude-sonnet-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
            _route("gemini", "gemini-3.1-pro-preview", "GEMINI_API_KEY",
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openrouter", "anthropic/claude-opus-4.5",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
    },
    ("SYNTH", "critical"): {
        "primary_routes": [
            _route("openrouter", "anthropic/claude-opus-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
            _route("gemini", "gemini-3.1-pro-preview", "GEMINI_API_KEY",
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openrouter", "anthropic/claude-opus-4.7",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openai", "gpt-5.5-pro", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", cache_strategy="auto"),
        ],
    },
    ("AGG", "low"): {
        "primary_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
        "sidefill_routes": [],
    },
    ("AGG", "medium"): {
        "primary_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
        "repair_routes": [
            _route("openai", "gpt-5.4", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openrouter", "anthropic/claude-sonnet-4.5",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
        "sidefill_routes": [
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
    },
}


def _swap_primary(
    cell: Dict[str, List[Dict[str, Any]]],
    *,
    new_primary: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Return a shallow-copy of `cell` with `primary_routes` replaced.

    Used to derive economy/quality/experimental cell ladders from the
    value-default baseline + Phase C "key differences" notes.
    """
    out = {k: list(v) for k, v in cell.items()}
    out["primary_routes"] = list(new_primary)
    return out


def _build_economy_cells() -> Dict[Tuple[str, str], Dict[str, List[Dict[str, Any]]]]:
    """Economy profile per Phase C abbreviated key differences.

    Cheapest capable model per cell; flex tier across the board; aggressive
    use of openai/gpt-5.x-mini variants.
    """
    base = {k: {kk: list(vv) for kk, vv in v.items()} for k, v in _VALUE_DEFAULT.items()}
    base[("CE", "medium")] = _swap_primary(
        base[("CE", "medium")],
        new_primary=[
            _route("openai", "gpt-5.1-codex-mini", "OPENAI_API_KEY",
                   service_tier="flex", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, cache_strategy="none"),
        ],
    )
    base[("EXTRACT", "medium")] = _swap_primary(
        base[("EXTRACT", "medium")],
        new_primary=[
            _route("xai", "grok-4-fast", "XAI_API_KEY"),
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="flex", cache_strategy="auto"),
        ],
    )
    base[("SYNTH", "high")] = _swap_primary(
        base[("SYNTH", "high")],
        new_primary=[
            _route("openrouter", "anthropic/claude-haiku-4.5",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openrouter", "anthropic/claude-sonnet-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
    )
    base[("SYNTH", "critical")] = _swap_primary(
        base[("SYNTH", "critical")],
        new_primary=[
            _route("openrouter", "anthropic/claude-sonnet-4.5",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openrouter", "anthropic/claude-opus-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
    )
    base[("AGG", "medium")] = _swap_primary(
        base[("AGG", "medium")],
        new_primary=[
            _route("openai", "gpt-5-mini", "OPENAI_API_KEY",
                   service_tier="flex", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openai", "gpt-5.4-mini", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
    )
    return base


def _build_quality_cells() -> Dict[Tuple[str, str], Dict[str, List[Dict[str, Any]]]]:
    """Quality profile per Phase C abbreviated key differences.

    Premium production: priority service tier where available; Opus 4.6 (not
    4.7) per Phase D consensus on SYNTH/critical to avoid the ~1.35x opus-4.7
    tokenization tax.
    """
    base = {k: {kk: list(vv) for kk, vv in v.items()} for k, v in _VALUE_DEFAULT.items()}
    base[("CE", "medium")] = _swap_primary(
        base[("CE", "medium")],
        new_primary=[
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="priority", strict_json_schema=True,
                   cache_strategy="auto"),
            _route("openrouter", "openai/gpt-5.5", "OPENROUTER_API_KEY",
                   strict_json_schema=True, cache_strategy="none"),
        ],
    )
    base[("CE", "high")] = _swap_primary(
        base[("CE", "high")],
        new_primary=[
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="priority", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
    )
    base[("SYNTH", "high")] = _swap_primary(
        base[("SYNTH", "high")],
        new_primary=[
            _route("openrouter", "anthropic/claude-opus-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="priority", cache_strategy="auto"),
        ],
    )
    base[("SYNTH", "critical")] = _swap_primary(
        base[("SYNTH", "critical")],
        new_primary=[
            _route("openrouter", "anthropic/claude-opus-4.6",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
            _route("openai", "gpt-5.5-pro", "OPENAI_API_KEY",
                   service_tier="priority", cache_strategy="auto"),
        ],
    )
    return base


def _build_experimental_cells() -> Dict[Tuple[str, str], Dict[str, List[Dict[str, Any]]]]:
    """Experimental profile per Phase C abbreviated key differences.

    Bleed-edge frontier models; tokenization tax + preview-quality caveats
    are documented in the profile block.
    """
    base = {k: {kk: list(vv) for kk, vv in v.items()} for k, v in _VALUE_DEFAULT.items()}
    base[("CE", "medium")] = _swap_primary(
        base[("CE", "medium")],
        new_primary=[
            _route("openai", "gpt-5.5", "OPENAI_API_KEY",
                   service_tier="default", strict_json_schema=True,
                   cache_strategy="auto"),
        ],
    )
    base[("SYNTH", "high")] = _swap_primary(
        base[("SYNTH", "high")],
        new_primary=[
            _route("openrouter", "anthropic/claude-opus-4.7",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
    )
    base[("SYNTH", "critical")] = _swap_primary(
        base[("SYNTH", "critical")],
        new_primary=[
            _route("openrouter", "anthropic/claude-opus-4.7",
                   "OPENROUTER_API_KEY",
                   cache_strategy="cache_control_explicit"),
        ],
    )
    return base


def build_lane_defaults() -> Dict[str, Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]]]:
    """Return the top-level lane_defaults block.

    Shape: lane_defaults[cost_profile][lane_class][capability_tier] →
    {primary_routes, repair_routes, sidefill_routes}.
    """
    out: Dict[str, Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]]] = {}
    builders = {
        "economy": _build_economy_cells(),
        "value-default": {k: {kk: list(vv) for kk, vv in v.items()} for k, v in _VALUE_DEFAULT.items()},
        "quality": _build_quality_cells(),
        "experimental": _build_experimental_cells(),
    }
    for profile in COST_PROFILE_ORDER:
        cells = builders[profile]
        profile_block: Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]] = {}
        for lane in LANE_CLASS_ORDER:
            tier_block: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
            for tier in CAPABILITY_TIER_ORDER:
                cell = cells.get((lane, tier))
                if cell is None:
                    continue
                tier_block[tier] = {
                    stage: [_canonical_route(r) for r in cell.get(stage, [])]
                    for stage in STAGE_ORDER
                }
            if tier_block:
                profile_block[lane] = tier_block
        out[profile] = profile_block
    return out


# ---------------------------------------------------------------------------
# Per-step override routes (hand-curated, preserved verbatim across runs)
# ---------------------------------------------------------------------------

# These are the 6 OVERRIDE_STEPS entries' per-step *_routes. Sourced from
# v2 model_map.yaml. Re-running the migration on v3 yaml preserves these
# byte-equal because they are emitted from this in-script reference.
OVERRIDE_ROUTES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "Z0": {
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "repair_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "sidefill_routes": [],
    },
    "C10": {
        # Phase C reclassified C10 to (SYNTH, high). The v2 routes here are
        # the BULK_CODE_HEAVY ladder retained verbatim per packet S4. A
        # future packet (E9 / F-VERIFY family) should reconcile against the
        # (SYNTH, high) cell defaults once phase_contract_map.py is updated
        # to honor lane_defaults at runtime.
        "primary_routes": [
            _route("openrouter", "anthropic/claude-sonnet-4.6",
                   "OPENROUTER_API_KEY"),
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY"),
        ],
        "repair_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY"),
        ],
        "sidefill_routes": [
            _route("openrouter", "openai/gpt-5.4-mini", "OPENROUTER_API_KEY"),
        ],
    },
    "S12": {
        # Strict-schema CE-high; preserved from v2.
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "repair_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "sidefill_routes": [
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
    },
    "T0": {
        # Task packet factory (structural; critical). Preserved from v2.
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "repair_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "sidefill_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
    },
    "T1": {
        # Mixed-kind packet emission. Preserved from v2.
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "repair_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "sidefill_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
    },
    "T3": {
        # Batched packet generation. Preserved from v2.
        "primary_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
            _route("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "repair_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
        "sidefill_routes": [
            _route("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY",
                   strict_json_schema=True, strict_passthrough_verified=True),
        ],
    },
}

# ---------------------------------------------------------------------------
# Derivation functions
# ---------------------------------------------------------------------------


def step_sort_key(step_id: str) -> Tuple[str, int]:
    match = re.match(r"^([A-Z]+)(\d+)$", step_id)
    if not match:
        return (step_id[:1], 999999)
    return (match.group(1), int(match.group(2)))


def reasoning_depth_for_step(step_id: str) -> str:
    if step_id in REASONING_DEPTH_HIGH_STEPS:
        return "high"
    if step_id in REASONING_DEPTH_LOW_STEPS:
        return "low"
    return "medium"


def impact_class_for_step(step_id: str) -> str:
    if step_id in IMPACT_CLASS_STRUCTURAL:
        return "structural"
    if step_id in IMPACT_CLASS_SECURITY_SENSITIVE:
        return "security_sensitive"
    if step_id in IMPACT_CLASS_IMPORTANT:
        return "important"
    return "routine"


def capability_tier_for_step(step_id: str) -> str:
    """Derive capability_tier per the documented one-directional rule.

    impact_class ∈ {structural, security_sensitive} ⇒ critical
    step_id ∈ HAND_PICKED_CRITICAL_TIER ⇒ critical
    Otherwise: low/medium/high from reasoning_depth.
    """
    impact = impact_class_for_step(step_id)
    if impact in ("structural", "security_sensitive"):
        return "critical"
    if step_id in HAND_PICKED_CRITICAL_TIER:
        return "critical"
    return reasoning_depth_for_step(step_id)


def lane_class_for_step(
    step_id: str,
    *,
    v2_lane_class: str,
    phase: str,
) -> str:
    """Derive v3 lane_class from v2 lane_class + phase + reasoning_depth.

    v2 CE → v3 CE; v2 AGG → v3 AGG; v2 BULK_* → SYNTH or EXTRACT per rules.
    Explicit per-step exceptions in LANE_CLASS_EXCEPTIONS take precedence.
    """
    if step_id in LANE_CLASS_EXCEPTIONS:
        return LANE_CLASS_EXCEPTIONS[step_id]
    v2 = (v2_lane_class or "").strip().upper()
    if v2 in ("CE", "AGG"):
        return v2
    # BULK_DOCS_GENERAL / BULK_CODE_HEAVY → SYNTH or EXTRACT.
    reasoning = reasoning_depth_for_step(step_id)
    phase_upper = (phase or "").strip().upper()
    if phase_upper in ("R", "S") and reasoning == "high":
        return "SYNTH"
    return "EXTRACT"


def tags_for_step(step_id: str, *, phase: str) -> List[str]:
    """Auto-infer step tags per Phase D consensus.

    - control_plane on R0/S0/T0
    - security_sensitive on R11
    - long_context on R/S/T/Q/Z phase steps with
      partition_input_size_class=large (Q is included because its merge/QA
      steps aggregate large cross-phase inputs per B.5 §2 — the previous
      omission was inconsistent with PARTITION_INPUT_SIZE_LARGE_STEPS).
    """
    tags: List[str] = list(AUTO_TAGS_FIXED.get(step_id, []))
    phase_upper = (phase or "").strip().upper()
    if (
        phase_upper in ("R", "S", "T", "Q", "Z")
        and step_id in PARTITION_INPUT_SIZE_LARGE_STEPS
        and "long_context" not in tags
    ):
        tags.append("long_context")
    return sorted(tags)


def tag_rationale_for_step(step_id: str, tags: List[str]) -> Optional[str]:
    """Return a joined rationale for the step's tags.

    Per-step text where registered in STEP_TAG_RATIONALES; otherwise the
    tag definition's generic rationale. Multi-tag rationales are joined
    by " | " for compact yaml emission.
    """
    if not tags:
        return None
    parts: List[str] = []
    for tag in tags:
        text = STEP_TAG_RATIONALES.get((step_id, tag))
        if text is None:
            text = TAG_DEFINITIONS.get(tag, {}).get("rationale", tag)
        parts.append(f"{tag}: {text}")
    return " | ".join(parts)


def materialize_routes_for_step(
    step_id: str,
    *,
    lane_class: str,
    capability_tier: str,
    lane_defaults: Dict[str, Any],
    cost_profile: str = "value-default",
) -> Dict[str, List[Dict[str, Any]]]:
    """Return the materialized per-step routes for a non-override step.

    Looks up `lane_defaults[cost_profile][lane_class][capability_tier]`.
    Raises if the cell is not populated — fail closed per packet S9 audit.
    """
    profile_block = lane_defaults.get(cost_profile, {})
    lane_block = profile_block.get(lane_class, {})
    cell = lane_block.get(capability_tier)
    if cell is None:
        raise ValueError(
            f"materialize_routes_for_step: no lane_defaults cell for "
            f"({cost_profile!r}, {lane_class!r}, {capability_tier!r}) "
            f"required by step {step_id}"
        )
    return {stage: [_canonical_route(r) for r in cell.get(stage, [])]
            for stage in STAGE_ORDER}


# ---------------------------------------------------------------------------
# Deterministic emission
# ---------------------------------------------------------------------------


def _canonical_route(route: Dict[str, Any]) -> Dict[str, Any]:
    """Return route dict with fields in ROUTE_FIELD_ORDER (skipping unset)."""
    out: Dict[str, Any] = {}
    for field in ROUTE_FIELD_ORDER:
        if field in route:
            out[field] = route[field]
    # Bool defaults; never emit missing — always explicit for diff stability.
    if "strict_json_schema" not in out:
        out["strict_json_schema"] = False
    if "strict_passthrough_verified" not in out:
        out["strict_passthrough_verified"] = False
    return out


def _canonical_step(
    *,
    phase: str,
    step_id: str,
    lane_class: str,
    capability_tier: str,
    impact_class: str,
    strict_schema_required_primary: bool,
    sidefill_enabled: bool,
    repair_mode: str,
    tags: List[str],
    tag_rationale: Optional[str],
    routes: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Return one step dict with fields in canonical order."""
    step: Dict[str, Any] = {
        "phase": phase,
        "step_id": step_id,
        "lane_class": lane_class,
        "capability_tier": capability_tier,
        "impact_class": impact_class,
        "strict_schema_required_primary": bool(strict_schema_required_primary),
        "sidefill_enabled": bool(sidefill_enabled),
        "repair_mode": repair_mode,
    }
    if tags:
        step["tags"] = list(tags)
        if tag_rationale:
            step["tag_rationale"] = tag_rationale
    for stage in STAGE_ORDER:
        step[stage] = list(routes.get(stage, []))
    return step


class _CanonicalDumper(yaml.SafeDumper):
    """SafeDumper with stable output ordering + indent.

    PyYAML's default safe_dump emits container content with implicit flow
    style for short sequences and inconsistent key ordering. The custom
    Dumper enforces block style throughout and respects insertion order.
    """


def _represent_dict_preserve_order(dumper: yaml.Dumper, data: Dict[Any, Any]) -> Any:
    return dumper.represent_mapping(
        "tag:yaml.org,2002:map", list(data.items()), flow_style=False
    )


def _represent_list_block_style(dumper: yaml.Dumper, data: List[Any]) -> Any:
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq", data, flow_style=False
    )


_CanonicalDumper.add_representer(dict, _represent_dict_preserve_order)
_CanonicalDumper.add_representer(list, _represent_list_block_style)


def emit_v3_yaml(payload: Dict[str, Any]) -> str:
    """Serialize the v3 doc deterministically."""
    return yaml.dump(
        payload,
        Dumper=_CanonicalDumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
        width=10000,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Migration orchestrator
# ---------------------------------------------------------------------------


def migrate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build the v3 model_map payload from v2 (or v3) input.

    Reads only {phase, step_id, strict_schema_required_primary,
    sidefill_enabled, repair_mode, lane_class} per step. All other fields
    are derived from this script's reference tables. Idempotent.
    """
    steps_in = payload.get("steps")
    if not isinstance(steps_in, list):
        raise ValueError("Input model_map.yaml must contain a list at `steps`.")
    seen_ids: Set[str] = set()
    canonical_steps: List[Dict[str, Any]] = []
    lane_defaults = build_lane_defaults()

    for row in steps_in:
        if not isinstance(row, dict):
            raise ValueError(f"Each step entry must be a mapping; got {type(row).__name__}.")
        step_id = str(row.get("step_id") or "").strip().upper()
        phase = str(row.get("phase") or "").strip().upper()
        if not step_id or not phase:
            raise ValueError(
                f"Step entry missing phase/step_id: {row!r}. Migration fails "
                "closed rather than silently dropping a step."
            )
        if step_id in seen_ids:
            raise ValueError(
                f"Duplicate step_id {step_id} in input. Migration requires "
                "unique step IDs."
            )
        seen_ids.add(step_id)

        v2_lane_class = str(row.get("lane_class") or "").strip().upper()
        lane_class = lane_class_for_step(
            step_id, v2_lane_class=v2_lane_class, phase=phase
        )
        capability_tier = capability_tier_for_step(step_id)
        impact_class = impact_class_for_step(step_id)
        tags = tags_for_step(step_id, phase=phase)
        rationale = tag_rationale_for_step(step_id, tags)

        if step_id in OVERRIDE_STEPS:
            routes = {
                stage: [_canonical_route(r) for r in OVERRIDE_ROUTES[step_id].get(stage, [])]
                for stage in STAGE_ORDER
            }
        else:
            routes = materialize_routes_for_step(
                step_id,
                lane_class=lane_class,
                capability_tier=capability_tier,
                lane_defaults=lane_defaults,
            )

        # repair_mode + sidefill_enabled + strict_schema_required_primary are
        # operational flags that come from the input yaml (unchanged from v2).
        # Defaults align with v2 semantics if input is missing them.
        canonical_steps.append(_canonical_step(
            phase=phase,
            step_id=step_id,
            lane_class=lane_class,
            capability_tier=capability_tier,
            impact_class=impact_class,
            strict_schema_required_primary=bool(
                row.get("strict_schema_required_primary", False)
            ),
            sidefill_enabled=bool(row.get("sidefill_enabled", False)),
            repair_mode=str(row.get("repair_mode") or "targeted_only").strip(),
            tags=tags,
            tag_rationale=rationale,
            routes=routes,
        ))

    # Step count guard: any silent drop is a migration bug.
    if len(canonical_steps) != len(steps_in):
        raise RuntimeError(
            f"Step count mismatch after derivation: input={len(steps_in)} "
            f"output={len(canonical_steps)}."
        )

    # Sort steps by canonical step_sort_key (alphabetic phase, numeric step).
    canonical_steps.sort(key=lambda s: step_sort_key(str(s["step_id"])))

    # Audit gate: impact_class structural/security_sensitive ⇒ critical;
    # 8-tag enum bound; tag_rationale required on tagged steps; openrouter
    # strict routes must carry strict_passthrough_verified=True (the v5
    # runtime fails closed at run_extraction_v5.py:5367 otherwise — the
    # _route() auto-default makes this hold for non-override steps; the
    # explicit check below catches override-step drift).
    audit_failures = []
    for step in canonical_steps:
        impact = step.get("impact_class")
        tier = step.get("capability_tier")
        if impact in ("structural", "security_sensitive") and tier != "critical":
            audit_failures.append(
                f"{step['step_id']}: impact_class={impact} requires "
                f"capability_tier=critical (got {tier!r})"
            )
        for tag in step.get("tags", []) or []:
            if tag not in TAG_ENUM_ORDER:
                audit_failures.append(
                    f"{step['step_id']}: tag {tag!r} is not in the 8-tag enum "
                    f"{TAG_ENUM_ORDER}."
                )
        if step.get("tags") and not step.get("tag_rationale"):
            audit_failures.append(
                f"{step['step_id']}: tagged step requires tag_rationale."
            )
        for stage in STAGE_ORDER:
            for route in step.get(stage, []) or []:
                if (
                    str(route.get("provider", "")).lower() == "openrouter"
                    and bool(route.get("strict_json_schema"))
                    and not bool(route.get("strict_passthrough_verified"))
                ):
                    audit_failures.append(
                        f"{step['step_id']}.{stage}: openrouter strict route "
                        f"{route.get('model_id')!r} requires "
                        "strict_passthrough_verified=true "
                        "(v5:5367 fail-closed enforcement)."
                    )
    if audit_failures:
        joined = "\n  - ".join(audit_failures)
        raise RuntimeError(
            f"Migration audit gate failed:\n  - {joined}"
        )

    # Tag definitions in fixed enum order.
    tag_definitions = {tag: TAG_DEFINITIONS[tag] for tag in TAG_ENUM_ORDER}

    out: Dict[str, Any] = {
        "version": "3.0",
        "policy": payload.get("policy") or {
            "no_auto_transport_flips": True,
            "scope": "json_managed_only",
            "strict_required_behavior": "fail_closed",
        },
        "schema_provenance": {
            "migration_source": "scripts/migrate_model_map_v2_to_v3.py",
            "migration_packet": "TP-RTE-COSTPROFILE-E8-YAML-V3-001",
            "design_inputs": [
                "claudedocs/research/routing-design-2026-05.md (Phase C)",
                "claudedocs/research/routing-consensus-2026-05.md (Phase D)",
                "claudedocs/research/step-complexity-analysis-2026-05.md (Phase B.5)",
            ],
            "warning": (
                "lane_defaults is the canonical source of routing intent. "
                "Per-step *_routes for the 130 non-override steps are "
                "materialized expansions of lane_defaults and will be "
                "overwritten on the next migration re-run. To change routing "
                "for a non-override step, edit lane_defaults and re-run "
                "scripts/migrate_model_map_v2_to_v3.py."
            ),
            "override_steps": sorted(OVERRIDE_STEPS),
            "default_cost_profile_for_materialization": "value-default",
        },
        "lane_defaults": lane_defaults,
        "tag_definitions": tag_definitions,
        "steps": canonical_steps,
    }
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate model_map.yaml from v2 to v3. Idempotent: re-running "
            "on v3 output produces byte-equal yaml."
        )
    )
    default_input = (
        Path(__file__).resolve().parent.parent / "model_map.v2.yaml.bak"
    )
    default_output = (
        Path(__file__).resolve().parent.parent / "model_map.yaml"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input,
        help=f"Input yaml path (default: {default_input.name}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output yaml path (default: {default_output.name}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary and exit without writing.",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help=(
            "With --dry-run, print a unified diff of the proposed output "
            "against the current --output file."
        ),
    )
    return parser.parse_args(argv)


def lane_defaults_cell_count(v3_payload: Dict[str, Any]) -> int:
    lane_defaults = v3_payload.get("lane_defaults")
    if not isinstance(lane_defaults, dict):
        return 0
    total = 0
    for lanes in lane_defaults.values():
        if not isinstance(lanes, dict):
            continue
        for tiers in lanes.values():
            if isinstance(tiers, dict):
                total += len(tiers)
    return total


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    if not args.input.exists():
        print(f"ERROR: input does not exist: {args.input}", file=sys.stderr)
        return 2
    raw = args.input.read_text(encoding="utf-8")
    payload = yaml.safe_load(raw)
    if not isinstance(payload, dict):
        print(f"ERROR: input is not a yaml mapping: {args.input}", file=sys.stderr)
        return 2

    try:
        v3_payload = migrate(payload)
    except Exception as exc:
        print(f"MIGRATION FAILED: {exc}", file=sys.stderr)
        return 1

    serialized = emit_v3_yaml(v3_payload)

    print(
        f"migrate: input={args.input.name} "
        f"steps_in={len(payload.get('steps', []))} "
        f"steps_out={len(v3_payload['steps'])} "
        f"overrides={len(OVERRIDE_STEPS)} "
        f"lane_defaults_cells={lane_defaults_cell_count(v3_payload)}",
        file=sys.stderr,
    )

    if args.dry_run:
        if args.diff:
            current = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
            diff = list(difflib.unified_diff(
                current.splitlines(keepends=True),
                serialized.splitlines(keepends=True),
                fromfile=f"a/{args.output.name}",
                tofile=f"b/{args.output.name}",
            ))
            sys.stdout.writelines(diff)
        return 0

    args.output.write_text(serialized, encoding="utf-8")
    print(
        f"wrote {args.output} ({len(serialized.encode('utf-8'))} bytes)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
