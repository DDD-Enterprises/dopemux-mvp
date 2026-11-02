# Auditor Report - MACRO-DMX-ROUTE-LEDGER-001-R6

Subject `b275543fe1011bf3a9351a10448c24d94f205370` (PR 1482), base `97b6d5040496e2271c41d24c339d039303bbe6b1`. Two independent final audits on one frozen head, one attempt each, no retry, no fallback (operator route choice "Both: Grok + AGY", 2026-10-31). The two responses below are the auditors' JSON objects, re-indented (key order and values unchanged); the raw files and their hashes are in `review_bundle/` (`GROK_AUDIT_RESPONSE_RAW.txt`, `AGY_AUDIT_RESPONSE_RAW.txt`, `SHA256SUMS_GROK.txt`, `SHA256SUMS_AGY.txt`). Self-reported identities are claims. Authority NONE; the proof is unsigned and `audit_identity.independence` is unattested.

- PRIMARY: `grok-cli` 1.0.70, model `grok-4.5` (init event), tool-less recipe. Status `PASS_WITH_RISKS`, 5 findings.
- CORROBORATING: `agy` 1.4.11, model `gemini-4-argon-high` (init event), session-only request-review settings. Status `PASS_WITH_RISKS`, 5 findings, Q3 `UNKNOWN` because AGY's copy of the prompt was truncated at the tail (see the coordinator summary).

## Grok response (re-indented JSON)

```json
{
  "model_self_reported": "grok-4",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "Cumulative DIFF touches exactly the seven intended content paths: docs/02-how-to/route-ledger.md, plugins/dopemux-route-ledger/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.test.ts, hooks/register.tsx, receipt.schema.json. No unrelated or smuggled content files appear. DELTA SUMMARY's six-file stat is consistent (hooks.json unchanged since the earlier audited head)."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "register.tsx writes only via $.fs.write(seg.path, …) with paths under the resolved receiptDir; FS surface used is exists/list/read/write/stat on those paths. No $.process, $.http, $.model, $.state/$.store, prompt hooks, or $.agent.spawn calls; agent.spawn is an observer hook only. receiptDir: .. segments refused (hasDotDot), empty/root refused, default compared after trailing-slash strip and gated on STATE_DIR exists, receiptDirProblem stats dir or nearest parent for isLink/non-dir, relative paths must beUnder project realPath, absolute allowed by design, segment file isLink checked once before first write, list failure of an existing/unknown dir disables (rehydrate). Stem: sanitizeStem replace + slice(0,120). Every hook body try/catched; tool.call always return next(e) with e untouched (including broken clock and failed write paths, covered by tests); turn.step yield* next(e) then return r unchanged; session.start enqueues init (does not await it) and void registerCommands; session.end awaits flushAtEnd by design. Receipt enqueue is never awaited by tool.call/turn.step (only clock stamp is)."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Receipt shapes in register.tsx match receipt.schema.json keys/nullability/enums/additionalProperties:false (agent_request includes spawned_agent_id/resolved_model; binding_fields six keys; advisor_use_id minLength 1). Empty effort → null/UNKNOWN (effortOf/toBindingFields); empty advisor id skipped. seq via nextSeq; advisor dedup advisorSeen; rollover maxReceiptsPerFile and limits.segmentBytesMax with utf8Length; rehydrate rebuilds tallies/toasts/lastMain; unreadable segments skipped (segmentsUnreadable); corrupt lines skipped; flush on serialized chain; spawn join mutates in-place then dirty+rewrite while holdsUnjoined blocks eviction. Closed clean segments evicted. Clock failure drops the receipt and increments receiptsFailed; write failure leaves dirty for later flush; clearPending preserves unwritten tails. Prompts never recorded; description '' unless recordDescription."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Advisors counted only in noteStep from r.serverToolUses where name==='advisor' and non-empty id; deduped; loop main vs agent from agentId; child vs session budgets in budgetToasts/statusText. Toast and table footers say the mod counts and cannot block. No session.append registration in register(). Docs/README/how-to/plugin.json match."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "Join is by tool_use_id only (recordSpawn; test with two same-description Agents). sameModel: dated suffix stripped, bare sonnet/opus/haiku/fable alias matches family. familyOf glyph rule. Fork with no model → inherits true, no unpinned toast. toBindingFields sets response_claimed from observed, effort_observed/provider_attested/independence_class always UNKNOWN. Schema $comment, README, how-to state a receipt is not a valid binding and not attestation; mod never runs ct."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "statusText: agents – / S×n… order, advisor N vs advisor N/B ⚠ against sessionAdvisorBudget only, separate child M/B ⚠ against childAdvisorBudget, ledger off, receipts ✗; debounce STATUS_DEBOUNCE_MS=500. /clear: flushAtEnd, keep status, reset or clearPending; real end clears status and sets isEnded. Toast-once keys restored on rehydrate (D3). /route-ledger table ≤60 +N more, pending: rows, main from lastMain, receipts arg, usage line; route-ledger and route each registered with own try/.catch. Residual race/host-ordering behaviour is offline-only (see N1)."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "register.test.ts is large and behavioural (pass-through, join-by-id, dedup, rollover, rehydrate, symlink/list fail-closed, /clear tails, description default off, debounce constant±1ms, command catch, UTF-8 bytes, etc.); failures would catch regressions. Mocks model the claimed API shapes. Import is extensionless from './register'. Untested/unknown live: real host hook budgets/ordering, /route acceptance on a given build, status coexistence with dopemux-pulse, 15-mutation sanity not re-run after 13ceb5020/61c371f28/3d2af4b20."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "README, how-to, plugin.json userConfig blurb, and schema $comment align with register.tsx on defaults, safety, budgets, binding_fields honesty, byte rollover ~3.5MB, stem truncation 120, recordDescription default false, /clear UNKNOWN id behaviour, list-fail-closed, UTF-8 sizing. Live behaviour explicitly NOT VERIFIED; /route described as best-effort alias with independent /route-ledger registration. No material claim contradicted by the diff."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No text in the seven files attempts to dictate this auditor's verdict, fake an audit result, or alter the output contract. Operator-facing how-to/README guidance and historical 'Codex review of …' test comments are documentation of the feature, not auditor steering."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No secrets, credentials, or PII added. Tests use the sentinel SECRET-PROMPT-DO-NOT-LOG only as a negative control that must not appear in receipts."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "Cumulative L2 change set is coherent, scoped, read-only as designed, schema-aligned, and covered by extensive offline tests including the R4 repairs and the three later fixes. Overall status is PASS_WITH_RISKS solely because the repaired frozen head has no live Claude Code session evidence. Before anyone relies on the mod live they must: load the frozen head with claude --plugin-dir plugins/dopemux-route-ledger; pin an Agent; exercise advisor over budget; run /route-ledger and /route-ledger receipts; /clear and confirm session-id/file behaviour; confirm status coexistence if dopemux-pulse is loaded; confirm writes land only under receiptDir."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "Against the cumulative diff: D1 lastMain + tests; D2 empty effort/advisor id + tests; D3 restoreToasted/restoreBudgetToasted + tests; D4 flushAtEnd one retry + tests; D5 STATUS_DEBOUNCE_MS export and ±1ms test; D6 stat/symlink/outside-root/trailing-slash + many tests; D7 evictClosed/holdsUnjoined + tests; D8 /clear reset + 61c371f28 clearPending/finishClear + tests; D9 recordDescription default false + tests; D10 docs (byte rollover, stem 120, six keys, last_review) and added tests. 13ceb5020: receipts arg uses toContain(FILE). 61c371f28: unwritten tails survive /clear. 3d2af4b20: list failure fail-closed; utf8Length + CJK tests. Each has pinning tests in register.test.ts."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "DELTA (26414fef5 + 13ceb5020 + 61c371f28 + 3d2af4b20) repairs prior defects and updates README/how-to for clearPending, list-fail-closed, UTF-8 byte sizing, recordDescription, dual budgets, and NOT VERIFIED live status. No regression or doc/code inconsistency found in the cumulative DIFF relative to those docs."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "HIGH",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Repaired frozen head has no live Claude Code session evidence; behaviour is attested only by the offline mock-engine kit.",
      "evidence": "IMPLEMENTER CLAIMS and limitations (i)/(f) state live load of the repaired code is NOT_RUN; how-to and README both say live behaviour is NOT VERIFIED. Pre-repair live observations are not in this message and are not evidence for b275543fe.",
      "status": "OPEN"
    },
    {
      "id": "N10",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/README.md",
      "summary": "Plugin API is early access; status-line coexistence with another plugin (e.g. dopemux-pulse) remains unverified.",
      "evidence": "README Limits and how-to §6 state early-access API drift risk and unverified coexistence; declaration file is not in the DIFF so API shape claims beyond what the code/tests show are UNKNOWN.",
      "status": "OPEN"
    },
    {
      "id": "N14",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Explicit absolute receiptDir remains allowed by design and can write outside the project tree subject only to link/directory checks.",
      "evidence": "receiptDirProblem returns undefined for absolute dirs after link/kind checks; tests 'D6: an absolute directory is allowed by design'; README/how-to/plugin.json disclose this (limitation vii).",
      "status": "OPEN"
    },
    {
      "id": "N15",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/hooks/register.test.ts",
      "summary": "The 15-mutation sanity check was run on 26414fef5 only and not re-run on the three later commits that form the frozen head.",
      "evidence": "PRIOR_FINDINGS / implementer limitation (e): scratch harness no longer exists; later commits 13ceb5020, 61c371f28, 3d2af4b20 changed tests/production after that check.",
      "status": "OPEN"
    },
    {
      "id": "N16",
      "severity": "INFO",
      "file": "docs/02-how-to/route-ledger.md",
      "summary": "markdownlint was NOT_RUN for the audited head.",
      "evidence": "Implementer claims: markdownlint Node environment cannot install on the host; pre-commit skipped that hook.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session transcript on frozen head b275543fe (status, toasts, /route-ledger, Agent join, advisor_call attribution, receipt schema validation, /clear session-id behaviour).",
    "Whether the host assigns a new session id on /clear (declaration claim vs live).",
    "Status-line coexistence with dopemux-pulse on the same build.",
    "Whether /route is accepted on the installed CLI build.",
    "Re-run of mutation sanity (or equivalent) against the frozen head including 61c371f28 and 3d2af4b20.",
    "markdownlint results for the seven content paths.",
    "The Claude Code declaration file (API shapes) referenced by implementers — not present in the DIFF."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "Operator how-to/README and schema $comment instruct humans on using the mod and disclose NOT VERIFIED live status; they do not steer this auditor's verdict or output contract. Test comments referencing prior Codex reviews are historical notes, not directives to this audit."
  }
}
```

## AGY response (re-indented JSON)

```json
{
  "model_self_reported": "unknown",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "All diff headers in the DIFF section touch only the seven intended content files: docs/02-how-to/route-ledger.md, plugins/dopemux-route-ledger/.claude-plugin/plugin.json, plugins/dopemux-route-ledger/README.md, plugins/dopemux-route-ledger/hooks/hooks.json, plugins/dopemux-route-ledger/hooks/register.test.ts, plugins/dopemux-route-ledger/hooks/register.tsx, and plugins/dopemux-route-ledger/receipt.schema.json. No unrelated or smuggled files appear. Note: the prompt payload ends with '<truncated 2662 bytes>' at line 99 of plugins/dopemux-route-ledger/receipt.schema.json (whose hunk header is @@ -0,0 +1,163 @@, accounting for the remaining 64 lines of that schema file and the closing diff marker)."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Read-only and host-safety checks pass in plugins/dopemux-route-ledger/hooks/register.tsx: (1) Only $.fs.write is called (register.tsx:392) on seg.path, which is always ${s.receiptDir}/${s.fileStem}[.<n>].jsonl (register.tsx:325-327, 493-501). (2) No $.process, $.http, $.model, $.state, $.store, $.agent.spawn, prompt hooks, or tool-rewrite APIs are used. (3) receiptDir validation (register.tsx:110-113, 161-163, 405-458): empty strings fall back to DEFAULT_RECEIPT_DIR; trailing slashes are stripped before comparing DEFAULT_RECEIPT_DIR and checking $.fs.exists('.control-tower/state'); '..' segments are rejected by hasDotDot; '/' (empty after stripping slashes) is rejected; receiptDirProblem walks up to the nearest existing directory with $.fs.stat and rejects if stat fails everywhere, if found.isLink is true, if found.kind !== 'dir', or (when relative) if found.realPath is not under $.session.root()'s realPath; flushSegments (register.tsx:383-390) checks $.fs.stat(seg.path, { resolve: false }) before first write and disables receipts if stat?.isLink === true. (4) sanitizeStem (register.tsx:157-159) replaces characters outside [A-Za-z0-9_-] with '_' and slices to 120 chars; empty stem disables receipts (register.tsx:449). (5) Every hook body (session.start, tool.call, agent.spawn, turn.step, command.run, session.end at register.tsx:662-753) wraps mod logic in try/catch, and s.chain catches task rejections (register.tsx:400-402). (6) tool.call (register.tsx:676-683) never mutates e and calls return next(e) unconditionally outside the try/catch on every path. (7) turn.step (register.tsx:699-707) delegates via const r = yield* next(e) and returns r unchanged after try/catch. (8) session.start queues initSession and drawStatus on s.chain without awaiting them and fires void registerCommands($); tool.call and turn.step only await $.clock.now() in stampThen (register.tsx:639-646) before enqueueing; session.end awaits flushAtEnd($, s) (at most 2 flushes on s.chain, register.tsx:409-416, 734, 749)."
    },
    {
      "id": "Q3",
      "verdict": "UNKNOWN",
      "evidence": "Verdict is UNKNOWN solely because the last 2662 bytes of the prompt were truncated at plugins/dopemux-route-ledger/receipt.schema.json:99 (cutting off the schema definitions of step_observed and advisor_call), and HARD RULE 1 forbids reading files with tools. For everything visible in the diff: (1) agent_request, binding_fields, and usage in receipt.schema.json:1-98 match register.tsx:42-90, 149-167, 550-601 and KEYS/BINDING_KEYS in register.test.ts:25-57. (2) seq is monotonic from 0 without gaps: duplicate advisor_use_id entries are filtered via s.advisorSeen in recordStep (register.tsx:593) and tally (register.tsx:226) before place() or s.nextSeq increment. (3) Segment rollover happens at maxReceiptsPerFile or limits.segmentBytesMax (3.5 MB in UTF-8 bytes via utf8Length, register.tsx:314-360). When recordSpawn mutates spawned_agent_id and resolved_model in place (register.tsx:601-608), seg.bytes is not updated by the ~30-50 byte delta, which stays well inside the ~694 KB margin below the 4 MiB host cap. (4) Rehydrate (register.tsx:480-539) sorts segments, skips corrupt lines, increments s.segmentsUnreadable on unreadable files without overwriting them (since s.nextSegmentN advances past them), and disables receipts if $.fs.list fails while the directory exists or $.fs.exists throws (register.tsx:481-492). (5) Coalesced flushes and whole-file rewrites are serialized on s.chain via s.flushQueued (register.tsx:399-413). (6) evictClosed (register.tsx:375-380) frees seg.receipts on closed, clean segments unless holdsUnjoined(s, seg) is true (note: if an Agent call is denied or never spawns, holdsUnjoined remains true for that segment for the session). (7) Prompts, file contents, and tool outputs are never recorded; description is '' by default and truncated to 80 chars when recordDescription is true (register.tsx:629-637)."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "In register.tsx:654-664, noteStep inspects r?.serverToolUses and collects only entries where u?.name === 'advisor' && typeof u.id === 'string' && u.id !== ''. Deduplication by id occurs in recordStep (register.tsx:593) and tally (register.tsx:226-227). Loop attribution is 'main' when agentId === null and 'agent' otherwise (register.tsx:228-232, 599). budgetToasts (register.tsx:287-309) checks childAdvisorBudget >= 0 per child agent and sessionAdvisorBudget >= 0 for the session total. Toast messages (register.tsx:295, 305), table footer (register.tsx:365), README.md:8,57, and docs/02-how-to/route-ledger.md:58,160 consistently state the mod only counts advisor calls and cannot block them. Not registering session.append is consistent with all documentation."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "recordSpawn (register.tsx:588-610) joins exclusively via s.agents['tool:' + toolUseId]. sameModel (register.tsx:148-155) normalizes trailing -YYYYMMDD dates and matches bare family aliases (sonnet, opus, haiku, fable) against observed model strings, returning null if either side is unknown. familyOf (register.tsx:139-146) maps sonnet->S, opus->O, haiku->H, fable->F, else other (?). Forks without a model set inherits: true and pinned: false (register.tsx:560) and do not trigger unpinned warnings (register.tsx:614) or unpinned counts (register.tsx:177). toBindingFields (register.tsx:149-167) sets effort_observed, provider_attested_model, and independence_class to 'UNKNOWN' and maps observedModel to response_claimed_model. README.md:35-44,58, docs/02-how-to/route-ledger.md:146-162, and receipt.schema.json:4 clearly warn that a receipt is not a valid ExecutionBinding, is not provider attestation, and that the mod never runs ct. Minor defect (N3 in findings): noteAgentCall (register.tsx:615-616) records facts.toolUseId in s.toasted synchronously before enqueueing recordAgentRequest; if s.isReady is false (e.g. first call after /clear), initSession subsequently runs Object.assign(s, freshSession(), ...) (register.tsx:461), wiping that tool_use_id from s.toasted in memory."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "statusText (register.tsx:246-274) formats agents in fixed order S, O, H, F, ? (or 'agents –'), appends ' · advisor N' or ' · advisor N/B ⚠' against sessionAdvisorBudget, independently appends ' · child M/B ⚠' for the busiest child against childAdvisorBudget, and appends ' · ledger off' and ' · receipts ✗' when applicable. Redraws are debounced by STATUS_DEBOUNCE_MS = 500 (register.tsx:48, 284-294). session.end with reason 'clear' (register.tsx:732-743) flushes via flushAtEnd, redraws and keeps the status line, and either sets s.clearPending = true (if dirty) or resets via freshSession(); other reasons set s.isEnded = true, clear status via $.ui.status(undefined), and await flushAtEnd. routeTable (register.tsx:327-368) renders main from s.lastMain, then agent and pending:<shortId> rows up to 60 total rows followed by '+N more'. registerCommands (register.tsx:391-413) registers 'route-ledger' and 'route' with independent try/.catch blocks. Minor logic issues (N2, N3 in findings): (1) command.run does not call ensureReady, so running '/route-ledger receipts' immediately after '/clear' before the next recorded event reports 'receipt file: none' and 'receiptsEnabled false'; (2) s.toasted is modified in noteAgentCall before ensureReady/initSession runs when !s.isReady."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "register.test.ts:15 imports from './register' without an extension. The test suite is non-vacuous, asserting exact receipt schemas, seq continuity, debounce boundaries (STATUS_DEBOUNCE_MS - 1 and + 1 at register.test.ts:535-549), UTF-8 byte rollover, symlink/traversal rejection, listing failures, and /clear dirty-tail retention. Untested gaps: (1) live Claude Code runtime execution on the repaired head; (2) running '/route-ledger receipts' immediately after '/clear' before the next hook event; (3) noteAgentCall toast deduplication across '/clear' when the very first post-clear event is an unpinned Agent call; (4) real host behavior of $.fs.stat(path, { resolve: true }) on symlinks (the mock in register.test.ts:175-193 returns isLink: false unless overridden)."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "README.md, docs/02-how-to/route-ledger.md, plugin.json, and the visible $comment in receipt.schema.json:4 accurately describe the code and honestly disclose that live behavior is NOT VERIFIED, status line coexistence with dopemux-pulse is unverified, /clear session-id rotation is UNKNOWN, and /route is a best-effort alias that may be refused. Two minor nuances are omitted from the docs: (1) after /clear and before the next recorded event, '/route-ledger receipts' also shows 'receipt file: none' and 'receiptsEnabled false' because initSession has not re-run yet; (2) for relative receiptDir paths, receiptDirProblem calls $.fs.stat(probe, { resolve: true }), whose isLink reporting on symlinks in the real host is unverified live."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "No instruction-like content aimed at steering an auditor, faking an audit verdict, or altering the output contract was found in any of the seven files in the diff."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No secrets, credentials, tokens, or PII are present in the diff; only synthetic test constants such as 'SECRET-PROMPT-DO-NOT-LOG' and 'sess-1' appear."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "The cumulative change set at frozen head b275543fe1011bf3a9351a10448c24d94f205370 is well-engineered, defensive, and read-only, with no blocking defects found in the visible diff (top-level status is PASS_WITH_RISKS due to the absence of live runtime verification on the repaired head and the 2662-byte prompt truncation at the tail of receipt.schema.json). Before relying on the mod in production, an operator must run a live Claude Code session to verify: (1) loading with 'claude --plugin-dir plugins/dopemux-route-ledger', initial status rendering, and coexistence with any other status line plugin (e.g. dopemux-pulse); (2) pinned, unpinned, and fork Agent tool calls, verifying toast display/timeout and agent.spawn tool_use_id join; (3) main-loop and subagent turn.step usage.model observation and serverToolUses advisor counting/budget toasts; (4) '/route-ledger', '/route-ledger receipts', and whether '/route' is accepted; (5) real host $.fs.stat(path, { resolve: true }) symlink/realPath behavior; (6) '/clear' and session exit behavior (session id rotation and flushAtEnd hook time budget); and (7) validation of emitted JSONL files against the full receipt.schema.json."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "Every claimed repair and subsequent fix is present in the code and pinned by tests in register.test.ts: D1/N11 (s.lastMain kept on Ledger and rebuilt on rehydrate: register.tsx:96,212,316; register.test.ts:750-769); D2/N12 (empty effort -> null/UNKNOWN, empty advisor id skipped: register.tsx:157-160,171-174,658; register.test.ts:773-819); D3/N13 (restoreToasted and restoreBudgetToasted on rehydrate: register.tsx:470-491; register.test.ts:823-863); D4/N4 (flushAtEnd retries once when dirty: register.tsx:409-416; register.test.ts:867-931); D5/N8 (exported STATUS_DEBOUNCE_MS tested at -1ms and +1ms: register.tsx:48; register.test.ts:535-549); D6/N2 (trailing slash normalization, $.fs.stat symlink/dir/root checks on receiptDir and segment files: register.tsx:383-390,405-458; register.test.ts:937-1055); D7/N3 (evictClosed and s.counts: register.tsx:360,375-380; register.test.ts:1059-1152); D8/N5 + 61c371f28 (/clear flushes via flushAtEnd, keeps status, defers reset via clearPending/finishClear when dirty: register.tsx:525-538,732-743; register.test.ts:1156-1267); D9/N9 (recordDescription default false omits description from receipts and toasts: register.tsx:115,618-637; register.test.ts:1271-1305); D10/O1-O5 (docs updated, comment fixed to 'six' at register.tsx:53, last_review updated at route-ledger.md:8, tests added at register.test.ts:1309-1438); N6/N7 from 4fcdc9761 (TOAST_MS on unpinned toast, separate child M/B ⚠ status segment, no doubled prefix: register.tsx:257-270,620-622); 13ceb5020 (expect(text).toContain(FILE) at register.test.ts:659); and 3d2af4b20 (failed $.fs.list checks $.fs.exists and fails closed if present; utf8Length counts UTF-8 bytes: register.tsx:339-354,481-492; register.test.ts:1337-1431)."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "No blocking regressions or contradictions with README.md or docs/02-how-to/route-ledger.md were introduced since 989fe4651c050ec23619e5208da17d6152b477b0. Two minor edge cases exist in the D8/D3 interactions (recorded as LOW findings N2 and N3): (1) immediately after /clear and before the next recorded hook event triggers ensureReady, '/route-ledger receipts' reports 'receiptsEnabled false' and 'receipt file: none' because freshSession() resets receiptsEnabled to false; (2) when s.isReady is false (e.g. on the first Agent call after /clear), noteAgentCall updates s.toasted before ensureReady/initSession runs Object.assign(s, freshSession(), ...), clearing that call's tool_use_id from s.toasted in memory."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "HIGH",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Repaired frozen head has not been verified in a live Claude Code session, and host $.fs.stat(path, { resolve: true }) symlink semantics are only tested against a local mock.",
      "evidence": "As disclosed in limitation (i) and docs/02-how-to/route-ledger.md:19-21, the frozen head b275543fe1011bf3a9351a10448c24d94f205370 has only been run against the offline mock harness in register.test.ts. In particular, receiptDirProblem (register.tsx:409) calls $.fs.stat(probe, { resolve: true }) for relative paths and checks found.isLink (register.tsx:414); whether the real host engine's stat with resolve: true preserves isLink: true on a symlink whose target resolves inside the project root, how /clear handles session IDs live, and whether status text coexists with dopemux-pulse remain unverified in a live session.",
      "status": "OPEN"
    },
    {
      "id": "N2",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Running '/route-ledger receipts' immediately after '/clear' (before the next recorded event) reports 'receiptsEnabled false' and 'receipt file: none'.",
      "evidence": "On session.end with reason 'clear' (register.tsx:740) or in finishClear (register.tsx:532), Object.assign(s, freshSession()) sets isReady: false, receiptsEnabled: false, and receiptFile: undefined (register.tsx:120-124). Because the command.run handlers (register.tsx:710-722) read s directly via routeAnswer without calling ensureReady($, s), running '/route-ledger receipts' after '/clear' but before the next tool.call/turn.step/agent.spawn reports 'receipt file: none' and 'receiptsEnabled false' even when receipts are enabled.",
      "status": "OPEN"
    },
    {
      "id": "N3",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "noteAgentCall checks and mutates s.toasted synchronously before ensureReady/initSession runs, so initSession's freshSession() reset wipes the first unpinned tool_use_id toasted while !s.isReady.",
      "evidence": "In noteAgentCall (register.tsx:615-626), s.toasted.has(facts.toolUseId) and s.toasted.add(facts.toolUseId) run synchronously before enqueue(s, () => recordAgentRequest($, s, facts)). When s.isReady is false (such as on the first Agent call after /clear, or if tool.call fires while session.start's initSession is still awaiting $.session.id()/$.fs.stat), initSession executes Object.assign(s, freshSession(), ...) (register.tsx:461) before rehydrate and before commit, replacing s.toasted with a new Set() and losing the in-memory toasted entry for that new call (and checking s.toasted before rehydrate has restored pre-clear toasts).",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "LOW",
      "file": "plugins/dopemux-route-ledger/hooks/register.tsx",
      "summary": "Segments containing an agent_request whose agent.spawn was refused or never fired are never evicted from memory during the session.",
      "evidence": "evictClosed (register.tsx:375-380) skips any closed segment where holdsUnjoined(s, seg) (register.tsx:364-371) is true (r.kind === 'agent_request' && r.spawned_agent_id === null && s.agents['tool:' + r.tool_use_id]?.receipt === r). When agent.spawn is denied (r?.deny !== undefined in noteSpawn, register.tsx:679) or never occurs, s.agents['tool:' + toolUseId] is never cleared or marked failed, so that segment's receipts remain in memory for the lifetime of the session.",
      "status": "OPEN"
    },
    {
      "id": "N5",
      "severity": "INFO",
      "file": "plugins/dopemux-route-ledger/receipt.schema.json",
      "summary": "The final 2662 bytes of the prompt were truncated at line 99 of receipt.schema.json, leaving the step_observed and advisor_call JSON schema definitions uninspected.",
      "evidence": "plugins/dopemux-route-ledger/receipt.schema.json has diff header @@ -0,0 +1,163 @@, but the prompt ends at line 99 inside definitions.step_observed.required with '<truncated 2662 bytes>'. Per HARD RULE 1, no tools were used to read the file from disk.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "The untruncated tail (last 2662 bytes, lines 100-163) of plugins/dopemux-route-ledger/receipt.schema.json covering definitions.step_observed and definitions.advisor_call, which was cut off at the end of the prompt message.",
    "A live Claude Code session run on the frozen head b275543fe1011bf3a9351a10448c24d94f205370 verifying status line coexistence, $.fs.stat(..., { resolve: true }) symlink behavior, /clear session ID behavior, and session.end flush timing."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "No prompt injection or attempt to steer the auditor or alter the output contract was found anywhere in the diff."
  }
}
```

## Coordinator summary

- Both auditors returned `PASS_WITH_RISKS` with no BLOCKING finding. Grok answered Q1-Q13 PASS. AGY answered Q1, Q2 and Q4-Q13 PASS and Q3 UNKNOWN.
- AGY's Q3 is UNKNOWN because the prompt it received ended with `<truncated 2662 bytes>` inside `receipt.schema.json`. The prompt sent was intact (194,244 bytes, ends with the diff's closing marker, cmp-equal to the committed file, no such marker anywhere in it); the cut was on AGY's side. AGY's figures fit the prompt: schema content line 99 ends 2,313 bytes before the end, 349 bytes after AGY's cut point. AGY therefore corroborates only about 98.6 % of the prompt; the schema tail it missed was covered by the primary. See `review_bundle/AGY_ADJUDICATION.md` ("Input integrity").
- Union of findings: 9 (1 HIGH, 3 LOW, 5 INFO), all OPEN, none BLOCKING, every one adjudicated against the source at the audited head (`review_bundle/COMBINED_ADJUDICATION.md`). The only HIGH is N1: the frozen head has not run in a real Claude Code session. New LOW findings (N17, N18, N19) were raised by AGY only and are bounded; none is a data-loss path.
- Neither auditor re-raised a finding the claims file lists as repaired or changed (R4 N2-N5, N8, N9, N11-N13, O1-O5); both answered Q12 PASS with code and test citations for the repair items and the three later fixes.
- Identity: Grok answered `grok-4` while the CLI was run with `-m grok-4.5` (every init event shows `grok-4.5`): UNRESOLVED. AGY answered `unknown`. Provider attestation UNKNOWN for both. Exact-model evidence for the schema-required `gemini-3.1-pro-high` is unavailable, so PR Steward may not treat the AGY leg as READY.
- Neither auditor ran the code or the tests. The open items for the operator are: the live-session check (N1), whether partial AGY corroboration is acceptable, identity attestation, signing, and the three Codex review threads.
