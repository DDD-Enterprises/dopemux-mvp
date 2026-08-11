---
id: TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001
title: AGY Gemini 3.1 Pro High Model Authority Repair
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-31'
prelude: Repair PR 1165 to bind exact AGY Gemini model authority.
last_review: '2026-08-02'
next_review: '2026-10-31'
---
# TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001

## Decision

Repair the existing draft PR #1165 in place.

## Objective

Repair PR #1165 so the canonical embedded-audit schema approves the exact AGY Gemini 3.1 Pro High selector only for auditor_tool=agy — and so the trusted local-attestation route actually enforces that contract. A trust contract the trusted path does not enforce is not a trust contract.

## Commit Topology

Named explicitly, because an audit cannot audit its own output:

- **AUDITED_TREE** — the exact substantive tree sent to the auditor (schema, validator, workflow, docs, tests, packets).
- **AUDIT_EVIDENCE_HEAD** — successor adding only the resulting auditor report, the raw runner transcript, and deterministic runner evidence.
- **SIGNED_PROOF_HEAD** — successor adding or replacing only the permitted signed proof artefacts under `proof/pr_merge/embedded-audit/pr-1165/`.

## Stop Conditions

- Exact AGY high selector absent
- gemini-3.1-pro-preview remains approved
- Audit verdict FAIL, or any BLOCKER / MUST_FIX finding
- A signed embedded_audit accepted by the local route that the canonical Draft7Validator rejects
- PR Steward not READY
