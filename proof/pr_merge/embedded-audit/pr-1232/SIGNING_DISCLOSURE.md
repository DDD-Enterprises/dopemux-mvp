# Local Signed Audit Attestation - PR 1232

- Audited head: `9e3d2623f2cc0ba6e65e9b39ce68843a5c51a11f`
- Finalization proof commit: created after the audited C1 and limited to approved proof paths.
- Canonical packet proof: `proof/TP-DMX-RTE-V5-PR1232-P1-FOLLOWUP-001/PROOF.json`
- Auditor: Claude Code `2.1.238`, requested `opus`, response-claimed `claude-opus-5`
- Verdict: `PASS`
- Signature namespace: `dopemux-embedded-audit`
- Signer policy: existing `config/audit/embedded-audit-allowed-signers`; no signer policy or key change.

The signature binds the exact bytes of `PROOF.json`, whose `head_sha` remains C1R rather than this proof-only successor commit. Canonical packet proof and raw audit output are committed before signing.
