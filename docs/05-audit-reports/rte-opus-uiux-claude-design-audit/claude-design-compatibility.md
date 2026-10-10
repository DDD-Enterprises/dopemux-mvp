---
id: CLAUDE_DESIGN_COMPATIBILITY
title: Claude Design Compatibility
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Claude Design Compatibility (explanation) for dopemux documentation and developer
  workflows.
---
# CLAUDE_DESIGN_COMPATIBILITY.md

Per-file compatibility ledger for every Claude/design-adjacent artifact that affects how humans or LLM agents interact with RTE.

**Columns**
- **Path** — file location relative to repo root.
- **Declared authority** — what the file claims to be (frontmatter `type:`, in-file prose, or implicit by location).
- **Observed authority tier** — where it lands under the audit's authority order (1=runtime, 2=runtime writers, 3=AGENTS/governance, 4=TRUTH/SYSTEM, 5=docs/design/Claude, 6=historical).
- **Drift** — is what the file declares consistent with what runtime/governance actually says?
- **Claude-Design safety** — is this file safe to feed to Claude Design or an automation agent as authoritative? Values: `runtime-safe`, `governance-safe`, `evidence-only`, `not-for-implementation`, `non-authoritative`, `stub`.
- **Risk class** — `low` / `medium` / `high` based on operator/agent confusion potential.
- **Finding refs** — IDs from FINDINGS_LEDGER.md.

---

| Path | Declared authority | Observed tier | Drift | Claude-Design safety | Risk class | Finding refs |
|------|---------------------|---------------|-------|----------------------|------------|--------------|
| `AGENTS.md` | governance / agent runtime guidance | 3 | self-consistent; truth order at §2 differs from README.md and brand-voice-guidelines.md | governance-safe (within its own scope) | high | F-OPUS-CRIT-2 |
| `README.md` | governance / project overview | 3 | truth order at §5 omits Task Packets that AGENTS.md §2 puts first | governance-safe (operator-facing); not authoritative against runtime | high | F-OPUS-CRIT-2 |
| `ARCHITECTURE.md` | governance / observed-runtime architecture | 3 | §5.5 still names `dopemux upgrades` as operator path; deprecated by README.md §4 | governance-safe with caveat | medium | F-OPUS-MED-1 |
| `.claude/CLAUDE.md` (root) | Claude operating guidance (5) | 5 | self-consistent for general Dopemux; **silent on RTE consent/`DPMX_LIVE_OK`/spend caps** | not-for-RTE-implementation | high | F-OPUS-CRIT-3 |
| `.claude/claude.md` (lowercase variant, same file on case-insensitive filesystem) | same as above | 5 | same | same | high | F-OPUS-CRIT-3 |
| `services/.claude/CLAUDE.md` | Claude services-tree guidance (5) | 5 | Key Services table omits `repo-truth-extractor`; service tree omits it | not-for-RTE-implementation | high | F-OPUS-CRIT-3, F-OPUS-MED-5 |
| `src/.claude/CLAUDE.md` | Claude source-code guidance (5) | 5 | mentions `extractor_commands.py` exports but not RTE consent invariants | not-for-RTE-implementation | medium | F-OPUS-CRIT-3 |
| `.claude/brand-voice-guidelines.md` | reference / lint-enforced brand voice (5 escalating to runtime via `brand_lint.py`) | 5 + runtime-enforced subset | self-consistent; §9 decision ladder differs from AGENTS.md §2 and README.md §5 | governance-safe; lint-enforced for code, advisory for prose | medium | F-OPUS-CRIT-1, F-OPUS-CRIT-2, F-OPUS-HIGH-1, F-OPUS-HIGH-5 |
| `CLAUDE_AUTOMATION_INSTRUCTIONS.md` | reference / batch-prompt-rewrite harness instructions | 5 | not RTE operator guidance despite name suggesting Claude+RTE alignment | not-for-implementation | low | — |
| `docs/ux/ux-style-guide.md` | explanation / self-demoted | 5 | body prescribes a palette ("Spaceage Operationalism", green/red/yellow/blue chips) directly contradicting `cli-ux-design-spec.md` ("Neon Mint", mint/pink/violet) | non-authoritative (explicitly demoted) | high | F-OPUS-HIGH-2 |
| `docs/ux/terminal-rendering-guide.md` | explanation | 5 | empty stub (296 bytes, frontmatter only); referenced indirectly by brand-voice §4 | stub | medium | F-OPUS-HIGH-3 |
| `docs/04-explanation/branding/cli-ux-design-spec.md` | explanation; marked "single source of truth for all CLI/TUI output styling" | 5 (claims runtime-spec but not runtime-enforced beyond `theme.py`) | self-consistent within its own scope; aligned with `brand-voice-guidelines.md` §4 | governance-safe (visual layer) | low | F-OPUS-HIGH-1, F-OPUS-HIGH-2, F-OPUS-HIGH-6 |
| `docs/03-reference/brand-compliance-checklist.md` | reference / release gate | 5 | (not deeply inspected here; brand-voice §9.6 places it at tier 6 of its own decision ladder, after `BRAND_SYSTEM.md`/`BRAND_VOICE_BIBLE.md`/`brand-resource-pack.md`) | governance-safe (pre-PR checklist) | low | — |
| `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md` | reference / audit report | 6 | verdict at line 17 says "evidence pack only, do not implement"; PM-cockpit-scoped, not RTE | evidence-only | medium | F-OPUS-MED-7, F-OPUS-OBS-1, F-OPUS-OBS-13 |
| `docs/05-audit-reports/cockpit-design-input-merged-brief-2026-04-24.md` | reference / design brief | 6 | input synthesis for cockpit redesign; not RTE | evidence-only | low | F-OPUS-OBS-13 |
| `docs/05-audit-reports/cockpit-pm-implementer-callable-inventory-2026-04-24.md` | reference / inventory snapshot | 6 | snapshot of MCP/HTTP/CLI surfaces at 2026-04-24 | evidence-only | low | F-OPUS-OBS-13 |
| `docs/05-audit-reports/cockpit-pm-implementer-design-brief-2026-04-24.md` | reference / design brief | 6 | PM cockpit, not RTE | evidence-only | low | F-OPUS-OBS-13 |
| `docs/05-audit-reports/cockpit-archive-intent-pack-2026-04-24.md` | reference / archive intent | 6 | not RTE | evidence-only | low | F-OPUS-OBS-13 |
| `docs/05-audit-reports/cockpit-adhd-lifestyle-feature-map-2026-04-24.md` | reference / feature map | 6 | not RTE | evidence-only | low | F-OPUS-OBS-13 |
| `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | reference / RTE audit history | 6 | not re-validated against current HEAD; treat as historical | evidence-only | low | — |
| `docs/05-audit-reports/rte-live-certification-gates.md` | reference / RTE gates documentation | 6 | not re-validated against current HEAD | evidence-only | low | — |
| `docs/05-audit-reports/rte-production-certification-audit-20260414.md` | reference / RTE production-cert audit | 6 | historical certification snapshot | evidence-only | low | — |
| `docs/05-audit-reports/rte-prelive-audit-pack-2026-04-23.md` | reference / RTE pre-live pack | 6 | historical | evidence-only | low | — |
| `docs/05-audit-reports/rte-canonical-entrypoint-implementation-2026-04-23.md` | reference / RTE entrypoint history | 6 | historical | evidence-only | low | — |
| `docs/05-audit-reports/rte-gemini-deep-pal-audit-2026-04-23.md` | reference / RTE Gemini audit | 6 | historical | evidence-only | low | — |
| `docs/05-audit-reports/rte-branch-integration-audit-2026-04-23.md` | reference / RTE branch-integration audit | 6 | historical | evidence-only | low | — |
| `proof/` (TP-RTE-\* and rte-\* `.proof.json`) | runtime-emitted proof artifacts | 2 | proof bundles correctly self-classify against `lib/proof_contract.py` authority ranks | runtime-safe-evidence | low | F-OPUS-OBS-7 |
| `services/repo-truth-extractor/README.md` | reference / service documentation | 5 (effectively runtime-companion since it documents canonical CLI) | self-consistent; includes the `$10 March 2026` incident anchor and the `COST_ABORTED` no-resume rule | governance-safe operator doc | low | F-OPUS-OBS-6, F-OPUS-OBS-11, F-OPUS-OBS-12 |
| `services/repo-truth-extractor/run_extraction_v5.py` | runtime (1) | 1 | strongest authority for RTE behavior | runtime-safe | low | F-OPUS-OBS-4, F-OPUS-OBS-8, F-OPUS-HIGH-5, F-OPUS-MED-6 |
| `services/repo-truth-extractor/output_safety.py` | runtime (1) | 1 | strongest authority for redaction | runtime-safe | low | F-OPUS-OBS-5 |
| `services/repo-truth-extractor/rte_config.py` | runtime (1) | 1 | constants for paths, env vars, preset caps | runtime-safe | low | — |
| `services/repo-truth-extractor/lib/proof_contract.py` | runtime (1) | 1 | authoritative authority-rank classifier for proof bundles | runtime-safe | low | F-OPUS-OBS-7 |
| `services/repo-truth-extractor/lib/risk_dashboard.py` | runtime (1) | 1 | runtime writer for risk dashboard | runtime-safe | low | F-OPUS-OBS-2 |
| `services/repo-truth-extractor/lib/spend_ledger.py` | runtime (1) | 1 | runtime writer for spend ledger | runtime-safe | low | F-OPUS-OBS-3 |
| `services/repo-truth-extractor/validate_pre_live_gate_v25.py` | runtime (1) | 1 | fail-closed pre-live validator subprocess | runtime-safe | low | — |
| `services/repo-truth-extractor/reporting.py` | runtime (1) | 1 | runtime writer for step metrics, failure index, run dashboard | runtime-safe | low | — |
| `src/dopemux/cli.py` (RTE region 4859–5539) | runtime (1) | 1 | strongest authority for CLI surface | runtime-safe (but violates brand-voice in help text) | medium | F-OPUS-CRIT-1, F-OPUS-HIGH-1, F-OPUS-HIGH-4, F-OPUS-HIGH-6, F-OPUS-MED-2, F-OPUS-MED-4, F-OPUS-MED-6, F-OPUS-LOW-1, F-OPUS-LOW-3 |
| `src/dopemux/commands/extractor_commands.py` | runtime (1) | 1 | legacy promptset/prescan tooling with deprecation echo | runtime-safe | low | F-OPUS-MED-3, F-OPUS-OBS-10 |
| `task-packets/` (authored) | reference / work-instruction | 5 | per AGENTS.md §2.1, *active* Task Packets are tier-1 for the slice they cover; inactive Task Packets are tier-5 evidence | varies | medium | F-OPUS-CRIT-2 |
| `task-packets/generated/` | generated artifacts | 6 | generated, not authored | evidence-only | medium | F-OPUS-CRIT-2 |
| `docs/03-reference/Dopemux Cockpit TUI Design System/` (HTML/CSS spec) | design system spec | 5 | not deeply inspected; treat as design-intent only | governance-safe (visual layer) | low | — |
| `docs/flight_deck/operator-signoff-rules.md` | governance / tactical approval | 3 | (not deeply inspected) | governance-safe | low | — |
| `docs/governance/handoff-contract.md` | governance / PM transition authority | 3 | (not deeply inspected) | governance-safe | low | — |
| `docs/pr_prep/operator-contract.md` | governance / PR operator rules | 3 | (not deeply inspected) | governance-safe | low | — |
| `docs/pr_prep/high-risk-handoff-rules.md` | governance / risk escalation | 3 | (not deeply inspected) | governance-safe | low | — |
| `docs/rollout/operator-onboarding.md` | operator doc | 5 | (not deeply inspected) | governance-safe | low | — |
| `docs/arbitration/operator-supervision-guide.md` | operator doc | 5 | (not deeply inspected) | governance-safe | low | — |
| `docs/arbitration/operator-review-checklist.md` | operator doc | 5 | (not deeply inspected) | governance-safe | low | — |

---

## Drift summary by class

**Authority-tier conflicts (high-risk):**
- Truth-order conflict across `AGENTS.md`, `README.md`, `brand-voice-guidelines.md` §9, and this audit packet. (`F-OPUS-CRIT-2`)
- `dopemux upgrades` named as operator path in `ARCHITECTURE.md` despite README.md deprecating it. (`F-OPUS-MED-1`)
- `docs/ux/ux-style-guide.md` self-demotes but body prescribes incompatible palette. (`F-OPUS-HIGH-2`)

**RTE-specific guidance gaps (high-risk for agents):**
- Zero RTE consent/spend/redaction guidance in any `.claude/CLAUDE.md` variant. (`F-OPUS-CRIT-3`)
- `services/.claude/CLAUDE.md` Key Services table omits RTE. (`F-OPUS-MED-5`)
- No cockpit audit report scopes RTE specifically. (`F-OPUS-OBS-13`)

**Stub or empty content (medium-risk):**
- `docs/ux/terminal-rendering-guide.md` is frontmatter-only. (`F-OPUS-HIGH-3`)

**Positive observations (do not change):**
- `lib/proof_contract.py` carries the authority-rank model into the proof bundle itself. (`F-OPUS-OBS-7`)
- `risk_dashboard.py` self-tags `READY_FOR_LIMITED_DRY_STATIC_USE` honestly. (`F-OPUS-OBS-2`)
- `spend_ledger.py` is honest about pricing fallback. (`F-OPUS-OBS-3`)
- `output_safety.py` redaction patterns are comprehensive. (`F-OPUS-OBS-5`)
- `services/repo-truth-extractor/README.md` "$10 March 2026" incident anchor is exemplary. (`F-OPUS-OBS-6`)
- Comparison lane never overwrites canonical outputs. (`F-OPUS-OBS-12`)

---

## What this means for Claude/agents

For an LLM agent (Claude, Codex, or otherwise) being asked to *work on* RTE:

1. **Runtime authority wins.** `services/repo-truth-extractor/run_extraction_v5.py` and adjacent runtime files are tier 1. Anything else is evidence, not law.
2. **No `.claude/CLAUDE.md` variant teaches RTE invariants.** Agents must read AGENTS.md §6 (line 81 — "Repo Truth Extractor audits and extracts repo truth only; its outputs are evidence artifacts, not runtime truth") and the runtime consent gates in `run_extraction_v5.py:2880-3076` directly.
3. **Three different truth orders exist.** Until reconciled (F-OPUS-CRIT-2), agents should prefer the order most specific to their task: brand work → `brand-voice-guidelines.md` §9; PM/architecture work → `AGENTS.md` §2; operator-doc work → `README.md` §5.
4. **Cockpit audit reports are evidence packets, not specifications.** All six 2026-04-24 cockpit reports cover PM cockpit, not RTE. Their "do not implement from this packet" caveat is prose at the head of each file, not a structured frontmatter flag.
5. **Generated `.proof.json` artifacts never outrank runtime.** This is operationalised in `lib/proof_contract.py:119-127` as `_AUTHORITY_RANK`. Agents using proof bundles as evidence should preserve the `authority_boundary` field unchanged.

End of CLAUDE_DESIGN_COMPATIBILITY.md.
