# Authorization record - MACRO-DMX-MEMORY-BRIDGE-001-R5

All typed by the operator in this session's chat on 2026-10-30 (not relayed):

1. `Repair N12` (after the R4 audit). The coordinator issued R5 (hashes in `ISSUANCE.md`).
2. `Change the key rule` (a reply button). The coordinator asked which rule to use instead (reversible escape, fail closed only, or hash every key); the operator did not answer the question and sent instead:
3. `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_EXECUTION=YES`
4. `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`

Reading: the authorization lines cover R5 as issued (pinned hashes below), so R5 is executed unchanged with its key rule: ordinary ids (`[A-Za-z0-9_-]{1,80}`) stay as they are; any other id becomes a sanitized prefix of up to 56 characters, `~`, and a 16-hex synchronous FNV-1a hash of the whole id. No amendment was made. Still excluded: push, PR update, signing, attestation, merge, a second audit, any advisor call.

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `0e304de1c7a315820aca2012afeb328b817e09eb78f20142bcaea80bef623c4e` |
| `EXECUTION_BINDING.json` | `30c31df0875a861bbd60665d1ef75a68936aee294e2de55ccd598a339b7a352c` |
| `W01_TASK_PACKET.json` | `7d86d0f5f07e6eba7f2c0f49f23e9ff5c342ed0980252546229213cd722d0879` |
| `W02_TASK_PACKET.json` | `66ea395f5164d77a969c91bff8b6ec35895cd79022491ac4da5a2cc43af548b2` |
