# Dopemux Second Brain Architecture — Ratified Authority

## Status

```text
authority status:                    RATIFIED
governing candidate:                 TP-DMX-SECOND-BRAIN-ARCHITECTURE-SYNTHESIS-001-R2-CANDIDATE.zip
governing candidate SHA-256:         94b735c72ff3533f0cd73bed18fd3fb64b164530f7ef360f37584c73504a4e8e
ratification binding SHA-256:        a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34
ratification package SHA-256:        fe336eb871b19896fd77d553a46d88ef1c03e1f7af5818d0c7c11085d7beac72
decision count:                      32
accepted:                            32 / 32
deferred:                            0
rejected:                            0
ratification verdict:                ARCHITECTURE_RATIFIED_READY_FOR_IMPLEMENTATION_PLANNING
implementation planning:             AUTHORIZED
implementation execution:            NOT_AUTHORIZED
ADR acceptance:                      NOT_AUTHORIZED
```

## FO-01

```text
architecture ratification blocker:   NO
ADR acceptance blocker:              YES
required resolution:                 REPAIR_AND_REVERIFY_TRACEABILITY_BEFORE_ANY_ADR_ACCEPTANCE
```

## R2A-01

```text
disposition:                         CORRECTED_BY_EXTERNAL_RATIFICATION_RECORD
```

## Remaining empirical states

```text
runtime conformance:                 NOT_RUN
retrieval benchmarks:                NOT_RUN
purge completeness:                  NOT_RUN
multi-project isolation:             NOT_RUN
split-brain proof:                   NOT_RUN
encryption implementation:           ABSENT
```

## MA-08 standing requirement

A fresh drift recheck against `origin/main` is a standing precondition for any future action that
builds on this authority. The baseline at ratification time was `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda`.

## Proof pointers

```text
ARCHITECTURE_AUTHORITY_HEAD.json
ARCHITECTURE_RATIFICATION_RECORD.md
OPERATOR_DECISION_LEDGER.yaml
RATIFICATION_BINDING.json
RATIFICATION_CORRECTIONS.md
FINAL_RATIFICATION_VERDICT.md
PROOF_POINTERS.json
SOURCE_SHA256SUMS.txt
PERSISTENCE_RECEIPT.json
```

---

This directory persists ratified architecture authority.
It does not itself amend the architecture.

ADR acceptance remains blocked by FO-01 until traceability is repaired
and independently reverified.

Implementation execution remains unauthorized.
