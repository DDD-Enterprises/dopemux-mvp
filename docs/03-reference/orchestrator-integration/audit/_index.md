---
id: orchestrator-audit-index
title: Red-Team Auditing
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference detailing structured red-team validation and proof verification gates.
related_packets:
  - TP-DMX-ORCH-011
---

# Red-Team Auditing & Verification

Provides a safety verification harness to run post-step output validators on features, hooks, and prompt Map YAML files.

## Invariant Checks
1.  **Hygiene Audits**: Restricts non-allowlisted writes.
2.  **Attestation Attest**: Confirms presence of a compliant proof-bundle before transitions.
