**Status:** Draft | **Owner:** <TBD> | **Last Updated:** 2025-09-02

## Wave 2 PR Queue (after PR-9)

| #         | Conventional Title                                             | Scope (what lands)                                                                                                                                                                               | Maps to Specs / AC / NFR                                                                           |
| --------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| **PR-10** | `feat(imessage): iPhone backup mode (--from-backup)`           | Read iTunes/Finder backup dir (unencrypted or encrypted w/ password prompt), locate messages DB + Attachments, reuse normalizer → canonical `Message` JSONL; tests with synthetic backup layout. | ADR-0003 DB-first extraction; baseline iMessage AC (timestamps, replies, reactions, provenance).   |
| **PR-11** | `chore(imessage): backup UX & guards`                          | CLI help, detection of missing backup artifacts, clear errors, redaction of sensitive paths in logs; doc snippet on granting macOS Full Disk Access and backup password handling.                | Test Strategy “Extractor – iMessage”; Observability expectations.                                  |
| **PR-12** | `feat(instagram): parse official data ZIP`                     | `chatx instagram pull --zip ./instagram.zip` → merge `message_*.json` per thread, fold likes/reactions, reference media (no uploads), emit canonical `Message`; golden fixture + schema tests.   | ADR-0004; AC Instagram story.                                                                      |
| **PR-13** | `feat(extractor): identity resolution (handles → contact id)`  | Normalize iMessage handles (phone/email) + Instagram usernames → stable `sender_id`/`contact` mapping; deterministic tokens for ME/contacts using local salt (no PII in artifacts).              | NFR pseudonymization; AC/ADR provenance & determinism.                                             |
| **PR-14** | `feat(extractor): attachment hashing & dedupe`                 | SHA-256 each copied file; hashed layout (already used) + dedupe map; emit `source_meta.hash` for attachments; tests for collision handling and stable paths.                                     | Attachment object contract; Observability artifacts.                                               |
| **PR-15** | `feat(reports): missing_attachments schema + CI validation`    | Add `schemas/missing_attachments_report.schema.json`; validate `out/missing_attachments.json` in CI; unit tests.                                                                                 | Test Strategy “Schemas (unit)”; CI Architecture Gates (Schema Validity).                           |
| **PR-16** | `adr(transcription): local engine & SLAs`                      | ADR choosing the local engine (e.g., Whisper-class), languages, latency/quality targets; wire config toggles (still local-only).                                                                 | NON_FUNCTIONAL SLAs; cloud off by default; enrichment governance.                                  |
| **PR-17** | `feat(extractor): transcription engine plugin`                 | Replace mocked transcription with real local plugin behind `--transcribe-audio local`; offline model loading; tests via fake backend.                                                            | Privacy rule “attachments never uploaded”; NFR perf targets.                                       |
| **PR-18** | `feat(extractor): iCloud completeness assistant (report-only)` | Add `chatx imessage audit --db …` to summarize per-chat missing files and generate operator guidance (no automation/AppleScript claims); exit 0.                                                 | AC observability; Safety defaults.                                                                 |
| **PR-19** | `feat(observability): run_report.json + metrics`               | Emit machine-readable run report (counts, bytes, elapsed, throughput) + metrics JSONL; add schema + CI presence check.                                                                           | CI Architecture Gates “Observability Presence”; NFR Observability.                                 |
| **PR-20** | `feat(imessage): PDF fallback ingestion`                       | Minimal ingestion per ADR-0016 for PDF exports: prefer text layer, OCR fallback; map to canonical JSONL (marked “fallback” in `source_meta`).                                                    | ADR-0016; Dialogue JSONL canon.                                                                    |

### Definition of Done (applies to each PR)

* Schema-valid outputs; new code ≥90% coverage; mypy/ruff clean
* Deterministic behavior; sensitive data never leaves device; clear error messages
* Proper artifacts: manifest + run_report, metrics JSONL, quarantine (if any)

---

### PR-14 — `feat(extractor): attachment hashing & dedupe`

Add **streaming SHA-256** hashing for every copied attachment; maintain a content-addressed layout and a dedupe map.

Best-practice highlights

* Compute hashes **streaming** (e.g., 1–4 MB chunks) and prefer SHA-256 over MD5 for integrity.

Scope

* `src/chatx/attachments/hash.py`; update extractors to call it; include `source_meta.hash` in JSONL.

Tests

* Duplicate files across platforms collapse to one stored blob; JSONL refers to the same hash.

---

### PR-15 — `feat(reports): missing_attachments schema + CI validation`

Emit `out/missing_attachments.json` and validate in CI via **jsonschema**.

Best-practice highlights

* Use `jsonschema` validators and fail builds on schema errors.

Scope

* `schemas/missing_attachments_report.schema.json`; validator in CI; unit tests that feed invalid/valid samples.

---

### PR-16 — `adr(transcription): local engine & SLAs`

Draft an ADR selecting a **local** speech-to-text engine and targets.

Best-practice highlights

* Choose **faster-whisper (CTranslate2)** for local/offline perf; supports 8-bit quantization and is 2–4× faster at similar accuracy. Set latency/quality targets, CPU/GPU notes, and language coverage.
* Include optimization tips (batching, chunking/VAD, parallelism).

Scope

* `docs/ADR-0017-transcription-engine.md`: decision, options, consequences, rollout.

---

### PR-17 — `feat(extractor): transcription engine plugin`

Implement `--transcribe-audio local` plugin using **faster-whisper** with streaming/chunking and offline models; no network calls.

Best-practice highlights

* Use short chunks with overlap; optional VAD to split; load model once; allow CPU/GPU quantization.

Scope

* `src/chatx/transcribe/local_whisper.py`; adapter interface; tests with short audio fixtures (golden text to tolerance).

---

### PR-18 — `feat(extractor): iCloud completeness assistant (report-only)`

Add `chatx imessage audit --db ...` that reports **missing local attachment files** and produces human guidance to fetch them **manually** (no automation).

Best-practice highlights

* When Messages uses **iCloud with Optimize Storage**, attachments may be evicted; Apple’s **per-conversation “Download”** button in the Info panel is the supported way to redownload **for that conversation** (no bulk download). Cite and reflect this in guidance text.

Scope

* Scanner enumerates `attachment` rows whose files are absent; generates a JSON + console summary with per-chat counts and step-by-step instructions.

---

### PR-19 — `feat(observability): run_report.json + metrics`

Emit a **machine-readable run report** and a small **metrics JSONL** capturing throughput, elapsed, counts, error tallies. Map to SRE **golden signals** where applicable (latency, traffic, errors, saturation proxies like CPU/memory if available).

Scope

* `out/run_report.json`: `{ started_at, ended_at, duration_ms, messages, attachments, bytes_copied, errors }`.
* `out/metrics.jsonl`: counters/histograms friendly to later OTel ingestion. Include labels like extractor, platform, db_source.

Tests

* Presence + schema validation; fields consistent with a small fixture run.

---

### PR-20 — `feat(imessage): PDF fallback ingestion`

Add minimal ingestion for **PDF exports** of conversations: prefer **text layer**; fallback to **OCR** by adding/searching a text layer **locally**; then map messages to canonical JSONL with `source_meta.mode="pdf_fallback"`.

Best-practice highlights

* Prefer modern PDF extractors (**PyMuPDF / pypdfium2**) for speed/quality; for image-only PDFs, run **OCRmyPDF** to add a text layer and re-extract.

Scope

* `src/chatx/pdf_ingest/reader.py`: text-first; OCR fallback; careful with page order and timestamps heuristics.
* Tests: one text-PDF, one image-only PDF; both yield minimal but valid messages.

---

## Notes for commits/README (optional)

* Backups live at `~/Library/Application Support/MobileSync/Backup/` on macOS; `Manifest.db` maps hashed filenames to `domain` + `relativePath` (e.g., `HomeDomain/Library/SMS/sms.db`).
* If **Messages in iCloud** is enabled, messages sync and are not included in daily iCloud backups; local completeness depends on “Optimize Storage.”
* SQLite safety: open read-only with `immutable=1` to avoid locking and ensure no writes.
* ZIP safety: avoid Zip Slip by validating entry paths before writing/extracting.
* Pseudonymisation: use a keyed hash (HMAC) with a local secret salt; document rotation plan.
* Transcription: faster-whisper (CTranslate2) offers local, faster inference; chunking/VAD improves throughput.
