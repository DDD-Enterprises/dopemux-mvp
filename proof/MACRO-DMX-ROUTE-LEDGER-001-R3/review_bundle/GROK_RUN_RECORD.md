# Grok final audit (PRIMARY) - run record (MACRO-DMX-ROUTE-LEDGER-001-R3, W02)

This record was written and committed BEFORE the verdict was read. It states facts about the run only. The assistant's answer was not read, summarized or parsed for content; the only thing checked about it is that it parses as one JSON object with the contract's top-level keys.

**Subject**: content head `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0` on `claude/route-ledger-001-8d8032`, base `93050d135ffc2592000c1d0edef82b2912935525`. Prompt `AUDIT_PROMPT.txt`, 135,918 bytes, committed in `c02748b05` (sha256 in SHA256SUMS_INPUTS.txt); the file in the sealed directory is byte-identical (cmp).
**Route**: `grok` 1.0.70 (R2 used 1.0.67), model `grok-4.5` (listed by `grok models`; the init event of every run shows `grok-4.5`), `--effort high`, the tool-less recipe of the R2 bundle. Authorized by the operator's verbatim R3 gate line 2026-10-30 (`..._AUDIT_ROUTE_GROK_CLI_GROK_4_5=YES`).
**Attempts**: ONE audit attempt. Zero retries. No fallback route. The other route's output was never used.
**Run**: launched 2026-10-30T09:27:47Z, finished 09:29:53Z, exit 0. Details in GROK_TIMES.txt.

## Containment (machine evidence)

- Probe 1 (base deny rules only, content-free prompt): `init.tools` listed the same 24 built-in tools as in R2; every one of them is in GROK_DISALLOWED.txt (checked); 0 tool_use blocks; cost 0.016574592 USD.
- Probe 2 (the 38-id deny list and the no-skills system prompt): `init.tools == []`; 0 tool_use blocks; cost 0.011783176 USD. No deny-list extension was needed for 1.0.70 and no re-probe was made (2 of 3 allowed probes used).
- The real run: `init.tools == []`; event types `system`, `assistant`, `result`; 0 tool_use blocks; `num_turns` 1; result subtype `success`, `is_error` false; permissionMode `default`; stderr 137 bytes (the harmless warning that six guessed ids in the deny list name no tool); cost 0.05553968 USD; `duration_ms` 124,476.
- Sealed directory: held only `AUDIT_PROMPT.txt` (and, for the probes, the content-free `GROK_PROBE_PROMPT.txt`); no repository mount, no secrets (a pattern scan of every bundle file found none, see the W01 notes and the closing scan). The run used `env -i HOME PATH`: no variable exported in the tool shell was passed to grok. `grok models` under that environment reported the login and listed `grok-4.5` before any prompt was sent.
- The recipe files are byte-identical to the R2 bundle's (sha256 in SHA256SUMS_GROK.txt equal the R2 record): GROK_DISALLOWED.txt `0c3f1773...`, GROK_SYSTEM_PROMPT.txt `416516c4...`, GROK_PROBE_PROMPT.txt `007e86af...`.
- Residuals the recipe cannot remove (as in R2): the init event lists 156 slash-command names, 143 skill names and 7 MCP server names from the home-level configuration, with zero tools exposed. No tool was called.
- One launch-script error before any send: the first `run.sh probe1` died in bash 3.2 on an unbound empty array and never started grok (GROK_TIMES.txt, first line). Nothing left the machine and no probe or attempt was consumed.

## What the auditor saw

`AUDIT_PROMPT.txt` only: hard rules, subject and intent, the implementer claims and disclosed limitations, Q1-Q13, the JSON output contract, the delta since the earlier audit, the earlier findings as untrusted claims, and the cumulative diff. It was not given the other auditor's output and no R2 verdict text.

## Custody

Every raw artifact was copied flat into this bundle and committed BEFORE the verdict was read: the three streams (`.jsonl` renamed `.txt`), stderr files, the probe prompt, the recipe files, the invocation script (GROK_INVOCATION.txt), GROK_AUDIT_RESPONSE_RAW.txt (the `result` text extracted mechanically from the final stream event, not read) and GROK_TIMES.txt. Hashes are in SHA256SUMS_GROK.txt.

## Allowances used by this workstream (PROPOSED caps in ALLOWANCES.json)

Audit attempts 1 of 1; retries 0 of 0; probes 2 of 3; wall clock probes plus run 2 min 44 s of 20 min (the run 2 min 6 s of 10); cost 0.083897448 USD of 0.30; coordinator advisor calls 0.

## Limits of this evidence

Provider-attested identity is UNKNOWN: the CLI's init event shows `grok-4.5`; whatever the auditor reports about itself is a claim, not attestation. The auditor has no tools and judged the diff text only: it could not run the code or the tests.
