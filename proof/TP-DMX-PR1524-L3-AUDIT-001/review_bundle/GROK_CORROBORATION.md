# Grok corroborating audit (does not govern)

- Runner: grok grok 1.0.92 (b06756fd6256) [stable] -m grok-4.7 --effort high contained; receipt model ['grok-4.7-build']; session 01a21b5c-c605-7ce1-98ec-1cc3c82571b1
- Containment: `init.tools == []` in the stream, 0 tool_use blocks; the pre-run probe also gave `init.tools == []`.
  The harness still injects a system block and home-level context (as in earlier audits); no tool could be called.
- Bundle carries `GROK_RESPONSE.txt` (the final text block), `GROK_SYSTEM_PROMPT.txt`, `GROK_INIT_TOOLS.json`. The raw stream
  and the tool probe stay in custody; sha256 in `CUSTODY.md`.
- Result: success, 262 s, reported cost USD 0.06099328
- Verdict: **PASS_WITH_RISKS**, validation NOT_RUN (`GROK_VERDICT.json`)

| # | Severity | Path | Finding |
|---|---|---|---|
| G-1 | LOW | ui-dashboard/src/components/TaskQueue.tsx confirm() returns null when listed.role === result.newRole for work|queue | The confirmed action chip drops the orchestrator anomaly note whenever the fresh read lists the clicked item in the returned new role. A Start/Finish whose previous/new roles differ from queue→work or work→terminal still renders [CONFIRMED] when that new role is work or queue and visible in the first 20 rows. |
| G-2 | LOW | ui-dashboard/src/taskQueue.ts parseTransitionResult | The browser parser accepts any contract body with a known status and, for applied, a new_role. It does not require item_id to equal the row that was clicked. The backend parser does require that match before it will report applied. |

Grok's risks are verbatim in `GROK_VERDICT.json`.
