# Grok corroborating audit (does not govern)

- Runner: grok grok 1.0.77 (50ca579fa996) [stable] -m grok-4.7 --effort high contained; receipt model ['grok-4.7-build']; session 01a1f723-f586-75f3-9e7c-47b2e5743817
- Containment: `init.tools == []` in the stream, 0 tool_use blocks; the pre-run probe also gave `init.tools == []`.
  The harness still injects a system block and home-level context (as in earlier audits); no tool could be called.
- Bundle carries `GROK_RESPONSE.txt` (the final text block), `GROK_SYSTEM_PROMPT.txt`, `GROK_INIT_TOOLS.json`. The raw stream
  and the tool probe stay in custody; sha256 in `CUSTODY.md`.
- Result: success, 380 s, reported cost USD 0.082654
- Verdict: **PASS_WITH_RISKS**, validation NOT_RUN (`GROK_VERDICT.json`)

| # | Severity | Path | Finding |
|---|---|---|---|
| G-1 | LOW | `services/adhd-dashboard/orchestrator_tasks.py:read_task_queue` | The post-read owner check treats an unchanged container id as proof the publisher stayed the same. Docker keeps that id across stop and start, so the same container can pass both checks while another publisher holds port 7890 during list_role_items. |
| G-2 | LOW | `services/adhd-dashboard/backend.py:get_tasks` | The route and README state that GET /api/tasks always returns HTTP 200 with status ok, empty, unavailable, or wrong_project. get_tasks does not catch exceptions. resolve_expected_project catches only OSError and SubprocessError, and list_role_items parses the MCP body outside the transport try. |

Grok's risks are verbatim in `GROK_VERDICT.json`.
