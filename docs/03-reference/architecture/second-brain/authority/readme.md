---
id: second-brain-architecture-authority
title: Dopemux Second Brain Architecture Authority
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-07'
last_review: '2026-08-07'
next_review: '2026-11-05'
prelude: Entry point for the ratified Dopemux Second Brain architecture authority, proof custody, projections, downstream gates, and implementation-planning status.
---
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

## Repository representation

This directory separates three kinds of content:

**Immutable source authority bytes** — exact copies of the signed ratification package's
authoritative Markdown members, held outside the active docs tree so repository documentation
rules cannot require them to change:

```text
proof/TP-DMX-SECOND-BRAIN-ARCHITECTURE-AUTHORITY-PERSISTENCE-CI-REPAIR-001/source-authority/04_RATIFICATION_CORRECTIONS.md
proof/TP-DMX-SECOND-BRAIN-ARCHITECTURE-AUTHORITY-PERSISTENCE-CI-REPAIR-001/source-authority/08_ARCHITECTURE_RATIFICATION_RECORD.md
proof/TP-DMX-SECOND-BRAIN-ARCHITECTURE-AUTHORITY-PERSISTENCE-CI-REPAIR-001/source-authority/10_FINAL_RATIFICATION_VERDICT.md
```

Plus the three exact-byte machine records that were always active docs:

```text
ARCHITECTURE_AUTHORITY_HEAD.json
OPERATOR_DECISION_LEDGER.yaml
RATIFICATION_BINDING.json
```

**Repo-native projections** — active, frontmatter-bearing, kebab-case Markdown that makes the
immutable source discoverable and CI-compliant. Removing exactly one leading YAML frontmatter
block from each projection reproduces its immutable source byte-for-byte:

```text
architecture-ratification-record.md  ->  proof/.../source-authority/08_ARCHITECTURE_RATIFICATION_RECORD.md
ratification-corrections.md          ->  proof/.../source-authority/04_RATIFICATION_CORRECTIONS.md
final-ratification-verdict.md        ->  proof/.../source-authority/10_FINAL_RATIFICATION_VERDICT.md
```

**Generated persistence metadata** — not authority content, regenerated as the persistence record
evolves:

```text
this file (readme.md)
PROOF_POINTERS.json
SOURCE_SHA256SUMS.txt
PERSISTENCE_RECEIPT.json
```

The projections are not a second architecture authority. The exact source bytes under `proof/`
remain the evidentiary authority; the projections exist solely to satisfy repository documentation
rules while pointing back to that authority.

## Proof pointers

```text
ARCHITECTURE_AUTHORITY_HEAD.json
OPERATOR_DECISION_LEDGER.yaml
RATIFICATION_BINDING.json
architecture-ratification-record.md
ratification-corrections.md
final-ratification-verdict.md
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
