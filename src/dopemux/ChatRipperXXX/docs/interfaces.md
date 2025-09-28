Title: Interfaces & Contracts
Status: Master | Owner: You | Last Updated: 2025-09-02 PT

Principles
- Local-first operation; deterministic transforms; strict provenance.
- Mandatory **Policy Shield** pre-cloud redaction with coverage thresholds (default 0.995; strict 0.999).
- Cloud is **disabled by default** and MAY only be used after a successful preflight on **redacted** inputs. **Attachments are NEVER uploaded.**
- Coarse label taxonomy is shared to cloud when needed; fine-grained labels remain local-only.
- Evidence-based outputs: answers MUST include citations to retrieved chunks/messages.
- Local model default: gemma-2-9b (quantized, deterministic: streaming off; fixed seed).
- Cloud calls REQUIRE passing Policy Shield preflight and explicit --allow-cloud.

CLI (explicit pipeline — canonical)
```
# Extraction
chatx imessage pull --contact "<phone|email|name>" \
  [--db ~/Library/Messages/chat.db | --from-backup <~/Library/Application Support/MobileSync/Backup/<UDID>>] \
  [--backup-password <pw>] \
  [--include-attachments] [--copy-binaries] \
  [--transcribe-audio local|off] [--report-missing|--no-report-missing] \
  [--out ./out]
chatx instagram pull --zip ./instagram.zip --user "<Your Name>" [--author-only "<username>"] [--out ./out]
chatx imessage audit --db ~/Library/Messages/chat.db [--contact <id>] [--out ./out]
chatx imessage pdf --pdf ./conversation.pdf --me "<Your Name>" [--ocr] [--out ./out]
chatx whatsapp pull --input ./export.json|.txt [--out ./out]

# Transform & Redact
chatx transform --input ./out/messages.jsonl --to jsonl --chunk turns:40 --stride 10 --contact "<id>"
chatx redact --input ./out/chunks.jsonl --pseudonymize --opaque --threshold 0.995 --salt-file ./salt.key --report ./out/redaction_report.json [--enable-dp --dp-epsilon 1.0 --dp-delta 1e-6]
chatx preflight cloud --input ./out/redacted/*.json --threshold 0.995 --hardfail-classes csam
# Enrichment backends
chatx enrich messages --contact "<key>" --backend local|cloud|hybrid \
  --local-model "gemma-2-9b-q4_K_M" --tau 0.7 --tau-low 0.62 --tau-high 0.78 \
  --allow-cloud [--batch 100] [--context 2] [--max-out 800] [--no-hosted-retrieval]
chatx enrich units    --contact "<key>" --backend local|cloud|hybrid \
  --local-model "gemma-2-9b-q4_K_M" --tau 0.7 --tau-low 0.62 --tau-high 0.78 \
  --allow-cloud [--window turns:50]
chatx redact    --input ./out/chunks/*.json --pseudonymize --opaque --threshold 0.995 [--strict] --salt-file ./salt.key --report ./out/redaction_report.json [--enable-dp --dp-epsilon 1.0 --dp-delta 1e-6]

# Index
chatx index     --input ./out/redacted/*.json --store chroma --collection chatx_<contact>

# Labeling / Issues / Episodes / Graph
chatx label build        --contact "<key>" [--taxonomy ./labels.yml]
chatx issues build       --contact "<key>" [--gap-hours 12]
chatx episodes detect    --contact "<key>" --types fight,topic
chatx issues graph build --contact "<key>" [--lag-weeks 8] [--theta 0.35] [--nmin 4]
chatx backfill          --contact "<key>" [--raw ./raw.json] [--labels ./labels.yml] [--since <date>] [--until <date>] [--out ./out]

# Enrichment (local-first cascade; cloud optional after preflight)
chatx enrich messages  --contact "<key>" --backend local|cloud|hybrid --local-model "<id>" --tau 0.7 --allow-cloud [--batch 100] [--context 2] [--max-out 800] [--no-hosted-retrieval]
chatx enrich units     --contact "<key>" --backend local|cloud|hybrid --local-model "<id>" --tau 0.7 --allow-cloud [--window turns:50]

# Retrieval & Assist
chatx query    "<question>" --contact "<key>" [--since <date> --until <date>] [--labels-any <...>] [--labels-all <...>] [--labels-not <...>] --k 32 --retriever local|cloud [--allow-cloud]
chatx simulate "<what-if>"  --contact "<key>" [--allow-cloud]
chatx reply    --contact "<key>" --message-id <id> --tone "warm+direct" [--allow-cloud]

# Ops & Safety
chatx timeline show   --contact "<key>" [--label intimacy_connection] [--period weekly]
chatx factors analyze --contact "<key>" --label intimacy_connection --window P14D
chatx tokens  inspect --ledger ./out/token_ledger.json --id <id8>
chatx preflight cloud --input ./out/redacted/*.json --threshold 0.995 --hardfail-classes csam
```

Deprecated Aliases (effective 2025-08-16)
> Umbrella shortcuts are deprecated in favor of explicit pipeline commands and MAY be removed after one minor release.
- `chatx ingest …` → replace with: `imessage|instagram|whatsapp pull` → `transform` → `redact` → `index`.
- `chatx reindex …` → replace with targeted rebuilds using: `transform`, `index`, `label build`, `issues build`, `episodes detect`, `issues graph build`.

Canonical Schemas (reference)
- Message (pre-redaction)
```json
{
  "msg_id":"string","conv_id":"string","platform":"imessage|instagram|whatsapp|txt",
  "timestamp":"ISO-8601","sender":"string","sender_id":"string","is_me":true,
  "text":"string","reply_to_msg_id":"string|null",
  "reactions":[{"from":"string","kind":"love|like|...","ts":"ISO-8601"}],
  "attachments":[{"type":"image|video|audio|file","filename":"...","abs_path":"...","mime_type":"...","uti":"..."}],
  "source_ref":{"guid":"string","path":"string"}
}
```
- Chunk (LLM-ready; redacted for any cloud path)
```json
{
  "chunk_id":"string","conv_id":"string","text":"concat lines",
  "meta":{"contact":"CN_<id6>","platform":"imessage","date_start":"...","date_end":"...",
           "labels_coarse":["..."],"episode_ids":["..."]}
}
```
- Enrichment (message-level)
```json
{
  "msg_id":"string","speech_act":"ask|inform|promise|refuse|apologize|propose|meta",
  "intent":"string","stance":"supportive|neutral|challenging","tone":"string",
  "emotion_primary":"joy|anger|fear|sadness|disgust|surprise|neutral",
  "certainty":0.0,"directness":0.0,"boundary_signal":"none|set|test|violate|reinforce",
  "repair_attempt":false,"inferred_meaning":"<=25 words","map_refs":["msg_id"],
  "confidence_llm":0.0,"source":"local|cloud"
}
```
- CU Enrichment (conversation-unit)
```json
{
  "cu_id":"string","topic_label":"<=6 words","vibe_trajectory":["tone"],
  "escalation_curve":"low|spike|high|resolve",
  "ledgers":{"boundary":[],"consent":[],"decisions":[],"commitments":[]},
  "evidence_index":["msg_id"],"confidence_llm":0.0,"source":"local|cloud"
}
```
// Message (post-redaction view)
```json
{ "msg_id":"str", "body_redacted":"str",
  "pseudonyms":{"me":"ME","other":"CN_<id6>"},
  "shield":{"coverage":0.0,"strict":false,"hardfail_triggered":false},
  "provenance":{"schema_v":"semver","run_id":"uuid","source_hash":"sha256"} }
```

// Chunk (LLM-ready; redacted only; now with message_ids)
```json
{ "chunk_id":"str","conv_id":"str","text":"str",
  "meta":{"contact":"CN_<id6>","platform":"str",
          "date_start":"ISO-8601","date_end":"ISO-8601",
          "message_ids":["str"], "labels_coarse":["str"], "episode_ids":["str"]},
  "provenance":{"schema_v":"semver","run_id":"uuid","source_hash":"sha256"} }
```

// Enrichment (per message) — unchanged fields + audit/provenance
```json
{ "msg_id":"str", "speech_act":"ask|inform|promise|refuse|apologize|propose|meta",
  "intent":"str","stance":"supportive|neutral|challenging","tone":"str",
  "emotion_primary":"joy|anger|fear|sadness|disgust|surprise|neutral",
  "certainty":{"val":0.0}, "directness":{"val":0.0},
  "boundary_signal":"none|set|test|violate|reinforce", "repair_attempt":false,
  "inferred_meaning":"<=200 chars","map_refs":["msg_id"],
  "coarse_labels":["str"], "fine_labels_local":["str"],
  "confidence_llm":0.0, "source":"local|cloud",
  "provenance":{"schema_v":"semver","run_id":"uuid","model_id":"str","prompt_hash":"sha256"} }
  ```

// CU Enrichment
```json
{ "cu_id":"str","topic_label":"<=6 words","vibe_trajectory":["tone"],
  "escalation_curve":"low|spike|high|resolve",
  "ledgers":{"boundary":[],"consent":[],"decisions":[],"commitments":[]},
  "issue_refs":["str"], "coarse_labels":["str"], "fine_labels_local":["str"],
  "evidence_index":["msg_id"],
  "confidence_llm":0.0,"source":"local|cloud",
  "provenance":{"schema_v":"semver","run_id":"uuid","model_id":"str","prompt_hash":"sha256"} }
  ```

HTTP APIs (optional; **disabled by default**)
> The HTTP server is for **local/dev** only. It MUST bind to loopback (127.0.0.1) and enforce Policy Shield rules.
> Each request MUST complete within **60s** or stream partials.

### Common
- **Base:** `http://127.0.0.1:<port>/v1`
- **Headers:** `Content-Type: application/json`, `Accept: application/json`; optional `X-Request-Id` echoed in responses.
- **AuthZ:** Local user only (loopback). No tokens required by default.
- **Safety gates:** Cloud work requires `"allow_cloud": true` **and** a passing preflight on the **redacted** inputs. Fine labels NEVER leave device; attachments are never uploaded.
- **Errors:** RFC‑7807 JSON with fields: `error`, `code`, `detail`, `hint`.
- **Streaming:** If the server cannot complete within 60s, it MAY stream partials; otherwise it MUST return `TIMEOUT`.

### 1) POST /v1/query — Question answering with filters
**Purpose**: Answer a question over a contact’s conversations; honor time/label filters; return citations.

**Request (JSON)**
```json
{
  "contact": "CN_123abc",
  "question": "What changed after February?",
  "filters": {
    "since": "2025-02-01",
    "until": "2025-03-01",
    "labels_any": ["attention_availability","time_scarcity"],
    "labels_all": [],
    "labels_not": []
  },
  "k": 32,
  "retriever": "local",
  "allow_cloud": false
}
```

**Response (JSON)**
```json
{
  "answer": "Concise synthesis grounded in retrieved chunks.",
  "citations": [
    {"chunk_id":"ch_01ab","msg_ids":["m_1001","m_1007"],"score":0.83}
  ],
  "retrieval": {"k":32,"retriever":"local","filters":{"since":"2025-02-01","until":"2025-03-01"}},
  "metrics": {"tokens_in":0,"tokens_out":0,"latency_ms":0}
}
```

**Validation rules**
- `contact` MUST reference a known contact key (e.g., `CN_<id6>`).
- Filter labels MUST be members of the **coarse** taxonomy.
- Citations MUST be returned (non-empty) unless `"answer"` is an explicit refusal with an error code.

### 2) POST /v1/simulate — What‑if scenario over retrieved context
**Purpose**: Outline likely dynamics given a hypothetical message/tone; return evidence refs used.

**Request (JSON)**
```json
{"contact":"CN_123abc","scenario":"If I say 'I need more reliability' in a warm+direct tone, how is it likely received?","allow_cloud":false}
```
**Response (JSON)**
```json
{"simulation":"Expected responses/dynamics with caveats","evidence_refs":[{"chunk_id":"ch_01ab","msg_ids":["m_1001","m_1007"]}]}
```

### 3) POST /v1/reply — Suggest a reply grounded in recent context
**Purpose**: Draft a reply for a specific message window and tone; return citations.

**Request (JSON)**
```json
{"contact":"CN_123abc","message_id":"m_456","tone":"warm+direct","allow_cloud":false}
```
**Response (JSON)**
```json
{"suggested_reply":"Drafted text with one concrete next step.","citations":[{"msg_id":"m_451"}]}
```

### Error Catalog (RFC‑7807)
All endpoints MUST return:
```json
{"error":"<Type>","code":"<MACHINE_CODE>","detail":"...","hint":"..."}
```
Required codes:
- `INVALID_INPUT` — schema/field errors.
- `INVALID_CONTACT` — unknown `contact` or message scope invalid.
- `POLICY_SHIELD_FAILURE` — preflight failed or hard‑fail class detected.
- `CLOUD_DISABLED` — cloud requested when disabled or not explicitly allowed.
- `TIMEOUT` — exceeded 60s without streaming.
- `INTERNAL` — unexpected failure with correlation id.

## Differential Privacy

The system supports (ε,δ)-differential privacy for statistical aggregation, enabling safe sharing of aggregate insights while protecting individual privacy.

### Privacy Parameters
- **Epsilon (ε)**: Privacy parameter controlling noise level (default: 1.0, smaller = more private)
- **Delta (δ)**: Failure probability for (ε,δ)-DP guarantees (default: 1e-6)
- **Sensitivity**: Query sensitivity for noise calibration (automatically determined per query type)

### Supported Query Types
- **Count queries**: `COUNT(*)` with optional filters on coarse labels
- **Sum queries**: `SUM(field)` for numerical aggregation  
- **Mean queries**: `AVG(field)` with bounded value ranges
- **Histogram queries**: Distribution analysis with configurable bins

### Integration Points
- **PolicyShield Integration**: `--enable-dp --dp-epsilon 1.0 --dp-delta 1e-6` on `chatx redact`
- **Statistical Summaries**: Privacy-safe aggregate reports for cloud processing
- **Budget Management**: Automatic privacy budget composition across multiple queries
- **Deterministic Noise**: Reproducible results with salt-based seeding

### Privacy Guarantees
The implementation provides formal (ε,δ)-differential privacy with:
- Calibrated Laplace noise injection based on query sensitivity
- Privacy budget tracking and composition
- Non-negativity constraints for realistic statistical outputs
- Integration with existing redaction and preflight validation

SLAs & Limits
- Requests MUST finish in ≤60s or stream partials.
- Default LLM output tokens ≤800; context packing ±2 turns.
- Observability: structured logs and artifacts (e.g., `redaction_report.json`); echo `X-Request-Id` if provided.
- Gate defaults: τ=0.7; hysteresis τ_low=0.62, τ_high=0.78 (reduce thrash).
- Default chunking: turns:40, stride:10 for dense chats; use daily for sparse days.
- Redaction coverage threshold: ≥0.995 (≥0.999 with --strict); hard-fail classes block cloud.

Change Log (since 2025-08-15)
- Normalized CLI section and deprecated aliases.
- Finalized HTTP request/response shapes, validation rules, and error catalog; confirmed 60s/streaming SLA.
- iMessage CLI: added `--copy-binaries`, `--transcribe-audio local|off`, and `--report-missing` options; missing attachments report defined with non-error exit semantics when attachments are missing.
- iMessage backup mode: `--from-backup` and optional `--backup-password`. In backup mode, attachments resolve via Manifest.db (hashed fileIDs) and can be copied with `--copy-binaries`; transcription can resolve backup files without copying.

## CLI: Index Metadata Update (no re-embedding)
- **Name | Command | Purpose**
  - Index Metadata Update | `chatx index update --collection <name> [--enrich-msg <path>] [--enrich-cu <path>] [--id-map <path>] [--dry-run] [--upsert-fields <csv>]` | Merge enrichment metadata into existing vectors **without** changing embeddings or redacted text.

- **Behavior**
  - Reads one or both enrichment files:
    - `--enrich-msg` → `enrichment_message.jsonl` (per-message; must validate `SCHEMAS/enrichment_message.schema.json`)
    - `--enrich-cu`  → `enrichment_cu.jsonl` (per conversation-unit; must validate `SCHEMAS/enrichment_cu.schema.json`)
  - Resolves targets by:
    - Message-level: upserts metadata onto all **chunks** whose `meta.message_ids[]` contains `msg_id`.
    - CU-level: upserts metadata onto all chunks whose `chunk_id` or `msg_id`s intersect the CU `evidence_index[]`.
  - Fields upserted by default (if present):
    - From message enrichment: `coarse_labels`, `influence_class`, `influence_score`, `stance`, `tone`, `emotion_primary`, `boundary_signal`, `repair_attempt`.
    - From CU enrichment: `topic_label`, `vibe_trajectory`, `escalation_curve`, `ledgers.*`, `issue_refs`, `coarse_labels`.
  - `--upsert-fields <csv>` limits the set of keys to merge; unknown keys are ignored by default.
  - **Never** modifies embeddings or `text`. If a change to `text` or vectors is requested, the command MUST fail with `POLICY_EMBEDDING_IMMUTABLE`.
  - `--id-map <path>` (optional) provides a JSON object for GUID/ROWID reconciliation if needed during iMessage mapping.
  - `--dry-run` prints a summary (counts per field, matched chunks, skipped) and exits **without** writing.

- **Input Schema (logical)**
  - `enrichment_message.jsonl` lines MUST conform to `SCHEMAS/enrichment_message.schema.json`.
  - `enrichment_cu.jsonl` lines MUST conform to `SCHEMAS/enrichment_cu.schema.json`.

- **Output**
  - Writes metadata updates to the `<collection>` in Chroma.
  - Emits `out/reports/index_update_report.json` like:
    {
      "collection": "chatx_<contact>",
      "updated_chunks": 123,
      "skipped_no_match": 7,
      "fields_upserted": ["coarse_labels","stance","emotion_primary","topic_label"],
      "dry_run": false
    }

- **Errors**
  - `SCHEMA_INVALID`, `COLLECTION_NOT_FOUND`, `POLICY_EMBEDDING_IMMUTABLE`, `ID_RESOLUTION_FAILED`
  - RFC-7807 fields: `type`, `title`, `status`, `detail`, `code`.

- **SLA**
  - 25k upserts/min on a developer laptop (best-effort).
### CLI Error Model (RFC‑7807)
- Flag: `--error-format json|text` (default: text). When `json`, fatal CLI errors are emitted as Problem JSON on stderr and exit non‑zero.
- Common error codes:
  - `INVALID_INPUT` — invalid arguments or failed parse (e.g., bad ZIP)
  - `MISSING_DB` — Messages `chat.db` not found (iMessage paths)
  - `MISSING_BACKUP_DIR` — backup directory not found
  - `ENCRYPTED_BACKUP_PASSWORD_REQUIRED` — encrypted backup requires password
  - `MISSING_ZIP` — Instagram data ZIP not found
  - `UNSAFE_ZIP_ENTRY` — ZIP contains an unsafe member path (blocked)
  - `NO_VALID_ROWS` — all rows failed schema validation (see `out/quarantine/messages_bad.jsonl`)

Example (stderr):
```json
{
  "type": "https://chatx.local/problems/NO_VALID_ROWS",
  "title": "No valid rows",
  "status": 1,
  "detail": "All rows failed schema validation; see quarantine/messages_bad.jsonl",
  "instance": "./out/messages_friend.json",
  "code": "NO_VALID_ROWS"
}
```
