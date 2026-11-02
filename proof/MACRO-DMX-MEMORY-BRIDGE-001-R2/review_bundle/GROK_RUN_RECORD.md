# Grok final audit - run record (MACRO-DMX-MEMORY-BRIDGE-001-R2)

Written and committed BEFORE the verdict was read.

**Subject**: content head `52855fb35ea40f420bdacdcab9e092f8d15292c6`, base `93050d135ffc2592000c1d0edef82b2912935525`, 3 commits touching 6 content files (`plugins/dopemux-memory-bridge/**`, `docs/02-how-to/memory-bridge.md`). Cumulative diff 137194 bytes, sha256 `575b241961879971e51ba908b4ecc19cd35125877832971a1a9a336a0d1b7856` (`FROZEN_CUMULATIVE.diff`). Proof head at launch: `d8ce61a15ae21422871d9abf7d3bdf3518cc466f` (proof-only commit on top; `proof/` excluded from the diff).
**Route**: operator-approved: "grok-cli grok-4.5 final audit ... one attempt each, zero retries, no fallback, sealed directory with only the prompt, the tool-less recipe with init.tools probed empty first, raw streams and evidence saved into each flat review_bundle, then adjudicate and build an unsigned PROOF.json. No push, sign or merge." The message reached this session through the commissioning session and arrived cut off mid-word; the remainder is that session's offered button wording. Tool `grok` 1.0.67, model `grok-4.5`, effort `high`. One attempt, zero retries, no fallback.
**Recipe**: reused unchanged from `MACRO-DMX-PULSE-002-R2` (`GROK_DISALLOWED.txt` sha256 `0c3f1773...8d487f`, `GROK_SYSTEM_PROMPT.txt` sha256 `416516c4...3445f`, flags as in `GROK_INVOCATION.txt`). Only the subject, intent, authority facts, limitations and questions of the prompt were adapted (`AUDIT_PROMPT_TEMPLATE.txt`).

## Times and result of the run (no verdict content here)

- Probe launched 2026-10-24T07:00:01Z, exit 0: content-free prompt, same flags. `init.tools == []`, 0 `tool_use` blocks, reply `OK`. Cost 0.01126692 USD.
- Real run launched 2026-10-24T07:00:30Z, finished 07:03:32Z, exit 0. Event types `['system', 'assistant', 'result']`; `init.tools == []`; model `grok-4.5`; permissionMode `default`; **0** `tool_use` blocks; `num_turns` 1; `duration_ms` 180409; `is_error` false; cost 0.065607216 USD; stderr 137 bytes (the same harmless warning that six guessed tool ids in the deny list name no tool).
- Sealed directory held only `AUDIT_PROMPT.txt` (150302 bytes, sha256 `24fcd6245ae524018f9be71d2bdb909ee8e856742079851ecbacc8eefef70f7b`); no repository mount, no secrets. No launch, sandbox or quota failure occurred.
- Residuals the recipe cannot remove (same as the Pulse run): the init event lists 124 skills and 137 slash commands from the home directory and seven global MCP servers (`browser-use`, `figma`, `MCP_DOCKER`, `dope-context`, `gpt-researcher`, `pal-stdio`, `serena`) with status `pending`; no tool was exposed or called. Provider-attested identity is UNKNOWN.

## Custody

All raw artifacts were copied from the scratchpad into this flat bundle (`.txt`, `.diff`, `.md`) and committed in the same hour as the run, before the verdict was read; the committed bytes were compared with `cmp` against the originals. Hashes in `SHA256SUMS_AUDIT.txt`.

## Allowances used

Audit: 1 route, 1 attempt, 0 retries, no fallback. Probe plus run: 07:00:01Z to 07:03:32Z wall clock; run 180.4 s; cost 0.0769 USD in all (as reported by the streams). Prompt 150302 bytes: the operator set no size cap for this audit; the Pulse allowance of 150000 bytes was exceeded by 302 bytes and is not treated as a limit here.

## Worktree state note

At launch the worktree also held unrelated changes made outside this macro (`.codex/config.toml` modified, `.agents/` untracked). They are not part of any commit here and not part of the audited diff.
