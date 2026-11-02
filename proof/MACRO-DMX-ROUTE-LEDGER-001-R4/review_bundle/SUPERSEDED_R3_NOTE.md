# R3 is superseded by R4 (facts)

| Item | Record |
|---|---|
| R3 gate line | typed verbatim by the operator 2026-10-30; covers R3 (subject `4fcdc9761`) only |
| R3 W01 | a Sonnet child (observed model claude-sonnet-5-5 in its transcript): 0 advisor blocks, 0 Agent calls, 35 tool uses, 131,633 tokens, 2.9 min active; verified and corrected by the coordinator; committed `c02748b05` |
| R3 W02 (grok-cli 1.0.70, grok-4.5, tool-less recipe) | ran ONCE on `4fcdc9761`: exit 0, `init.tools == []`, 0 tool_use, `duration_ms` 124,476, cost USD 0.05553968 (probes 0.016574592 and 0.011783176; total 0.083897448). Custody commit `4b8838cf3`. **The verdict is UNREAD and is not used by R4.** |
| R3 W03 (agy 1.4.11, gemini-4-argon-high, session-only request-review hardening) | probes clean (12,963 and 13,480 tokens); the one real attempt was stopped by the coordinator at 2026-10-30T09:34:56Z (SIGTERM; `error: interrupted`, exit 1 at 09:35:01Z); no response, no result event, no verdict. Custody commit `ad8a141c6` |
| Why superseded | the operator answered "Run it in order" to "Which way should the merge train go?" (relayed by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`): `main` requires up-to-date branches and a signed proof binds to the audited head, so the audit subject had to include current main (`97b6d5040`, PR 1472 merged 2026-10-30T08:59:28Z) as a merge commit |
| The merge | `989fe4651c050ec23619e5208da17d6152b477b0`, made by the app's `sync_with_base_branch` tool, local, nothing pushed; the unrelated local `.codex/config.toml` edit was backed up, reverted for the merge and restored byte for byte |

R4 uses none of the R3 audit outputs. R3's allowances are sunk cost, not R4 budget. The R3 Grok verdict stays unread unless the operator asks for it, after the R4 adjudication, as information about an older subject whose seven content files are identical to the R4 subject's.
