# AGY final audit (CORROBORATING) - run record (MACRO-DMX-ROUTE-LEDGER-001-R4, W03)

This record was written and committed BEFORE the verdict was read. It states facts about the run only. The assistant's answer was not read, summarized or parsed for content; the only thing checked about it is that it parses as one JSON object with the contract's top-level keys.

**Subject**: the merge commit `989fe4651c050ec23619e5208da17d6152b477b0` (parents `ad8a141c6` and `97b6d5040`); its seven content paths are byte-identical to the repair commit `4fcdc9761`. Prompt `AUDIT_PROMPT.txt`, 136,451 bytes, sha256 `169e3e91f9527ff5ed4c5d25180c75208398ad6aceae91e849b8dea17916452d`, committed in `0e0e9b40e` (the same file Grok received; the sealed copy was byte-identical, checked by the driver before the real run).
**Route**: `agy` 1.4.11, model `gemini-4-argon-high` (the exact id listed by `agy models`; the init event of every run shows it). Authorized by the operator's verbatim R4 gate line 2026-10-30 (`..._R4_AUDIT_ROUTE_AGY_GEMINI_4_ARGON_HIGH=YES`), which also accepts the residual exposure described below.
**Attempts**: ONE audit attempt. Zero retries. No fallback route. Grok's output was not used (and had not been read).
**Run**: launched 2026-10-30T10:45:46Z, finished 10:50:50Z, exit 0, result status `SUCCESS`, 300.11 s, 85,070 tokens. (R3's single AGY attempt, on the older subject, was stopped by the coordinator and produced no verdict; it is not counted here. R4's allowance is its own.)

## Containment (machine evidence)

- A mechanical gate in the driver script required, for each probe, exit 0, an init event with `permission_mode = request-review` and model `gemini-4-argon-high`, only `user_input` and `agent_response` step types, and result status `SUCCESS`. Both probes passed (2 of 2 allowed). The real prompt was sent only after both passed and after the sealed prompt was re-compared with the committed one.
- Real run: the init event reports `permission_mode = request-review` and the model `gemini-4-argon-high`; the stream has 892 lines whose step types are only `user_input` (1) and `agent_response` (889 streaming updates): **no tool step of any kind**. This meets the packet's admissibility gate.
- **agy cannot be made tool-less.** The init event lists 60 built-in tools (including `run_command`, `call_mcp_tool`, `write_to_file`, `search_web`, browser tools) and no flag removes them; `agy mcp list` shows 11 global MCP servers enabled. The operator's SAVED settings are `toolPermission = always-proceed` and `allowNonWorkspaceAccess = true` with an allow list that includes `git commit` and `gh`. This run used `--settings` (session-only, never saved) with `toolPermission=request-review`, `allowNonWorkspaceAccess=false`, `permissions.allow=[]`, plus `env -i HOME PATH`, `--sandbox`, `--disable-slash-commands` and a sealed cwd. No agy or gemini settings file and no MCP configuration was changed. The containment evidence is the stream gate above, not an absence of tools.
- Sealed directory: only the prompt (and the content-free probe prompt for the probes); no repository mount, no `--add-dir`. agy stores its conversation history under `~/.gemini/antigravity-cli`, so the prompt text (the diff of the seven files) is kept there: a residual.
- Probe 2 asks the model to name its model identifier and the tools it believes it can call; its answer is a claim and was not used for any decision beyond the gate.

## What the auditor saw

`AUDIT_PROMPT.txt` only, the same text Grok received: hard rules, subject and intent, the implementer claims and disclosed limitations (including the merge-commit disclosure), Q1-Q13, the JSON output contract, the delta since the earlier audit, the earlier findings as untrusted claims, and the cumulative diff. It was not given Grok's output, any R3 audit output or any R2 verdict text.

## Custody

Every raw artifact was copied flat into this bundle and committed BEFORE the verdict was read: version and model list, the probe prompt, the three streams (`.jsonl` renamed `.txt`), stderr files (all empty), the invocation (the run script, the driver, the gate script and the gate log), AGY_AUDIT_RESPONSE_RAW.txt (the `response` text extracted mechanically from the final result event, 20,919 bytes, not read) and AGY_TIMES.txt. Hashes are in SHA256SUMS_AGY.txt.

## Allowances used by this workstream (PROPOSED caps in ALLOWANCES.json)

Audit attempts 1 of 1; retries 0; probes 2 of 2; wall clock probes plus run 5 min 43 s of 30 min (the run 5 min 4 s of 10); total tokens 113,399 of 400,000 (probes 12,970 and 15,359, run 85,070); cost UNKNOWN; coordinator advisor calls 0.

## Limits of this evidence

Provider-attested identity is UNKNOWN: the init event shows the configured model id; whatever the auditor reports about itself is a claim, not attestation. Exact-model evidence for the schema-required `gemini-3.1-pro-high` is UNAVAILABLE (that id is no longer listed): the proof will record `auditor_tool: agy` with the generic `auditor_model: gemini` and this invocation; PR Steward may not treat that as READY. The auditor judged the diff text; whether it used any hidden capability beyond what the stream shows cannot be proven, only that the stream shows none.
