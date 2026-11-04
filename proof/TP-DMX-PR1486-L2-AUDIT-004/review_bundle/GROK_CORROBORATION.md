# Grok corroborating audit (does not govern), round 8

- Runner: grok grok 1.0.70 (f50904eaee6c) [stable] -m grok-4.7 --effort high contained; receipt model ['grok-4.7-build']; session 01a1a5d0-98c4-7143-89ae-6c79f709d324
- Containment: `init.tools == []` in the stream, 0 tool_use blocks; the pre-run probe also gave `init.tools == []`.
  The harness still injects a system block and home-level context (as in r5-r7); no tool could be called.
- Bundle carries `GROK_RESPONSE.txt` (the final text block), `GROK_SYSTEM_PROMPT.txt`, `GROK_INIT_TOOLS.json`. The raw stream
  and the tool probe stay in custody; sha256 in `CUSTODY.md`.
- Result: success, 522 s, reported cost USD 0.11634052
- Verdict: **PASS_WITH_RISKS**, validation NOT_RUN (`GROK_VERDICT.json`)

| # | Severity | Path | Finding |
|---|---|---|---|
| G-1 | MEDIUM | `ui-dashboard/src/App.tsx` | After any live state_update, a still-in-flight GET is ignored for load, energy, attention, recommendation, and upstream errors, then still applied when its mapped prediction is non-null and the current prediction is null. That branch calls applyReading without forecastCarried, so the late body becomes a new forecast arrival: forecastReceivedAtRef is set to Date.now(), the 15-minute expiry timer restarts, and lastUpdated advances. A socket snapshot that included predicted_load_15min and mapped it to null is treated the same as a snapshot that never had a forecast, so the older GET can put a number back on screen. |
| G-2 | MEDIUM | `ui-dashboard/src/components/TaskSequencer.tsx` | The task queue and team board are still local sample data with the sequencer controls left in place. The chip text is now [SAMPLE] not connected, and TeamDashboard has the same label. A known load band still runs the sample sequence and the footer says the sequencer is calibrated for that band. |
| G-3 | LOW | `ui-dashboard/src/components/TaskSequencer.tsx` | The overtime clock still uses brandTokens.colors.gremlinPink. theme.ts labels that token as a brand accent that is never a status color, and this refresh edited the same timer style block while leaving the color in place. |
| G-4 | LOW | `ui-dashboard/src/App.tsx` | Retry always clears liveReadingSeenRef, sets the socket to connecting, and bumps retryTrigger, which closes the current WebSocket and opens another. A retry for an HTTP failure while the socket is open drops a live socket. |

Grok's risks are verbatim in `GROK_VERDICT.json`.
