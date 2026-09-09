# Late canonical R1 repair-proof closure

`PROOF_MATERIALIZATION=LATE_REPAIR_CLOSURE`.

This report materializes the canonical proof location required for
`TP-DMX-GOV-G0-LITE-PR1282-REPAIR-001`. It records, rather than reruns, the
observed R1 final L2 audit:

- audited SHA: `e339c74239e3a3ec157eeaaf1aa6fa580fea1ee7`
- audited tree: `8c481613a467fe70c745455cca9af2828ba4faca`
- audit verdict: `PASS_WITH_RISKS`
- audit ID: `TP-DMX-GOV-G0-LITE-PR1282-REPAIR-001-FINAL-L2`

Observed source receipt: `proof/DMX-GOV-G0-LITE-IMPLEMENTATION-AUTHORITY-001/`
at this repair branch's starting head.

This proof did not exist when R1 audit ran. It makes no claim that it did, and
does not audit R2 content. R2 needs early review stabilization, then one final
independent audit on its frozen content head.

Current binding records in `PROOF.json` cover R1 packet identity, authority
record subject, current G0 packet digest/blob, and overlap actions. In
particular, `SUPERSET=STOP_FOR_SUPERVISOR_ADJUDICATION`; it cannot continue
without supervisor adjudication.
