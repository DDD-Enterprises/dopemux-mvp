# RTE-PKT-09 Future Proof Artifact Schema

This schema defines required artifact families for a future live validation run. It is not an implementation schema for current runtime code.

## Required Future Artifacts

`LIVE_VALIDATION_MANIFEST.json`
- packet ID
- run ID
- repo root
- branch
- git SHA
- clean status before run
- operator authorization reference
- providers authorized
- models authorized
- spend cap
- timeout cap
- batch cap
- artifact root
- validation commands
- no-secret scan result
- cleanup status

`LIVE_PROVIDER_PREFLIGHT.json`
- provider
- route kind
- requested model
- auth status
- model availability status
- rate/quota status if available
- account identifiers redacted
- retention/ZDR observed/unknown marker
- not billing truth marker

`LIVE_RESPONSE_METADATA_MATRIX.json`
- provider
- route kind
- transport
- requested model
- returned model
- effective model
- response ID
- status code
- finish reason
- usage
- refusal field or null marker
- incomplete field or null marker
- provider error reason
- redacted request metadata reference
- redacted response summary reference

`LIVE_STRUCTURED_OUTPUT_RESULTS.json`
- provider
- route kind
- requested model
- response format type
- schema name
- schema hash
- schema acceptance result
- local schema validation result
- provider failure or success
- no silent downgrade marker

`LIVE_BATCH_PILOT_INDEX.json`
- provider
- route kind
- requested model
- batch ID
- request count
- custom_id map
- poll status log reference
- terminal status
- output file ID if present
- error file ID if present
- downloaded file hashes
- row count reconciliation
- missing rows
- duplicate rows
- partial failure marker
- cancel/cleanup status

`LIVE_BATCH_OUTPUT_ERROR_INVENTORY.md`
- file inventory
- hashes
- line counts
- parsed row counts
- invalid row counts
- output row shape summary
- error row shape summary
- redacted excerpts only
- reconciliation result

`LIVE_RETENTION_ZDR_EVIDENCE.md`
- provider
- account scope redacted
- evidence source
- evidence timestamp
- ZDR verdict
- retention verdict
- remote file lifecycle verdict
- cleanup/deletion result
- unknowns

`LIVE_SPEND_ESTIMATE.md`
- cap
- estimated spend
- provider-reported usage if available
- explicit not-billing-truth statement
- billing truth evidence status

`LIVE_REDACTION_SCAN_REPORT.md`
- scanned artifact root
- scanner command
- patterns classed by risk
- hits
- dispositions
- blocking status

`LIVE_VALIDATION_SUMMARY.md`
- lane verdicts
- findings disposition
- evidence references
- failures
- remaining unknowns
- next-step recommendation

`LIVE_NO_SECRET_ATTESTATION.md`
- credentials not printed
- headers not stored
- raw payloads not committed
- downloaded files scanned
- any redactions performed

`LIVE_ROLLBACK_CLEANUP_REPORT.md`
- local artifact rollback path
- remote validation-created jobs
- remote validation-created files
- cancel attempts
- deletion attempts if authorized
- remaining remote resources
- manual operator action required

## Serialization Rules

JSON artifacts:
- UTF-8
- stable top-level key order where practical
- explicit nulls for unavailable live fields
- no implicit success defaults
- evidence references must point to local artifact paths

Markdown artifacts:
- concise
- evidence-labeled
- no unredacted secrets
- no raw provider payload dumps
- no billing truth overclaim

## Required Evidence Labels

Use only:
- `OBSERVED`
- `INFERRED`
- `CLAIMED`
- `UNKNOWN`
- `CONFLICTING`
- `RECOMMENDED`
- `LIVE_VALIDATION_REQUIRED`
- `MISSING`
- `BLOCKING`
- `ACCEPTED_WITH_RISK`
