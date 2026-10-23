# Auditor Report - MACRO-DMX-PULSE-001

**Subject**: `feat/pulse-001` @ `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147` (base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`), frozen diff sha256 `aebcd086...58b4`.
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli`, model `grok-4.5` (self-reported `grok-4`).
**Route**: operator-approved Grok route after the agy fallback failed with a 429 quota error (`review_bundle/AGY_ATTEMPT_RECORD.md`). Tool-less recipe, `init.tools == []` attested by the coordinator.
**Evidence limit**: the raw Grok and agy streams were lost with the session scratchpad; containment is attested, not reproducible (`review_bundle/GROK_RUN_RECORD.md`).
**Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.

## Auditor response (verbatim)

```json
{
  "model_self_reported": "grok-4",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "Diff touches exactly 8 files matching the three workstreams: services/adhd_engine/api/routes.py + services/adhd_engine/tests/test_state_contract.py (W01); plugins/dopemux-pulse/{.claude-plugin/plugin.json,README.md,hooks/hooks.json,hooks/register.tsx,hooks/register.test.ts} (W02); docs/02-how-to/pulse-status-line.md (W03). No unrelated paths, binaries, lockfiles, or config outside that set."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Both visible return paths in routes.py add aliases equal to primaries: success path energy_level/attention_state := energy_str/attention_str (~1587-1596); except path energy_level/attention_state := 'medium'/'focused' matching energy/attention (~1601-1608). Additive only; energy/attention/session_minutes/user_id unchanged → non-breaking for primary-key readers. test_state_contract.py STATE_KEYS requires both aliases and asserts equality on normal, unknown-user, and _RaisingDict-forced fallback paths; without the alias lines those asserts fail. Full try-body of get_adhd_state is not in the diff, so additional return paths are UNKNOWN from this message alone; consumers named in comments are outside the diff (no consumer-side risk visible here)."
    },
    {
      "id": "Q3",
      "verdict": "FAIL",
      "evidence": "Only network use is $.http.fetch(`${s.baseUrl}/api/v1/state`) in fetchState (register.tsx); test 'the plugin makes no call beyond one GET' asserts a single URL set and throws on process.run. No process/fs/store/state/model/agent/tool/prompt APIs appear in register.tsx. engineUrl() requires /^https?:\\/\\/[^\\s/]+/i and strips trailing slashes; file:///etc/passwd test expects zero fetches. Hook bodies and timer callbacks are try/catch wrapped so failures return text or next(e) rather than throwing into the host (residual risk if next(e) itself throws). FAIL criterion: after Promise.race timeout, the underlying $.http.fetch is not cancelled (authority: fetch has no timeout option). poll clears isPolling after the 2s race, so a hung engine can accumulate one orphaned in-flight GET per POLL_MS indefinitely — unbounded pending-fetch growth / overlapping in-flight requests despite the isPolling re-entrancy guard. Timers themselves are cancelled on non-clear session.end via pollTimer/stopFocus/stopContinuous."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "parseState prefers energy/attention then energy_level/attention_state (register.tsx parseState). Toast-once: wasUp===true→!ok toasts unreachable/malformed; wasUp===false→ok toasts 'is back'; never-up leaves wasUp undefined then false with no toast. parseMinutes: empty→25; /^\\d{1,4}$/ and 5..120 only. session.end reason==='clear' returns next(e) without cancelling; other reasons set isEnded, cancel poll/focus/nudge, clear status. /pulse-focus restarts via stopFocus then new block; continuousSince/nudge only set when undefined (chained restarts keep the 90m clock). /break and /done both stopFocus+stopContinuous. Band: no focus or hasSurvey → next(e). Session minutes from sessionStartedAt via clock.now. Disclosed comment/code mismatch: comment claims continuous 'from the first block after a break (or the session start)' but code starts continuousSince at first /pulse-focus (how-to follows code). Race note: orphaned hung fetches after timeout (see Q3); no other logic error evident in the diff."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "Tests assert concrete status strings, toast arrays, registered names, band Text, URL lists, and post-end poll/toast freezes — would fail if aliases, toast-once, bounds, clear-survival, cancel-on-end, idle band, or single-GET broke (non-vacuous). Mocks cover clock, http.fetch behaviours (ok/raw/status/down/slow), ui.status/toast, command.register, session.start/end reasons, AbovePrompt mount — aligned with authority API notes; register refusal of built-in /focus is not simulated (mod simply never registers 'focus'). Untested/important gaps: live engine + real paint/typeahead; whether real $.http.fetch retains orphaned connections after race timeout; fs/model/agent unused except by code inspection (only process.run hooked); https engineUrl; registration failure if 'break'/'done' ever become built-ins (.catch swallows); desktop surface beyond terminal mounts."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "No how-to claim contradicts register.tsx/routes.py behaviour checked here (POLL_MS 60s, alias preference, /pulse-focus bounds, clear survival, toast-once, fallback medium/focused, mod-counted session minutes, continuous start at first /pulse-focus with reset on /break|/done). Diff cannot support: 'Port 3025 … in services/registry.yaml', container port 8095, and commit SHA 3dbced397 (not present in the provided diff; SHA survival issue is disclosed). 'session_minutes is always 0 … nothing writes it' is only partially supported (handler/test show empty _session_start_times; writers not in diff). Not verified section is honest on live engine, paint/typeahead, real /clear, and non-clear session end; it does not mention orphaned hung-fetch behaviour or silent command-register failure."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "plugin.json description, README, how-to, register.tsx command name 'pulse-focus', and tests all use /pulse-focus. /focus appears only to explain Claude Code's refusal to register that built-in name (README, how-to §3, test comment)."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "Diff contains user/how-to documentation and implementation comments (including 'never surface' exception policy and /clear semantics). No text instructs an auditor to emit PASS/FAIL, forge validation receipts, or alter this JSON contract. Honest 'Not verified' disclosures are documentation, not verdict steering."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No secrets, API keys, credentials, tokens, or PII added. Default engineUrl is http://127.0.0.1:3025. file:///etc/passwd appears only as a rejected URL in a test case."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "W01 aliases on both return paths with a non-vacuous contract test; W02 is read-only GET-only by inspection with broad exception wrapping and solid mocked tests; W03 matches the code on behaviour that the diff can support. Residual risks (no live run, hung-fetch accumulation after timeout, unverified other adhd_engine failures, README continuous-focus wording vs /done, unverifiable registry/SHA claims) are non-blocking relative to stated L2 intent → overall PASS with risks reflected in status and findings."
    }
  ],
  "findings": [
    {
      "id": "F1",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "Timed-out polls leave $.http.fetch promises running; a hung engine can accumulate unbounded in-flight GETs (one per minute) because Promise.race does not cancel fetch.",
      "evidence": "fetchState races $.http.fetch against $.clock.after(2000); on 'timeout' it returns {kind:'down'} and finally only cancels the timer. Authority states fetch has no timeout option. poll's isPolling guard blocks overlapping poll() entry but not prior raced fetches still pending.",
      "status": "OPEN"
    },
    {
      "id": "F2",
      "severity": "HIGH",
      "file": "plugins/dopemux-pulse/",
      "summary": "Mod has never been exercised in a real Claude Code session against a live ADHD engine; /clear survival and UI paint are test-kit only.",
      "evidence": "Stated DISCLOSED LIMITATION (i); how-to and README 'Not verified' sections agree. Mocked 24-pass suite does not substitute for host integration.",
      "status": "OPEN"
    },
    {
      "id": "F3",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "Comment claims continuous-focus count runs from first block after a break (or session start); code starts it at the first /pulse-focus.",
      "evidence": "Comment above continuousSince assignment vs `if (s.continuousSince === undefined) { s.continuousSince = now; ...}`. How-to follows the code; README still says 'first block after a break' and under-describes /done resetting the count (code stopContinuous on both /break and /done).",
      "status": "OPEN"
    },
    {
      "id": "F4",
      "severity": "LOW",
      "file": "docs/02-how-to/pulse-status-line.md",
      "summary": "How-to asserts engine host/container ports via services/registry.yaml and cites commit 3dbced397; neither is evidenced by this diff.",
      "evidence": "§4 port 3025/8095 and §5 'Since commit 3dbced397'; frozen head given as 1d2219e8…; SHA squash fragility disclosed as limitation (v).",
      "status": "OPEN"
    },
    {
      "id": "F5",
      "severity": "MEDIUM",
      "file": "services/adhd_engine/tests/",
      "summary": "Suite outside test_state_contract.py has 28 failures and 4 collection errors; whether they pre-exist is UNVERIFIED.",
      "evidence": "DISCLOSED LIMITATION (ii). Diff only changes get_adhd_state returns and adds test_state_contract.py; cannot confirm baseline from this message.",
      "status": "OPEN"
    },
    {
      "id": "F6",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "command.register failures for pulse-focus/break/done are swallowed with .catch(() => undefined); a future built-in name collision would silently disable commands.",
      "evidence": "session.start registration block. Mock always accepts names; only /focus refusal is documented. No production assertion that break/done remain free.",
      "status": "OPEN"
    },
    {
      "id": "F7",
      "severity": "INFO",
      "file": "services/adhd_engine/api/routes.py",
      "summary": "Exception fallback still returns HTTP 200 medium/focused (with new aliases); mod cannot distinguish fallback from real healthy state.",
      "evidence": "except branch ~1601-1608; documented in how-to §5 and DISCLOSED LIMITATION (iii). Pre-existing behaviour; W01 only mirrors aliases onto it.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Full get_adhd_state try-body to confirm _RaisingDict.get is what trips the except path and that no third return path exists",
    "Whether Claude Code's $.http.fetch cancels or bounds abandoned requests after a raced timeout",
    "Live Claude Code session run against a real engine on :3025 including /clear and status/band paint",
    "Baseline comparison for the 28 failing / 4 collection-error tests under services/adhd_engine/tests",
    "services/registry.yaml (or equivalent) to verify host port 3025 / container 8095 claims",
    "Whether 'break' or 'done' are reserved Claude Code command names in the target host version"
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "How-to/README are operator documentation (including AI-assistant readers) and contain no directives to forge audit verdicts or reshape this output contract. Implementation 'never surface' comments are exception-safety notes, not auditor steering."
  }
}
```
