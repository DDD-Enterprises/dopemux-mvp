# Upstream Serena Follow-up Plan

## Slice 1 — Monolith Decomposition (Optional/Future)
- **Objective:** Refactor local `mcp_server.py` into modular components to match upstream structure and improve maintainability.
- **Action:** Break down tools into `navigation_tools.py`, `adhd_tools.py`, and `analysis_tools.py`.

## Slice 2 — Memory System Alignment
- **Objective:** Evaluate if `SerenaAdapter` in Dopemux should be replaced or augmented by upstream's memory/embedding system.
- **Action:** Compare retrieval accuracy between local embeddings and upstream's implementation.

## Slice 3 — Contract Documentation
- **Objective:** Formally document Dopemux Serena as a read-only fork to manage operator expectations.
- **Action:** Add a `FORK_DECISION.md` or update `AGENTS.md` with the "Own the Fork" rationale.
