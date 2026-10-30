# Failed agy audit attempt (MACRO-DMX-PULSE-001) - recorded, not hidden

- **Approved route**: `agy --model gemini-4-argon-high`, sealed directory, frozen diff only, recorded as `auditor_model: gemini`. `gemini-3.1-pro-high` was absent from `agy models` (agy 1.4.4).
- **Launched**: 2026-10-22T10:59:37Z. Same audit prompt as `GROK_AUDIT_PROMPT.txt` (sha256 `3e0510fe...ce69`).
- **Outcome**: failed at start. `status: ERROR`, `RESOURCE_EXHAUSTED` 429, "Individual quota reached", reset in about 40h27m (about 2026-10-24T03:30Z). 0 tokens, no audit content, no verdict.
- **Effect**: no agy verdict exists. The agy attempt does not count as an audit. The operator then approved the Grok route (`GROK_RUN_RECORD.md`).
- **EVIDENCE LOST**: the raw agy stream (`agy_out.ndjson`) and `agy_err.txt` were in the deleted session scratchpad. This record is the coordinator's attestation from the time.
