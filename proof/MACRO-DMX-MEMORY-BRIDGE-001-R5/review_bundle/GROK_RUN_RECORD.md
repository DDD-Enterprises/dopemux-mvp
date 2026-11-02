# Grok final audit - run record (MACRO-DMX-MEMORY-BRIDGE-001-R5)

Written and committed BEFORE the verdict was read.

**Subject**: content head `bce150b5858528bfb26b3b15e3248cb1294a65e5` (W01 `29d355beb`, W02 `bce150b58`), base `93050d135ffc2592000c1d0edef82b2912935525`. Cumulative diff of the 6 content files (9 commits touch them), 156563 bytes, sha256 `c9ad11865273be83e396378aad537b8ac7e1d9950ab9836ebdf853195f4d8a7b` (`FROZEN_CUMULATIVE.diff`). The previous audited head was `88e7b7de3`; the change against it is 4 files, 110 insertions, 17 deletions.
**Route**: the operator's verbatim line `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT` (`AUTHORIZATION_RECORD.md`). Model `grok-4.5`, effort `high`. One attempt, zero retries, no fallback.
**Recipe**: unchanged from the earlier audits (`GROK_DISALLOWED.txt` sha256 `0c3f1773...8d487f`, `GROK_SYSTEM_PROMPT.txt` sha256 `416516c4...3445f`, copied from the committed R4 custody files and hash-checked). The prompt template is R4's with the subject, the audit history (claim: N12 repaired by the key rule (e3); N7-N11 unchanged), the closure question Q12 and the key part of Q13 adapted (`AUDIT_PROMPT_TEMPLATE.txt`, script `PREP_PROMPT_SCRIPT.txt`).

## Times and result of the run (no verdict content here)

- Probe launched 2026-10-30T08:56:23Z, exit 0: `init.tools == []`, 0 `tool_use` blocks, reply `OK`. Cost 0.012040896 USD.
- Real run launched 2026-10-30T08:56:53Z, finished 08:59:36Z, exit 0. Event types `['system', 'assistant', 'result']`; `init.tools == []`; model `grok-4.5`; permissionMode `default`; **0** `tool_use` blocks; `num_turns` 1; `duration_ms` 160260; `is_error` false; cost 0.067970896 USD; stderr 137 bytes (the known deny-list warning).
- Sealed directory held only `AUDIT_PROMPT.txt` (174381 bytes, sha256 `83d9d608e31a4746bbb8e7e74da15f6aed18701e0f1697041dbe1d02e933f373`). No launch, sandbox or quota failure.
- Residuals as before: 143 skills and seven global MCP servers `pending` in the init event; no tool exposed or called. Provider-attested identity UNKNOWN.

## Custody

All raw artifacts copied into this flat bundle and committed before the verdict was read; bytes compared with `cmp`. Hashes in `SHA256SUMS_AUDIT.txt`.

## Allowances used

1 route, 1 attempt, 0 retries, no fallback. Probe plus run 08:56:23Z to 08:59:36Z; run 160.3 s; cost 0.0800 USD in all.

## Deviations and errata

- `tsc` used the Claude Code 2.1.309 declaration (sha256 `c1ae9e374c7b541111f35e6a65a152878aeb01a05a859e2e55c3638f6de70723`).
- Packet erratum (W01 K05): "every key matches `/^[A-Za-z0-9_~-]{1,73}$/`" is wrong for ordinary ids of 74-80 characters, which K02 keeps as their own key; the correct bounds are 80 for the first form and 73 for the second. The implementation follows K02; the tests assert the 73 bound only for keys of the second form and the test ids. No code change.
- The worktree holds unrelated changes by other sessions (`.codex/config.toml`, `.agents/`), excluded from every commit and from the audited diff.
