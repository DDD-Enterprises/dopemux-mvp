---
id: REPORT
title: Report
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Report (explanation) for dopemux documentation and developer workflows.
---
# REPORT.md — RTE-OPUS-UIUX-CLAUDE-DESIGN-AUDIT-001

**Executive summary, scope, evidence map, verdict.**

## 1. What this is

A read-only, source-grounded UI/UX + Claude/design audit of the Repo Truth Extractor (RTE), conducted at HEAD `a234f798947d51915b2adea3e0bc5a2917ac595b` on branch `claude/youthful-neumann-b94cc0` of `dopemux-mvp`. The audit is *not* a remediation packet; it does not edit source, prompts, schemas, or any Claude/governance file. It produces seven deliverables under `out/rte-opus-uiux-claude-design-audit/`.

This audit was scoped by the user as a **fresh independent pass** (no cross-referencing of prior P0–P5 finding IDs) with **balanced weighting** across five evaluation areas: operator CLI, proof/dashboard/risk surfaces, Claude/design adjacency, terminal ergonomics, and error states.

## 2. The two questions

The audit's primary and secondary questions, with one-line answers:

- **Primary — Does RTE expose a coherent, safe, understandable, low-friction operator experience across CLI commands, doctor/preflight/status/reporting, proof artifacts, error states, and agent-facing design/Claude guidance?**
  **Answer:** Partly. The *runtime* is rigorous (belt-and-suspenders consent gates, honest pricing fallback, comprehensive redaction, hard-coded honest risk-dashboard labels, runtime-enforced authority ranks in `lib/proof_contract.py`). The *operator-facing surface around the runtime* — Click help text, voice register, emoji density, error message shape, Claude-targeted guidance, conflicting truth orders — undercuts the safety contract the runtime works to keep.
- **Secondary — Do Claude/design-related files accurately support RTE operation without overclaiming authority, encouraging unsafe automation, or muddying the line between runtime truth, generated proof, design intent, and live provider behavior?**
  **Answer:** Generally yes on the *authority bounding* (AGENTS.md §6 line 81 correctly scopes RTE outputs as evidence, `lib/proof_contract.py` operationalises authority ranks, generated artifacts carry an `authority_boundary` field). The gap is on *coverage*: no Claude-targeted file teaches RTE-specific safety invariants, and three competing truth-order documents make it ambiguous which one wins for a given task.

## 3. Top findings (3 CRIT, 6 HIGH)

The CRIT-tier findings are the audit's core takeaway:

- **`F-OPUS-CRIT-1` — CLI surface broadly violates `brand-voice-guidelines.md §2A`.** Click docstrings across `rte run/doctor/status/preflight/scan/promptset/list/trace` use thematic prose ("Ignite Pipeline", "Ritual Apothecary", "Catalog Phases", "Pre-Ignition Check", "Ritual Integrity", "Engages the high-fidelity extraction engines") that maps directly to the §2A ❌ examples ("Your workflow is now supercharged"). The brand-voice contract is the *production* spec for operator-facing surfaces and is lint-enforced for a subset of files — but Click help text appears to be outside that subset.
- **`F-OPUS-CRIT-2` — Three truth-order documents disagree.** `AGENTS.md §2` ranks Task Packets first; `README.md §5` doesn't mention Task Packets and groups governance docs at tier 3; `brand-voice-guidelines.md §9` has a third order specifically for voice. The audit packet itself introduces a fourth. Operators and Claude agents reading any single source form different mental models of which wins.
- **`F-OPUS-CRIT-3` — No `.claude/CLAUDE.md` variant teaches Claude how to operate RTE safely.** Four `CLAUDE.md` files exist (root, `.claude/`, `services/.claude/`, `src/.claude/`), all generic Dopemux platform guidance. Zero mention `DPMX_LIVE_OK`, `--execute`, RTE consent gates, spend caps, redaction obligations, or the `first-live` preset. `services/.claude/CLAUDE.md`'s Key Services table even omits `repo-truth-extractor` entirely.

The six HIGH-tier findings address: emoji whitelist overrun, conflicting `docs/ux/` style guides, empty `terminal-rendering-guide.md` stub, `dopemux rte promptset audit` being v4-only, pre-live validator NO_GO error shape, and 30+-option `--help` with no progressive disclosure. See `FINDINGS_LEDGER.md` for full evidence.

## 4. What the audit affirms (positive observations)

The audit found multiple positive signals that should not be regressed:

- **Belt-and-suspenders consent gates** (`F-OPUS-OBS-4`). `dopemux rte scan` requires `--allow-legacy-v3-scan` AND `--execute` AND `DPMX_LIVE_OK=1`. `enforce_live_operation_consent` checks for both `--execute` AND env var. `enforce_pre_live_validator_for_execution` then runs a subprocess validator. Four independent fail-closed layers.
- **Honest pricing fallback** (`F-OPUS-OBS-3`). `lib/spend_ledger.py:11-16` is explicit that pricing authority is incomplete; the fallback uses MAX-of-known rates and records `pricing_status: UNPRICED_UNKNOWN`. Operators are never lied to about cost.
- **Honest risk-dashboard self-labeling** (`F-OPUS-OBS-2`). `live_use_readiness: "READY_FOR_LIMITED_DRY_STATIC_USE"` is hard-coded with an in-file comment explaining the choice — the dashboard does not pretend to compute live readiness from runtime state.
- **Authority ranks operationalised in code** (`F-OPUS-OBS-7`). `lib/proof_contract.py:119-127` carries `_AUTHORITY_RANK` into the proof bundle as a literal string field — generated artifacts cannot be confused with runtime truth because they carry their own non-authority label.
- **Comprehensive output redaction** (`F-OPUS-OBS-5`). `output_safety.py` covers OAuth bearers, JWT, AWS keys, GitHub/GitLab PATs, Google API keys, private-key blocks, plus defense-in-depth long-token-candidate redaction in `sanitize_text_for_provider_payload`.
- **README cost-incident anchor** (`F-OPUS-OBS-6`). `services/repo-truth-extractor/README.md:262-264` quotes a specific incident — "$10 in March 2026" — that is exactly the operator-anchored warning style the audit framework values.
- **`is_read_only_introspection_mode` cleanly enumerates safe paths** (`F-OPUS-OBS-8`). 11 introspection flags listed in one place; `should_enforce_pre_live_validator` reuses the same list.
- **Comparison lane is non-blocking** (`F-OPUS-OBS-12`). Outputs go to a separate tree; canonical run is unaffected by comparison failures.
- **`first-live` preset codifies conservative defaults** (`F-OPUS-OBS-11`). `--routing-policy cost`, `--max-cost-usd 5.0`, `--partition-workers 1`, `--no-batch`.

## 5. Evidence map (where to verify each claim)

| Section | Key files |
|---------|-----------|
| Section 1 (CLI) | `src/dopemux/cli.py:4830-5570`, `src/dopemux/commands/extractor_commands.py:1-523` |
| Section 2 (proof/risk/spend) | `services/repo-truth-extractor/lib/proof_contract.py`, `lib/risk_dashboard.py`, `lib/spend_ledger.py`, `output_safety.py`, `reporting.py`, `run_extraction_v5.py:2780-3130` |
| Section 3 (Claude/design) | `AGENTS.md`, `.claude/CLAUDE.md`, `services/.claude/CLAUDE.md`, `src/.claude/CLAUDE.md`, `.claude/brand-voice-guidelines.md`, `docs/ux/ux-style-guide.md`, `docs/ux/terminal-rendering-guide.md`, `docs/04-explanation/branding/cli-ux-design-spec.md`, `docs/05-audit-reports/cockpit-*.md`, `services/repo-truth-extractor/README.md`, `README.md`, `ARCHITECTURE.md` |
| Section 4 (terminal ergonomics) | derived from Section 1 (help-text scan) + Section 3 (brand-voice/style cross-check) |
| Section 5 (error states) | `src/dopemux/cli.py:4909-4931, 5495-5500`, `src/dopemux/commands/extractor_commands.py:111-118, 291-293, 339-341`, `services/repo-truth-extractor/run_extraction_v5.py:2992-3076`, `services/repo-truth-extractor/validate_pre_live_gate_v25.py:101-162`, `output_safety.py:98` |

## 6. Verdict

**For operator daily use of the runtime:** the safety surface is in good shape. The consent gates, redaction, validator subprocess, spend ledger, risk dashboard, and proof contract are rigorous, honest, and consistent with each other. An operator following the `services/repo-truth-extractor/README.md` and using `--preset first-live` has a coherent safe-onboarding path. This audit does not recommend gating RTE runtime use behind any of the findings below.

**For operator-experience around the runtime:** there is meaningful drift. CLI help text reads like marketing copy in a brand-voice contract that explicitly bans marketing copy. The visual UX layer has two competing prescriptions in `docs/ux/`. The pre-live validator NO_GO error — the most consequential error path — does not match the prescribed `error_panel(problem, why, fix)` shape. Operators get the *behavior* the runtime promises but the *framing* the runtime would otherwise reject.

**For Claude/agent-assisted RTE work:** there is a coverage gap. Four `CLAUDE.md` files exist and none of them mentions `DPMX_LIVE_OK`, `--execute`, or the consent-gate code paths. An agent acting on RTE must derive these invariants from runtime code; that derivation works for a careful agent and breaks for an impatient one. Closing this gap (`R-OPUS-3`) is the single most impactful change available.

**For Claude/design authority hygiene:** the runtime authority bound is solid (AGENTS.md §6 line 81, `lib/proof_contract.py:119-127`). The cross-document truth-order conflict (CRIT-2) is the largest *latent* risk — it has not produced a known incident, but it will the first time two valid documents disagree on a decision that matters.

## 7. Counts

| Severity | Count |
|----------|------:|
| CRIT     | 3 |
| HIGH     | 6 |
| MED      | 7 |
| LOW      | 3 |
| OBS      | 13 (including 1 negative meta-finding about audit hygiene and 12 substantive observations of which 9 are positive) |
| **Total** | **32** |

Plus 19 recommendations across CRIT/HIGH/MED/LOW tiers in `RECOMMENDATIONS.md`.

## 8. Deliverable index

| File | Purpose |
|------|---------|
| [`REPORT.md`](report.md) | This file. Executive summary, scope, evidence map, verdict. |
| [`FINDINGS_LEDGER.md`](findings-ledger.md) | Every finding with ID, severity, label, evidence (`file:line`), authority tier, recommendation reference. |
| [`FINDINGS_LEDGER.json`](FINDINGS_LEDGER.json) | Machine-readable mirror of the ledger. |
| [`CLAUDE_DESIGN_COMPATIBILITY.md`](claude-design-compatibility.md) | Per-file compatibility ledger for every Claude/design-adjacent artifact. |
| [`UX_RISK_LEDGER.md`](ux-risk-ledger.md) | 14 prioritized operator-UX risks (separate from findings). |
| [`RECOMMENDATIONS.md`](recommendations.md) | 19 `RECOMMENDED` items, ordered. Strictly separated from observed findings. |
| [`METHODOLOGY.md`](methodology.md) | How the audit was conducted, files inspected, decision rules, reproducibility. |

## 9. What this audit did not do (reaffirming the hard non-goals)

- No edits to source, prompts, promptsets, schemas, or `CLAUDE.md`.
- No implementation packets, no code patches, no UI mockups.
- No live extraction. No provider preflight. No provider API calls. No batch operations.
- No PRs / merges / pushes.
- No claims about live provider behavior.
- No collapsing RTE into broader Dopemux authority.
- No cross-referencing of P0–P5 finding IDs.

## 10. Reading order for consumers

- **Operators who just want to use RTE safely:** read `services/repo-truth-extractor/README.md` first; this audit's findings do not change the runtime behavior they rely on.
- **A maintainer prioritizing fixes:** start with `RECOMMENDATIONS.md` §"Suggested execution order"; the first four items (R-OPUS-2, 3, 14, 1, 4, 8) cover the highest-impact paths.
- **A Claude/Codex agent assigned an RTE task:** read `CLAUDE_DESIGN_COMPATIBILITY.md` §"What this means for Claude/agents" first; then read the runtime files cited there.
- **An auditor verifying these findings:** read `METHODOLOGY.md` and re-check `FINDINGS_LEDGER.md` against current HEAD.

End of REPORT.md.
