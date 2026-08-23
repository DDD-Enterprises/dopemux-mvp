# Cross-referenced evidence: which model served the PR #1227 round-2 audit

**This is not this packet's audit.** These files are runner session metadata from a
*different* packet's independent audit. They are captured here because they are the
evidence for admitting `grok-4.5` specifically, rather than some other Grok model.

## Why it was needed

`TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001` (PR #1227) recorded its round-2
auditor honestly as:

```json
"model": "UNKNOWN_TO_PRODUCER",
"model_note": "The CLI does not report the served model in plain output mode.
               Recorded as unknown rather than guessed."
```

The invocation pinned no `-m`, so the served model was whatever the runner defaulted
to at that moment. That was fine to leave unknown while no Grok model was
representable. It stops being fine the moment a proof is asked to *name* the model:
writing `grok-4.5` on the strength of an assumption would be precisely the
fabrication this packet exists to prevent.

The runner has since moved from 1.0.0 to 1.0.3, and its default changed from
`grok-4.5` to `grok-4.6`. So the answer could not be inferred from today's default
either.

## What these files show

The grok CLI persists per-session metadata under
`~/.grok/sessions/<url-encoded cwd>/<session-id>/`. The `session_dir_hint` recorded
in #1227's `AUDIT_PROMPT_CUSTODY_R2.json` names both session ids, which is the chain
from custody record to session directory to served model.

| File | Field | Value |
|---|---|---|
| `completed-run-019ff62b-summary.json` | `current_model_id` | `grok-4.5` |
| `completed-run-019ff62b-signals.json` | `primaryModelId` | `grok-4.5` |
| `killed-attempt-019ff628-summary.json` | `current_model_id` | `grok-4.5` |

Timestamps corroborate the mapping: the killed first attempt was created
`2026-08-12T13:28:26Z` and last active `13:30:46Z`; the run that produced the verdict
was created `13:31:43Z` and last updated `13:41:29Z`. That matches #1227's custody
record of a first invocation killed mid-run with 319 bytes and no verdict, followed
by a re-run from the same frozen head.

**Both sessions served `grok-4.5`.** Not the default at the time by coincidence —
recorded per session by the runner itself.

## What this does and does not establish

Establishes: the model id that the runner recorded for those sessions, which is what
makes `auditor_model: grok-4.5` a truthful statement about #1227's audit rather than
an assumption.

Does **not** establish: provider-side cryptographic attestation of the served model.
This is the runner's own record. That residual is the same one already carried for
the AGY route, and it is stated in the proof rather than papered over.

## Custody

These bytes were copied unmodified from live runner state, which is mutable and
prunable — the CLI had already upgraded itself underneath this work once. sha256 for
each file is recorded in `../../VALIDATION.json`. `~/.grok` was not written to.

The #1227 custody file is **not** edited by this packet. Resolving its
`UNKNOWN_TO_PRODUCER` field is work for that packet's own lane, after this one merges.
