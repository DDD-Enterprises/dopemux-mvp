---
id: ltaip-h0-segment-lock-recruitment-and-consent
title: LTAIP H0 Segment Lock Recruitment and Consent
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Recruitment criteria and consent/redaction rules for Horizon 0 segment-lock interviews.
---

# Recruitment and Consent

## Recruitment channels (authorized)

- Existing professional networks and community operators (no cold production customer scrape).
- Opt-in research calls framed as product-neutral PM workflow research.
- No paid acquisition required for Horizon 0 pilot.

## Inclusion

- Team delivery or ops role; tooling influence or daily workflow ownership.
- English or mutually workable language for note capture.
- Age of majority in participant jurisdiction.

## Exclusion

- Current production dependency that would require live production access.
- Inability or refusal to consent to redacted notes.
- Conflicted evaluators whose only input is internal Dopemux preference (not external participant).

## Consent script (summary)

1. Purpose: qualitative pilot to lock buyer/personas/workflows for parity fixtures — not a sale.
2. Data: operator notes only; no audio/video retention in repo; redaction before commit.
3. Rights: skip questions; withdraw anytime; no compensation obligation unless separately arranged.
4. Risk: low; no production system access requested.
5. Contact: research operator (opaque in public artifacts).

Consent must be affirmative before session evidence is retained.

## Redaction rules

| Allowed in git | Forbidden in git |
|----------------|------------------|
| Opaque ID `P-###` | Legal name, email, phone, handle mapping |
| Role archetype (e.g. eng manager) | Employer that deanonymizes without need |
| Redacted workflow steps | Customer secrets, credentials, private URLs |
| Aggregate counts | Verbatim private transcripts, recordings |

Participant register stores **only** opaque IDs, role class, buyer/user class, consent flag, session dates (UTC day), and withdrawal status.

## Data retention

- Raw notes (if any) stay off-repo under operator control and are destroyed or sealed after redaction.
- Repo holds redacted summaries in `session-evidence.jsonl` only.
