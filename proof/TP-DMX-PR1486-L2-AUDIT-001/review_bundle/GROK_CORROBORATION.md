# Grok corroborating audit (not governing)

Label: **TRANSCRIPT_RECOVERED_NOT_AUDITOR_WRITTEN**. Same trusted prompt (the recovered Grok prompt equals `AUDIT_PROMPT.txt` minus its trailing newline).

- Command (grok CLI 1.0.70, from the session transcript; `$DIS` = disallowed tool ids from DISALLOWED.txt, lost with the scratchpad):
  `grok -m grok-4.7 --effort high --sandbox workspace --cwd <sealed dir> --system-prompt-override "You are an independent code auditor. You have no tools and no skills; do not request or load any. Read the audit request in the user message and reply only with the JSON object it specifies, nothing else." --disallowed-tools "$DIS" --deny "Bash,Read,Edit,Write,WebFetch,WebSearch,XSearch,CallMcpTool,FetchMcpResource,ListMcpResources" --no-subagents --disable-web-search --no-plan --permission-mode default --max-turns 2 --verbatim --output-format streaming-messages-json --prompt-file AUDIT_PROMPT.txt`
- Run: 2026-10-30T11:41:52Z to 11:51:02Z, exit 0. A first attempt failed when the disk filled (kept in custody as `grok-failed-enospc`).
- Receipt: `model_id grok-4.7-build`, fingerprint `fp_5719f1aec35dd73c`, `reasoning_effort high`.
  `tool_definitions.json` is `[]` and no tool calls were made. The harness still injected a `user_info` block (19,191 chars),
  a skills-catalog reminder (49,516 chars) and an MCP-connecting notice (394 chars).
- Why it does not govern: the schema pins `auditor_tool: grok-cli` to `auditor_model: grok-4.5`; this run was grok-4.7,
  so recording it as the embedded audit would misstate the model.
- Verdict **PASS_WITH_RISKS**: F1 MEDIUM (socket errors are never cleared by a later valid update), F2 LOW (memo base and
  results not re-run for this head), risks R1-R5. Full text in `GROK_VERDICT_RECOVERED.json`.
