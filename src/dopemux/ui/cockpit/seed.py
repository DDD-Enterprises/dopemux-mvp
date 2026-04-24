"""Authoritative deterministic seed for static cockpit snapshots."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SEED_DATA: dict[str, Any] = {
    "version": "1.0",
    "generated_at": "2026-04-23T00:00:00Z",
    "note": "Deterministic seed data for static renderer only. Values are illustrative, not runtime truth.",
    "workspace": {"id": "dopemux-mvp", "instance": "local", "SRC": "dopemux"},
    "top_level_modes": ["PM", "Implementer", "Overview", "Services", "Events"],
    "placeholder_modes": {
        "PM": {
            "authority": "conport+leantime",
            "status_chip": "EDGE",
            "message": "[EDGE] placeholder mode. UNKNOWN: PM renderer not wired in slice 1. NEXT: implement PM mode.",
        },
        "Implementer": {
            "authority": "task-orchestrator+dope-context",
            "status_chip": "EDGE",
            "message": "[EDGE] placeholder mode. UNKNOWN: Implementer renderer not wired in slice 1. NEXT: implement focus and retrieval panes.",
        },
        "Overview": {
            "authority": "dopemux",
            "status_chip": "EDGE",
            "message": "[EDGE] placeholder mode. UNKNOWN: Overview renderer not wired in slice 1. NEXT: implement rollup view.",
        },
        "Events": {
            "authority": "split-per-event",
            "status_chip": "EDGE",
            "message": "[EDGE] placeholder mode. UNKNOWN: Events renderer not wired in slice 1. NEXT: implement per-event SRC stream.",
        },
    },
    "services": {
        "authority": "dopemux",
        "selected": "repo-truth-extractor",
        "rows": [
            {"name": "dopemux", "status": "LIVE", "kind": "control", "summary": "operator control surface", "SRC": "dopemux"},
            {"name": "task-orchestrator", "status": "LIVE", "kind": "workflow", "summary": "workflow transitions", "SRC": "task-orchestrator"},
            {"name": "conport", "status": "LIVE", "kind": "structured", "summary": "decisions progress context", "SRC": "conport"},
            {"name": "dope-memory", "status": "LOGGED", "kind": "chronicle", "summary": "durable evidence ledger", "SRC": "dope-memory"},
            {"name": "dope-context", "status": "LOGGED", "kind": "retrieval", "summary": "code docs retrieval", "SRC": "dope-context"},
            {"name": "dopecon-bridge", "status": "OVERRIDE", "kind": "adapter", "summary": "proxy only not authority", "SRC": "dopecon-bridge"},
            {"name": "adhd-engine", "status": "LIVE", "kind": "support", "summary": "operator support state", "SRC": "adhd-engine"},
            {"name": "repo-truth-extractor", "status": "AFTERCARE", "kind": "extraction", "summary": "repo truth extraction v5", "SRC": "repo-truth-extractor"},
        ],
        "inspector": {
            "subject": "repo-truth-extractor",
            "authority": "repo-truth-extractor",
            "provenance": "EXTRACTED",
            "rows": [
                {"label": "canonical", "value": "services/repo-truth-extractor/run_extraction_v5.py", "SRC": "repo-truth-extractor"},
                {"label": "boundary", "value": "workload view not shell owner", "SRC": "dopemux"},
                {"label": "state", "value": "seed only no live run", "SRC": "repo-truth-extractor"},
            ],
            "bridge": {
                "status_chip": "EDGE",
                "footer": "[EDGE] bridge is adapter/proxy only. NEXT: prefer canonical write.",
                "actions": [
                    {"label": "ADAPTER -> dopecon-bridge : replay-event", "enabled": False, "SRC": "dopecon-bridge"}
                ],
            },
        },
    },
    "rte_child_surface": {
        "parent_mode": "Services",
        "authority": "repo-truth-extractor",
        "tabs": ["R1 Runs", "R2 Active", "R3 Prescan", "R4 Doctor", "R5 Coverage", "R6 Audit"],
        "rendered_tab": "R1 Runs",
        "runs": [
            {"run_id": "v5-2026-04-22T14:32Z-a91c", "repo": "dopemux", "branch": "main", "scope": "services", "status": "LIVE", "phase": "normalize", "providers": "anthropic openai", "duration": "00:07:41", "artifacts": 412, "alerts": 2, "SRC": "repo-truth-extractor"},
            {"run_id": "v5-2026-04-22T11:04Z-7f18", "repo": "dopemux", "branch": "main", "scope": "repo-truth-extractor", "status": "BLOCKER", "phase": "preflight", "providers": "anthropic", "duration": "00:00:22", "artifacts": 3, "alerts": 1, "SRC": "repo-truth-extractor"},
            {"run_id": "v5-2026-04-22T09:51Z-3e2a", "repo": "dopemux", "branch": "feat-bridge-auth", "scope": "dopecon-bridge", "status": "LOGGED", "phase": "verify", "providers": "anthropic openai groq", "duration": "00:19:04", "artifacts": 1284, "alerts": 1, "SRC": "repo-truth-extractor"},
            {"run_id": "v5-2026-04-21T22:48Z-1d9b", "repo": "dopemux", "branch": "main", "scope": "docs", "status": "OVERRIDE", "phase": "coverage", "providers": "anthropic", "duration": "00:11:50", "artifacts": 902, "alerts": 6, "SRC": "repo-truth-extractor"},
        ],
    },
    "status_rail": {"left": "workspace dopemux-mvp", "middle": "mode Services", "right": "seed static no-writes"},
}


def load_seed() -> dict[str, Any]:
    """Return a copy so callers cannot mutate package seed state."""

    return deepcopy(SEED_DATA)
