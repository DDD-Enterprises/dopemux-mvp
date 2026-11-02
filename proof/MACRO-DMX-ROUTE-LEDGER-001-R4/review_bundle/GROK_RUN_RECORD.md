# Grok final audit (PRIMARY) - run record (MACRO-DMX-ROUTE-LEDGER-001-R4, W02)

This record was written and committed BEFORE the verdict was read. It states facts about the run only. The assistant's answer was not read, summarized or parsed for content; the only thing checked about it is that it parses as one JSON object with the contract's top-level keys.

**Subject**: the merge commit `989fe4651c050ec23619e5208da17d6152b477b0` on `claude/route-ledger-001-8d8032` (parents `ad8a141c6` and `97b6d5040`, the latter current origin/main with PR 1472); its seven content paths are byte-identical to the repair commit `4fcdc9761`. Prompt `AUDIT_PROMPT.txt`, 136,451 bytes, sha256 `169e3e91f9527ff5ed4c5d25180c75208398ad6aceae91e849b8dea17916452d`, committed in `0e0e9b40e`; the file in the sealed directory was byte-identical (cmp, checked before the probes and again before the real run).
**Route**: `grok` 1.0.70, model `grok-4.5` (listed by `grok models`; the init event of every run shows `grok-4.5`), `--effort high`, the tool-less recipe of the R2 bundle. Authorized by the operator's verbatim R4 gate line 2026-10-30 (`..._R4_AUDIT_ROUTE_GROK_CLI_GROK_4_5=YES`).
**Attempts**: ONE audit attempt. Zero retries. No fallback route. The other route's output was not used (the AGY run had not started).
**Run**: launched 2026-10-30T10:42:07Z, finished 10:43:54Z, exit 0. Details in GROK_TIMES.txt.

## Containment (machine evidence)

- Probe 1 (base deny rules only, content-free prompt): `init.tools` listed the same 24 built-in tools as in R2 and R3; none was absent from GROK_DISALLOWED.txt (checked); 0 tool_use blocks; cost 0.014798296 USD.
- Probe 2 (the 38-id deny list and the no-skills system prompt): `init.tools == []`; 0 tool_use blocks; cost 0.011786576 USD. No deny-list extension and no re-probe were needed (2 of 3 allowed probes used). The real prompt was sent only because a mechanical gate in the shell required `init.tools == []`, 0 tool_use, model `grok-4.5` and exit 0 from probe 2.
- The real run: `init.tools == []`; event types `system`, `assistant`, `result`; 0 tool_use blocks; `num_turns` 1; result subtype `success`, `is_error` false; permissionMode `default`; stderr 137 bytes (the harmless warning that six guessed ids in the deny list name no tool); cost 0.053820096 USD; `duration_ms` 106,641.
- Sealed directory: only `AUDIT_PROMPT.txt` (and, for the probes, the content-free `GROK_PROBE_PROMPT.txt`); no repository mount, no secrets (pattern scans of every bundle file found none). The run used `env -i HOME PATH`: no variable exported in the tool shell was passed to grok. `grok models` under that environment reported the login and listed `grok-4.5` before any prompt was sent.
- The recipe files are byte-identical to the R2 bundle's (sha256 equal to the R2 record): GROK_DISALLOWED.txt `0c3f1773...`, GROK_SYSTEM_PROMPT.txt `416516c4...`, GROK_PROBE_PROMPT.txt `007e86af...`. The launch script is the one R3 used (GROK_INVOCATION.txt).
- Residuals the recipe cannot remove (as in R2 and R3): the init event lists 156 slash-command names, 143 skill names and 7 MCP server names from the home-level configuration, with zero tools exposed. No tool was called.

## What the auditor saw

`AUDIT_PROMPT.txt` only: hard rules, subject and intent, the implementer claims and disclosed limitations (including the merge-commit disclosure), Q1-Q13, the JSON output contract, the delta since the earlier audit, the earlier findings as untrusted claims, and the cumulative diff. It was not given the other auditor's output, any R3 audit output or any R2 verdict text.

## Custody

Every raw artifact was copied flat into this bundle and committed BEFORE the verdict was read: the three streams (`.jsonl` renamed `.txt`), the stderr files, the probe prompt, the recipe files, the invocation script, GROK_AUDIT_RESPONSE_RAW.txt (the `result` text extracted mechanically from the final stream event, not read) and GROK_TIMES.txt. Hashes are in SHA256SUMS_GROK.txt.

## Allowances used by this workstream (PROPOSED caps in ALLOWANCES.json)

Audit attempts 1 of 1; retries 0 of 0; probes 2 of 3; wall clock probes plus run 2 min 16 s of 20 min (the run 1 min 47 s of 10); cost 0.080404968 USD of 0.30; coordinator advisor calls 0.

## Limits of this evidence

Provider-attested identity is UNKNOWN: the CLI's init event shows `grok-4.5`; whatever the auditor reports about itself is a claim, not attestation. The auditor has no tools and judged the diff text only: it could not run the code or the tests.
