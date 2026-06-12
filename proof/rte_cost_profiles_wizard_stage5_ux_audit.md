# Stage 5: Validation UI and Wizard UX Audit

## 1. Rich/Plain Parity
- **Parity Status:** Mostly consistent. Both `rich` and `plain` outputs show `run_id`, `stage`, `spend`, `routing_policy`, `consent`, `why_stopped_spending`, and `blockers`.
- **Gaps:** `rich` uses a table format for blockers with actionable "Next Action" hints. `plain` only lists the raw blocker messages.

## 2. Information Visibility (Spend, Policy, Blockers)
- **Spend Clarity:** Shows estimated upper bound USD. Does not explicitly show the `--max-cost` cap compared to the estimate.
- **Provider Clarity:** Shows present API keys (`consent=... keys=...`). It does not explicitly list *missing* but *required* keys for the chosen routing ladder, except if they bubble up as blockers.
- **Policy Clarity:** Shows `routing_policy`. It does not show the `target_profile` or clarify if the displayed policy is just the validator's test target vs. the runtime's actual default.

## 3. Launch Authority vs Diagnostics
- The wizard implies launch authority ("Phase-by-phase extraction... The v5 upgrades wrapper gives the wizard explicit control"). But the wizard lacks crucial launch parameters (like `max-cost`), delegating incomplete authority.
- The validation UI (`validate-live`) accurately reports the "Safe to spend" state (`yes` or `no`), but the CLI might bypass it entirely if run without `--validate-live`.

## 4. Verdict
**PARTIAL.** The UI needs to explicitly surface `--max-cost` bounds alongside the spend estimate. The wizard must not imply it is a "safe wrapper" while omitting the spend boundary and validation gates.
