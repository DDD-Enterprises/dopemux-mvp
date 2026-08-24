"""Shared constants for Repo Truth Extractor (RTE) CLI surfaces.

Both `src/dopemux/cli.py` (the canonical `dopemux rte ...` entrypoint, see
TP-RTE-TRUTH-R4-002 / F-42) and `src/dopemux/commands/audit_commands.py`
(`dopemux audit wizard`, mounted as `rte.add_command(audit.commands["wizard"],
"wizard")`) need the same `--routing-policy` choice set. Before
TP-RTE-TRUTH-R4-004 (F-43) each module carried its own copy of the literal
list -- identical in practice, but with no structural guarantee they would
stay that way. This module is the single place that list is spelled out, so
both surfaces import the same object instead of maintaining independent
literals.

This module MUST NOT import from `..cli` or `.audit_commands` -- cli.py
imports `audit_commands.audit` at module load time
(`from .commands.audit_commands import audit`), so a reverse import here
would be circular. Keep this file free of any import beyond the stdlib.
"""

from __future__ import annotations

from typing import List

# Canonical routing-policy choices for every RTE surface that exposes
# `--routing-policy` as a `click.Choice` (rte run, rte preflight,
# rte validate-live, audit wizard). Sourced from run_extraction_v5.py's
# ROUTING_LADDERS keys; extend here (not per-callsite) if v5 gains a new
# named policy.
ROUTING_POLICY_CHOICES: List[str] = [
    "cost",
    "balanced",
    "balanced_openrouter",
    "balanced_grok_openrouter",
    "quality",
    "openrouter",
    "gemini_primary",
    "optimal",
]
