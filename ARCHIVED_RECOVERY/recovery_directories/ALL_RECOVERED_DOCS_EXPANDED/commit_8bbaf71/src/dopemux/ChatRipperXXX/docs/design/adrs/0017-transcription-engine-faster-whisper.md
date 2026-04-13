# ADR-0017: Transcription Engine Choice (faster-whisper)

Status: Proposed | Owner: You | Last Updated: 2025-09-02 PT

## Context
- We currently expose `--transcribe-audio local` for iMessage voice notes. ADR-0003 established a local-only approach with a mock/whisper switch for tests vs. real runs.
- We need a concrete, high‑performance local engine with predictable performance on common developer hardware (CPU/GPU), offline model availability, and permissive licensing.

## Decision
- Adopt faster-whisper (CTranslate2) as the default local transcription engine behind `--transcribe-audio local`.
- Target models: `small` (default) with 8‑bit quantization; allow override via config/env.
- Load models offline from a local cache directory; never fetch models during extraction unless explicitly approved by the operator.

## SLAs (Targets)
- Accuracy: comparable to OpenAI Whisper `small` for English; acceptable WER for short voice notes; document caveats for noisy inputs.
- Latency (reference hardware: 8‑core CPU, 16GB RAM):
  - `small` int8: ≥ 1.5x audio realtime on CPU; ≥ 4x on modest GPU.
  - End‑to‑end: ≤ 2s per 30s clip median in batch of 100 on CPU; ≤ 0.5s median on GPU.
- Throughput: scalable via chunking with overlap; parallelize across files with capped worker pool.
- Memory: ≤ 2GB RSS during steady‑state CPU inference for `small`.

## Operational Guidelines
- Chunking: 15–30s windows with 5s overlap; stitch segments; VAD optional to reduce silence.
- One‑time model initialization per process; cache across files.
- Determinism: avoid nondeterministic seeds; stable decoder settings; document version pin.
- Privacy: strictly local execution; no network calls; attachments never uploaded.

## Configuration
- `CHATX_STT_ENGINE=whisper-fast` (default when `--transcribe-audio local`).
- `CHATX_STT_MODEL=small-int8` (default); allow `base`, `medium`, etc.
- `CHATX_STT_DEV=cpu|cuda` with `CHATX_STT_NUM_THREADS` and `CHATX_STT_BEAM_SIZE` knobs.
- `CHATX_STT_CACHE_DIR=~/.cache/chatx/models` (no auto‑download unless `CHATX_STT_ALLOW_DOWNLOAD=1`).

## Consequences
- PR-17 will implement `src/chatx/transcribe/local_whisper.py` using faster-whisper bindings, with a small shim to keep the current `transcribe_local()` signature intact for tests.
- Tests will use short audio fixtures and golden text with tolerance; mock backend remains for unit tests.
- Docs will include a troubleshooting section for model setup and environment detection (CPU/GPU).

## Alternatives Considered
- whisper.cpp: excellent portability, but slower on some CPUs and less ergonomic Python integration vs faster-whisper.
- Cloud STT: rejected for privacy and policy (“attachments never uploaded”).

## Rollout
- Phase 1 (this ADR): lock decision, define SLAs and toggles.
- Phase 2 (PR‑17): implement engine adapter; keep mock for tests; pin versions.
- Phase 3: document benchmarks and tune defaults; optional GPU support guide.

## References
- faster-whisper (CTranslate2) performance claims and usage.
- Practitioner tips for chunking, VAD, batching to increase throughput.

