---
id: orchestrator-ui-index
title: UI Dashboard Reference
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference for UI Dashboard and Cockpit panel integration inside Task Orchestrator.
related_packets:
  - TP-DMX-ORCH-015
  - TP-DMX-ORCH-015-TUI
---

# UI Dashboard & Cockpit Integration

The orchestrator daily planning and tracking data is surfaced dynamically through CLI-rendered TUIs and dashboard frames.

## TUI Framework Selection

We select **Textual** (v6.2.1) as the standard, premium terminal user interface (TUI) framework. Textual provides a modern, fast, asynchronous component model with rich reactive attributes and a clean CSS styling layer (`.tcss`), which aligns perfectly with our need for reactive, ADHD-friendly dashboard telemetry.

### Dependency Footprint
*   **Engine**: `textual >= 6.2.0` (already installed and verified in `.venv`).
*   **Styles**: Pre-styled themed panels matching the `dopemux.tcss` palette (`$base`, `$mantle`, `$crust`, `$green`, `$blue`, `$mauve`, `$red`, `$peach`, `$yellow`, `$mint-dim`).

---

## Dashboard Panels Structure

The dashboard organizes operational telemetry into eight read-only diagnostic panels:

1.  **Context Freshness Panel (`context`)**: Summarizes the freshness of data sources (`dope-context`, `ConPort`, `dope-memory`) and marks any dirty or stale caches.
2.  **Unblocked Queue Panel (`packets`)**: Displays the status of generated task packets (`task-packets/generated/*.json`), classifying them as valid, invalid, or draft.
3.  **PR Readiness Grid (`pr_queue`)**: Automatically inspects PR build checks, reviews, and proof attachments to categorize them into action lanes.
4.  **Proof Verification Panel (`proof`)**: Audits compiled `PROOF.json` envelopes and confirms attestation verdicts.
5.  **Risks & Threats Panel (`risks`)**: Surfaces active security/capability tiers that carry elevated risk (e.g. `TX`, `TU`, `T6`).
6.  **Authority & Writer Policies (`authority`)**: Lists registered capabilities and maps them to their respective writer tiers.
7.  **Refusal Matrix (`do_not_touch`)**: Displays prohibited/fail-closed states to prevent accidental double-writes or dangerous bypasses.
8.  **General Snapshot Panel (`today`)**: Provides a unified overview of the operator's daily planning matrix.
