---
id: ltaip-h0-segment-lock-research-protocol
title: LTAIP H0 Segment Lock Research Protocol
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Pre-registered qualitative protocol for Horizon 0 economic-buyer, persona, and must-win workflow lock.
---

# LTAIP H0 Segment Lock Research Protocol

## Claim posture

- **OBSERVED:** Stage 08 authorizes `VALIDATE_WITH_PROTOTYPE` only; EPIC-08-001 requires one economic buyer, two primary personas, three must-win workflows.
- **PROPOSED:** This protocol pre-registers qualification, consent, redaction, evidence grading, dissent, and stop rules before any scoring.
- **UNKNOWN:** Whether enough qualified participants can be recruited in-window.
- **FORBIDDEN:** Base-product preference, production credentials, raw personal data in git, marketing claims.

## Horizon and authorization

| Field | Value |
|-------|--------|
| Packet | `TP-LTAIP-H0-001` |
| Series | `LTAIP-H0-VALIDATION-001` |
| Authorization | `HORIZON_0_PROTOTYPE` |
| Risk | HIGH |
| Statistical claim | Not authorized (qualitative pilot only) |

## Research questions

1. Who is the economic buyer for a self-hosted / operator-grade AI-augmented PM stack in the target segment?
2. Which two primary personas must be co-served for the wedge to be viable?
3. Which three workflows must be product-neutral parity fixtures across Leantime and OpenProject candidates?

## Qualification (pre-registered)

A participant is **qualified** when all hold:

1. Active role in software/product delivery or IT ops for a team of ≥3.
2. Influence or ownership over PM tooling selection, budget, or self-host operations **or** daily heavy use of PM workflows under study.
3. Able to describe at least two concrete workflows with pain or frequency.
4. Explicit consent for redacted note capture under `recruitment-and-consent.md`.

## Buyer vs user evidence

| Class | Definition | May influence |
|-------|------------|---------------|
| `buyer` | Budget ownership, purchase influence, or self-host operating responsibility | Economic-buyer ranking, switching triggers, procurement constraints |
| `user` | Hands-on workflow execution without purchase authority | Persona support, workflow frequency/pain, UX constraints |
| `mixed` | Both classes in one session | Counts toward both with separate scoring columns |

Buyer evidence and user evidence are ranked **separately** before synthesis. Internal operator preference is **not** participant evidence.

## Minimum evidence gate (stop rules)

Packet may complete only when:

1. ≥5 distinct qualified participants.
2. ≥3 sessions include buyer-class responsibility.
3. Each selected primary persona supported by ≥3 independent sessions (overlap allowed).
4. Each selected workflow supported by ≥3 sessions and top-five in **both** buyer importance and user frequency/pain.
5. No unresolved P0 contradiction.

If gate fails → status `BLOCKED_INSUFFICIENT_SEGMENT_EVIDENCE`. No weighted rescue after gate failure (EPIC-08-001 constraint).

## Evidence grading

| Grade | Meaning |
|-------|---------|
| A | Direct observation or first-person workflow walkthrough with concrete steps |
| B | First-person report with specific frequency/pain, no walkthrough |
| C | Second-hand or abstract preference |
| X | Invalid / withdrawn / consent incomplete — excluded from ranking |

Only A/B count toward minimum gate. Grade C may inform dissent only.

## Contradiction and dissent

- Every contradiction logged in session evidence and carried to `assumptions-and-dissent.md`.
- P0 = blocks lock (e.g., buyer class impossible to serve with stated workflows).
- P1 = material risk, must appear in reversal criteria.
- Averaging away dissent is forbidden.

## Redaction and privacy

See `recruitment-and-consent.md`. Opaque IDs only in repo. No names, emails, recordings, verbatim private transcripts, or customer secrets.

## Fixtures neutrality

Workflow fixtures must not name a preferred base product. Success measures must be runnable on both Leantime and OpenProject candidate editions.

## Withdrawal

Participant may withdraw any time before lock merge. Withdrawal moves evidence grade to X and recalculates gates.

## Outputs of this packet

Protocol (this file), consent rules, interview guide, redacted register, session-evidence ledger, criteria ranking, segment-workflow lock (md+json), fixture spec, ADR, dissent register, proof + embedded audit.
