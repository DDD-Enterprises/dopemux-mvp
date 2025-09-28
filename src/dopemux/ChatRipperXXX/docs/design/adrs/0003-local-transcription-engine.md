ADR-0003: Local Transcription Engine

Status: Accepted | Owner: You | Last Updated: 2025-09-02 PT

## Context

Voice notes are common in iMessage. We must transcribe audio locally for privacy and determinism. Attachments are never uploaded to cloud.

## Decision

Use a local transcription path with two engines:

- `mock` engine for tests and environments without a local model (deterministic fixed output).
- `whisper` engine for real local transcription (e.g., via whisper.cpp/whisperx), selected with `--transcribe-audio local`.

Transcripts are stored as additive metadata in `source_meta.transcript` and must not modify original message text or attachment payloads.

## Consequences

- CLI supports `--transcribe-audio local|off`.
- No audio leaves the device; cloud transcription is disallowed by policy.
- Tests should validate transcript presence, determinism (mock), and schema compliance.

## Alternatives Considered

- Cloud transcription: rejected due to privacy policy and attachment egress prohibition.
- Defer transcription: hurts downstream labeling and retrieval for audio content.

## References

- Acceptance Criteria – Transcribe iMessage voice notes locally
- Interfaces.md – CLI contracts
- iMessage Extractor Spec – operational details

