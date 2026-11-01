# Auditor Report - MACRO-DMX-ROUTE-LEDGER-001-R4

**Subject**: merge head `989fe4651c050ec23619e5208da17d6152b477b0` on branch `claude/route-ledger-001-8d8032` (parents `ad8a141c6` and `97b6d5040496e2271c41d24c339d039303bbe6b1`), cumulative base `97b6d5040496e2271c41d24c339d039303bbe6b1` (current origin/main); the seven content files are byte-identical to the repair commit `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0`.
**Verdict**: `PASS_WITH_RISKS` from BOTH routes. PRIMARY: `grok-cli` 1.0.70, configured model `grok-4.5` (self-reported `grok-4.7`, unresolved), Q1-Q13 PASS, 8 findings. CORROBORATING: `agy` 1.4.11, model `gemini-4-argon-high` (self-reported `Gemini 4 Argon (High)`), Q1-Q13 PASS, 11 findings. Union: 11 findings (1 HIGH, 5 MEDIUM, 4 LOW, 1 INFO), none BLOCKING.
**Route**: operator-approved by the verbatim R4 gate line 2026-10-30; one attempt per route, zero retries, no fallback or promotion; verdict-blind custody (commits `0e1755a5a` and `118e1ecfc` precede the first read of either verdict).
**Run records**: `review_bundle/GROK_RUN_RECORD.md`, `review_bundle/AGY_RUN_RECORD.md`. **Adjudication**: `review_bundle/GROK_ADJUDICATION.md`, `review_bundle/AGY_ADJUDICATION.md`, `review_bundle/COMBINED_ADJUDICATION.md`. **Gates**: `review_bundle/GATES_PRE_AUDIT.txt`, `review_bundle/GATES.txt`.
**Signature**: none. Signing is an operator step. `audit_identity.independence` is left unattested.

## Grok response (verbatim)

```json
{
  "model_self_reported": "grok-4.7",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "Cumulative DIFF touches exactly seven paths: docs/02-how-to/route-ledger.md, plugins/dopemux-route-ledger/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.test.ts, hooks/register.tsx, receipt.schema.json. No unrelated or smuggled content files appear in the DIFF."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Writes only via $.fs.write to `${receiptDir}/${stem}[.n].jsonl` (register.tsx flushSegments / currentSegment). No $.process, $.http, $.model, $.state/$.store; no prompt hooks; agent.spawn is observed only (on handler + next), never $.agent.spawn. receiptDir: `..` disables (hasDotDot), empty/root disables, default requires `.control-tower/state` exists; absolute explicit dir allowed by design. Session stem sanitized (sanitizeStem). Hook bodies try/catch; tool.call always `return next(e)` after try (including broken clock / failed write paths); turn.step `yield* next(e)` then returns r unchanged. Receipt writes are enqueued, not awaited on tool.call/turn.step; session.start enqueues init; session.end awaits s.chain (designed). Residual: no symlink check (N2); absolute receiptDir (disclosed)."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Receipt shapes in register.tsx match receipt.schema.json keys/nullability/enums/additionalProperties:false (agent_request/step_observed/advisor_call + binding_fields). seq from nextSeq; advisor dedup via advisorSeen by id; rollover at maxReceiptsPerFile and SEGMENT_BYTES_MAX (3.5e6); rehydrate from session stem files; unreadable segments skipped (segmentsUnreadable); flush serialized on promise chain; spawn join mutates in-place then dirties+scheduleFlush on same chain. Prompts never recorded; description truncated to 80. Residuals: closed segments retained in memory (N3); failed final flush can leave dirty tail lost after end (N4); description unredacted (N9)."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Advisors taken only from turn.step result serverToolUses with name==='advisor', deduped by id before commit; loop main vs agent from agentId nullness; budgets childAdvisorBudget / sessionAdvisorBudget drive toasts and status only. Toasts/docs repeatedly say counts and cannot block. No session.append registration in register.tsx; consistent with docs that counting is from turn.step only."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "Spawn join keys solely on tool_use_id (recordSpawn looks up `tool:${toolUseId}`); sameModel strips -YYYYMMDD and matches bare family aliases; familyOf glyph rule; fork with no model sets inherits true and skips unpinned toast. toBindingFields sets effort_observed/provider_attested_model/independence_class UNKNOWN; response_claimed_model from usage.model. Schema $comment, README, and how-to state a receipt is not a valid binding and observed is not attestation; mod never runs ct."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "statusText: session total only vs sessionAdvisorBudget; separate ` · child M/B ⚠` from Math.max of advisorByAgent vs childAdvisorBudget; ledger off / receipts ✗ appends; STATUS_DEBOUNCE_MS=500. clear reason returns next(e) without ending; other reasons clear status and await chain. toastOnce keys advisor-child:/advisor-session; unpinned uses toolUseId. route-ledger/route each registered with own .catch; table caps ROUTE_ROWS_MAX=60 with +N more; pending: rows; receipts arg; usage on unknown args. Logic matches repaired tests. Residual: test advances 1000 ms while debounce is 500 (N8)."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "Tests assert unchanged e/result, receipt keys/seq, spawn join by id not description, advisor dedup, rollover, rehydrate, path confinement, status child vs session, toast text/timeouts/no route-ledger: prefix, command registration independence — non-vacuous. Import is `from './register'` (extensionless). Mocks model clock/fs/toast/status/command/tool/spawn/turn.step as described by implementers (real API fidelity UNKNOWN without declaration). Gaps: live session NOT_RUN for repaired code; debounce slack; symlink; final-flush loss; coexistence with other status plugins."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "README/how-to/plugin.json/schema $comment align with code on budgets, child segment, counting-only, binding_fields UNKNOWN rules, receiptDir rules, fork inheritance. How-to §3 states `/route` best-effort and may be refused; README Limits likewise; What-it-shows calls it an alias but Limits qualifies. NOT VERIFIED / Not run yet statements match disclosed lack of live run for repaired tip. No material claim contradicted by the DIFF; minor staleness of how-to last_review date only."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No text in the DIFF instructs an auditor to alter verdicts, fake PASS/FAIL, or change this output contract. Docs/comments describe runtime behaviour for operators; treated as data under audit, not as instructions to this auditor."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No API keys, credentials, tokens, or PII stores added. Tests use SECRET-PROMPT only to assert it never enters receipts/toasts. Agent description (≤80 chars) may carry operator-chosen text into receipts/toasts by design (N9)."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "Cumulative change implements the stated read-only route-ledger mod; N6/N7/prefix repairs match code+tests+docs. Overall status PASS_WITH_RISKS due to OPEN residuals (no live run of repaired tip, symlink, memory growth, possible lost dirty tail on failed final flush, debounce test slack). Before reliance: load repaired tip in a real Claude Code session; exercise Agent+spawn join, turn.step advisor attribution, status child vs session segments, unpinned toast timeout, /route-ledger table and receipts, receipt JSONL vs schema, /clear vs real end, and coexistence with other status plugins."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "N7: statusText no longer puts session total over child budget; uses advisor N[/sessionB] plus separate child worstChild/childB (register.tsx statusText); tests expect `agents S×1 · advisor 1 · child 1/0 ⚠`, both segments when session over, and clean agent not rewriting figures. N6: unpinned toast passes `{ timeoutMs: TOAST_MS }` (8000); test expects toastTimeouts[0] > 4000. Prefix: route-ledger: removed from budget/unpinned toasts and command error text; tests assert not.toMatch(/^route-ledger:/)."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "Delta updates README and how-to to the session-total vs child-segment grammar matching register.tsx; toast prefix removal is consistent (docs never required the doubled host+plugin prefix). No new contradiction between repaired code and the two docs."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "HIGH",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Repaired tip has no live Claude Code session evidence in this packet; offline mock kit only for the N6/N7/prefix repair.",
      "evidence": "Disclosed limitation (i): pre-repair content was observed live; repaired commit covered only by register.test.ts. Docs correctly say NOT VERIFIED / Not run yet. Blocks reliance, not necessarily merge of an L2 observability mod.",
      "status": "OPEN"
    },
    {
      "id": "N2",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "receiptDir checks `..`, empty/root, and default parent existence, but never stats for symlinks; an explicit dir that is or contains a symlink can be followed.",
      "evidence": "initSession uses hasDotDot, empty dir disable, exists(STATE_DIR) for default; no $.fs.stat. Absolute explicit receiptDir allowed (limitation vii).",
      "status": "OPEN"
    },
    {
      "id": "N3",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Rolled-over segments remain in s.segments with full receipt arrays for process lifetime; memory grows with receipt volume.",
      "evidence": "currentSegment pushes new segments without dropping old ones; rehydrate loads all matching files into memory; routeTable/lastMainStep scan all segments.",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "A failed write leaves the segment dirty; session.end schedules one flush and awaits the chain once, so a failed final flush can lose the dirty tail after the process ends.",
      "evidence": "flushSegments catches, increments receiptsFailed, leaves dirty; session.end scheduleFlush then await s.chain. Status ` · receipts ✗` surfaces failure while session runs.",
      "status": "OPEN"
    },
    {
      "id": "N5",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "session.end reason `clear` is not treated as end; receipts continue under the old session id file with no session.start.",
      "evidence": "`if (e.reason === 'clear') return next(e)`; test expects descriptions one+two after clear. Disclosed limitation (v), by design.",
      "status": "OPEN"
    },
    {
      "id": "N8",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.test.ts",
      "summary": "Debounce test advances 1000 ms while production STATUS_DEBOUNCE_MS is 500, so a debounce regression up to 1000 ms would still pass.",
      "evidence": "register.tsx STATUS_DEBOUNCE_MS = 500; test const DEBOUNCE_MS = 1_000; settleStatus advances DEBOUNCE_MS.",
      "status": "OPEN"
    },
    {
      "id": "N9",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Agent call description (truncated to 80 chars, unredacted) is written into receipts and the unpinned toast; prompt itself is never recorded.",
      "evidence": "DESCRIPTION_MAX=80; readAgentCall slices description; schema maxLength 80; limitation (viii).",
      "status": "OPEN"
    },
    {
      "id": "N10",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/README.md",
      "summary": "Plugin API is early-access; declaration not in DIFF; coexistence of this status line with another plugin (e.g. dopemux-pulse) unverified.",
      "evidence": "README Limits and how-to §6 state unverified coexistence and early-access API. Implementer API shape claims are UNKNOWN to this auditor.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session loading the repaired tip (post-4fcdc9761 / merge head) with observed status, toasts, /route-ledger, spawn join, advisor_call attribution, and schema-valid receipts",
    "Whether /route is accepted on the target CLI build",
    "Coexistence with dopemux-pulse or other plugin status lines",
    "markdownlint result (NOT_RUN on this host)",
    "Real hook time budgets and ordering beyond offline mocks",
    "claude-code API declaration file (not in DIFF) to confirm turn.step/agent.spawn/tool.call shapes"
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "DIFF contains operator-facing how-to/README and schema $comment describing behaviour; none attempts to steer this auditor's verdict or output contract."
  }
}
```

## AGY response (verbatim)

```json
{
  "model_self_reported": "Gemini 4 Argon (High)",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "The supplied cumulative diff touches only the seven intended files: docs/02-how-to/route-ledger.md, plugins/dopemux-route-ledger/.claude-plugin/plugin.json, plugins/dopemux-route-ledger/README.md, plugins/dopemux-route-ledger/hooks/hooks.json, plugins/dopemux-route-ledger/hooks/register.test.ts, plugins/dopemux-route-ledger/hooks/register.tsx, and plugins/dopemux-route-ledger/receipt.schema.json. The delta touches four of those seven files. No unrelated or smuggled code appears in the diff. (Whether commits in base..head outside the supplied diff touched other paths cannot be independently verified without git tools.)"
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "1) Writes: The only file write in hooks/register.tsx is $.fs.write(seg.path, segmentText(seg)) in flushSegments (line 670), where seg.path is constructed exclusively as ${s.receiptDir}/${s.fileStem}.jsonl or ${s.receiptDir}/${s.fileStem}.${n}.jsonl in currentSegment (lines 656-657) and rehydrate (lines 759, 767). 2) Prohibited APIs: No $.process, $.http, $.model, $.state, $.store, $.agent.spawn, or prompt/tool-rewrite hooks are used. 3) Path validation: parseConfig (lines 213-223) trims receiptDir and falls back to DEFAULT_RECEIPT_DIR on empty strings; initSession (lines 729-738) rejects empty session stems, any '..' path segment via hasDotDot, root ('/'), and missing .control-tower/state for the default directory. However, symlinks are not checked (no $.fs.stat or entry.isLink check), explicit absolute paths are permitted, and a trailing slash on the default path (e.g. '.control-tower/state/route-ledger/') bypasses the exact string equality check s.config.receiptDir === DEFAULT_RECEIPT_DIR at line 734. 4) Stem sanitization: sanitizeStem (lines 323-325) replaces characters outside [A-Za-z0-9_-] with '_' and slices to 120 chars (turning '.' and '..' into '_' and '__'). 5) Exception safety: All hook bodies (session.start, tool.call, agent.spawn, turn.step, command.run, session.end) wrap mod logic in try/catch blocks and swallow errors. 6) tool.call passthrough: Lines 997-1004 wrap noteAgentCall in try/catch and always call return next(e) once at the end without mutating e, even if $.clock.now() rejects (caught in stampThen, lines 916-924) or writes fail. 7) turn.step passthrough: Lines 1019-1026 delegate via const r = yield* next(e) and return r unchanged. 8) Host blocking: session.start, tool.call, and turn.step do not await s.chain (tool.call and turn.step only await $.clock.now()); session.end (when reason !== 'clear', line 1060) schedules a flush and awaits s.chain."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "1) Schema conformance: Common and kind-specific keys in recordAgentRequest (lines 797-821), recordStep (lines 823-857), and toBindingFields (lines 266-283) match receipt.schema.json for normal inputs, with two minor edge cases: (a) readAgentCall (line 908) and noteStep (line 950) check typeof effort === 'string' || typeof effort === 'number' rather than text(effort), and toBindingFields (lines 271-274) only checks === null || === undefined, so an empty string e.effort: '' produces selection.effort: '' and effort_requested: '', violating minLength: 1 in receipt.schema.json (lines 30, 33); (b) noteStep (line 938) checks typeof u.id === 'string' without checking u.id !== '', whereas advisor_use_id requires minLength: 1 (receipt.schema.json line 156). 2) Ordering, dedup, rollover, rehydrate, races: All receipt mutations and flushes are serialized on s.chain via enqueue (lines 679-683). Duplicate advisor IDs are skipped before common() is called (line 846), preserving gapless seq numbering. currentSegment (lines 645-660) rolls over at maxReceiptsPerFile or SEGMENT_BYTES_MAX (3.5 MB). When recordSpawn (lines 859-881) mutates spawned_agent_id and resolved_model on an in-memory AgentRequestReceipt, it runs on s.chain, marks the containing segment dirty, and schedules a flush; serialization prevents write races (though seg.bytes is not incremented by the ~50-byte join). Unreadable segments during rehydrate increment segmentsUnreadable and are skipped (lines 771-775). 3) Loss/memory/sensitivity: Closed segments remain in s.segments for the process lifetime (linear memory growth, N3). A failed final flush at session.end is not retried and loses the dirty tail (N4). Prompts, file contents, and tool outputs are excluded; only Agent description truncated to 80 chars is recorded (N9)."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Advisor calls are extracted solely from turn.step result r.serverToolUses where u?.name === 'advisor' and typeof u.id === 'string' (lines 935-944). They are deduplicated via s.advisorSeen in both recordStep (line 846) and tally (line 392). Loop attribution splits on f.agentId === null ? 'main' : 'agent' (line 853) and tallies into s.advisorMain vs s.advisorByAgent[receipt.agent_id] (lines 394-398). Per-child budget (childAdvisorBudget, default 0) and session budget (sessionAdvisorBudget, default -1) are checked separately in statusText (lines 422-433) and budgetToasts (lines 474-500). All toasts (lines 482, 493), table footers (line 581), README.md (lines 8, 47), docs/02-how-to/route-ledger.md (lines 56, 115), plugin.json (line 4), and receipt.schema.json (line 4) state that the mod only counts advisor calls and cannot block, deny, or retry them. Not registering session.append is consistent with the docs."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "1) Spawn join: noteSpawn (lines 968-979) and recordSpawn (lines 859-881) join strictly by s.agents[`tool:${toolUseId}`], ignoring calls without tool_use_id or with r.deny !== undefined. 2) Model matching & glyphs: normalizeModel (lines 307-309) lowercases, trims, and strips a trailing -YYYYMMDD date suffix; sameModel (lines 313-321) returns null when requested is null or observed is UNKNOWN, true on normalized equality or when a bare family alias (sonnet, opus, haiku, fable) is a substring of observed, and false otherwise. familyOf (lines 254-261) maps sonnet->S, opus->O, haiku->H, fable->F, and anything else to 'other' (rendered as '?'). 3) Fork & unpinned warning: recordAgentRequest (lines 798, 809) sets pinned = f.model !== null and inherits = f.subagentType === 'fork' && !pinned; noteAgentCall (lines 888-899) warns at most once per non-empty toolUseId when model === null and subagentType !== 'fork'. 4) Honesty of binding_fields: toBindingFields (lines 266-283), README.md (lines 34-43, 48), docs/02-how-to/route-ledger.md (lines 99-117), and receipt.schema.json ($comment) clearly state that a receipt is not a valid ExecutionBinding, response_claimed_model is only API-reported (not provider attestation), effort_observed and provider_attested_model are always UNKNOWN, and the mod never invokes ct."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "1) Status & debounce: statusText (lines 413-441) formats non-zero agent counts in S, O, H, F, ? order (or 'agents –'), appends ' · advisor N' or ' · advisor N/B ⚠' against sessionAdvisorBudget, appends ' · child M/B ⚠' for worstChild against childAdvisorBudget, then ' · ledger off' and ' · receipts ✗'. Updates are debounced by STATUS_DEBOUNCE_MS = 500 via $.clock.after (lines 453-463). 2) /clear vs real end: session.end returns next(e) immediately when e.reason === 'clear' (line 1052); otherwise it sets s.isEnded = true, cancels statusTimer, clears status with $.ui.status(undefined), flushes, and awaits s.chain. 3) Command registration: registerCommands (lines 616-643) registers 'route-ledger' and 'route' in separate try/catch + .catch(() => undefined) blocks. 4) Logic flaws found in surface behaviour: (a) In commit (line 693), receipts are only pushed onto s.segments when s.receiptsEnabled is true, whereas lastMainStep (lines 513-521) reads the main loop's step_observed receipt from s.segments; consequently, whenever receipts are disabled (e.g. default config when .control-tower/state does not exist), the 'main' row in /route-ledger permanently shows UNKNOWN for model requested, model observed, effort requested, and match even after main steps have executed. (b) On hot reload, rehydrate (lines 757-794) does not restore s.toasted, so a subsequent advisor call will re-toast an already-exceeded session or child budget. (c) In tally (lines 377-390), a step_observed for an unjoined agent initializes record.requestedModel to null instead of receipt.requested_model."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "hooks/register.test.ts contains 55 non-vacuous tests that assert exact receipt structures, seq continuity, deduplication, status formatting, toast contents/timeouts, command outputs, and error handling, importing extensionlessly from './register' (line 12). Untested behaviours: 1) Byte-based segment rollover at SEGMENT_BYTES_MAX (3.5 MB) is never exercised; 2) Unreadable segment files (segmentsUnreadable) and corrupt JSON lines during rehydrate are never tested; 3) Running /route-ledger (table view) after main steps when receiptsEnabled is false is not tested (which masked the lastMainStep bug); 4) DEBOUNCE_MS in register.test.ts is 1000 ms (line 290) while STATUS_DEBOUNCE_MS in register.tsx is 500 ms (line 41), so a debounce regression between 500 ms and 1000 ms would still pass (N8); 5) Command handler catch block ('could not read the ledger.') is not exercised; 6) Whether the mock harness matches the real Claude Code runtime cannot be verified from the diff alone."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "README.md, docs/02-how-to/route-ledger.md, plugin.json, and receipt.schema.json accurately describe the mod's read-only nature, status grammar (including the separate advisor and child budget segments), toasts, options, binding_fields, best-effort /route alias, and unverified live runtime status. Minor omissions/discrepancies: 1) Neither README.md, docs/02-how-to/route-ledger.md, plugin.json, nor receipt.schema.json mentions that segments also roll over at ~3.5 MB (SEGMENT_BYTES_MAX = 3_500_000) before reaching maxReceiptsPerFile; 2) docs/02-how-to/route-ledger.md (line 85) states that sanitizeStem replaces characters outside A-Za-z0-9_- with '_' but omits that it also truncates the stem to 120 characters (register.tsx line 324); 3) register.tsx line 59 says BindingFields has 'five' keys whereas receipt.schema.json line 4 says 'six' (there are 6 keys in binding_fields); 4) Docs do not mention that the 'main' row in /route-ledger stays UNKNOWN for model/effort/match when receiptsEnabled is false."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "Scanned all seven files in the cumulative diff and the delta. No prompt injection, auditor-steering directives, fake audit verdicts, or attempts to alter the output contract exist."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No secrets, API keys, credentials, tokens, or PII are present in the diff (only the synthetic test literal 'SECRET-PROMPT-DO-NOT-LOG' in hooks/register.test.ts and the repo owner handle '@hu3mann' in docs/02-how-to/route-ledger.md)."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "Overall verdict is PASS_WITH_RISKS: the mod is read-only, exception-safe, and passes all input/output invariants, with no blocking defects. Before relying on the mod in production, an operator must run a live Claude Code session loading the repaired head (claude --plugin-dir plugins/dopemux-route-ledger) to verify: 1) plugin load and command registration (/route-ledger and whether /route is accepted); 2) unpinned Agent toast appearance, ~8s duration, and absence of a doubled 'route-ledger:' prefix; 3) agent.spawn tool_use_id join and turn.step usage.model / serverToolUses observation; 4) status line rendering of both session ('advisor N/B ⚠') and child ('child M/B ⚠') segments and coexistence with any other status line plugin (e.g. dopemux-pulse); 5) JSONL receipt writing, flushing on session.end, and schema validation against receipt.schema.json."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "1) N6 repair: noteAgentCall in hooks/register.tsx (lines 893-896) now passes { timeoutMs: TOAST_MS } (8000 ms) to $.ui.toast, pinned by expect(h.world.toastTimeouts[0]).toBeGreaterThan(4000) in hooks/register.test.ts (line 362). 2) N7 repair: statusText in hooks/register.tsx (lines 424-433) now evaluates sum.advisorTotal only against sessionAdvisorBudget ('· advisor N' or '· advisor N/B ⚠') and separately evaluates worstChild = Math.max(0, ...Object.values(sum.advisorByAgent)) against childAdvisorBudget ('· child M/B ⚠'), pinned by three tests in hooks/register.test.ts (lines 916-951). 3) Prefix repair: Leading 'route-ledger: ' was removed from the three toast messages (lines 482, 493, 894) and the two command error strings (lines 1039, 1046), with the three toast messages pinned by .not.toMatch(/^route-ledger:/) in hooks/register.test.ts (lines 360, 1006, 1033)."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "The delta updates hooks/register.tsx, hooks/register.test.ts, plugins/dopemux-route-ledger/README.md, and docs/02-how-to/route-ledger.md consistently. Both documentation files accurately reflect the separated 'advisor N/B ⚠' (session) and '· child M/B ⚠' (busiest child) status segments, and no regressions were introduced by the delta."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "HIGH",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Repaired head has not been verified in a live Claude Code session",
      "evidence": "Both README.md (line 54) and docs/02-how-to/route-ledger.md (lines 19-21, 141-143) state that live runtime behaviour is not verified, and limitation (i) discloses that commit 4fcdc9761 (and merge head 989fe4651) was only tested against the offline mock harness in hooks/register.test.ts.",
      "status": "OPEN"
    },
    {
      "id": "N2",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "receiptDir validation does not check for symlinks and allows explicit absolute paths",
      "evidence": "initSession (lines 729-738) checks for empty stem, '..' segments, root ('/'), and .control-tower/state existence for the default path, but never calls $.fs.stat or checks isLink on directory entries, and permits arbitrary non-root absolute paths when configured explicitly (and a trailing slash on the default path bypasses line 734's exact string check).",
      "status": "OPEN"
    },
    {
      "id": "N3",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Rolled-over segments remain in memory for the lifetime of the session",
      "evidence": "currentSegment (lines 645-660) and rehydrate (lines 757-794) append every Segment and its receipts array to s.segments and never evict closed segments after flushSegments writes them, causing memory usage to grow linearly with total session receipts.",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "A failed final flush during session.end loses the dirty segment tail",
      "evidence": "flushSegments (lines 665-675) increments s.receiptsFailed and leaves seg.dirty = true on error without retrying; session.end (lines 1051-1064) schedules and awaits a single flush before exiting, so if that final write fails, unwritten receipts in the dirty segment are lost.",
      "status": "OPEN"
    },
    {
      "id": "N5",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "After /clear, receipts continue writing under the pre-clear session ID",
      "evidence": "session.end (line 1052) returns next(e) untouched when e.reason === 'clear' because no session.start follows a /clear; consequently s.sessionId and s.fileStem are never refreshed if the host rotates the session ID on /clear.",
      "status": "OPEN"
    },
    {
      "id": "N8",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.test.ts",
      "summary": "Status debounce test advances 1000 ms for a 500 ms debounce timer",
      "evidence": "DEBOUNCE_MS in hooks/register.test.ts (line 290) is 1_000 while STATUS_DEBOUNCE_MS in hooks/register.tsx (line 41) is 500, so regressions that increase the debounce up to 1000 ms would still pass.",
      "status": "OPEN"
    },
    {
      "id": "N9",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Agent call description (up to 80 characters) is recorded unredacted in receipts and toasts",
      "evidence": "readAgentCall (line 910) slices e.description to DESCRIPTION_MAX (80), which is written into agent_request receipts (line 806) and displayed in the unpinned-agent toast (line 894). Prompts are never recorded.",
      "status": "OPEN"
    },
    {
      "id": "N10",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Early-access Claude Code mod API version drift and unverified status-line coexistence",
      "evidence": "As disclosed in README.md (lines 50, 52) and docs/02-how-to/route-ledger.md (lines 122-124), the plugin API is early access and coexistence of $.ui.status with another plugin's status line (such as dopemux-pulse) is unverified.",
      "status": "OPEN"
    },
    {
      "id": "N11",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "/route-ledger 'main' row always displays UNKNOWN for model, effort, and match when receipts are disabled",
      "evidence": "In tally (lines 376-391), step_observed receipts with agent_id === null (main loop) do not update s.agents; instead, routeTable (line 540) calls lastMainStep(s) (lines 513-521), which searches s.segments. However, commit (line 693) only pushes receipts into s.segments when s.receiptsEnabled is true. When receipts are disabled (e.g. default config when .control-tower/state is absent), s.segments remains empty and the 'main' row in /route-ledger permanently shows UNKNOWN for model requested, model observed, effort requested, and match even after main steps run.",
      "status": "OPEN"
    },
    {
      "id": "N12",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Empty-string effort or advisor id can violate minLength: 1 in receipt.schema.json",
      "evidence": "readAgentCall (line 908) and noteStep (line 950) accept e.effort === '' because they check typeof effort === 'string' instead of text(effort), and toBindingFields (lines 271-274) only checks === null || === undefined, producing selection.effort: '' and effort_requested: '' which violate minLength: 1 in receipt.schema.json (lines 30, 33). Similarly, noteStep (line 938) checks typeof u.id === 'string' without rejecting '', whereas advisor_use_id requires minLength: 1 (receipt.schema.json line 156).",
      "status": "OPEN"
    },
    {
      "id": "N13",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Hot reload does not restore s.toasted and unjoined step_observed ignores receipt.requested_model",
      "evidence": "rehydrate (lines 757-794) rebuilds advisor counts from existing segment files without repopulating s.toasted, so another advisor call after a hot reload will re-toast an already-exceeded child or session budget. Also, in tally (lines 377-390), when a step_observed arrives for an agentId not yet in s.agents, record.requestedModel is initialized to null rather than receipt.requested_model.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session execution of the repaired head (4fcdc9761 / 989fe4651) verifying status line rendering, toast duration/prefix, command registration, and receipt output.",
    "Inspection of the engine-laid plugins/dopemux-route-ledger/tsconfig.json and the claude-code type declaration file (not included in the diff).",
    "Git log/diff verification outside the seven content files for the merge commit 989fe4651c050ec23619e5208da17d6152b477b0."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "No instruction-like content, prompt injection, or attempt to steer the auditor was found anywhere in the diff."
  }
}
```

## Coordinator summary

See COMBINED_ADJUDICATION.md for the union table, the disagreements, the repair confirmation and the operator step per finding.
