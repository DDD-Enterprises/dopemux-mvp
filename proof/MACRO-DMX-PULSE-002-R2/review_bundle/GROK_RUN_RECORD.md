# Grok final audit - run record (MACRO-DMX-PULSE-002-R2)

**Subject**: content head `b5dc04dd7d9560ed31a2dc0fd2192218c727ea01` (C2 of the successor repair), cumulative base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (merge-base with origin/main), 8 content files, cumulative diff sha256 `ba5c6c92974ba3a273759c7790d159cf069446ae76b6cbd2d9430b823f35f5a8`. Proof-only head at launch: `990ef677c23f342bc57f90baa396dfecbb929e89`.
**Route**: the one proposed route (`AUDITOR_BINDING_PROPOSED.json`), approved by the operator's verbatim line `AUTHORIZE_MACRO_DMX_PULSE_002_R2_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`. Tool `grok` 1.0.67, model `grok-4.5`, effort `high`. One attempt, zero retries, no fallback route.
**Launched**: 2026-10-23T21:00:30Z. **Finished**: 2026-10-23T21:02:56Z. **Exit**: 0.

## Containment (machine evidence, preserved this time)

- Real run stream `GROK_AUDIT_STREAM.txt`: event types `['system', 'assistant', 'result']`; `init.tools == []`; model `grok-4.5`; permissionMode `default`; **0** `tool_use` blocks; `num_turns` 1; `duration_ms` 143645; `total_cost_usd` 0.042482456; stderr 137 bytes (only the harmless warning that some guessed tool ids in the deny list name no tool).
- Probe 1 (`GROK_PROBE1_STREAM.txt`, launched 2026-10-23T20:59:48Z): content-free prompt, the base deny rules only: `init.tools` listed the 24 built-in tools `run_terminal_command, read_file, search_replace, list_dir, grep, kill_command_or_subagent, todo_write, get_command_or_subagent_output, scheduler_create, scheduler_delete, scheduler_list, monitor, search_tool, use_tool, workflow, enter_plan_mode, exit_plan_mode, ask_user_question, send_feedback, image_gen, image_edit, image_to_video, reference_to_video, write`. It answered the probe text, no tool call. Cost 0.017712096.
- Probe 2 (`GROK_PROBE2_STREAM.txt`, launched 2026-10-23T21:00:10Z): the same prompt with `--disallowed-tools` built from probe 1's own `init.tools` (24 ids) plus 14 extra ids (`GROK_DISALLOWED.txt`, 38 in all; 6 of the extras name no tool) and the no-skills system prompt: `init.tools == []`, 0 tool_use blocks. Cost 0.01100376.
- Only after probe 2 showed an empty tool list was the real prompt run. Sealed directory held only `AUDIT_PROMPT.txt` (sha256 matches the bundle copy); no repository mount, no secrets. Exact command: `GROK_INVOCATION.txt`.
- Residuals that the recipe cannot remove (carried from the earlier run): home-level instruction files and skill names (124 skills, 141 slash commands) are listed in the init event, and seven global MCP servers (`browser-use`, `figma`, `MCP_DOCKER`, `dope-context`, `gpt-researcher`, `pal-stdio`, `serena`) showed status `pending` in the init event with no tools exposed. No tool was called.

## Custody

All raw artifacts were copied into this bundle as flat `.txt` files and committed in `98500222b67a2ed8ae490eafc4c3e601134fa6d8` BEFORE the verdict was read for adjudication; the committed bytes were compared (`cmp`) with the originals and are identical. Nothing important exists only in the scratchpad.

| File | sha256 |
|---|---|
| `AUDIT_PROMPT.txt` | `4543b16ab95da2d1ac44557e31293afa0f09dec73f9f321d95081244bc7f78c1` |
| `GROK_AUDIT_STREAM.txt` | `81bc3e82a5ce189e0fe032c8188b5e5ce5119628b9849e4b61da9481d5c6762f` |
| `GROK_AUDIT_RESPONSE_RAW.txt` | `127175a1ca36ce2afd61b01c023276c87b9ff1756ea9570c1b2562c7c2430f30` |
| `GROK_AUDIT_STDERR.txt` | `64b84c593388f05a0c35b69ebcd7ff8c0b542b1cfa1375db9fb8d1c48894b92c` |
| `GROK_PROBE1_STREAM.txt` | `a3fc4465b49dbf5c419ca797b8903cf9e82c7e4efca2d6839480d80dc6cfc599` |
| `GROK_PROBE2_STREAM.txt` | `f128d5fb2160af0d278c9e687680a1819bd14355a5d5bef572dd32a03b7f2c73` |
| `GROK_INVOCATION.txt` | `7dd450b0a328988863fe478ccb14610dfb1b041a6cbcc438b6caa38b6628ec94` |
| `GROK_SYSTEM_PROMPT.txt` | `416516c4179b8ac6ed5c83a0faf370decee0c0890882988450fce0c2cfc3445f` |
| `GROK_DISALLOWED.txt` | `0c3f1773ab88a65cc4dfedf6d91da39ad14c19a85f26139088117fabcf8d487f` |
| `FROZEN_CUMULATIVE.diff` | `ba5c6c92974ba3a273759c7790d159cf069446ae76b6cbd2d9430b823f35f5a8` |
| `FROZEN_DELTA.diff` | `393b4beeb74165fd712b21e5ca9c175dc74889e136751b062906193b2545bbd9` |

## Differences from the PULSE-001 audit

- The raw event stream, the init event, the probes, the invocation and the response bytes are preserved and hash-recorded; containment is reproducible from this bundle, not attested.
- The auditor again self-reported `grok-4` while the CLI's init event shows `grok-4.5`. Provider-attested identity is UNKNOWN.
- The auditor's Q11 verdict field says `PASS_WITH_RISKS`, which is outside the prompt's per-question enum (`PASS|FAIL|UNKNOWN`); the top-level `status` is the contract-valid `PASS_WITH_RISKS`. Recorded as a format deviation, not relabelled.

## Allowances used (PROPOSED, ratified by the operator's lines)

Audit: 1 route, 1 attempt, 0 retries. Probes plus run: 2026-10-23T20:59:48Z to 2026-10-23T21:02:56Z wall clock (limit 60 min elapsed); the run itself 143645 ms (limit 20 min active); cost 0.0712 USD in all (limit 1.00; reported by the streams); prompt 63060 bytes (limit 150000).
