# Grok final-audit run record (MACRO-DMX-ROUTE-LEDGER-001-R6, W02, PRIMARY route)

Facts only. Written BEFORE the auditor's answer was read: this workstream looked only at event types, the init event, the tool_use count, turns, duration, cost, exit code, stderr size, and the answer's shape (whether it parses as a JSON object, and its top-level key names). Authority NONE. The operator's R6 gate line (all three tokens) was typed in chat before anything ran.

## Subject and input
- Audit subject: `b275543fe1011bf3a9351a10448c24d94f205370` on `claude/route-ledger-001-8d8032` (PR 1482); base `97b6d5040496e2271c41d24c339d039303bbe6b1`.
- Prompt sent: `AUDIT_PROMPT.txt`, 194,244 bytes, sha256 `37561264c18acc86aef2104b9630a331e0507585b49318ee05c00e26c94964c0` (equal to the W01 record in `SHA256SUMS_INPUTS.txt`; the sealed copy was hashed before the run). Produced by W01 commit `37c63922e`.

## Route
| Item | Requested | Observed |
|---|---|---|
| Runner | `grok` CLI | `grok 1.0.70 (f50904eaee6c) [stable]` from `grok --version` |
| Model | `grok-4.5` | every init event shows `model: grok-4.5` (the configured model; provider attestation UNKNOWN) |
| Effort | `--effort high` | passed on the command line; effort observed UNKNOWN (no runtime receipt) |
| Auth | n/a | init `apiKeySource: oauth` |
- `grok models` under `env -i HOME PATH` listed `grok-4.5` (also `grok-4.7` default, `grok-4.7-build-fast`, `grok-4.6`). The same command printed "You are not authenticated." under `env -i HOME PATH` and "You are logged in with grok.com." in the plain tool shell, yet all three runs below authenticated under `env -i HOME PATH` (`apiKeySource: oauth`). Cause UNKNOWN; it did not block anything.
- Recipe: the R2 recipe files, copied byte-exact (sha256 equal to R2 `SHA256SUMS_AUDIT.txt`): `GROK_SYSTEM_PROMPT.txt`, `GROK_DISALLOWED.txt` (the R2/R4 list, unchanged), `GROK_PROBE_PROMPT.txt`; launcher `GROK_INVOCATION.txt` recreated from R4's script with only the macro id in the comment changed. Flags: `-m grok-4.5 --effort high --sandbox workspace --cwd <sealed> --system-prompt-override <file> --disallowed-tools <file> --deny 'Bash,Read,Edit,Write,WebFetch,WebSearch,XSearch,CallMcpTool,FetchMcpResource,ListMcpResources' --no-subagents --disable-web-search --no-plan --permission-mode default --max-turns 2 --verbatim --output-format streaming-messages-json --prompt-file <file>` under `env -i HOME PATH`.
- Sealed directories (outside the repo, not removed): the timestamped `grok_20261101T021035Z` directory under the session scratchpad; the real run's sealed directory held only `AUDIT_PROMPT.txt`, the probes' only `GROK_PROBE_PROMPT.txt`.

## Attempts
| Run | Start (UTC) | End (UTC) | Exit | Duration (CLI) | Cost (CLI, USD) | Turns |
|---|---|---|---|---|---|---|
| Probe 1 (no restrictions) | 2026-11-01T02:11:04Z | 02:11:10Z | 0 | 4,426 ms | 0.01855176 | 1 |
| Probe 2 (recipe) | 2026-11-01T02:11:23Z | 02:11:29Z | 0 | 4,363 ms | 0.011743056 | 1 |
| Real run (the one audit attempt) | 2026-11-01T02:11:46Z | 02:13:20Z | 0 | 92,902 ms | 0.066405536 | 1 |
- Audit attempts: 1. Retries: 0. Probes: 2 (the one allowed re-probe was not needed). Fallback: none. The other route's output was not used or seen.
- Wall clock, first probe start to real-run end: 2 min 16 s. Total cost as the streams report it: USD 0.096700 (probes 0.030295 plus run 0.066405536).

## Containment evidence (all PASS)
- Probe 1: `init.tools` listed 24 tools (no restrictions, as expected for the baseline); 0 tool_use blocks.
- Probe 2: `init.tools == []`; 0 tool_use blocks; stderr 137 bytes, one warning that six names in `--disallowed-tools` (`delegate`, `fetch`, `browser`, `computer`, `memory`, `read_many_files`) name no tool.
- Real run: `init.tools == []`; event types `system/init` 1, `assistant` 1, `result/success` 1; 0 tool_use blocks; `is_error` false; exit 0; stderr 137 bytes (same warning).
- Answer shape (not content): the `result` field is a string of 11,347 characters that parses as one JSON object whose top-level keys are `findings`, `instruction_like_content`, `model_self_reported`, `needs_more_evidence`, `questions`, `status`, `tools_used`.
- Allowances: attempts 1 of 1, retries 0, probes 2 of 3, wall clock 2 min 16 s of 30 min (run 94 s of 15 min), cost USD 0.0967 of 0.30, advisor calls 0.

## Residual exposure (as accepted with the Grok route token)
- The recipe exposes no tool, but the CLI still injects home-level names into the context: init lists 7 MCP server names, 143 skill names and 156 slash-command names (probe 1: 160 slash commands). No secret values were sent. The saved Grok configuration (always-approve, five global MCP servers) was not changed.
- The audit prompt (the diff of the seven content files) was sent to xAI once.
- Identity: whatever the auditor writes about itself is a claim; it was not read here. Provider attestation UNKNOWN.

## Custody
Raw artifacts are in this bundle: `GROK_PROBE1_STREAM.txt`, `GROK_PROBE1_STDERR.txt`, `GROK_PROBE2_STREAM.txt`, `GROK_PROBE2_STDERR.txt`, `GROK_AUDIT_STREAM.txt` (the real run's stream-json lines, renamed from `.jsonl`), `GROK_AUDIT_RESPONSE_RAW.txt` (the stream's `result` string, extracted byte-exact), `GROK_AUDIT_STDERR.txt`, `GROK_INVOCATION.txt`, `GROK_SYSTEM_PROMPT.txt`, `GROK_DISALLOWED.txt`, `GROK_PROBE_PROMPT.txt`, `GROK_TIMES.txt`, and this record. Hashes: `SHA256SUMS_GROK.txt`. The verdict has NOT been read; W04 reads it after the AGY custody commit exists as well.
