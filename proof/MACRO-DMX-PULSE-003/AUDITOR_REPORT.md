# Auditor Report - MACRO-DMX-PULSE-003

**Subject**: merge commit `4b0c430674de4b428302fb010159cdc40a62f1c1` on branch `feat/pulse-003-update` (main `93050d135ffc2592000c1d0edef82b2912935525` merged into the signed PR head `ee00d36552c6f7a8ef2b83dc0165b8de97481e5a` of PR #1472), cumulative base `93050d135ffc2592000c1d0edef82b2912935525`, cumulative diff sha256 `ba5c6c92974ba3a273759c7790d159cf069446ae76b6cbd2d9430b823f35f5a8` (8 content files, byte-identical to the previously audited ones).
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli`, model `grok-4.5` (self-reported `grok-4`).
**Route**: the one operator-approved route (`AUTHORIZE_MACRO_DMX_PULSE_003_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`); tool-less recipe; `init.tools == []`, zero tool calls, machine evidence in `review_bundle/GROK_AUDIT_STREAM.txt` and `review_bundle/GROK_PROBE2_STREAM.txt`.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.
**Predecessors**: audit 1 of PR #1472 (`1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`, `PASS_WITH_RISKS`, Q3 FAIL on F1) and audit 2 (`b5dc04dd7d9560ed31a2dc0fd2192218c727ea01`, `PASS_WITH_RISKS`) are preserved unchanged in `proof/MACRO-DMX-PULSE-001/`, `proof/MACRO-DMX-PULSE-002-R2/` and `proof/pr_merge/embedded-audit/pr-1472/`. This report is a new record on a different subject and does not alter or relabel them.
**Signature**: none. Signing is an operator step.

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
      "evidence": "Cumulative diff touches exactly eight paths: docs/02-how-to/pulse-status-line.md; plugins/dopemux-pulse/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.test.ts, hooks/register.tsx; services/adhd_engine/api/routes.py; services/adhd_engine/tests/test_state_contract.py. No unrelated or smuggled files in the subject diff."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "routes.py normal return adds energy_level/attention_state equal to energy_str/attention_str; exception fallback adds energy_level/attention_state equal to medium/focused. Additive only (non-breaking). test_state_contract.py forces fallback via _RaisingDict.get raising RuntimeError and asserts all six keys and alias equality on both paths; unknown-user path also asserts alias equality. Consumer files are outside the diff (UNKNOWN live consumer behaviour beyond the stated alias contract)."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "register.tsx fetchState issues only GET `${baseUrl}/api/v1/state`; no process/fs/store/model/agent/tool/prompt APIs. engineUrl() requires /^https?:\\/\\/[^\\s/]+/i. Hook bodies and registerCommand wrapped in try/catch. isFetching set true before race and cleared only in the underlying fetch promise's trailing .then (guard held until settle). Rejection handler maps to {kind:'down'}; late view is not written into s.view by the abandoned promise (only poll assigns s.view after await, and isEnded short-circuits). Late answer cannot update state after timeout, /clear, or real end (T1–T4). Permanent stall if host never settles is real and disclosed in code comment and README/how-to. No timer leak on real session.end (pollTimer/focus/nudge cancelled)."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "parseState prefers energy/attention then aliases; toast-once via wasUp true→false / false→true; parseMinutes enforces whole 5–120; session.end keeps state on reason clear and cancels on other reasons; /pulse-focus restart stopFocus without resetting continuousSince; AbovePrompt returns next(e) when idle/survey; session minutes from sessionStartedAt; registerCommand toasts dopemux-pulse: /<name> could not be registered. Residual races: N2 stall; N4 'ADHD engine is back' after initial failure (wasUp undefined→false→true) matches T2 expectations."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "Tests T1 (no second fetch while pending), T2 (resume after settle; stale answer not shown), T3 (late deny silent), T4 (end while pending silent), T5 (refused registration toasted; others still start) would fail if those behaviours broke. Mocks model clock.after/every/sleep, http.fetch deny/slow/status/ok, and command.register {deny}. Untested/important gaps: dedicated /done-alone continuous-clock reset (N3); live host paint/typeahead/engine (N1); whether production register refusal throws vs returns deny without reject (UNKNOWN)."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "How-to and README match code for /done and /break both clearing continuous-focus (starts at first /pulse-focus); guard/toast-on-refuse documented as built; no commit SHA or PR number in either doc. Not-verified sections honestly cover live engine, live paint/typeahead, and real /clear. Minor incompleteness only: recovery toast after an initial never-up failure (N4) is not called out as a toast case."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "/pulse-focus used consistently in plugin.json description, README, how-to, register.tsx command.register/run matchers, and tests. /focus appears only to explain Claude Code ships it and register refuses it."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "No text attempts to dictate auditor verdict, fake an audit result, or alter this output contract. Comments labelled F1/F6 in register.test.ts document repaired behaviours for humans; treat as data, not instructions."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No secrets, credentials, tokens, or PII added. Default engineUrl is loopback http://127.0.0.1:3025; file:// URL test is a negative case only."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "F1/F3/F4/F6 repaired in this cumulative subject; F2/F5/F7 remain out of scope as previously framed and reappear as N1/N5 (and F5 suite noise). N1–N5 still correctly stated and open. No regression of previously held behaviour visible in the diff; no new blocking defect."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "Diff content is coherent new-plugin + additive alias hunks; no conflict markers, no half-merged regions, no unrelated edits inside the eight Pulse files. Cannot recompute the stated sha256 equality from this message alone; nothing in the text contradicts the coordinator's no-edit/no-conflict claim."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "Overall cumulative change set is PASS_WITH_RISKS: W01 aliases + contract test, W02 read-only mod with F1/F6 repairs and tests, W03 how-to, R-F1/R-F3/R-F4/R-F6 present. Residual risks N1 (never live), N2 (permanent poll stall if abandoned fetch never settles), N3–N5 remain open and disclosed. No BLOCKING finding."
    }
  ],
  "predecessor_findings": [
    {
      "id": "F1",
      "disposition": "REPAIRED",
      "evidence": "isFetching cleared only when underlying $.http.fetch settles; poll gated on isFetching; T1–T4 cover hold, resume, late deny, and end-while-pending."
    },
    {
      "id": "F2",
      "disposition": "OUT_OF_SCOPE",
      "evidence": "Still never run live; restated as open N1 / disclosed limitation. Not a code defect in the diff."
    },
    {
      "id": "F3",
      "disposition": "REPAIRED",
      "evidence": "README and how-to state /done clears continuous-focus count like /break; code stopContinuous on both."
    },
    {
      "id": "F4",
      "disposition": "REPAIRED",
      "evidence": "how-to has no commit SHA; last_review/date metadata only."
    },
    {
      "id": "F5",
      "disposition": "OUT_OF_SCOPE",
      "evidence": "Other adhd_engine tests outside test_state_contract.py are not in this subject diff; authority notes them separately."
    },
    {
      "id": "F6",
      "disposition": "REPAIRED",
      "evidence": "registerCommand catches refuse and toasts dopemux-pulse: /<name> could not be registered; T5 asserts toast and remaining setup."
    },
    {
      "id": "F7",
      "disposition": "OUT_OF_SCOPE",
      "evidence": "Exception fallback still HTTP 200 medium/focused; documented; restated as N5."
    },
    {
      "id": "N1",
      "disposition": "STILL_OPEN",
      "evidence": "Correct: mod never exercised in a real Claude Code session against a live engine; tests are mocked only. Disclosed in README/how-to Not verified."
    },
    {
      "id": "N2",
      "disposition": "STILL_OPEN",
      "evidence": "Correct: if abandoned $.http.fetch never settles, isFetching stays true and polling pauses on unreachable; host network timeout UNKNOWN. Disclosed in register.tsx comment and docs."
    },
    {
      "id": "N3",
      "disposition": "STILL_OPEN",
      "evidence": "Correct: there is a break-resets-continuous test but no dedicated test that /done alone resets the 90-minute clock (code does call stopContinuous)."
    },
    {
      "id": "N4",
      "disposition": "STILL_OPEN",
      "evidence": "Correct: wasUp undefined→false on first failure then true toasts 'ADHD engine is back' without a prior unreachable toast; T2 expects that toast."
    },
    {
      "id": "N5",
      "disposition": "STILL_OPEN",
      "evidence": "Correct: engine exception fallback returns HTTP 200 with medium/focused; mod cannot distinguish; documented in how-to §5."
    }
  ],
  "findings": [
    {
      "id": "M1",
      "severity": "HIGH",
      "file": "plugins/dopemux-pulse/README.md",
      "summary": "Mod has still never been run in a real Claude Code session against a live ADHD engine (live paint, typeahead, /clear, real HTTP).",
      "evidence": "Disclosed Not verified in README and how-to; tests use mocked clock/HTTP only. Same residual as N1/F2.",
      "status": "OPEN"
    },
    {
      "id": "M2",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "If the host never settles an abandoned $.http.fetch, isFetching remains true and polling stays paused on unreachable indefinitely.",
      "evidence": "fetchState clears isFetching only in the fetch promise chain; no abort API; disclosed in code comment and docs. Same as N2.",
      "status": "OPEN"
    },
    {
      "id": "M3",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.test.ts",
      "summary": "No dedicated test that /done alone resets the 90-minute continuous-focus nudge clock.",
      "evidence": "Only 'a break resets the 90-minute continuous-focus clock' exists; /done path covered for ending the block but not for continuous reset. Same as N3.",
      "status": "OPEN"
    },
    {
      "id": "M4",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "'ADHD engine is back' can toast on first success after an initial failure without a prior unreachable toast.",
      "evidence": "wasUp starts undefined; first down sets wasUp=false without toast; later ok toasts recovery. Same as N4.",
      "status": "OPEN"
    },
    {
      "id": "M5",
      "severity": "INFO",
      "file": "services/adhd_engine/api/routes.py",
      "summary": "Handler exception fallback answers HTTP 200 with medium/focused, indistinguishable from healthy state to the mod.",
      "evidence": "except branch returns 200 aliases medium/focused; documented. Same as N5/F7.",
      "status": "OPEN"
    },
    {
      "id": "M6",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "Registration-failure toast depends on $.command.register rejecting/throwing; behaviour if the host only returns deny without rejecting is UNKNOWN.",
      "evidence": "registerCommand only toasts in catch; test harness returns {deny:'refused'} which the runner treats as failure for T5. Production refuse shape not evidenced in this message.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session against a running engine on :3025 (status line, band, /pulse-focus typeahead, real /clear).",
    "Whether production $.command.register refuses by throwing/rejecting versus returning deny without rejection.",
    "Independent recomputation of cumulative eight-file sha256 (claimed ba5c6c92974ba3a273759c7790d159cf069446ae76b6cbd2d9430b823f35f5a8) and byte-identity vs b5dc04dd7 — cannot verify from text alone.",
    "Full get_adhd_state handler body above the return hunks (to confirm _RaisingDict.get is the actual lookup used in production code paths).",
    "Host runtime network timeout / settle behaviour for abandoned $.http.fetch (drives residual N2 severity in practice)."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "Comments referencing F1/F6 describe repaired behaviours for maintainers; how-to/README are operational docs. No directive to the auditor to emit a verdict, alter the JSON contract, or accept fabricated proof."
  }
}
```
