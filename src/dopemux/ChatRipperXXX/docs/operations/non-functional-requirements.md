Title: Non-Functional Requirements
Status: Draft | Owner: XtractXact | Last Updated: 2025-09-02 PT

## Scope & Intent
This document defines measurable non-functional requirements (NFRs) for the **ChatX / XtractXact** toolchain. It operationalizes the local‑first + optional cloud **hybrid cascade** with strict **Policy Shield** preflight, schema‑locked enrichment, and forensic traceability. Requirements are written with RFC 2119 language and include verification methods.

## Defaults
Defaults
- Local model: gemma-2-9b-q4_K_M; temp ≤0.3; streaming off; fixed seed (deterministic).
- Chunking: turns:40, stride:10 (dense); fallback daily for sparse periods.
- Gate: τ=0.7; hysteresis τ_low=0.62, τ_high=0.78; context packing ±2 turns.
- Redaction: coverage ≥0.995 (≥0.999 strict); block hard-fail classes; attachments never uploaded.
- Targets: local tagging ≥25 msgs/s (Apple Silicon, 4-bit); detectors ≥200 msgs/s.

---

## Performance
**P1. Ingestion & Transform**
- MUST parse and normalize raw exports (iMessage PDFs/DB, Instagram JSON, WhatsApp JSON, TXT) at **≥ 10k messages/min** on a reference dev machine (8‑core CPU, 16GB RAM), excluding OCR/vision.
- SHOULD chunk conversations into windows (turns:40 or daily) at **≥ 50k messages/min**.
- Verification: timed run on 100k-message corpus; success threshold ≥ target throughput.

**P2. Redaction & Policy Shield**
- MUST achieve redaction **coverage ≥ 0.995** (strict mode **≥ 0.999**) with pseudonymization + opaque tokens ⟦TKN:…⟧ before any cloud call.
- SHOULD complete preflight on **100k messages in ≤ 120s** (p95 per 1k msgs ≤ 2s).
- Verification: redaction_report.json shows coverage; CI gate blocks if below threshold.

**P3. Local Enrichment (On‑device)**
- MUST produce schema‑valid **Message/CU Enrichment** at **≥ 25 msgs/s** average with **p95 latency ≤ 250 ms/msg** on reference machine, temp=0, fixed seed, streaming disabled.
- SHOULD maintain **confidence_llm** calibration drift ≤ ±0.05 vs golden set.
- Verification: benchmark harness with golden fixtures; JSON Schema validation pass rate = 100%.

**P4. Cloud Enrichment (Optional)**
- MUST be gated by τ=0.7 and passing preflight; MUST respect **max_output_tokens ≤ 800** and **±2 turns context** by default.
- SHOULD complete a batch of **100 target messages in ≤ 90s end‑to‑end** at QPS within provider limits; retries use exp backoff (jitter).
- Verification: provider stub + live smoke; enforce token ceilings in prompt runner.

**P5. Indexing & Retrieval**
- MUST index redacted chunks + enrichment facets for **≥ 50k messages in ≤ 90s**.
- SHOULD serve label/time queries with **p95 latency ≤ 150 ms**.
- Verification: timed index build; query latency sampling with 10k probes.

**P6. Large‑Scale Runs**
- MUST process a **1M‑message corpus** in segmented batches without OOM, with incremental checkpoints every ≤ 10k messages.
- Verification: stress plan with memory cap; monitor peak RSS ≤ 75% of system RAM.

---

## Reliability & Availability
**R1. Determinism**
- MUST run local inference deterministically (fixed seed; streaming disabled) and record **source_hash** for idempotency.
- Verification: repeated runs on unchanged redacted input yield identical outputs or cache hits.

**R2. Fault Tolerance**
- MUST resume safely after interruption using atomic writes and temp files; partial artifacts are recoverable.
- SHOULD retry transient provider errors with capped backoff; MUST never re‑upload attachments.

**R3. Data Integrity**
- MUST validate every output against JSON Schemas; invalid records are quarantined and do not corrupt aggregates.

---

## Security & Privacy
**S1. Data Boundaries**
- MUST keep original text and **fine_labels_local** on device; ONLY redacted text + **coarse_labels** MAY be sent to cloud.
- MUST NEVER upload attachments to cloud.
- Verification: prompt linter asserts visibility matrix; CI fails with **E_VISIBILITY_LEAK** or **E_ATTACHMENT_PRESENT**.

**S2. Pseudonymization**
- MUST tokenize identifiers (ME, CN_<id>, ⟦TKN:…⟧) deterministically with a salt file; salt is local‑only and never logged.

**S3. Hard‑Fail Classes**
- MUST block cloud calls if prohibited classes detected (e.g., CSAM) and emit **E_HARDFAIL_CLASS**.

**S4. Secrets Management**
- MUST NOT embed secrets in code; MUST use `.env`/Parameter Store with a `.env.example` only.

**S5. Least Privilege**
- SHOULD run with minimum filesystem and network permissions; cloud calls disabled by default; enable per run with `--allow-cloud`.

---

## Compliance
**C1. Auditability**
- MUST record **provenance** (schema_v, run_id, ts, model_id/sha, provider, prompt_hash, source_hash, token_usage, latency_ms, cache_hit) for every record.
- MUST record **shield** (coverage, strict, hardfail_triggered, nuance_level).

**C2. Logging & Retention**
- MUST log structured events (JSONL) with privacy‑safe fields; SHOULD provide log rotation and opt‑in anonymized metrics.
- SHOULD default to local data residency; cloud traffic is opt‑in and redacted.

**C3. Content & Platform Policies**
- SHOULD include configurable policy packs for platform filters; prompts MUST avoid banned terms when applicable.

---

## Observability
**O1. Metrics (required)**
- redaction_coverage, strict_flag_rate
- local_enrich_throughput, local_p95_latency
- cloud_batch_latency, cloud_retry_count
- token_usage_input/output/total
- cache_hit_ratio (target **≥ 0.80**)
- schema_invalid_count, visibility_leak_count
- Verification: metrics emitted to `./out/metrics/*.jsonl` and summarized in a run report.

**O2. Tracing**
- SHOULD tag spans for ingest → redact → enrich_local → enrich_cloud → validate → index with run_id correlation.

**O3. Health & Readiness (CLI)**
- MUST provide `--dry-run` and `--self-test` that validate environment, schemas, and provider tokens without sending data.

---

## Cost & Efficiency
**K1. Token Budgets**
- MUST cap **max_output_tokens ≤ 800** and enforce per‑call **input token ceilings** (configurable).
- SHOULD maintain average **token cost per message ≤ target budget** (project‑configurable).

**K2. Caching**
- SHOULD achieve **≥ 80%** cache hit on re‑runs over unchanged corpora; MUST key caches by (model_id, model_sha, prompt_hash, source_hash, schema_v).

**K3. QPS & Concurrency**
- MUST throttle cloud QPS to provider limits; SHOULD batch to minimize overhead; MUST expose `--qps` and `--concurrency` flags.

---

## Maintainability & Supportability
**M1. Code Quality**
- MUST pass lint, typecheck, and unit tests; **≥ 90%** line coverage for new code.

**M2. Docs & ADRs**
- MUST update ADRs on material design changes; SHOULD include minimal runnable examples in READMEs.

**M3. Extensibility**
- SHOULD support plugging alternate local models and vector stores via adapters; interfaces stable under semver minor.

---

## Portability & Compatibility
**T1. OS/Arch**
- MUST support macOS (Apple Silicon, Intel) and Linux x86_64; SHOULD provide container image for CI builds.

**T2. Dependency Bounds**
- MUST pin deterministic versions; SHOULD provide `requirements.txt`/`poetry.lock` and a `Makefile`/CI workflow.

---

## Backup & Disaster Recovery
**B1. Artifacts**
- MUST persist artifacts under `./out/` with stable naming; SHOULD provide `chatx export run --run-id <id>` bundling inputs, outputs, and metrics.

**B2. Reproducibility**
- MUST be able to regenerate enrichment exactly from redacted inputs + run metadata (provenance + source_hash).

---

## Usability & Accessibility
**U1. CLI UX**
- MUST offer clear help, verbose logs, progress bars, and machine‑readable errors with codes (**E_***).

**U2. Dry‑Run & Samples**
- MUST support `--dry-run` printing redacted prompt examples and **never** calling cloud.

---

## SLOs & SLAs (Summary Table)
| Area | Metric | SLO Target | SLA Breach Condition | Measurement |
|---|---|---:|---|---|
| Redaction | Coverage | ≥ 0.995 (strict ≥ 0.999) | Any cloud call with coverage below threshold | redaction_report.json |
| Local Enrichment | Throughput | ≥ 25 msgs/s | < 20 msgs/s sustained over 5 min | benchmark harness |
| Local Enrichment | p95 latency | ≤ 250 ms/msg | > 350 ms for 3 consecutive runs | metrics log |
| Cloud Enrichment | Batch E2E (100 msgs) | ≤ 90 s | > 120 s without provider incident | run report |
| Index Build | 50k msgs | ≤ 90 s | > 120 s | timed build |
| Retrieval | p95 query latency | ≤ 150 ms | > 200 ms | query sampler |
| Caching | Hit ratio | ≥ 0.80 | < 0.60 | cache stats |
| Schema Validity | Valid share | 100% | any invalid output not quarantined | validator log |

---

## Validation Plan
- **Automated:** CI workflow runs unit + schema tests, redaction coverage checks, prompt visibility lint, performance smoke, and golden‑set agreement.
- **Manual QA:** 1–2% sample human‑reviewed per run; discrepancies generate issues with CU/message links.
- **Release Gates:** CI must pass; ADR updated if design changed; semver and Conventional Commits enforced.

---

## Traceability (Where these are defined/used)
- **ARCHITECTURE.md** — Policy Shield, hybrid cascade, operational concerns, observability.
- **INTERFACES.md** — CLI contracts, outputs, error codes, visibility rules.
- **CLOUD_ENRICHMENT.md** — Schemas, thresholds, prompt contracts, provenance/shield/merge fields.
- **ACCEPTANCE_CRITERIA.md** — Gherkin tests for visibility, provenance, merge provenance, influence/relationship, idempotency.
- **labels.yml** — Coarse vs fine taxonomy (fine = local‑only).

---

## Exceptions & Changes
- Any waiver to MUST items requires an ADR with time‑boxed expiry and explicit compensating controls.
