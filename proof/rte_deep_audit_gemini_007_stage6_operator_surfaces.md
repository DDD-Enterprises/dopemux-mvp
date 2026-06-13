# RTE Deep Audit Stage 6: Operator UX, UI, & CLI

## UX Safety Signaling
- **Defaults:** `--dry-run` is the default execution mode, preventing accidental spend.
- **Enforcement:** Clear, multi-step consent requirement (`--execute` + `DPMX_LIVE_OK_ENV=1`) for live runs.
- **Fail-Closed Messaging:** When the pre-live validator fails, the UI provides actionable reason codes and directs the operator to specific fix scripts.

## UI Quality
- **Rich Interface:** The TUI (`UI` class using `rich`) is high-fidelity, providing real-time progress for parallel partitions and a comprehensive `status_table` upon completion.
- **Observability:** JSONL event streaming (`--jsonl-events`) allows for external monitoring/dashboards while the operator watches the TUI.

## CLI Ergonomics & Branding
- **Ritual Branding:** Commands like `Apothecary` (doctor) and `Batch Alchemist` (batch mode) are consistent with project branding but may introduce cognitive friction for operators accustomed to standard engineering terms.
- **Alias Drift:** `dopemux upgrades` is a direct alias to `dopemux rte`. This "Split-Brain Command" approach increases the surface area for documentation drift.
- **Legacy Surfaces:** `dopemux extractor run` remains in the help tree despite being disabled, creating "Dead-End Noise" for the operator.

## Verdict
Operator UX is **High-Quality but Opaque**. The branding-heavy CLI provides excellent safety guardrails but relies on "In-Group Terminology" that might delay critical operator intervention during failures.
