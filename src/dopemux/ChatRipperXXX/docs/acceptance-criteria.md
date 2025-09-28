Title: Acceptance Criteria
Status: Draft | Owner: You | Last Updated: 2025-09-02 PT

## User Stories (Gherkin)

### Story: Extract iMessage for a single contact with replies, reactions, and provenance

* AC:

  * Given a valid `chat.db` copied to a temp path,
    When I run `chatx imessage pull --contact "<id>" [--include-attachments]`,
    Then messages MUST include `is_me`, ISO-8601 timestamps, folded reactions, and stable `reply_to_msg_id`,
    And `source_ref` MUST include the conversation GUID and original DB path,
    And the output MUST validate against `message.schema.json`.

### Story: Transform to Dialogue JSONL and chunk deterministically

* AC:

  * Given `messages.jsonl`,
    When I run `chatx transform --to jsonl --chunk turns:40 --stride 10`,
    Then chunks MUST be deterministic on re-runs with identical inputs and seeds.

### Story: Redaction Policy Shield coverage

* AC:

  * Given `chunks.jsonl`,
    When I run `chatx redact --threshold 0.995`,
    Then coverage MUST be ≥0.995 (or ≥0.999 with `--strict`),
    And a `redaction_report.json` MUST be emitted.

### Story: Index & Query with citations

* AC:

  * Given redacted chunks,
    When I run `chatx index` and `chatx query "<q>" --contact "<id>"`,
    Then answers MUST include citations to chunk/message ids.

### Story: Enrichment (Local-first)

* AC:

  * Given redacted chunks,
    When I run `chatx enrich messages --backend local`,
    Then outputs MUST include provenance and confidence,
    And schema validation MUST pass.

### Story: HTTP API contracts (localhost only)

* AC:

  * Given the dev server,
    When I call `/v1/query|simulate|reply`,
    Then responses MUST meet RFC-7807 for errors and 60s SLA,
    And echo `X-Request-Id` when present.

### Story: Copy iMessage attachments to workspace with metadata

* AC:

  * Given a valid `chat.db` and `--include-attachments --copy-binaries --out ./out`,
    When I run `chatx imessage pull --contact "<id>"`,
    Then each message’s `attachments[]` MUST include `{type, filename, abs_path?, mime_type?, uti?}` per schema,
    And binary files MUST exist under `./out/attachments/**`,
    And no attachment data MUST be uploaded to any cloud service.

### Story: Transcribe iMessage voice notes locally

* AC:

  * Given audio attachments and `--transcribe-audio local`,
    When extraction completes,
    Then each audio message MUST include a transcript stored in `source_meta.transcript` (text),
    And extraction MUST NOT send any audio to cloud,
    And transcript presence MUST NOT alter original `text` or attachment payloads except for additive metadata.

### Story: Report missing/evicted attachments for operator remediation

* AC:

  * Given `--include-attachments` and some attachment paths missing from disk,
    When extraction completes,
    Then the tool MUST emit `out/missing_attachments.json` listing `{conv_guid, msg_id, filename}` for all missing items,
    And the CLI MUST exit **0** (not an error) when messages are extracted but some attachments are missing,
    And the summary MUST include counts per conversation to guide manual fetch.
