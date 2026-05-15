# RTE-PKT-09 Retention And ZDR Evidence Plan

This is a future evidence plan only. It does not assert provider retention, ZDR, storage, or deletion truth.

## Evidence Classes

Acceptable future evidence:
- provider account setting observed through an authorized redacted API or console export
- response header or API field that directly states retention/ZDR behavior
- provider documentation captured with date and source, clearly marked as provider-claimed
- remote file lifecycle evidence for validation-created artifacts
- cleanup/delete result for validation-created files, if separately authorized

Insufficient evidence:
- SDK defaults
- blog posts without account-specific applicability
- environment variable names
- credentials being present
- static code support for a provider
- local estimates
- assumptions from OpenAI-compatible API shape

## Redaction Requirements

Must redact:
- account IDs unless operator separately authorizes their inclusion
- organization IDs
- project IDs
- request headers
- credential values
- raw provider payloads
- billing identifiers
- file content unless synthetic and explicitly allowed

Allowed:
- boolean setting presence
- redacted setting names
- provider name
- validation-created file IDs in redacted or hashed form when needed for cleanup proof
- response header names without values unless value is non-sensitive and relevant

## Future Retention/ZDR Artifact

`LIVE_RETENTION_ZDR_EVIDENCE.md` must include:
- provider
- account scope, redacted
- evidence source
- evidence timestamp
- whether evidence is observed, claimed, inferred, missing, or conflicting
- ZDR status
- retention status
- remote file lifecycle status
- cleanup/deletion authorization status
- cleanup/deletion result
- residual unknowns

## Stop Conditions

Stop if:
- provider evidence would expose secrets
- account identifiers cannot be redacted
- cleanup target was not created by the validation run
- cleanup/deletion was not explicitly authorized
- evidence is only inferred but would be reported as observed
- provider documentation conflicts with observed account/API behavior

## Verdict Rules

Allowed verdicts:
- `NOT_TESTED`
- `CLAIMED_BY_PROVIDER_DOCS_ONLY`
- `OBSERVED_ACCOUNT_SETTING_REDACTED`
- `OBSERVED_RESPONSE_HEADER_REDACTED`
- `OBSERVED_REMOTE_FILE_LIFECYCLE`
- `UNKNOWN`
- `CONFLICTING`

ZDR and retention must remain `UNKNOWN` unless direct provider/account/API evidence is captured and redacted.
