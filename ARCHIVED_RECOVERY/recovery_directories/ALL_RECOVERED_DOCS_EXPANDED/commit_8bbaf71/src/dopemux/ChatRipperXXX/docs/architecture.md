# ChatX/ChatRipper Architecture
*Status: Master | Owner: Team | Last Updated: 2025-09-02*

## Context & Goals

**Problem:** We need a private, local-first forensic chat analysis tool that ingests large multi-platform exports, redacts and pseudonymizes sensitive data, enriches messages with structured meaning, and supports retrieval/analytics—while optionally escalating to cloud LLMs under strict controls.

**Goals:**
- Local-first enrichment with optional cloud escalation guarded by **Policy Shield**
- Deterministic, schema-locked outputs with evidence links and full **provenance**
- Fast ingestion/indexing and low-latency retrieval over large corpora (50k–1M messages)
- CI-enforced **privacy, validation, and performance** gates
- Extensible adapters for new sources, models, stores

**Non-Goals:**
- No always-on cloud processing (cloud is opt-in per run)
- No GUI (CLI-only surface in this scope)
- No attachment uploads to cloud

---

## System Overview (C4 Level 1-2)

### External Systems & Users
- **User (Analyst)** runs CLI on a workstation
- **Cloud LLM Providers** (optional) receive only **redacted** text and **coarse** labels
- **Filesystem** stores inputs, outputs, artifacts under `./out/`
- **Optional: Vector Store (Chroma)** hosts per-contact collections on-device

### Core Components

1. **Ingestor** — parses iMessage DB/PDF, Instagram JSON, WhatsApp JSON, TXT into canonical **Message** records
2. **Transformer** — normalizes, sessionizes, and **chunks** conversations (turns:40 or daily windows)
3. **Policy Shield** — pseudonymizes people, tokenizes sensitive strings (⟦TKN:…⟧), measures redaction **coverage**; blocks hard-fail classes
4. **Differential Privacy Engine** — provides (ε,δ)-differential privacy for statistical aggregation with calibrated noise injection and budget management
5. **Indexer** — writes redacted chunks + facets to **Chroma** collections (per contact) for retrieval
6. **Local Enricher** — on-device LLM generates **Message/CU Enrichment** (schema-locked, deterministic)
7. **Hybrid Orchestrator** — gates by confidence **τ=0.7** and preflight; if allowed, performs **Cloud Enrichment** with minimal context and token ceilings
8. **Validator** — enforces JSON Schemas; clamps enums & bounds; quarantines invalid rows
9. **Observer** — metrics, logs, artifacts (e.g., `redaction_report.json`, validation summaries)

---

## Module Boundaries

- **cli/** — argument parsing, commands
- **core/** — business logic (pure functions where possible)  
- **adapters/** — external integrations (HTTP, files, models)
- **extractors/** — platform-specific data extraction (iMessage, Instagram, etc.)
- **privacy/** — differential privacy engine and mechanisms for statistical aggregation
- **redaction/** — enhanced policy shield with PII detection and DP integration
- **tests/** — unit + integration tests

---

## Key Data Flows

### 1. Extract → Transform → Redact → Index
**Trigger:** `chatx <source> pull` → `chatx transform` → `chatx redact` → `chatx index`
**Components:** Ingestor → Transformer → Policy Shield → Indexer
**Data:** Raw platform data → canonical Message JSON → normalized chunks → redacted windows → indexed collections
**Outcome:** Safe, searchable message corpus

### 2. Enrich (Local-first, Hybrid Optional)
**Trigger:** `chatx enrich messages|units --backend hybrid --tau 0.7 [--allow-cloud]`
**Components:** Local Enricher → (optional) Hybrid Orchestrator → Cloud LLM
**Data:** Redacted chunks → local enrichments → (gated) cloud enrichments
**Outcome:** Schema-locked enrichment metadata with confidence scores

### 3. Query & Analysis
**Trigger:** `chatx query "<question>" --contact "<id>"`
**Components:** Indexer (retrieval) → Local/Cloud LLM (synthesis)
**Data:** Query → relevant chunks → contextual answer with citations
**Outcome:** Evidence-backed responses

### 4. Privacy-Safe Statistical Aggregation
**Trigger:** PolicyShield statistical summary generation for cloud processing
**Components:** Differential Privacy Engine → Privacy-safe statistical queries → Noisy aggregates
**Data:** Redacted chunks → statistical queries → (ε,δ)-DP results → privacy-safe summaries
**Outcome:** Safe statistical insights for cloud processing while protecting individual privacy

---

## Data at Rest Structure

```
./out/
├── raw/           # Original platform exports
├── messages/      # Canonical Message JSON
├── chunks/        # Normalized conversation chunks  
├── redacted/      # Pseudonymized, safe data
├── enriched/      # LLM-generated metadata
├── indexed/       # Vector embeddings & search indices
├── reports/       # Validation, redaction, performance reports
└── cache/         # Prompt/output cache for efficiency
```

---

## Privacy & Security Architecture

### Policy Shield (Core Security Component)
- **Coverage Thresholds:** ≥99.5% redaction coverage required (99.9% in strict mode)
- **Pseudonymization:** Consistent tokenization of PII across sessions
- **Hard-fail Classes:** CSAM detection blocks all cloud operations
- **Preflight Validation:** All cloud-bound data validated against coverage thresholds

### Differential Privacy Engine
- **Statistical Aggregation:** (ε,δ)-differential privacy for safe statistical queries
- **Privacy Parameters:** Default ε=1.0, δ=1e-6 with calibrated Laplace noise
- **Query Types:** Count, sum, mean, histogram with proper sensitivity analysis
- **Budget Management:** Privacy budget composition and tracking across queries
- **Integration:** Seamless integration with PolicyShield redaction pipeline

### Data Classification
- **Fine-grained labels:** Remain local-only
- **Coarse labels:** Shared to cloud when necessary for enrichment
- **Statistical summaries:** Privacy-safe aggregates via differential privacy
- **Attachments:** Never uploaded to cloud under any circumstances

---

## Observability

### Logging
- Structured JSON logs at INFO level by default
- DEBUG level for troubleshooting
- All cloud API calls logged with request/response metadata (redacted)

### Metrics & Reports
- Pipeline duration and message throughput
- Redaction coverage and validation statistics
- Token usage and cost tracking for cloud operations
- Schema validation success/failure rates

### Artifacts
- `redaction_report.json` — Coverage statistics and validation
- `missing_attachments.json` — iCloud eviction reporting
- `run_summary.json` — Performance and processing statistics

---

## Extensibility Points

### New Platform Support
Implement `BaseExtractor` interface:
- `extract_messages()` → canonical Message schema
- Platform-specific SQL/API parsing
- Attachment handling with local-only policy

### New LLM Backends
Implement `BaseLLMClient` interface:
- Local models via Ollama/llama.cpp
- Cloud APIs with Policy Shield integration
- Confidence calibration and fallback strategies

### New Storage Backends
Implement `BaseVectorStore` interface:
- Chroma (default)
- pgvector, Weaviate, etc.
- Consistent query interface across implementations

---

## Performance Targets

- **Extraction:** ≥5k messages/min/contact (dev laptop)
- **Enrichment:** ≥1k messages/min local, ≥500/min hybrid
- **Query Response:** <5s for typical queries over 100k message corpus
- **Memory:** <4GB peak for 1M message processing

---

## References

- [Acceptance Criteria](acceptance-criteria.md) — User stories and test scenarios
- [Interfaces](interfaces.md) — CLI contracts and API specifications
- [Design Specifications](design/specifications/imessage-extractor.md) — Detailed component specs
- [ADRs](design/adrs/index.md) — Architecture decision records
- [Test Strategy](development/test-strategy.md) — Testing approach and coverage targets

> Update this file when boundaries or flows change. Record critical decisions in ADRs.
