# Embedded audit — TP-DOPECONTEXT-VOYAGE4-REPAIR-0002

## Status

**PENDING_INDEPENDENT_AUDITOR**

The packet requires an independent embedded auditor (Gemini CLI preferred).
The implementer session must not self-certify PASS.

## Required challenges (for independent auditor)

1. Reconstruct six-vector compatibility matrix from code.
2. Prove collection identity changes under every profile mutation.
3. Seed legacy-collection metadata; prove no new write reaches it.
4. Prove rollback cannot split index and query.
5. Prove embedding/upsert failures preserve prior points.
6. Prove no silent zero-result budget starvation.
7. Compare implementation against all Opus findings.
8. Reject PASS if any blocking finding remains.

## Interim implementer self-check (not a formal verdict)

- Local pytest: 74 passed
- Docker smoke: SMOKE_OK (voyageai 0.5.0)
- Blocking F-001/F-002/F-003 addressed in source

Formal `auditor_verdict` remains unset until independent audit completes.
