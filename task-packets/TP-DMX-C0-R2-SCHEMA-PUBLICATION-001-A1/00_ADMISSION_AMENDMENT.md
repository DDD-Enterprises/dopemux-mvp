# TP-DMX-C0-R2-SCHEMA-PUBLICATION-001-A1 — Publication admission amendment

```text
PARENT_PACKET=TP-DMX-C0-R2-SCHEMA-PUBLICATION-001
REPAIR_CLASS=L0_INPUT_ADMISSION_AND_PROVENANCE_BINDING_ONLY
SEMANTIC_PUBLICATION_TASK_CHANGE=NO
```

## Control Tower ruling

The prior publication attempt correctly stopped because #1283 is unmerged, but it incorrectly reported C0-R2 ratification as incomplete.

The exact admitted operator record says:

```text
RECORD_ID=TP-UAG-C0-R2-OPERATOR-RATIFICATION-001
DECISION=RATIFY
SUBJECT_ZIP_SHA256=a9d51a5b19170589cff38fee951fd611436e65711af4a8bbfcff4084ab884c19
C0_R2_CONTRACT_RATIFIED=YES

IMPLEMENTATION_AUTHORIZED=NO
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO
```

The package containing that record is bound by:

```text
TP-UAG-C0-R2-OPERATOR-RATIFICATION-001_AND_WAVE1.zip
SHA256=d48186344e6ba9f9003cb4bd4852ca0297a912c9dc2391290c071087fb612776
```

The later template `OPERATOR_RATIFICATION_RECORD_C0_R2.md` with
`STATUS=PROPOSED_UNSIGNED` is a redundant draft produced after the operator
ratification record. It is not a revocation and is not an additional required
signature gate.

```text
C0_R2_RATIFICATION=PASS
NEW_SIGNATURE_REQUIRED=NO
REDUNDANT_UNSIGNED_TEMPLATE=DO_NOT_SIGN_FOR_THIS_GATE
```

## Live publication blocker at issuance

```text
PR_1283_HEAD=bc7d96d539dac82c23caf67850742196dcc550c5
PR_1283_MERGED=NO
```

Reharvest at execution. Until merged:

```text
FINAL_STATUS=BLOCKED_PR1283_UNMERGED
REPOSITORY_MUTATION=0
NEXT_GATE=OPERATOR_PR1283_MERGE_DECISION
```

After #1283 merges, resume the original publication packet at post-merge
main/schema/manifest reharvest. Do not regenerate the publication packet merely
because main moved through the expected #1283 merge.
