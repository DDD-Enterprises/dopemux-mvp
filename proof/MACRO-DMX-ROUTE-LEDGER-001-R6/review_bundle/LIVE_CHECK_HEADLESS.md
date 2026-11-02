# Headless live check of the repaired plugin (MACRO-DMX-ROUTE-LEDGER-001-R6, after the audits)

Additive evidence for finding N1, recorded after both audits and after the proof was written. It is NOT part of what either auditor saw and it changes no audited content path. Authority NONE.

## What was run
- Claude Code 2.1.316 loaded the plugin from the repaired tree (`--plugin-dir plugins/dopemux-route-ledger`, content identical to the audited head `b275543fe1011bf3a9351a10448c24d94f205370`) in a headless session: `claude --plugin-dir <plugin> --setting-sources user --strict-mcp-config --mcp-config '{"mcpServers":{}}' --model claude-haiku-5-5 --allowedTools Agent --output-format json -p "<two Agent calls>"`.
- The session ran from a scratch project directory OUTSIDE the repository with an empty `.control-tower/state`, so the default receipt directory was used and nothing was written into the repository. Run window 2026-11-01T03:15:05Z to 2026-11-01T03:15:24Z; CLI-reported result: is_error False, num_turns 1, duration_ms 3296, total_cost_usd 0.01764891.
- The prompt asked for two Agent calls: one with `model` set to `haiku`, one with no `model` parameter. Both subagents were asked to reply `OK`.

## What the receipts show (`LIVE_CHECK_HEADLESS_RECEIPTS.txt`, the file the mod wrote, unedited)
- 9 receipts: 2 `agent_request`, 7 `step_observed`; all 9 validate against `receipt.schema.json`.
- Request 1: `requested_model` haiku, `pinned` true. Request 2: `requested_model` null, `pinned` false (the unpinned case). Both carry `description: ""` (D9: not recorded by default) and were joined by `tool_use_id` to their spawned agent id with `resolved_model` `claude-haiku-5-5`.
- `step_observed` receipts report `observed_model` `claude-haiku-5-5` for the main loop and for both subagents.
- The default receipt directory was used because `.control-tower/state` existed; the mod loaded, joined `agent.spawn` to its request, and wrote whole-file segments through the host's `$.fs.write`.

## What this does NOT show (N1 stays OPEN)
Headless mode has no status line, toast display, or interactive `/clear`. Not observed: the status segment text, the unpinned-agent toast and its 8 s timeout, `/route-ledger` and `/route-ledger receipts` output, whether `/clear` changes the session id, an advisor-calling child and the budget toasts, coexistence with dopemux-pulse, a symlinked `receiptDir`, and `fs.stat` symlink behaviour on the real host. Those remain the operator's interactive check. Model identity: the receipts' `observed_model` is the API-reported model (response-claimed), not attestation.
