# Local Signed Audit Attestation - PR 1232

- Audited head: `a0ccfd3e6dce298ff8651eed6e053710d0bc9ce0`
- Finalization proof commit: created after the audited C1 and limited to approved proof paths.
- Canonical packet proof: `proof/TP-DMX-RTE-V5-PR1232-CUMULATIVE-CLOSURE-001/PROOF.json`
- Auditor: `grok-cli`, requested `grok-4.6`, recorded per the admitted schema pairing (PR #1228) as `grok-4.5`
- Verdict: `PASS`
- Signature namespace: `dopemux-embedded-audit`
- Signer policy: existing `config/audit/embedded-audit-allowed-signers`; no signer policy or key change.

The signature binds the exact bytes of `PROOF.json`, whose `head_sha` matches this audited commit directly. Canonical packet proof and raw audit output are committed before signing.
