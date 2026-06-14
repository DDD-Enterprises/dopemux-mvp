# RTE Deep Audit Stage 4: Prescan-to-Real-Scan Integration

## Material Improvements
- **Dynamic Tiering:** Trace confirms that prescan intelligence (importance/complexity) is used to override `step_tier`. High-risk files are automatically routed to premium models (`synthesis` tier) even if the base step is `extract`.
- **Partition Contextualization:** `PartitionBriefGenerator` injects global repo insights into local partition prompts, effectively de-risking "context blindness" in deep subdirectories.
- **Fail-Fast Routing:** The `provider_readiness_matrix` built during prescan identifies unauthorized or over-quota providers *before* real-scan ignition, preventing mid-run stalls.

## Unused/Decorative Products
- **Code Graph:** `CODE_GRAPH.json` is generated but not natively consumed by the v5 extraction logic. It appears to be an observability artifact for the Dashboard.
- **Archaeology Report:** Provides excellent git context for humans but has limited impact on LLM route admission.

## Prescan-Value vs. Real-Scan-Value
- **Prescan-Value-First:** The system acts as an "Intelligence-Led Extractor" where the real-scan is merely the execution of a prescan-designed plan.
- **Real-Scan-Value-First:** The system acts as a "Deterministic Scanner" where prescan is just a hygiene pass to avoid simple errors.
- **Audit Verdict:** The implementation leans heavily toward **Prescan-Value-First**, making the `IntelligenceRouter` the true heart of the system.

## Verdict
Prescan-to-Real-Scan integration is **Material and Structural**. The system successfully uses prescan intelligence to improve cost-efficiency (via tiering) and truth-fidelity (via reordering and briefing).
