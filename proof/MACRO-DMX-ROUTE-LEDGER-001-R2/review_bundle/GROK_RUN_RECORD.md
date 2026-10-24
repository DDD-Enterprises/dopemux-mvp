# Grok final audit - run record (MACRO-DMX-ROUTE-LEDGER-001-R2)

This record was written and committed BEFORE the verdict was read. It states facts about the run only; the adjudication is a separate file written afterwards.

**Subject**: frozen head `93969e7a3ca2775c7b435e1ce1b6528ad2173c4a` on branch `claude/route-ledger-001-8d8032`, base `93050d135ffc2592000c1d0edef82b2912935525` (equal to `origin/main` at the time), 4 commits (`01aa4a123` W01, `ff61c185f` W02, `5dd7e998a` W03, `93969e7a3` W01 repair), 7 content files, cumulative diff sha256 `f9a2d0c16da05d6937b8302715bddf2dacd860b50d9d925ce211808d5a6c66bd` (104061 bytes). The issuance package and the packet files are not part of the audited diff.
**Route**: `grok` 1.0.67, model `grok-4.5`, effort `high`, the tool-less recipe of the Pulse R2 bundle. Approved by the operator in a message relayed by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`, quoted there as: "Approve the grok-cli grok-4.5 final audit for MACRO-DMX-ROUTE-LEDGER-001-R2 (head 93969e7a3) and MACRO-DMX-MEMORY-BRIDGE-001-R2 (content head 52855fb35): one attempt each, zero retries, no fallback, sealed directory with only the prompt, the tool-less recipe with init.tools probed empty first, raw s" (cut off at "raw s" in transit; the relaying session supplied the remainder as "...treams and evidence saved into each flat review_bundle, then adjudicate and build an unsigned PROOF.json. No push, sign or merge."). The route is not an `AUTHORIZE_..._AUDIT_ROUTE` line as in Pulse; this is the wording the relay gave.
**Attempts**: ONE. Zero retries. No fallback route.
**Launched**: 2026-10-24T06:59:59Z. **Finished**: 2026-10-24T07:02:46Z. **Exit**: 0.

## Containment (machine evidence)

- Real run stream `GROK_AUDIT_STREAM.txt` (the raw `.jsonl`, renamed): event types `['system', 'assistant', 'result']`; `init.tools == []`; model `grok-4.5`; permissionMode `default`; **0** `tool_use` blocks; `num_turns` 1; `duration_ms` 160753; `total_cost_usd` 0.055076736; result subtype `success`, `is_error` false; stderr 137 bytes (only the harmless warning that six guessed tool ids in the deny list name no tool).
- Probe 1 (`GROK_PROBE1_STREAM.txt`, launched 2026-10-24T06:59:30Z): the content-free prompt `GROK_PROBE_PROMPT.txt` with the base deny rules only: `init.tools` listed the same 24 built-in tools as in the Pulse R2 probe (every one of them is in `GROK_DISALLOWED.txt`); 0 tool_use blocks; cost 0.018157224.
- Probe 2 (`GROK_PROBE2_STREAM.txt`, launched 2026-10-24T06:59:46Z): the same prompt with `--disallowed-tools` from `GROK_DISALLOWED.txt` (the Pulse R2 38-id list, unchanged) and the no-skills system prompt `GROK_SYSTEM_PROMPT.txt`: `init.tools == []`, 0 tool_use blocks; cost 0.010927056.
- Only after probe 2 showed an empty tool list was the real prompt run. The sealed directory held only `AUDIT_PROMPT.txt` (sha256 matches the bundle copy, `cmp` identical); no repository mount, no secrets (a pattern scan of the prompt diff and of this bundle found none). Exact command: `GROK_INVOCATION.txt`.
- Residuals the recipe cannot remove (as in the Pulse R2 record): the init event lists home-level instruction and skill names and slash commands, and global MCP servers with no tools exposed. No tool was called.
- The recipe files `GROK_DISALLOWED.txt` and `GROK_SYSTEM_PROMPT.txt` are byte-identical to the Pulse R2 bundle's (sha256 `0c3f1773...` and `416516c4...`).

## What the auditor saw

`AUDIT_PROMPT.txt` (116483 bytes): the hard rules, the subject and intent, the implementer claims and disclosed limitations, eleven questions, the JSON output contract, and the cumulative diff. `AUDIT_PROMPT_TEMPLATE.txt` is the template before substitution. The auditor has no predecessor audit to lean on; it was told that.

## Custody

All raw artifacts were copied into this bundle as flat files and committed before the verdict was read (the commit is the first commit of this bundle in `git log`; its hash is in the closing report). `.jsonl` was renamed to `.txt`. Hashes of the audit artifacts are in `SHA256SUMS_AUDIT.txt`. The R2 issuance package (macro, coordinator binding, `ALLOWANCES.json`, the three task packets and bindings, `ISSUANCE.md`) is flattened here as `MACRO_PACKET.json`, `EXECUTION_BINDING.json`, `ALLOWANCES.json`, `Wnn_TASK_PACKET.json`, `Wnn_EXECUTION_BINDING.json`, `ISSUANCE.md`; the R1 package's hash list is `R1_PACKAGE_SHA256S.txt` (R1 itself was never executed to completion and is preserved unchanged outside the repo history). `ALLOWANCE_LEDGER.json` is the draft measured-versus-cap ledger of the build; `ALLOWANCE_LEDGER_LIVE.json` is its event log.

## Allowances used by the audit (ratified only as "one final audit"; the figures below are informational)

Audit: 1 route, 1 attempt, 0 retries. Probes plus run: 2026-10-24T06:59:30Z to 2026-10-24T07:02:46Z wall clock (3 min 16 s); the run itself 160753 ms; cost 0.0841 USD in all as the streams report it (0.018157224 + 0.010927056 + 0.055076736); prompt 116483 bytes. No second audit was run.

## Limits of this evidence

Provider-attested identity is UNKNOWN: the CLI's init event shows `grok-4.5`, and whatever the auditor reports about itself in its own answer is a claim, not attestation. The audit has no tools, so it judged the diff text only; it could not run the code or the tests.
