Security & Threat Model (STRIDE-lite)

Status: Draft | Owner: You | Last Updated: 2025-09-02 PT

Data Boundaries
	•	Local-only: raw text, attachments, fine labels, salt, source_meta, logs with raw fields (guarded).
	•	Cloud-eligible: only redacted text + coarse labels after passing Policy Shield preflight.

Threats & Controls
	•	Data Exfiltration: Accidental cloud egress of raw or fine data.
	•	Control: Preflight gates; coverage thresholds; static prompt linter; CI checks E_VISIBILITY_LEAK, E_ATTACHMENT_PRESENT.
	•	Re-identification: Pseudonym reversal.
	•	Control: Salted deterministic pseudonyms; salt never logged or uploaded; .env/Parameter Store only.
	•	Provider Over-collection:
	•	Control: Token ceilings; restricted context; minimal required metadata; audit provenance of every call.
	•	Integrity/Determinism:
	•	Control: Fixed seeds; streaming off; schema validation; quarantine invalid rows; cache keyed by (model_id, model_sha, prompt_hash, source_hash, schema_v).
