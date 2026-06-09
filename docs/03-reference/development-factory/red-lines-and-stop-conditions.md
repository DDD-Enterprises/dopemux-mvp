---
id: red-lines-and-stop-conditions
title: Red Lines And Stop Conditions
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Red Lines And Stop Conditions (reference) for dopemux documentation and developer
  workflows.
---
# Red Lines & Stop Conditions

Hard stops that apply to ALL capsule executions regardless of supervisor instruction.

A red line is non-negotiable. It is not a warning. It is not a suggestion that can be overridden by a downstream agent. It is a halt condition. The only entity that can waive a red line is a human operator with full knowledge of the risk — and even then, the waiver must be recorded in the capsule's PROOF.json under `stop_conditions_met`.

---

## Red Line Register

| Red Line | Source | Status |
|---|---|---|
| `LIVE_WRITE_READY` is undefined | `schemas/dcp/README.md` + DCP packets | UNDEFINED — blocks L4+ |
| `DCP-RED-MERGE-SEAM-0001` active | `schemas/dcp/README.md:101-111` | ACTIVE — blocks `queue_drain.py` and `batch_resolve_and_merge.py` |
| `queue_drain.py execute=True` | `src/dopemux_pr_merge_specialist/queue_drain.py` | HARD-BLOCKED |
| `scripts/batch_resolve_and_merge.py` | `scripts/batch_resolve_and_merge.py` | HARD-BLOCKED |
| RTE S7 truth-split gate — VERIFY behavior | `validate_pre_live_gate_v25.py` (`collect_truth_split` → `all_blockers`) | Implementation present at HEAD `8042f9f9f`; the prior "always-PASS stub" claim is stale. Do NOT trust RTE readiness until the gate is run against injected drift and confirmed to FAIL (verify-and-close) |
| RTE SP contracts — VERIFY enforcement | `validate_pre_live_gate_v25.py` (`SP_CONTRACT_MISSING` blocker) | `SP_CONTRACT_MISSING` blocker present at HEAD `8042f9f9f`; verify it blocks ungated SP rather than assuming the pipeline is unguarded |
| Agent authority unresolved | `AGENTS.md:88`, `truth-canonicals.md:248` | Three families, no canonical — agents must not be granted authority |
| `claudedocs/` is advisory only | File assembly recon | Never use as primary evidence for proof |
| Compose ≠ runtime proof | Patched census global caveat | `runtime_process_verified: false` on all compose entries |
| No implementer self-audit | All capsules | Audit must be by external tool or independent model |
| No secrets | All capsules | Never read, print, or commit `.env`, API keys, tokens, passwords |
| No scope escape | Capsule `allowed_files` | Edits outside allowed_files = immediate halt |
| `monitoring-dashboard` at 0.0.0.0:8098 unauthenticated | `services/monitoring-dashboard/server.py:1563` | HIGH security risk if started — binds all interfaces, no auth on own endpoints. Latent: NOT running at last verification. (Prior "1561" was a line-number confusion; real port is **8098**.) Do not invoke, do not expose |
| Proof bundle not committed for a completed packet | `docs/03-reference/governance/proof-directory-rules.md`, `evidence-and-proof-flow.md` | A governed capsule must not be marked complete, PR-clean, or DONE without a committed `PROOF.json` and `SUMMARY.md`. Use `git add -f` to force-track sanitized proof past the `proof/*` gitignore. Claiming "done" without a committed proof is a proof-integrity violation. |

---

## Stop Condition Protocol

On any red line trigger, the capsule **must**:

1. **Halt immediately** — no further writes, no further tool calls, no further PAL chains
2. **Record the trigger** in `PROOF.json` under `stop_conditions_met` — include the red line ID, the triggering file/line if known, and a brief description of what was observed
3. **Emit `SUMMARY.md`** with `verdict: STOPPED` — the summary must name the red line and the exact point at which the halt occurred
4. **Escalate to supervisor** (GPT-5.5 Pro or human) — do not attempt diagnosis or repair; surface the trigger and wait
5. **Do NOT attempt repair within the same capsule** — a stopped capsule is closed; repair requires a new capsule with a new task-orchestrator item and a fresh proof bundle

### SUMMARY.md template for a stopped capsule

```markdown
# Capsule SUMMARY — STOPPED

packet_id: TP-DMX-<id>
head_sha: <sha>
verdict: STOPPED

## Red Line Triggered

- red_line_id: <id from register above>
- source: <file:line or schema ref>
- observed: <what the capsule saw that triggered the halt>
- point_of_halt: <which step in the capsule was executing>

## Actions Taken

- [ ] Halt issued
- [ ] stop_conditions_met recorded in PROOF.json
- [ ] Supervisor notified

## Required Next Step

A human operator or GPT-5.5 Pro Supervisor must review this trigger before any further work proceeds on this capsule's scope.
```

---

## Notes on Specific Red Lines

### `DCP-RED-MERGE-SEAM-0001`

This red line was set because the merge seam between `queue_drain.py` and `batch_resolve_and_merge.py` has no safe guard against unintended live writes. Until `LIVE_WRITE_READY` is defined and the seam is gated, both scripts must remain inert. Any capsule that attempts to call either script with `execute=True` or with live credentials = immediate stop.

**Enforcement status (verify, do not assume docs-only):** the prior census framed this seam as "defined in `schemas/dcp/README.md` only, not code-enforced." As of HEAD `8042f9f9f` that is partly stale — executable enforcement code exists: `src/dopemux/dcp/red_lane_scanner.py` (`RedLaneScanner`), `red_lane.py`, `red_lane_rules.py`, with tests. **However**, `RedLaneScanner` is referenced only in `src/dopemux/dcp/`, `tests/`, and one packet doc — **not** in `.github/`, `tools/pr_steward/`, `tools/auditor_router/`, or `scripts/`. So the scanner exists but is **not wired into the CI/merge/steward path**. The follow-up (`TP-DMX-DCP-SEAM-ENFORCEMENT-001`) is therefore "wire the existing scanner," not "build enforcement from scratch." The hard-block on `queue_drain.py` / `batch_resolve_and_merge.py` remains in force regardless.

### RTE S7 truth-split gate (verify, do not assume missing)

The earlier census claimed `validate_pre_live_gate_v25.py:476-478` unconditionally returns `PASS`. As of HEAD `8042f9f9f` that is **stale**: `collect_truth_split` (≈line 523) builds rows, calls `classify_truth_split_row`, emits `SP_CONTRACT_MISSING` / `TARGET_TRUTH_SPLIT_MISMATCH` blockers, and the live-gate path extends those blockers into `all_blockers` (≈line 1419). The line numbers in the original claim no longer point at a stub — the file was substantially rewritten. **This was a code read, not a gate run.** The red line therefore stands as *verify-and-close*: run the gate against injected drift and confirm a FAIL before trusting any RTE readiness verdict. Do not assume the gate is broken, and do not assume it is correct, until the behavior is exercised (`TP-RTE-S7-DRIFT-FIX-001`, re-scoped to verification).

### `monitoring-dashboard` at 0.0.0.0:8098

This service binds to all interfaces with no authentication layer. Do not invoke it programmatically, do not expose it externally, and do not include its output in any proof bundle as primary evidence. Treat it as a local-only debug surface until auth is added.

### No implementer self-audit

The model or agent that wrote the code cannot audit it. PAL clink must call an independent external model. If the session cannot reach PAL clink, the capsule must declare `pal_codereview_status: SKIPPED` and escalate — it must not substitute an internal review pass and call it an audit.
