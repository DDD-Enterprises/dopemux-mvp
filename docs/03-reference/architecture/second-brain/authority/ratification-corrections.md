---
id: second-brain-ratification-corrections
title: Second Brain Ratification Corrections
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-07'
last_review: '2026-08-07'
next_review: '2026-11-05'
prelude: Repo-native projection of immutable Second Brain ratification corrections, including R2A-01 and the FO-01 downstream ADR gate.
projection: true
source_authority: proof/TP-DMX-SECOND-BRAIN-ARCHITECTURE-AUTHORITY-PERSISTENCE-CI-REPAIR-001/source-authority/04_RATIFICATION_CORRECTIONS.md
ratification_binding_sha256: a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34
---
# 04 — Ratification Corrections

## R2A-01

R2 `DRIFT_RECHECK.md` attributes the post-audit `AGENTS.md` touch to

```text
33d6c353
```

The independently revalidated source commit is:

```text
7f75f9e0
PR #1184
```

This correction supersedes only that commit attribution.

It does not change:

- whether `AGENTS.md` changed;
- the described governance content;
- the drift window;
- any package count or digest;
- the `MATERIAL_DRIFT_CONTAINED` disposition;
- any Second Brain authority boundary;
- any architecture decision.

```text
R2A-01 disposition: CORRECTED_BY_EXTERNAL_RATIFICATION_RECORD
```

The R2 ZIP was **not** mutated. Its SHA-256 remains
`94b735c72ff3533f0cd73bed18fd3fb64b164530f7ef360f37584c73504a4e8e`. This file is the external
correction record.

## FO-01 (raised by this packet, not by 002A)

`24_ADR_CANDIDATES.md` cites SB-DEC ids that do not match the ADR subject matter in at least
ADR-SB-003, -006, -007, -009 and -010; `SB-DEC-031` and `SB-DEC-032` have no ADR candidate.
`03_ARCHITECTURE_DECISION_REGISTER.yaml` is unaffected and internally correct.

002A verified `24_ADR_CANDIDATES.md` byte-identical as a frozen member — freezing proves unchanged,
not semantically coherent, and ADR↔decision mapping was outside 002A scope.

```text
FO-01 severity:    OBSERVATION (ADR-gate scope)
architecture effect on the 32 decisions: NONE
disposition:       DEFERRED_TO_SEPARATE_ADR_GATE
```

No repair was applied here: §13 forbids semantic modification during ratification.

### FO-01 carry-forward semantics (operator-directed)

```text
architecture_ratification_blocker: NO
ADR_acceptance_blocker:            YES
required_resolution:               REPAIR_AND_REVERIFY_TRACEABILITY_BEFORE_ANY_ADR_ACCEPTANCE
```

No ADR in `24_ADR_CANDIDATES.md` may be accepted until its decision traceability is repaired and
independently reverified. This binds the future ADR gate; it does not modify the R2 candidate.
