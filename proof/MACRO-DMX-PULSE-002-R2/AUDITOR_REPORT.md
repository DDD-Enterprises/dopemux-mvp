# Auditor Report - MACRO-DMX-PULSE-002-R2

**Subject**: content head `b5dc04dd7d9560ed31a2dc0fd2192218c727ea01` on branch `claude/pulse-f1-001-5a321f` (base of the repair: `f4115046484ed0dc580cc4337bb8c7cf55d39af7` = `origin/feat/pulse-001`, the head of PR #1472), cumulative base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`, cumulative diff sha256 `ba5c6c92974ba3a273759c7790d159cf069446ae76b6cbd2d9430b823f35f5a8` (8 content files).
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli`, model `grok-4.5` (self-reported `grok-4`).
**Route**: the one operator-approved route (`AUTHORIZE_MACRO_DMX_PULSE_002_R2_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`); tool-less recipe; `init.tools == []`, zero tool calls, machine evidence preserved in `review_bundle/GROK_AUDIT_STREAM.txt` and `review_bundle/GROK_PROBE2_STREAM.txt`.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.
**Predecessor**: the audit of PR #1472 at `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147` (`PASS_WITH_RISKS`, Q3 FAIL on F1) and the operator's acceptance of F1 are preserved unchanged in `proof/MACRO-DMX-PULSE-001/` and `proof/pr_merge/embedded-audit/pr-1472/`. This report is a new record on a different subject and does not alter or relabel them.
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
      "evidence": "Cumulative diff touches exactly eight paths: services/adhd_engine/api/routes.py, services/adhd_engine/tests/test_state_contract.py, plugins/dopemux-pulse/.claude-plugin/plugin.json, plugins/dopemux-pulse/README.md, plugins/dopemux-pulse/hooks/hooks.json, plugins/dopemux-pulse/hooks/register.tsx, plugins/dopemux-pulse/hooks/register.test.ts, docs/02-how-to/pulse-status-line.md. No unrelated or smuggled files."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "routes.py normal return adds energy_level/attention_state equal to energy_str/attention_str; except fallback adds energy_level/attention_state equal to medium/focused. Additive keys only (non-breaking). test_state_contract.py forces fallback via _RaisingDict.get raising RuntimeError and asserts all six keys and alias equality on both paths; unknown user_id also covered. Consumer spellings are cited in comments; those consumers are outside the diff (UNKNOWN whether they still call the endpoint, but alias addition cannot remove primary keys)."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "register.tsx: sole network use is $.http.fetch(`${s.baseUrl}/api/v1/state`) with no method/body; no process/fs/store/state/model/agent/tool/prompt APIs. engineUrl() requires /^https?:\\/\\/[^\\s/]+/i after trim/strip trailing slashes; bad URL -> bad-url, no fetch. Hook bodies, registerCommand, redraw, toast paths wrapped in try/catch; fetch rejection handled in .then second arg so late deny fulfills. isFetching set true after attaching handlers; cleared only in answer chain .then (not when 2s race wins); poll() returns early while isFetching. Late view discarded (only race winner assigned to s.view). Late settle after isEnded: poll bails on isEnded before mutating view/toasts (T4). Permanent stall if host never settles abandoned request: yes; disclosed in fetchState comment, README Limits/Engine dependency, how-to §6."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "parseState prefers energy/attention then energy_level/attention_state via word(). Toast transitions only when wasUp===true->!ok or wasUp===false->ok (never-up stays silent while down). parseMinutes: empty->25, /^\\d{1,4}$/ and 5..120 else refuse. session.end reason==='clear' returns next without cancelling; other reasons set isEnded, cancel pollTimer, stopFocus, stopContinuous, clear status. /pulse-focus restart: stopFocus then new block; continuousSince set only if undefined (chained blocks keep nudge). Band: idle/survey -> next(e). Session minutes from sessionStartedAt. registerCommand catch -> toast `dopemux-pulse: /${name} could not be registered`. /done and /break both call stopContinuous. Mild UX quirk: first success after an initial failure/timeout can toast 'ADHD engine is back' because wasUp becomes false on first down (see findings)."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "Non-vacuous: T1 no second URL while slow pending; T2 resume after 10min settle + recovery toast only; T3 slow-then-deny late refuse changes no status/toast (runner would fail file on unhandled rejection); T4 end while pending stays silent on settle; T5 denyCommand 'break' toasts and still polls/registers others. Alias preference, bounds, /clear survival, band next(e), URL slash/file refusal, process.run throw guard covered. Mocks: clock.sleep for hung fetch; http deny/status/raw/ok; command.register deny; session.end reasons — matches authority (no abort, refuse via deny). Gaps: no dedicated assert that /done alone resets the 90m continuous clock (only /break has that test); live host refuse/abort/network-timeout behaviour untested (disclosed)."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "How-to and README match code on poll 60s, 2s timeout, single GET, alias parse, /pulse-focus 5-120, band/limit/nudge, /done and /break both clear continuous-focus (count starts at first /pulse-focus), registration-failure toast, in-flight guard and hang-until-settle, never-settle stall, Not verified (live engine, paint, typeahead, real /clear). No commit SHA or PR number in either doc. Port 3025/registry and consumer list are authority claims not proven by this diff alone (not contradicted). Soft ambiguity only: 'is back' can fire on first-ever success after initial failures (docs read as recovery-from-reachable)."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "Command registered and documented as /pulse-focus everywhere (plugin.json description, README, how-to, register.tsx name 'pulse-focus', tests). /focus appears only to explain Claude Code ships it and register refuses it."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "No text in the eight files tries to dictate auditor verdict, forge an audit record, or alter this output contract. Test comments labeled F1/F6 describe repaired behaviours; normal human/AI how-to prose. Treated as data, not instructions."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No secrets, credentials, tokens, or PII added. Default URL is loopback; file:///etc/passwd appears only as a refused negative test input."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "F1/F3/F4/F6 repaired in code+docs+tests as claimed. F2/F5/F7 correctly left out of scope with disclosure. No regression of prior intended behaviour found in the diff; repair introduces no BLOCKING defect. Residual risks remain: never-live (F2), pre-existing engine suite (F5), fallback-looks-healthy (F7), disclosed never-settle stall."
    },
    {
      "id": "Q11",
      "verdict": "PASS_WITH_RISKS",
      "evidence": "W01 aliases+contract test hold; W02 read-only mod with repaired in-flight guard, late-reject handling, registration toast; W03 how-to accurate without SHA; successor R-F1/R-F3/R-F4/R-F6 closed. Risks that keep this from clean PASS: F2 still true (never run live against a real engine/session), disclosed permanent poll stall if host never settles abandoned fetch, engine exception fallback still HTTP 200 medium/focused indistinguishable to the mod, and /done continuous-reset covered by code but not by a dedicated test."
    }
  ],
  "predecessor_findings": [
    {
      "id": "F1",
      "disposition": "REPAIRED",
      "evidence": "register.tsx fetchState keeps isFetching true until the underlying $.http.fetch promise chain settles (.then clears flag); poll skips while isFetching. Timeout only affects returned view. Tests T1–T4 cover hold, resume, late deny, end-while-pending."
    },
    {
      "id": "F2",
      "disposition": "OUT_OF_SCOPE",
      "evidence": "Intentionally not addressed; README and how-to Not verified sections still state no live session/engine run. Remains HIGH residual for the cumulative feature."
    },
    {
      "id": "F3",
      "disposition": "REPAIRED",
      "evidence": "README and how-to state /done clears continuous-focus count; count starts at first /pulse-focus; chained blocks do not reset. Code: command.done calls stopContinuous(s)."
    },
    {
      "id": "F4",
      "disposition": "REPAIRED",
      "evidence": "how-to and README contain no commit SHA or PR number in the diff text."
    },
    {
      "id": "F5",
      "disposition": "OUT_OF_SCOPE",
      "evidence": "Successor does not touch the broader adhd_engine suite; only routes.py alias lines and new test_state_contract.py. Pre-existing failures claimed identical on base — not re-verifiable from this message alone."
    },
    {
      "id": "F6",
      "disposition": "REPAIRED",
      "evidence": "registerCommand catches refuse and toasts `dopemux-pulse: /${spec.name} could not be registered` without stopping other setup. Test T5 denies 'break', expects that toast and continued poll/status."
    },
    {
      "id": "F7",
      "disposition": "OUT_OF_SCOPE",
      "evidence": "Fallback still returns HTTP 200 medium/focused with aliases; documented in how-to §5 and README Limits. Mod cannot distinguish. Correctly left unchanged."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "HIGH",
      "file": "plugins/dopemux-pulse/README.md",
      "summary": "Cumulative feature still never exercised in a real Claude Code session against a live ADHD engine; /clear survival and new guard proven only under mocks.",
      "evidence": "Disclosed Not verified in README and how-to; predecessor F2 deliberately OUT_OF_SCOPE. Blocks confidence in live paint, typeahead, real HTTP, and real session.end/clear behaviour.",
      "status": "OPEN"
    },
    {
      "id": "N2",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "If the host never settles an abandoned $.http.fetch, isFetching stays true forever: polling pauses and status remains unreachable.",
      "evidence": "Explicit trade-off in fetchState comment; README and how-to §6 disclose it. Host network timeout UNKNOWN. By design given no abort API, but residual availability risk.",
      "status": "OPEN"
    },
    {
      "id": "N3",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.test.ts",
      "summary": "No dedicated test that /done alone resets the 90-minute continuous-focus nudge clock (only /break is asserted).",
      "evidence": "stopContinuous is called in the done handler (register.tsx); test 'a break resets the 90-minute continuous-focus clock' covers break only. Behaviour likely correct but unguarded against regression.",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "LOW",
      "file": "plugins/dopemux-pulse/hooks/register.tsx",
      "summary": "Recovery toast 'ADHD engine is back' can fire on the first successful poll after an initial failure/timeout even though the engine was never previously up in-session.",
      "evidence": "wasUp becomes false on first down (including 2s timeout); next ok with wasUp===false triggers recovery toast. T2 expects ['ADHD engine is back'] after slow->healthy without a prior ok. Docs describe toast as coming back from reachable.",
      "status": "OPEN"
    },
    {
      "id": "N5",
      "severity": "INFO",
      "file": "services/adhd_engine/api/routes.py",
      "summary": "Exception fallback still answers HTTP 200 with medium/focused (plus aliases); mod treats it as healthy state.",
      "evidence": "except branch in routes.py; documented in how-to §5. Predecessor F7 OUT_OF_SCOPE.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Full get_adhd_state try/except body beyond the two return dicts (to independently confirm _RaisingDict.get is on the path that hits the fallback).",
    "Live Claude Code session transcript against a running engine on :3025 (status paint, band, /pulse-focus typeahead, real /clear, real register refuse).",
    "Whether production $.command.register rejects (throw) vs returns deny when refusing a name — test harness uses deny; toast path assumes rejection/catch.",
    "Host runtime behaviour/timeout for abandoned $.http.fetch after the mod's 2s race (UNKNOWN per disclosure)."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "Diff contains normal docs/README/how-to and repair-oriented test comments (F1/F6). No auditor-steering, fake verdict, or output-contract rewrite directed at this audit."
  }
}
```
