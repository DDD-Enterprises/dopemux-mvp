# Publication classification note

This packet implements the reconciliation disposition:

```text
C0-R2 ↔ DCP P0/#1283 = COMPATIBLE
PUBLICATION_VEHICLE = dedicated successor after #1283 merge
RISK_LANE = L0 deterministic only if exact-byte publication
```

Why not extend #1283:
- #1283 has frozen/audited/signature-bound content.
- Adding C0-R2 schemas would create a new subject and invalidate its current proof/audit binding.

Why not re-audit exact publication:
- exact schema bytes are already independently audited as C0-R2;
- publication changes location/registry membership, not semantics;
- deterministic digest equality and loader/reference closure are the governing proof.

Any semantic edit immediately invalidates this L0 disposition.
