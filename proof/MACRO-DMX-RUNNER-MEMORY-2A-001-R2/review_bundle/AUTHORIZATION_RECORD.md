# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Authorization Record

**Operator words (verbatim, chat, 2026-10-31):** "Approve and authorize"

**In answer to (verbatim):** "Approve Wave 2A design revision 2 and authorize R2 (W01-W09, starting with the ADR-227 carve-out)?"

**Recorded at:** 2026-10-31T21:14:42Z by the team lead (Control Tower supervisor session).

Equivalent to `AUTHORIZE_MACRO_DMX_RUNNER_MEMORY_2A_001_R2_EXECUTION=YES` as defined in `ISSUANCE.md`:

- **Design approved:** `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md` revision 2, sha256 `c83aea50bb6bbf98160311c6b46a5ef3fc1741a130705cd955163bf4610734ed` (commit `5335a9e7d`). The design file stays byte-identical until J04-FREEZE; this file is the record.
- **Execution authorized:** W01-W09 inside `MACRO_PACKET.json` (sha256 `b7ffb0833774728a0e59d1f6a54f0a44c6a726ab9c943b029d339562696fd491`), within its PROPOSED allowances, which this accepts.

**Not authorized by this answer** (in-run operator gates, ISSUANCE.md): accepting ADR-227 (J01-CARVEOUT; no red-lane edit before it); approving a carve-out PR to main if W09 finds the branch-local exemption ineffective; the keychain ACL procedure before W03. Push/PR, signing, the audit route, token issuance, migrations, the enforce switch, the ADR-MCPINT-002 amendment, the live Codex run and merge stay separate.
