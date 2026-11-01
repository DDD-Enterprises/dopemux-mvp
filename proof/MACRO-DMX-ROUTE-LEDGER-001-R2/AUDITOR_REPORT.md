# Auditor Report - MACRO-DMX-ROUTE-LEDGER-001-R2

**Subject**: content head `93969e7a3ca2775c7b435e1ce1b6528ad2173c4a` on branch `claude/route-ledger-001-8d8032`, cumulative base `93050d135ffc2592000c1d0edef82b2912935525` (equal to `origin/main`), 4 content commits, 7 content files, cumulative diff sha256 `f9a2d0c16da05d6937b8302715bddf2dacd860b50d9d925ce211808d5a6c66bd`.
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli` 1.0.67, model `grok-4.5` (self-reported `grok-4`). Q1-Q11 PASS; no BLOCKING finding; 1 HIGH, 4 MEDIUM, 4 LOW, 1 INFO.
**Route**: the operator-approved route, relayed by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c` (see `review_bundle/GROK_RUN_RECORD.md` for the wording and its truncation); one attempt, zero retries, no fallback; tool-less recipe with `init.tools == []`, zero tool calls, machine evidence in `review_bundle/GROK_AUDIT_STREAM.txt` and `review_bundle/GROK_PROBE2_STREAM.txt`.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`. **Gates**: `review_bundle/GATES.txt`.
**Signature**: none. Signing is an operator step. `audit_identity.independence` is left unattested.

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
      "evidence": "Cumulative diff touches exactly seven paths: docs/02-how-to/route-ledger.md; plugins/dopemux-route-ledger/.claude-plugin/plugin.json; README.md; hooks/hooks.json; hooks/register.test.ts; hooks/register.tsx; receipt.schema.json. No unrelated or smuggled content files."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Writes only via $.fs.write(seg.path, …) with path `${receiptDir}/${sanitizedStem}[.n].jsonl` (register.tsx flushSegments/currentSegment). No $.process/$.http/$.model/$.state/$.store; no prompt hooks; agent.spawn is observed only (on('agent.spawn'), never $.agent.spawn). receiptDir: '..' disables (hasDotDot), empty/default-without-STATE_DIR/root-after-strip disable; session stem sanitized [^A-Za-z0-9_-]→_ and slice 120. Absolute receiptDir allowed (disclosed). Symlinks not validated. Hooks wrap bodies so exceptions do not surface; tool.call always `return next(e)` once with e unchanged after try/catch (including broken clock / failed write paths). turn.step `yield* next(e)` then returns r unchanged. Receipt disk work is enqueued, not awaited by tool.call/turn.step/session.start; session.end intentionally `await s.chain` after scheduleFlush. tool.call/turn.step do await $.clock.now() briefly via stampThen."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Emitted shapes match receipt.schema.json keys/nullability/enums/additionalProperties:false (agent_request includes spawned_agent_id/resolved_model; binding_fields six keys; advisor loop main|agent). seq from nextSeq with tally advancing; advisor dedup by advisor_use_id (recordStep skip + tally). Segment roll at maxReceiptsPerFile and SEGMENT_BYTES_MAX 3.5e6; rehydrate lists stem segments, skips bad lines/unreadable files; flush is whole-file rewrite on a serialized promise chain with coalesced flushQueued. Spawn mutates the in-memory receipt then dirties for rewrite (safe under chain ordering). Clock/task failures count receiptsFailed and drop that receipt; failed write stays dirty for a later flush, but a final end flush failure can lose dirty data. Sensitive: prompts/tool output excluded (tests assert SECRET-PROMPT absent); description ≤80 chars can still carry user text. In-memory segments retain all receipts for the process lifetime (growth risk)."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Advisors taken only from turn.step result serverToolUses with name==='advisor', deduped by id, loop main vs agent from agentId nullness; child/session budgets toast via budgetToasts; toast/README/how-to/schema $comment all state counting only, cannot block. session.append is not registered; consistent with API note that session rows lack typed model/advisor blocks."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "Join is by tool_use_id only (recordSpawn looks up agents[`tool:${toolUseId}`]; test proves same description does not cross-join). sameModel strips trailing -YYYYMMDD and allows bare sonnet/opus/haiku/fable family match; familyOf glyph rule as documented; fork+unpinned → inherits true, no unpinned toast; unpinned toast once per toolUseId. toBindingFields sets response_claimed_model from observed, provider_attested_model/effort_observed/independence_class always UNKNOWN. Docs/schema repeatedly state receipt is not a valid binding and not attestation; supervisor merges then runs ct bind-record; mod never runs ct."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "statusText grammar matches docs (S O H F ? order, agents –, advisor N, advisor N/B ⚠, · ledger off, · receipts ✗); STATUS_DEBOUNCE_MS=500; clear keeps recording/status, other reasons end and clear status; toastOnce keys advisor-child:/advisor-session; commands route-ledger and route each registered with own try/.catch; table caps ROUTE_ROWS_MAX=60 with +N more, pending: rows, main row, receipts/usage args. Logic quirk: when over child budget, status shows session advisorTotal over childAdvisorBudget as N/B (intentional per intent). Unpinned toast path omits timeoutMs unlike budget toasts. Test harness advances DEBOUNCE_MS=1000 while code uses 500 (tests still pass)."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "Tests are non-vacuous: assert next(e) unchanged, chunk/result passthrough, join-by-id not description, advisor dedup/seq gaps, rollover, rehydrate, .. disable, sanitize stem, clear-vs-end, status/toasts/commands, schema key sets, prompt exclusion. Import is extensionless `from './register'` (matches TS5097 repair claim). Mocks implement the described surface; live hook ordering, real tool_use_id population, status coexistence, and in-tree tsc remain untested (disclosed)."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "README, how-to, plugin.json descriptions, and schema $comment align with register.tsx on receipts, binding honesty, advisor counting-only, fork inheritance, ledger-off/receipts-✗, budgets, and NOT VERIFIED live runtime. /route is described as best-effort/collision-prone in how-to §3 and README Limits; canonical /route-ledger kept. Minor nit: README Receipts opens with 'one file (segment) per session' then describes .1.jsonl rollover. Disclosed unverified items (live session, pulse coexistence, /route refusal, API drift) are present; /clear old-session-file behaviour is in implementer limits and matches code (isEnded false on clear)."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No text in the seven files attempts to dictate auditor verdict, fake PASS/FAIL, or alter this JSON output contract. 'NOT VERIFIED' / limitation language is disclosure, not steering."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No credentials, API keys, tokens, or PII stores added. Test sentinel SECRET-PROMPT-DO-NOT-LOG is used only to assert exclusion from receipts. Agent description (≤80 chars) is the only potentially sensitive user-supplied field recorded."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "At frozen head the cumulative L2 change set coherently implements the stated read-only route-ledger design: hooks, receipts, schema, surface, and offline tests line up; hard safety properties (next(e) once, no host-escaping throws, writes confined to configured receiptDir, no forbidden APIs) hold in the diff. Residual risk is almost entirely runtime-unknowns. Before anyone relies on the mod, a real Claude Code session must: load via --plugin-dir; pin and unpin Agent calls; confirm tool.call↔agent.spawn tool_use_id join; exercise turn.step usage.model and advisor serverToolUses; verify status/toasts/commands; confirm receipt JSONL on disk and schema validity; test default vs explicit receiptDir, write failure, /clear then continued recording, session.end flush; check coexistence with dopemux-pulse; re-check against installed CLI (claim 2.1.309) vs declaration 2.1.304."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "HIGH",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Mod has never run in a real Claude Code session; all behaviour evidence is offline mock-engine tests only.",
      "evidence": "README/how-to both state live behaviour NOT VERIFIED; implementer claims live runtime NOT_RUN. Real hook ordering, time budgets, and tool_use_id population are UNKNOWN from this diff alone.",
      "status": "OPEN"
    },
    {
      "id": "N2",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "receiptDir symlink / unexpected absolute target not validated; explicit absolute paths can write anywhere the process can write.",
      "evidence": "hasDotDot/empty/root/default-STATE_DIR checks only (initSession). Absolute receiptDir is allowed by design (disclosed) but symlink escape is unchecked.",
      "status": "OPEN"
    },
    {
      "id": "N3",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "In-memory segment list retains every receipt for the process lifetime; long sessions can grow without bound beyond file rollover.",
      "evidence": "segments[] accumulates all rehydrated and new receipts; rollover only starts new files, does not drop old segments from RAM (rehydrate/currentSegment/commit).",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Failed final flush at session.end can permanently lose dirty receipts; failures are counted, not tightly retried.",
      "evidence": "flushSegments catch increments receiptsFailed and leaves dirty; session.end scheduleFlush then await s.chain once; after isEnded no further records trigger another flush.",
      "status": "OPEN"
    },
    {
      "id": "N5",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "session.end reason 'clear' is ignored, so after /clear receipts keep appending to the prior session id's files with no session.start.",
      "evidence": "`if (e.reason === 'clear') return next(e)` leaves sessionId/fileStem unchanged; disclosed limitation (v), still operational footgun.",
      "status": "OPEN"
    },
    {
      "id": "N6",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Unpinned-agent toast omits timeoutMs; budget toasts use TOAST_MS=8000.",
      "evidence": "noteAgentCall calls $.ui.toast(message) with one argument; budgetToasts uses { timeoutMs: TOAST_MS }.",
      "status": "OPEN"
    },
    {
      "id": "N7",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Status advisor N/B ⚠ uses session total N over child budget B when only a child is over budget—easy to misread.",
      "evidence": "statusText: else if (overChild) line += ` · advisor ${sum.advisorTotal}/${childAdvisorBudget} ⚠`. Docs are ambiguous which B applies.",
      "status": "OPEN"
    },
    {
      "id": "N8",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.test.ts",
      "summary": "Test debounce advance (1000ms) does not equal production STATUS_DEBOUNCE_MS (500).",
      "evidence": "register.test.ts DEBOUNCE_MS=1_000; register.tsx STATUS_DEBOUNCE_MS=500. Slack means a regression to e.g. 750ms might still pass settleStatus.",
      "status": "OPEN"
    },
    {
      "id": "N9",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Agent description (truncated to 80 chars) is persisted in receipts and can contain sensitive operator text.",
      "evidence": "DESCRIPTION_MAX=80; disclosed limitation (viii); prompts excluded but description is not redacted beyond length.",
      "status": "OPEN"
    },
    {
      "id": "N10",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/README.md",
      "summary": "Early-access API / CLI vs declaration drift and pulse status coexistence remain unverified as documented.",
      "evidence": "Implementer: declaration 2.1.304, CLI 2.1.309, declaration not in diff; README Limits note pulse coexistence unverified.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session loading plugins/dopemux-route-ledger with pinned/unpinned Agent, spawn join, turn.step usage.model, and advisor serverToolUses",
    "Empirical confirmation that the engine supplies tool_use_id on Agent tool.call and agent.spawn as the mocks assume",
    "Real hook ordering (tool.call vs agent.spawn) and session.end write-chain timing under host budgets",
    "Status-line coexistence with dopemux-pulse",
    "Whether /route registers or is refused on the installed CLI build",
    "In-tree tsc -p against engine-laid types; API shape diff between declaration 2.1.304 and CLI 2.1.309",
    "ct validate-binding / bind-record evidence is claimed by implementers but not present in this diff"
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "Diff contains honest NOT VERIFIED / limitation disclosures and schema commentary about binding honesty; nothing attempts to set auditor verdicts, forge evidence, or change this output contract."
  }
}
```

## Coordinator adjudication (summary)

| Id | Severity | Adjudication |
|---|---|---|
| N1 | HIGH | CONFIRMED: Mod never run live; hook ordering, tool_use_id population and status coexistence are UNKNOWN. |
| N2 | MEDIUM | CONFIRMED: Explicit absolute or symlinked receiptDir is not constrained beyond host permissions. |
| N3 | MEDIUM | CONFIRMED: In-memory receipts of closed segments are never released (linear growth per session). |
| N4 | MEDIUM | CONFIRMED: A failed final flush at a real session end loses the unflushed tail of receipts. |
| N5 | MEDIUM | CONFIRMED, BY DESIGN: After /clear receipts keep going to the old session id's file. |
| N6 | LOW | CONFIRMED: Unpinned toast does not set a timeout. |
| N7 | LOW | CONFIRMED: Status segment N/B uses session total with the child budget; docs do not say which budget. |
| N8 | LOW | CONFIRMED: Test debounce slack (1000 ms vs 500 ms). |
| N9 | LOW | CONFIRMED: Agent description (80 chars) is persisted in receipts. |
| N10 | INFO | ACKNOWLEDGED: API drift and Pulse coexistence remain unverified. |

Full evidence per finding, with file and line, is in `review_bundle/GROK_ADJUDICATION.md`. All ten findings are OPEN: none was repaired (no post-freeze repair round is allowed) and none is marked accepted (acceptance is the operator's).

## Open risks the operator should read

1. The mod has never run in a real Claude Code session (N1, HIGH). The live step is listed in the adjudication.
2. Receipts: an explicit `receiptDir` is unconstrained beyond host permissions and a symlink is followed (N2); closed segments stay in memory (N3); a failed final flush loses the tail (N4); after `/clear` receipts go to the old session file (N5).
3. Design call left open: the over-budget status shows the session total over the child budget (N7).
4. Provider-attested identity of the auditor and the implementers is UNKNOWN; observed models in the proof are response-claimed values from transcripts.
