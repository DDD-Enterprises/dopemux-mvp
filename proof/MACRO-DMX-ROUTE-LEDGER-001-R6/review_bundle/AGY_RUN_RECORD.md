# AGY final-audit run record (MACRO-DMX-ROUTE-LEDGER-001-R6, W03, CORROBORATING route)

Facts only. Written BEFORE either auditor's answer was read: this workstream looked only at event kinds, the init event, step types and counts, the result status, turns, duration, token usage, exit codes, stderr sizes, and the answer's shape (whether it parses as a JSON object, and its top-level key names). Authority NONE. The operator's R6 gate line (all three tokens) was typed in chat before anything ran. The Grok custody commit `ced97d784` already existed; the Grok output was not given to this auditor.

## Subject and input
- Audit subject: `b275543fe1011bf3a9351a10448c24d94f205370` on `claude/route-ledger-001-8d8032` (PR 1482); base `97b6d5040496e2271c41d24c339d039303bbe6b1`.
- Prompt sent: `AUDIT_PROMPT.txt`, 194,244 bytes, sha256 `37561264c18acc86aef2104b9630a331e0507585b49318ee05c00e26c94964c0`. The sealed copy was cmp-equal to the prompt committed at HEAD (`git show HEAD:...`) before the real prompt was sent; the same prompt as W02.

## Route
| Item | Requested | Observed |
|---|---|---|
| Runner | `agy` CLI | `agy --version` printed `1.4.11` (as at R4) |
| Model | `gemini-4-argon-high` | `agy models` listed `gemini-4-argon-high  Gemini 4 Argon (High)` exactly; every init event shows `model: gemini-4-argon-high` (the configured model; provider attestation UNKNOWN) |
| Permission mode | `request-review` (session-only `--settings`) | every init event shows `permission_mode: request-review` |
| Effort | the High variant of the model id | no separate effort flag; effort observed UNKNOWN |
- Flags (all present in `agy --help`): `--model gemini-4-argon-high --sandbox --disable-slash-commands --output-format stream-json --print-timeout <3m probes | 15m real> --settings '{"toolPermission":"request-review","allowNonWorkspaceAccess":false,"permissions":{"allow":[]}}' --print="$(cat <prompt>)"`, under `env -i HOME PATH`, cwd a sealed directory holding only the prompt file(s). The scripts (run, driver, gate) were recreated from R4's `AGY_INVOCATION.txt`; changed: the macro id in comments and the real-run timeout 10m to 15m. `--add-dir` and `--dangerously-skip-permissions` were not used. `agy mcp disable` was not run and no agy or gemini settings file was edited.
- Sealed directories (outside the repo, not removed): the timestamped `agy_20261101T021453Z` directory under the session scratchpad.

## Attempts
| Run | Start (UTC) | End (UTC) | Exit | Duration (CLI) | Turns | Tokens in / out / thinking / total | Gate |
|---|---|---|---|---|---|---|---|
| Probe 1 | 2026-11-01T02:15:28Z | 02:15:57Z | 0 | 24.2 s | 1 | 13,067 / 50 / 40 / 13,117 | OK |
| Probe 2 | 2026-11-01T02:15:57Z | 02:16:25Z | 0 | 24.0 s | 1 | 13,114 / 2,592 / 1,730 / 15,706 | OK |
| Real run (the one audit attempt) | 2026-11-01T02:16:25Z | 02:21:47Z | 0 | 318.4 s | 1 | 74,128 / 30,407 / 24,431 / 104,535 | allowed step types only |
- Audit attempts: 1. Retries: 0. Probes: 2 of 2. Fallback: none; no other model or route used. Cost: UNKNOWN (agy reports tokens, not USD).
- Wall clock, first probe start to real-run end: 6 min 19 s. Total tokens 133,358 (probes 28,823 plus run 104,535).

## Containment evidence (mechanical gate; all PASS)
- Gate (exit 0, init `request-review`, init model `gemini-4-argon-high`, step types a subset of `user_input` and `agent_response`, result status SUCCESS): probe 1 `OK`, probe 2 `OK`; the sealed prompt matched the committed one; the real prompt was sent only after both passed (`GATES.txt` is in `AGY_INVOCATION.txt`).
- Real run stream: 827 events = 1 `init`, 825 `step_update` (1 `user_input`, 824 `agent_response`), 1 `result` (status SUCCESS, 1 turn). No tool, MCP, file or command step. stderr 0 bytes for all three runs.
- Answer shape (not content): `result.response` is a string of 19,457 characters (19,472 bytes) that parses as one JSON object (not fenced) with top-level keys `findings`, `instruction_like_content`, `model_self_reported`, `needs_more_evidence`, `questions`, `status`, `tools_used`.
- Allowances: attempts 1 of 1, retries 0, probes 2 of 2, wall clock 6 min 19 s of 30 min (run 5 min 22 s of 15 min), tokens 104,535 of 400,000 for the run, cost UNKNOWN, advisor calls 0.

## Residual exposure (as accepted with the AGY route token)
- agy cannot be made tool-less: the init event lists 60 built-in tools. R4 recorded 11 enabled global MCP servers; they were not re-counted here. The operator's saved agy settings (`always-proceed`, `allowNonWorkspaceAccess=true`, an allow list including `git commit` and `gh`) were overridden for the session only and not changed. Containment rests on the session-only settings, `env -i HOME PATH`, the sealed cwd and the stream gate; the absence of a tool step in the stream is evidence, not proof that no capability was available.
- The audit prompt (the diff of the seven content files) was sent to Google's Gemini service through agy once, and agy keeps the conversation in its history under `~/.gemini/antigravity-cli`.
- Exact-model evidence for the schema-required `gemini-3.1-pro-high` is UNAVAILABLE (that id is not listed). The proof will record `auditor_tool: agy`, `auditor_model: gemini`, and PR Steward may not treat that as READY.
- Identity: whatever the auditor writes about itself is a claim; it was not read here. Provider attestation UNKNOWN.

## Custody
Raw artifacts are in this bundle: `AGY_VERSION.txt`, `AGY_MODELS_LIST.txt`, `AGY_PROBE_PROMPT.txt`, `AGY_PROBE1_STREAM.txt`, `AGY_PROBE1_STDERR.txt`, `AGY_PROBE2_STREAM.txt`, `AGY_PROBE2_STDERR.txt`, `AGY_AUDIT_STREAM.txt` (the real run's stream-json lines, renamed from `.jsonl`), `AGY_AUDIT_RESPONSE_RAW.txt` (the result's `response` string, extracted byte-exact), `AGY_AUDIT_STDERR.txt` (empty), `AGY_INVOCATION.txt`, `AGY_TIMES.txt`, and this record. Hashes: `SHA256SUMS_AGY.txt`. The verdict has NOT been read; W04 reads both after this custody commit.
