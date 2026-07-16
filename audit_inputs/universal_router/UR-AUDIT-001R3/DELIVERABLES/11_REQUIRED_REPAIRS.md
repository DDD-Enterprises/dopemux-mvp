# 11 — Required Repair Plan (grouped by gate)

This audit does **not** rewrite the architecture. Each repair names finding IDs, exact sections, the semantic
change, whether new evidence is needed, an acceptance test, a recommended owner, and whether a delta re-audit is
required.

## A. Before architecture acceptance
None. No P0/P1 findings; the architecture is accepted to begin UR-TP-001 (disposition
`ACCEPT_BEGIN_UR_TP_001`). Groups B–H below are gate-scoped repairs that do not block acceptance.

## B. Before UR-TP-001 (contracts packet)
- **R-B1 (UR-AUDIT-R3-001, P2, provenance).** Sections: `18` Step 1, `19` UR-TP-001, `07`, `03` C-001,
  `20` UR-OQ-001. Change: cite the **tracked canonical paths** from `13_PROVENANCE_RESOLUTION.md`
  (proof-contract, proof-bundle-schema, handoff-contract, adapter-contract, adapter-schema,
  `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`, `docs/03-reference/governance/rules.md`,
  `docs/03-reference/systems/system-boundaries.md`) and the current tracked
  PROJECT/ARCHITECTURE/SERVICE_CATALOG/PM_PLANE/AGENTS; treat `TRUTH_*` as research-tier context only.
  New evidence: none — this audit supplies the Git evidence UR-OQ-001 requested. Acceptance test: every
  referenced contract/authority path resolves via `git cat-file -e <impl_commit>:<path>` and no bundle
  archive name is used as a canonical authority ref. Owner: implementer + architecture supervisor.
  Delta re-audit: not required (documentation-level).
- **R-B2 (UR-AUDIT-R3-003, P2, contract).** Section: `07`, `18` Step 1 gate, `19` UR-TP-001 validation gates.
  Change: convert prose "minimal fields" into strict versioned schemas (`additionalProperties:false` for
  authority-bearing sections) with explicit types, required/optional flags, closed enums, plus
  valid/invalid/unknown/conflicting fixtures. New evidence: none. Acceptance test: `python -m json.tool`
  on each schema; contract tests reject undeclared fields; unknown/conflicting fixtures behave as specified.
  Owner: implementer. Delta re-audit: **light** — confirm schemas did not introduce a new authority field
  belonging to another subsystem.
- **R-B3 (UR-AUDIT-R3-004, P2, task_packet).** Section: `19` Common PR Steward requirement, `20` UR-OQ-006.
  Change: locate and pin the current canonical PR Steward invocation + `MERGE_READINESS.json` schema before
  opening the UR-TP-001 PR; do not build a replacement. New evidence: **yes** — current PR Steward runtime
  path/command at the implementation commit. Acceptance test: pinned invocation emits `MERGE_READINESS.json`;
  `READY` requires current head/checks/no unknown reviewer-bot/diff in allowlist. Owner: PR Steward maintainer +
  implementer. Delta re-audit: not required.

## C. Before UR-TP-002
- Confirm the `route` noun does not rewrite `routing` behavior (verified free at audit time:
  `routing_cli.py:588`) and that no route can enter handoff/execution states (packet stop condition). Owner:
  implementer. New evidence: none. Delta re-audit: not required.

## D. Before capability-snapshot ingestion (UR-TP-004)
- Resolve TTL calibration (UR-OQ-014) and provider-health acquisition path distinctions (UR-OQ-013) as policy
  defaults; sandbox denial must remain `SANDBOX_NETWORK_DENIED` (not provider outage). No architecture change
  required; policy may only shorten TTLs freely.

## E. Before first execution adapter (UR-TP-010)
- Resolve UR-OQ-007 (CRITICAL, provider-attested served-model identity) and UR-OQ-009 (CRITICAL, Codex
  wrapper/OS-enforced containment) with **new evidence** (fresh contained probes + provider-controlled metadata).
- Resolve UR-OQ-003/UR-OQ-020 (Freeflow read API; ref version compatibility) and UR-OQ-018 (HumanApprovalRef
  issuer). New execution ADR + explicit human approval required. Delta re-audit: **required** (independent
  containment audit) before enablement.

## F. Before bounded escalation (UR-TP-011)
- Resolve UR-OQ-008 (plan-credit observation) so credit guards are real, not inferred; ≥25 accepted low-risk
  executions + new supervisor approval. Delta re-audit: required.

## G. Before automatic routing (UR-TP-012)
- **R-G1 (UR-AUDIT-R3-002, P2, evaluation).** Sections: `15` certification tuple, `10` adapter tuple, `07`
  BenchmarkCertification. Change: add `identity_confidence` and `task_class` as explicit certification-tuple
  members; add `containment_profile` and `network_posture` to BenchmarkCertification's route tuple; any change
  to these invalidates certification. New evidence: none. Acceptance test: a certification fixture with a
  changed identity_confidence or task_class is rejected as out-of-scope. Owner: policy/evaluation owner.
  Delta re-audit: **required** at certification.
- Resolve UR-OQ-016 (policy-signing requirement) and UR-OQ-017 (≥200-task labeled corpus). ≥100 certified
  low-risk executions + new ADR + human promotion.

## H. Before release-sensitive use
- Unknown actual model identity must block pinned-model/benchmark/audit-independence/release-sensitive routes
  (already enforced). Resolve UR-OQ-015 (retention/encryption/access) before production storage of task text/
  corpora.

## P3 hardening (non-blocking, recommended)
- **UR-AUDIT-R3-005:** hash-chain journal events (`event_hash = H(payload_hash || prev_event_hash)`) so
  tampering is detectable on replay; document that triggers give integrity, not tamper-proofing. Owner:
  journal implementer (UR-TP-003).
- **UR-AUDIT-R3-006:** document per-worktree journal semantics; confirm `.dopemux/universal-router/` stays
  gitignored (verified at audit time); optionally allow a governance-approved shared journal location.
