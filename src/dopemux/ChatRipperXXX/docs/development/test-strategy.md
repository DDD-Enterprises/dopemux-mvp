Test Strategy (TDD)

Status: Draft | Owner: You | Last Updated: 2025-09-02 PT

Goals

Operationalize ACCEPTANCE_CRITERIA.md and NON_FUNCTIONAL.md into concrete tests: schema validation, redaction coverage gates, determinism, performance smoke, HTTP contracts.

Suites
	1.	Schemas (unit)
	•	Validate all produced JSON (message/chunk/enrichment/error/redaction_report) against SCHEMAS/*.json.
	•	MUST run in CI on each slice.
	2.	Extractor – iMessage (integration)
	•	Fixture chat.db with: plain text, one reply, one reaction (each kind), one attachment.
	•	Assert: fields present; ISO timestamps; reactions folded; stable reply_to_msg_id; source_ref populated; source_meta preserves raws.
	3.	Transform & Chunking (unit+integration)
	•	Given messages.jsonl → chunk windows (turns & daily) deterministic; include message_ids[], meta dates, labels if present.
	•	Round-trip stability: re-chunking unchanged inputs yields identical outputs.
	4.	Redaction & Preflight (policy)
	•	Coverage ≥ 0.995 normal (≥ 0.999 strict) on fixture spans; report validates to redaction_report.schema.json.
	•	Negative cases: visibility leak (fine labels/attachments) triggers E_VISIBILITY_LEAK; hard-fail classes trigger E_HARDFAIL_CLASS.
	5.	Index & Retrieval
	•	Index chunks w/ Chroma; filtered retrieval by contact/time/labels returns expected chunk/message ids; latency smoke.
	6.	Enrichment (local)
	•	Schema-valid outputs; seed-fixed determinism; confidence calibration drift within bounds.
	•	Cache hit tests on re-runs; provenance fields populated.
	7.	Hybrid (cloud)
	•	Gate by τ=0.7; cloud only after successful preflight; context packing ±2 turns; output tokens ≤ 800.
	•	Merge policy: retain higher-confidence fields; record source="cloud"; provenance verified.
	8.	HTTP API Contracts
	•	/v1/query|simulate|reply payload success & errors (RFC-7807); 60s timeout path; echo X-Request-Id; citations non-empty.
	9.	Determinism & Observability
	•	Repeat runs identical (or cache hits) given same redacted inputs/seeds.
	•	Artifacts existence: redaction_report.json, metrics logs, token ledger.

Coverage & Quality Gates
	•	New code ≥ 90% coverage; mypy clean; lint clean.
	•	Performance smoke: ingest ≥ 5k msgs/min (dev laptop), local enrich p95 ≤ 250 ms/msg (quantized), per NON_FUNCTIONAL.md.
