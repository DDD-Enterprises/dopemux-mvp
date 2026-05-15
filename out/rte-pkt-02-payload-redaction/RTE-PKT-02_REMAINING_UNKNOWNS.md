# RTE-PKT-02 Remaining Unknowns

## UNKNOWN-001: Exact named upstream proof files absent from tracked worktree

The user packet asked to read these exact files:
- `RTE-PKT-00_SOURCE_EXCERPTS.md`
- `RTE-PKT-00_GAPS_LEDGER.md`
- `RTE-PKT-00_PACKET_READINESS_UPDATE.md`
- `RTE-PKT-00_SECRET_REDACTION_NOTES.md`
- RTE-PKT-01 closeout proof

Searches of the tracked worktree did not find those exact files. The primary checkout contains untracked RTE audit/source addendum output directories, but not those exact filenames. Authority used instead:
- User-provided packet and evidence basis.
- Repo-local `AGENTS.md`.
- Runtime code in the targeted files.
- Existing tests and prescan models/walker code.

Impact: upstream packet-readiness wording is accepted from the user prompt, not re-verified from the exact named packet files.

## UNKNOWN-002: Direct lower-level BatchRequest construction outside v5 builder

Observed v5 runtime calls build batch requests through `run_extraction_v5.py:10907`, now sanitized before `BatchRequest` construction.

The lower-level `lib/batch_clients.py` client serializes whatever `BatchRequest` it receives. That file is outside the packet allowlist and was not changed. Direct construction of `BatchRequest` outside the observed v5 builder was not globally audited.

Impact: primary v5 batch request construction is covered; external/direct lower-level use remains a narrower unknown.

## UNKNOWN-003: Legacy v3 extraction provider paths

`run_extraction_v3.py` has separate provider/batch surfaces, but this packet target and allowlist name RTE v5 and Grok prescan paths. v3 was not changed.

Impact: no claim is made that legacy v3 provider-bound content is sanitized by this packet.

## Residual Risk

The sanitizer is pattern-based. It covers the packet's required classes and tests preserve hashes/model IDs/paths, but arbitrary unknown credential formats may still require future expansion if discovered.
