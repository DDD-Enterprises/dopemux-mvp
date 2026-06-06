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
| RTE S7 gate stub always-PASS | `validate_pre_live_gate_v25.py:476-478` | Must be fixed before trusting any RTE readiness verdict |
| RTE SP contracts missing | `repo_truth_map.json` + SP pipeline | SP pipeline runs ungated — go-live verdicts untrustworthy |
| Agent authority unresolved | `AGENTS.md:88`, `truth-canonicals.md:248` | Three families, no canonical — agents must not be granted authority |
| `claudedocs/` is advisory only | File assembly recon | Never use as primary evidence for proof |
| Compose ≠ runtime proof | Patched census global caveat | `runtime_process_verified: false` on all compose entries |
| No implementer self-audit | All capsules | Audit must be by external tool or independent model |
| No secrets | All capsules | Never read, print, or commit `.env`, API keys, tokens, passwords |
| No scope escape | Capsule `allowed_files` | Edits outside allowed_files = immediate halt |
| `monitoring-dashboard` at 0.0.0.0:1561 unauthenticated | `services/monitoring-dashboard/server.py` | HIGH security risk — do not invoke, do not expose |

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

### RTE S7 gate stub

The stub at `validate_pre_live_gate_v25.py:476-478` unconditionally returns `PASS` regardless of actual gate state. Any RTE readiness verdict produced while this stub is in place is untrustworthy. Do not cite RTE readiness verdicts as primary evidence until this is fixed and verified.

### `monitoring-dashboard` at 0.0.0.0:1561

This service binds to all interfaces with no authentication layer. Do not invoke it programmatically, do not expose it externally, and do not include its output in any proof bundle as primary evidence. Treat it as a local-only debug surface until auth is added.

### No implementer self-audit

The model or agent that wrote the code cannot audit it. PAL clink must call an independent external model. If the session cannot reach PAL clink, the capsule must declare `pal_codereview_status: SKIPPED` and escalate — it must not substitute an internal review pass and call it an audit.
