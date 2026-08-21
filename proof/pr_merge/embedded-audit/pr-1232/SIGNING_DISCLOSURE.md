# Local Signed Audit Attestation - PR 1232

- Audited head: `ec464f793ca5187864af7671104f27be00047311`
- Finalization proof commit: created after the audited C1 and limited to approved proof paths.
- Canonical packet proof: `proof/TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001/PROOF.json`
- Auditor: Claude Code `2.1.238`, requested `opus`, response-claimed `claude-opus-5`
- Verdict: `PASS_WITH_RISKS`
- Signature namespace: `dopemux-embedded-audit`
- Signer policy: existing `config/audit/embedded-audit-allowed-signers`; no signer policy or key change.

The signature binds the exact bytes of `PROOF.json`, whose `head_sha` remains C1 rather than this proof-only successor commit. Canonical packet proof and raw successor output are committed before signing.
