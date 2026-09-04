# Ratification authority reconciliation

## Authority chronology

1. An exact Control Tower operator-ratification record was created with:
   - `DECISION=RATIFY`;
   - exact C0-R2 subject digest;
   - `C0_R2_CONTRACT_RATIFIED=YES`;
   - no implementation/merge/activation authority.

2. A later, more verbose formal ratification template was generated with:
   - the same subject binding;
   - `STATUS=PROPOSED_UNSIGNED`.

The later draft did not contain an operator rejection, revocation, or supersession
decision. Therefore it cannot silently undo the prior explicit ratification.

Disposition:

```text
EARLIER_EXACT_RATIFICATION=AUTHORITATIVE
LATER_UNSIGNED_TEMPLATE=REDUNDANT_NONAUTHORITY_DRAFT
RATIFICATION_CONFLICT=NO
NEW_SIGNATURE_REQUIRED=NO
```

If a future operator explicitly revokes or supersedes the earlier ratification,
that later explicit operator decision would control. No such revocation is
present here.
