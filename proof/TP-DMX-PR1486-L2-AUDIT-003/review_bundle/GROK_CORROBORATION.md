# Grok corroborating audit (does not govern), round 7

- Runner: grok grok 1.0.70 (f50904eaee6c) [stable] -m grok-4.7 --effort high contained; receipt model ['grok-4.7-build']; session 01a195d2-9d7f-75d3-8bfc-43e3c521ccfd
- Containment: `init.tools == []` in the stream, 0 tool_use blocks; the pre-run probe also gave `init.tools == []`.
  The harness still injects a system block and home-level context (as in r5/r6); no tool could be called.
- Bundle carries `GROK_RESPONSE.txt` (the final text block), `GROK_SYSTEM_PROMPT.txt`, `GROK_INIT_TOOLS.json`. The raw stream
  and the tool probe stay in custody; sha256 in `CUSTODY.md`.
- Result: success, 564 s, reported cost USD 0.11892112
- Verdict: **PASS_WITH_RISKS**, validation NOT_RUN (`GROK_VERDICT.json`)

| # | Severity | Path | Finding |
|---|---|---|---|
| G-1 | MEDIUM | ui-dashboard/src/App.tsx isCurrent/liveReadingSeenRef and the state_update branch that calls carryForecast | In-flight GET is discarded entirely once any state_update arrives, including the only forecast source |
| G-2 | MEDIUM | ui-dashboard/src/cognitiveReading.ts FORECAST_TTL_MS and carryForecast | Forecast 15-minute TTL is checked only when another state_update arrives |
| G-3 | LOW | ui-dashboard/src/App.tsx isCritical, show-all branch, and SignalFeed mount | Critical load is not a live announcement |

Grok's risks are verbatim in `GROK_VERDICT.json`.
