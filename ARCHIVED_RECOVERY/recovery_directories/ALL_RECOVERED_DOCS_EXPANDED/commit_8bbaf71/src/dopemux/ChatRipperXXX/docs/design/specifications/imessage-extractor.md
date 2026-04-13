Title: iMessage Extractor Spec
Status: Draft | Owner: XtractXact | Last Updated: 2025-09-02 PT

## Context

* Goal: Full-fidelity iMessage ingestion on macOS (local disk) with replies, reactions, attachments, and voice notes, producing canonical Message records that feed transform → redact → index → enrich (local-first) flows.
* Scope Now: macOS `~/Library/Messages/chat.db` (+WAL) and `~/Library/Messages/Attachments/**`. Copy binaries to an output workspace; transcribe audio locally when enabled.
* Near-Next: iPhone (USB backup) and iCloud paths (specified at a high level; gated behind OPEN_QUESTIONS).
* Alignment: DB-first extraction (see ADRs), Dialogue JSONL canon (INTERFACES.md), CLI principles & safety (INTERFACES.md), AC performance & privacy gates (ACCEPTANCE_CRITERIA.md, NON_FUNCTIONAL.md).

## System Overview (C4 L2 positioning)

* Component: iMessageExtractor lives in Ingestor (source → raw Messages). Downstream: Transformer → PolicyShield → Indexer → LocalEnricher → (optional) CloudEnricher. See ARCHITECTURE.md for containers and flow.

## Key Flows

1. **Mac Local Disk (Primary)**

   * Preflight: ensure Full Disk Access for process; copy `chat.db` + `chat.db-wal` to a temp path, then open read-only.
   * SQL mapping:

     * `message` rows → canonical Message; `handle` resolves participants; `chat` + join tables map `conv_id`.
     * **Reactions:** fold Tapbacks; associate by `associated_message_guid` + `assoc_type` (2000–2005); do not emit as standalone rows.
     * **Replies:** populate `reply_to_msg_id` using `associated_message_guid` mapping (stable id).
     * **Attachments:** join `message_attachment_join` → `attachment`; fill `attachments[]` (type, filename, abs_path?, mime/uti). If `--copy-binaries`, copy to workspace and set `abs_path` to copied file.
   * **Provenance:** always emit `source_ref={"guid": <chat_guid>, "path": <original_db_path>}`.
* **Voice Notes:** when `--transcribe-audio local`, run local transcription on audio attachments; store transcript entries in `source_meta.transcripts[]`. Cloud transcription is disallowed by policy (attachments never uploaded). In backup mode, transcription resolves hashed fileIDs via Manifest.db without requiring `--copy-binaries`.
   * Output: newline-delimited Message JSON (pre-redaction), validating message.schema.json (all required fields).

2. **iPhone (USB Backup) — Outline**

   * Path: acquire backup (encrypted ok with password), locate messages database + attachments; run the same normalizer. **Open Question:** preferred toolchain and UX.

3. **iCloud — Outline**

   * If Messages-in-iCloud off: messages in device backup → treat like USB backup.
   * If on: messages E2EE mirror (specialized tooling). **Open Question:** whether we support this path and required creds/UX. Until decided, we only implement a local completeness scan (see below).

## Data Model Mapping → Canonical Message

* Conforms to message.schema.json fields (ids, timestamps, sender/is_me, text, reply_to_msg_id?, reactions[], attachments[], source_ref, source_meta).
* **Reactions:** `{"from","kind","ts"}` folded under the reacted message, not separate messages.
* **Attachments:** `{"type","filename","abs_path?","mime_type?","uti?","transfer_name?"}` as per schema; attachments are never uploaded to cloud.

## Operational Concerns

* **Safety & Privacy:** Cloud is OFF by default; any cloud path requires Policy Shield preflight on redacted inputs; attachments never go to cloud.
* **Determinism:** seed-fixed downstream; provenance required in all outputs (contact, platform, source_ref).
* **Performance Targets:** aim ≥ 5k msgs/min/contact for extraction (dev laptop) per NON_FUNCTIONAL.md.
* **Validation:** 100% schema-valid outputs; CI enforces schema, policy, and coverage gates.

## Completeness & Evicted Attachments

* **Local Completeness Scan:** after extraction, scan all attachment records and report any whose file is missing on disk to `out/missing_attachments.json`.
* **Actionable Report:** include per-chat counts and example filenames for user remediation (e.g., “open chat → info → Download All Attachments”).
* **Automation:** Open question: OS-supported automation to force downloads at scale (manual process is acceptable short-term).

## CLI (canonical)

```bash
chatx imessage pull --contact "<phone|email|name>" \
  [--db ~/Library/Messages/chat.db | --from-backup "~/Library/Application Support/MobileSync/Backup/<UDID>"] [--backup-password <pw>] \
  [--include-attachments] [--copy-binaries] \
  [--transcribe-audio local|off] [--report-missing|--no-report-missing] \
  [--out ./out]
```

## Testing (ties to TEST_STRATEGY.md)

* Provide golden fixture with reply + reaction + attachment; assert folded reactions, stable `reply_to_msg_id`, provenance, schema-valid JSON; add perf smoke per NON_FUNCTIONAL.md.

## Risks & Mitigations (excerpts)

* Missing attachments due to iCloud optimization → Completeness Report + operator instructions (mitigation now; automation later).
* Voice transcription drift → deterministic local models, store transcript in `source_meta`, keep original audio.

## Appendix — Developer Prompts (for CODEGEN slices)

* See the prompts included in the planning message; they reference schemas and ACs to ensure outputs meet CI gates.
