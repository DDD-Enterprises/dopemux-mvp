# Auditor Report — TP-DMX-AI-ROUTING-001

**TP**: TP-DMX-AI-ROUTING-001
**Subject**: Stage-based AI model routing governance policy
**Auditor**: Claude Code CLI (claude-sonnet-4.6) — self-audit after implementation
**Invocation**: self-audit inside Claude Code after edits
**Exit code**: 0
**Status**: PASS_WITH_RISKS
**Date**: 2026-06-06

---

## Verdict

**PASS_WITH_RISKS.** The implementation is correct and self-consistent. Three findings recorded; all are either resolved in follow-on work or accepted as intentional design decisions. No blocking issues.

---

## Scope Reviewed

- `config/ai/model-routing.policy.yaml` — new stage-based governance policy (285 lines)
- `.github/agents/dopemux-reader.agent.md` — model field updated to VERIFY_WITH_VENDOR_DOCS
- `.github/agents/dopemux-planner.agent.md` — model field updated to VERIFY_WITH_VENDOR_DOCS
- `.github/agents/dopemux-auditor.agent.md` — new file, model set to VERIFY_WITH_VENDOR_DOCS
- `.github/agents/dopemux-implementer.agent.md` — independent audit handoff added
- `docs/03-reference/governance/model-routing.md` — new 9-section reference doc
- `docs/02-how-to/model-routing-usage.md` — new operator how-to guide
- `task-packets/TEMPLATE_TASK_PACKET.md` — model_routing block added
- `proof/TP-DMX-AI-ROUTING-001/PROOF.json`

---

## Findings

### F1 — MEDIUM — tests/test_model_routing_policy.py orphaned with outdated structure

**ID**: F1
**Severity**: MEDIUM
**Status**: RESOLVED

`tests/test_model_routing_policy.py` (untracked, not in TP commit allowlist) referenced the
old YAML structure (`stage_slots`, `providers`, `tool_defaults` keys) that no longer exist
in the rewritten policy. Tests would fail if run against the new YAML. The file is orphaned
prior-session residue; it was outside the TP-001 allowlist and could not be fixed within
this packet.

**Resolution**: Fixed in follow-on commit `eb0c29272` (test: align model-routing policy tests
to stages/provider_routes structure). All 10 tests pass against the new structure.

---

### F2 — LOW — proof-bundle-schema.md and proof-contract.md modified outside TP allowlist

**ID**: F2
**Severity**: LOW
**Status**: RESOLVED

`docs/03-reference/governance/proof-bundle-schema.md` and `proof-contract.md` contained
prior-session modifications adding advisory reference pointers to the new policy. These files
were NOT in the TP-001 allowlist and were not committed by this packet.

**Resolution**: Resolved by TP-DMX-AI-ROUTING-002 (commit `61ebef588`), which classified both
modifications as KEEP and committed them with a dedicated proof bundle.

---

### F3 — INFO — All provider model selectors are VERIFY_WITH_VENDOR_DOCS

**ID**: F3
**Severity**: INFO
**Status**: ACCEPTED_RISK

All `provider_routes` model values use the `VERIFY_WITH_VENDOR_DOCS` sentinel. No validated
model IDs are committed.

**Accepted risk**: This is intentional per TP invariants. The policy documents governance
intent only. Operators must replace sentinels with verified model strings before treating
the policy as executable configuration. The sentinel prevents false confidence in unverified
model IDs.

---

## Remaining Risks

- R1: tests/test_model_routing_policy.py orphaned — resolved in follow-on eb0c29272.
- R2: proof-bundle-schema.md and proof-contract.md prior-session edits — resolved by TP-002.
- R3: All provider model selectors are VERIFY_WITH_VENDOR_DOCS — policy is advisory until
  operators substitute verified model IDs.
