# Orchestrator-wide Implementation Order, Runner Routing & Luna-Readiness Replan

**Date**: 2026-08-02 · **Author**: Claude (Fable 5) operator session, subagent fleet (opus/sonnet/haiku)
**Baseline**: origin/main @ `87fbdda574` · orchestrator DB post-defrag (2026-08-01)
**Scope**: all **539** non-terminal work items across 24 real root trees (+6 TEST junk roots)
**Companion artifacts**: per-item tags written into task-orchestrator (`wave-*`, `rec-*`,
`model-*`, `alt-*`, flags), enriched luna-ready summaries on thin packets,
`routing-table.json` appendix (generated from DB after write-back).

## 1. What this replan does

1. Deep-audits every non-terminal task/TP (content quality, dependencies, staleness vs main).
2. Assigns a global implementation order (waves 0–5 + operator-decision ledger).
3. Tags every item with a recommended runner+model and a backup runner+model.
4. Rewrites under-specified packets to a "luna-ready" bar: implementable by a
   low-reasoning model (gpt-5.6-luna) with zero inference — exact files, numbered steps,
   acceptance criteria, runnable VERIFY commands, stop conditions.

## 2. Tag vocabulary (written onto orchestrator items)

| Tag | Meaning |
|---|---|
| `wave-0`…`wave-5` | Global order bucket (see §4) |
| `rec-<runner>` / `model-<model>` | Primary runner + model (e.g. `rec-codex`,`model-gpt-5-6-luna`) |
| `alt-<runner>` / `alt-model-<model>` | Backup runner + model |
| `reasoning-<low/medium/high/xhigh>` | Reasoning-effort hint |
| `luna-ready` | Packet meets the zero-inference bar; safe for gpt-5.6-luna |
| `verify-close-candidate` | Evidence *suggests* work may be done — verify then close; **tag alone never authorizes closure**; attach evidence refs |
| `stale-candidate` | Superseded/phantom/duplicate — candidate for cancel/delete |
| `needs-rescope` | Premise changed on main; do not implement as written |
| `unblock-candidate` | All blockers terminal; blocked state is stale |
| `operator-gate` | Human decision required; no rec-* tags on purpose (blocks auto-pickers) |
| `cross-repo-parked` | Not actionable from dopemux-mvp |

### Record class (export field `class`)

| Class | Routing |
|---|---|
| `actionable_leaf` | Exactly one primary runner, primary model, backup runner, backup model |
| `series_or_phase_container` | Routing N/A — container only |
| `operator_gated_decision` | No executable runner/model recommendation |
| `cross_repository_parked` | No local dispatch recommendation |
| `stale_or_cancellation_candidate` | No dispatch (includes `needs-rescope` rewrite/cancel cohort) |

Routing rubric (full text: session scratchpad `routing-rubric.md`, derived from
`config/ai/model-routing.policy.yaml` + `claudedocs/beta-readiness-2026-05-29/04-IMPLEMENTER-ASSIGNMENTS.md`):
red-lane/security/architecture/ADR/consensus → claude-code+opus-4-8 (alt codex+gpt-5-3);
well-specified multi-file impl → codex+gpt-5-3-codex ↔ claude-code+sonnet-5;
mechanical+deterministic-verify → codex+gpt-5-6-luna (alt haiku-4-5), `luna-ready`;
docs → gemini-cli(+PAL chain per AGENTS §5) alt haiku; verify-close-candidate audits → haiku alt sonnet;
PAL consensus gates → opus+reasoning-xhigh.
**Schema constraint**: `dopetask-canonical-spec.json` is `additionalProperties:false` —
routing recommendations live in orchestrator tags / packet markdown `## Model Routing`
sections / load-plan `executor_defaults`, never as new TP-JSON fields.

## 3. Verified staleness baseline (2026-08-02)

- PR **#1136** (RTE-TRUTH remediation, head frozen `5f52cad522`) **OPEN unmerged**; followup
  branch `claude/rte-truth-followup` also unmerged. All "LANDED" finding claims = on-branch,
  not on main. #1043 closed unmerged.
- Embedded-audit signers file `config/audit/embedded-audit-allowed-signers` **contains
  hue@local key** — local attestation machinery is LIVE (several packet premises said "inert").
- Merged: #1068, #961 (TO-CANON 000-004), #1174, #894, #885, #858, #879, #1000, #1164.
- Closed unmerged: #1040, #1056 (merge-integrity ADR + runner) → those items `needs-rescope`.
- Still stranded on custody branches: SVCFEAT packets (81354ee9), DCP-MCP-RO remainder (8f64113).
- Beta-readiness spot checks: SEC-01 **partial** (env master key fixed; compose litellm still not loopback-bound → needs-rescope); SEC-03 partial (weak dev-password
  fallback remains); INSTALL-03 (compose profiles) still absent; CLI-05 exit-0 bug confirmed
  at `src/dopemux/cli.py:791-794`.
- `.worktrees/gpt55-recon-chain` gone → GPT-5.5 recon chain notes stale.
- PR #1127 open; ~39 PRs open overall.

## 4. Global implementation order

### Wave 0 — DB truth & hygiene (cheap; kills phantom work first)
Junk TEST roots (6) → delete. PR#1127 duplicate tree `cb80e2fc` → cancel in favor of
`1c691cd2`. Stale-blocked unblocks (COLDSTART-102, SVCFIN DASH-001, COCKPIT-FONTS 105/106).
Verify-close-candidate sweep: CONPORT-Tier0-002 (PR #894), DCP-TOOLING TP-102 (PR #885),
beta SEC-01, TO-CONPORT-REPAIR children vs PR #1164, FLEET-P1 already-exists items,
dedup FLEET-P3-001 ↔ CONPORT-OPTIMAL-106.
*Routing: haiku/luna verify tasks.*

### Wave 1 — Security + open-PR finish-lines
DEPENDABOT CVE bumps (5, luna-ready as written). Beta SEC-02/03(rescoped)/04/05 + CLI-05.
PR #1127 CI repair children. DCP-TOOLING TP-101 (in review, near-complete).
COCKPIT-FONTS 105/106 cleanup.
*Routing: opus for security seams, luna/haiku for mechanical bumps.*

### Wave 2 — Governance gates with maximum unblock-leverage
EMBEDDED-AUDIT-RECONCILED chain (cd91e2eb — fresh, RICH, full metadata DAG; entry:
AUDIT-BUNDLE-001 ∥ CI-TRIGGERS-008 ∥ PR-STEWARD-FRESHNESS-005). DCP-MCP-RO 0019→0026
(0019 premise updated: attestation live). TO-CANON 005-007. RTE-TRUTH verify-close-candidate cohort +
operator gates (MERGE-001, embedded-audit decision) — merging PR #1136 closes the largest
single block of DB debt. TP-DCP-MCP-RO-0008 hardening.
*Routing: opus/codex-high; verify tasks haiku.*

### Wave 3 — Live in-flight programs (finish what's started)
COCKPIT-UI: review items (P2-01, P2-03, COMMAND-PALETTE-001, Phase-1 gate) → P2 queue →
P3-01 investigation → P3-02/03 (existing impl-* tags honored). RTE-TRUTH truly-open
packets (rewritten luna-ready/opus per class). MCPINT P3/P4 RICH packets → P7 non-gated →
consensus gates G6/G7/G8 (opus+PAL). SVCFIN MEMSPINE chain + ADHDLOOP + DASH-001.
START-WAVE3 offline-ok items (3C-5, 3E). ADHD-REMEDIATION T2/T3/T5. FLEET-P0 health.
CONPORT-Tier0-001 migration foundation.

### Wave 4 — New build-out
SVCFEAT: DOPECODE-001 keystone → DOPEMEM S/M chain → DOPEBRAIN-001 chain → SVCFEAT-001..004
(formal BLOCKS edges added). COLDSTART ladder (103/104/105 → 106/116 → 107-113 → 117/118).
DX-OVERHAUL Wave-0 (DELETE/PLUMB/PROMO-GATE; P6 topology cutover red-lane). LEANTIME S1 →
Stage-B → S2 fan-out → Stage-C. DCP-TOOLING remainder → TP-112 (operator). CONPORT-OPTIMAL
red-lane packets (post Tier-0). Beta Agent-Wrap (WRAP-00 re-spec first). ADR series
(backlog). ADHD T8. dNh residual lanes.

### Wave 5 — Backlog / design / deferred
CLAUDE-AUTO PAL design sequence. MCF specs. FLEET-P2..P5 remainder. ADHD-WIRE.
Beta Wave-2-non-SEC + Wave-3. ADHD T6/T7. ADOPS-RUNBOOK (post-rescope). RTE-TRUTH D-tier.
DCP_BUILD_SERIES 0001-0005 (0006-0015 = stale-candidate phantoms). CONPORT 300-tier +
HARDENING. GPT-5.5 recon chain (stale notes; re-anchor first). LEANTIME S3/S4.

### Operator-decision ledger (never agent-runnable)
1. RTE-TRUTH MERGE-001: admin-merge PR #1136 (label `intentional-deletion` + attestation on
   final head). NOTE: MERGE-001 packet still referenced dead PR #1043 → retagged needs-rescope.
   Also: `claude/rte-truth-followup` @ a8faf22b49 (6 packets incl. the D-008 injection fix)
   has **no PR at all** — merging #1136 does not land it; a second PR must be opened.
   R4-003's complete impl is stranded on `feat/rte-truth-r4-003-004` @ 251310385a.
2. Embedded-audit/Steward readiness decision (9f8ad764) — premise updated: signers live.
3. R0-008 fixtures decision; D-003 live-spend cost cap.
4. COLDSTART OP-000 PyPI name; RELEASE-PIPELINE-113 depends on it.
5. DEPENDABOT ecdsa/diskcache no-patch triage.
6. DXO-W0-DOCTRINE §7.6 answers; DXO-W0-P6 APPROVAL.json (red-lane).
7. dNh Supervisor Acceptance + RC audit sign-off.
8. Merge-integrity ADR path (#1040/#1056 both dead — decide revive-vs-drop).
9. TP-112 C1+C5 → L3 promotion (supervisor).
10. Stranded-branch decisions (cherry-pick / re-PR / drop): SVCFEAT packets (81354ee9),
    DCP-MCP-RO remainder (8f64113), `claude/rte-truth-followup` (a8faf22b49, no PR),
    `feat/rte-truth-r4-003-004` (251310385a, complete R4-003 impl),
    `claude/intelligent-banach-8426ff` (real DCP-TOOLING load-plan + packet files),
    `feat/conport-optimal-tier0-hardening` (all 3 HARDENING packet files).
11. Beta WF-02 orchestrator split-brain: the prescribed rename touches
    `services/task-orchestrator/` = DCP-RED-MERGE-SEAM-0001 red-lane (M11/PR #1166 already
    failed on this) — needs operator seam decision.

## 5b. Notable premise flips found during write-back (already tagged on items)
- Fixed on main → verify-close-candidate (then re-checked): SEC-04, SEC-05, INSTALL-04/05, DOCS-01,
  TP-DCP-MCP-RO-0008 (all 22 hardening tests exist), DCP-TOOLING TP-102 (PR #885),
  ADHD 868c057f (ConPort port mismatch already fixed), 19 RTE-TRUTH packets (on unmerged PR #1136).
- Sampling demotions: SEC-01 → `needs-rescope` (loopback residual); CONPORT-OPTIMAL-002 verification
  `unknown` (weak PR #894 map); TO-CONPORT supervisor leaf → `operator-gate` until receipt;
  TO-CONPORT-REPAIR impl children may still be verify-close-candidate only with evidence refs.
- Still live, confirmed: CLI-05 exit-0 bug, DOCS-04 leaked AI tool-call markup at
  `docs/02-how-to/install.md:1252-1255`, exa-retire (4/5 files still reference exa —
  earlier "likely done" hint was wrong), FLEET-P0-006 (3 of 4 kill-list dirs already deleted).
- New defects surfaced: adhd-dashboard fail-open auth (`verify_api_key`→None allows all)
  on 0.0.0.0:8097 (folded into DASH-001 as security scope); `SuppressionTelemetry`
  referenced by tests/docs but absent from `event_coordinator.py` (possible regression);
  context_manager auto-save is a no-op stub unwired from Stop/PreCompact hooks.
- PR #1127: only real blocker is the missing signed embedded-audit attestation
  (`proof/pr_merge/embedded-audit/pr-1127/` absent); docs/lint checks already green.
- RTE-TRUTH ID collision: two distinct packets both answer to "TP-RTE-TRUTH-R3-007"
  (secret scrub = done; F-51 verdict contract = not started) — `id-collision-warning` noted.
- DXO-W0-DELETE would break CI as written: the "57 /tm:* commands" don't exist on main and
  the "6 dead hooks" are live dependencies (test fixture `tests/coldstart/test_l0_membership.py`,
  `adhd_engine/api/routes.py`, active CLAUDE.md) → needs-rescope.
- Already shipped → verify-close-candidate (then re-checked): START-WAVE3 3C-5, COLDSTART GLOBALS-SYNC-106
  (`dopemux mcp sync-globals` exists), MCPINT DOC-GUIDE-002; DXO-W0-P6's core cutover may
  already be done (`.mcp.json` shows task-orchestrator on HTTP) — verify before running.
- `link_conport_items` (MCPINT-FND-INSTRREPAIR-004) has no equivalent in the live 17-tool
  ConPort surface — genuine rescope, not a rename.
- DOPEMEM epic: real implementation lives at `services/working-memory-assistant/`, not
  `services/dope-memory/` (thin stdio adapter) — FILES paths corrected on items.

## 5c. Sampling repairs (TP-REPLAN-BASELINE-1182-REPAIR-001)

| ID | Item | Repair |
|---|---|---|
| `b807751c` | BETA-SEC-01 LiteLLM | Removed verify-close; `needs-rescope` + verification `partial_needs_rescope` (loopback bind residual) |
| `aafc2630` | CONPORT-OPTIMAL-002 | Verification `unknown` until strong PR↔packet map (PR #894 alone insufficient) |
| `207ec91a` | TO-CONPORT supervisor review | `operator-gate`; verification `unknown` until supervisor receipt |

Luna-ready: every retained item must pass deterministic packet bar (files, steps, acceptance/target, verify, stop/invariants; no destructive; no operator decision; no premise uncertainty). Items failing the bar lose `luna-ready` **and must not retain `primary_model=gpt-5-6-luna`** (Codex review P2).

## 5. Cross-tree corrections applied
- FLEET-P3-001 duplicates CONPORT-OPTIMAL-106 → stale-candidate w/ dedup note.
- SVCFIN ARCH-003 superseded by SVCFEAT DOPECODE-001.
- MCPINT HRD-SERENAWRAP-006 formally gated on DOPECODE-001 (cross-tree edge).
- ORCH-FOLLOWUP 014A-UPSTREAM → cross-repo-parked.
- Dependencies are **canonical in the task-orchestrator DB** (not re-embedded per item in
  the routing export). Deterministic reconciliation: instance
  `dopemux-mvp-2e346e2084bca021` exports **563** edges (`BLOCKS` 550 + `RELATES_TO` 13)
  into `routing-table.json` → `dependency_evidence` (full edge manifest). Do **not** claim
  dependency validation from the routing table alone without that manifest/count match.

## 6. Validation (repair TP-REPLAN-BASELINE-1182-REPAIR-001)

- Exact population: **539** unique non-terminal IDs (duplicate_ids=0).
- Class totals sum to 539 (`actionable_leaf` / `series_or_phase_container` /
  `operator_gated_decision` / `cross_repository_parked` / `stale_or_cancellation_candidate`).
- Routing invariants by class:
  - actionable leaf → primary_runner + primary_model + backup_runner + backup_model (no concat)
  - container / operator gate / cross-repo / stale → routing null + explicit `routing_na_reason`
- Summary counts reproduce from record data (no double-count of malformed `rec-*` tokens).
- `verify-close` removed; `verify-close-candidate` only, with `verification.evidence_refs` and
  `closure_authorized_by_tag_alone=false`.
- Luna-ready revalidated deterministically against repo packets; failing items demoted
  (destructive deletes never luna-ready).
- Dependency evidence: DB-exported edge manifest + count reconciliation in
  `routing-table.json` (`dependency_evidence.edge_count=563`).
- Staleness baseline: origin/main @87fbdda574 (replan write); soft-refresh vs current main
  required before READY.
- tp:validate on rewritten TP JSON files: NOT_RUN (export-only; schema
  `additionalProperties:false` keeps routing out of TP JSON fields).

## 6b. Six-file PR scope (do not split)

| Slice | Files |
|---|---|
| Inherited operational truth | `docs/03-reference/orchestrator-integration/db-defragmentation-2026-08-01.md`, index link, `load_plan-TO-CANON.json`, `load_plan-DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED.json` |
| Replan export | `MASTER-PLAN.md`, `routing-table.json` |

Rollback: revert replan export commit for routing freeze; revert load-plan/defrag commit only if receipts must be unwound (live DB is out-of-band).

## 7. Appendix
`routing-table.json` (same directory) — full per-item table after repair: id, title, tree,
role, priority, wave, **class**, routing fields (runner/model split), flags, verification,
plus top-level `population`, `dependency_evidence`, and reproducible `summary`.
