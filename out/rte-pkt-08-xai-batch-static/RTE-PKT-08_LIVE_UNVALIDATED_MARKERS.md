# RTE-PKT-08 Live-Unvalidated Markers

## Marker Locations

| Marker | Location | Meaning |
| --- | --- | --- |
| `STATIC_FIXTURE_VALIDATED` | `BATCH_STATIC_PROOF_MARKERS` in `batch_clients.py`; parser reports and static proof output | Local fixtures exercised the parser/correlation paths. |
| `DOWNLOADED_JSONL_MISSING_IF_NOT_FOUND` | `BATCH_STATIC_PROOF_MARKERS`; downloaded inventory proof | Downloaded provider JSONL artifacts were not found locally. |
| `NOT_LIVE_VALIDATED` | `BATCH_STATIC_PROOF_MARKERS`; parser reports and static proof output | Static fixture validation does not prove live provider behavior. |
| `LIVE_VALIDATION_REQUIRED` | `BATCH_STATIC_PROOF_MARKERS`; downloaded inventory and unknowns ledger | Submit/poll/retrieve/cancel and actual provider file shapes remain unproven. |
| `NO_PROVIDER_CALLS_PERFORMED` | `BATCH_STATIC_PROOF_MARKERS`; no-provider attestation | Validation used local fixtures and fake clients only. |

## Boundary

The markers apply to static parser and proof confidence. They do not declare live readiness, production readiness, remote file lifecycle correctness, or provider retention behavior.
