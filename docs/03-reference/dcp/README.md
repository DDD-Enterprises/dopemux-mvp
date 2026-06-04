# Declarative Control Plane (DCP) - Core Reference and Decision Shelf

This directory serves as the canonical authority shelf for Declarative Control Plane (DCP) decision, audit, and revision artifacts.

## Status: READ-ONLY / CONTRACT-ONLY / SEED-ONLY

> [!IMPORTANT]
> **DCP v1 is strictly read/export/pointer/dry-run only.**
> This directory and its subdirectories contain documentation and schemas only. No runtime wiring, no event-store append, no CRM writes, no channel sends, no GitHub mutations, and no live adapter bindings are installed or authorized under v1.

## Authority Order
Per [AGENTS.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/AGENTS.md) and [PROJECT.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/PROJECT.md), documentation remains advisory and is strictly subordinate to:
1. Active Task Packet for the current work slice.
2. Observed repository runtime code, configuration, tests, compose files, and active entrypoints.
3. Reference documentation (e.g., `TRUTH_*.md` and this directory).

External Deep Research (DR) and synthesis artifacts are NOT proof of runtime truth; they are design/audit inputs and proposals only.

## Invariants and Red Lanes

### `DCP-RED-MERGE-SEAM-0001` (Universal Red Lane)
- **Status**: `REPO_VALIDATED_BY_AUDIT` (Hard Block)
- **Constraint**: DCP must never import/call/wrap/wire `src/dopemux_pr_merge_specialist/queue_drain.py`'s `execute=True` seam, nor `scripts/batch_resolve_and_merge.py`.
- **Reasoning**: To prevent unauthorized self-certification and automated PR merging in the repository.

### Master Gate
- `LIVE_WRITE_READY` is strictly **UNDEFINED** and **blocking**.

---

## Contradiction Ledger & Preserved Risks
The audit and delta recheck highlighted load-bearing architectural and operational risks that remain open and preserved under v1:
1. **Unmerged CLI & Agent-Orchestrator Mode Drift**: Open PRs #765–#792 and generated TP series remain `CLAIMED_ONLY`. We cannot promote unmerged branches to repo authority.
2. **Provisional Field-Vocabularies**: Field lists derived from external/invented contracts (e.g., `DCP_EVIDENCE_HIT`, `DCP_CHRONICLE_RECEIPT`, `DCP_HELPER_RECEIPT`, `DCP_PROOF_POINTER`) carry a validation state of `PROVISIONAL_UNVERIFIED_ENFORCEMENT` and must not leave version `.v0` without localized reconciliation.
3. **Role Separation (Auditor != Implementer)**: Self-certifying loop is a hard block. Every packet must be audited by an actor distinct from the implementer, and supervisor sign-off must be recorded separately in the proof bundle.

---

## Preserved Decision & Audit Artifacts

The following artifacts are stored under [artifacts/](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/):

| Artifact File | Title / Subject | Status / Provenance |
| --- | --- | --- |
| [DCP_5_5_SYNTHESIS_INPUT_PACK.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/DCP_5_5_SYNTHESIS_INPUT_PACK.md) | GPT-5.5 Synthesis Input Pack | `EXTERNAL_PROPOSED` |
| [DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md) | Pre-Synthesis Contradiction Ledger | `EXTERNAL_PROPOSED` |
| [DCP_ARCHITECTURE_SYNTHESIS_GPT55.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_GPT55.md) | Architecture Synthesis | `SYNTHESIS_INVENTED` |
| [DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/DCP_ADVERSARIAL_ARCHITECTURE_AUDIT.md) | Adversarial Architecture Audit (Opus) | `EXTERNAL_PROPOSED` |
| [DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/DCP_ARCHITECTURE_SYNTHESIS_REVISED_DELTA.md) | Architecture Synthesis - Revised Delta (REV1) | `SYNTHESIS_INVENTED` |
| [DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md](file:///Users/hue/code/dopemux-mvp-wt-dcp-docs-001/docs/03-reference/dcp/artifacts/DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md) | External Constraints Ledger | `EXTERNAL_PROPOSED` |
