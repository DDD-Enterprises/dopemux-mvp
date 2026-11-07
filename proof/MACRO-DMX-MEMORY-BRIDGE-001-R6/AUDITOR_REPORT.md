# Auditor Report - MACRO-DMX-MEMORY-BRIDGE-001-R6

**Subject**: frozen content head `1cddbfb339650c4f8f02e87cb62e7aa8f08f90e1` on branch `claude/memory-bridge-001-b349d8` (the merge of main into the W03 head), base `6fb9d81798cbcca7f99c96f1b9fd07b6d3c7db68` (main after PR #1482), cumulative diff of 6 content files (11 commits), sha256 `172cc0db4deecd99f9b530aec21f735b08fe1ed404a178151642bfa2205a5ea1`. Proof-only commits follow it.
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli`, model `grok-4.5` (self-reported `grok`).
**Route**: the operator's verbatim line `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R6_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`; tool-less recipe; `init.tools == []` in probe and run, zero `tool_use` blocks.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.
**Signature**: none (operator step). `audit_identity.independence` unattested.

## Auditor response (verbatim)

```json
{
  "model_self_reported": "grok",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "Cumulative diff adds exactly six paths: docs/02-how-to/memory-bridge.md, plugins/dopemux-memory-bridge/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.test.ts, hooks/register.tsx. No other hosts, no hidden writes outside outbox/.dopemux/memory-bridge, $.store, git status, or dopemux capture emit. R6 DELTA touches only how-to, README, and register.test.ts."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Only subprocess argv arrays: ['git','status','--porcelain'] (dirtyFileCount) and ['dopemux','capture','emit','--event',JSON.stringify(event),'--mode','plugin','--repo-root',root] (emitOnce). No shell. Event built from LedgerEvent structs (title/summary already clean()). safeId confines file keys; relativeTo drops paths outside root; outboxDir is root/.dopemux/memory-bridge only; findRoot walks ≤40 ancestors; persistOnce writes only when .dopemux already exists. Session id / note / goal cannot reshape argv structure."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Outbox/store/ledger get only derived fields: clean() goal≤160, paths≤30, decisions≤3×200 from Decision:/DECISION: lines in first MAX_ANSWER_SCAN_CHARS=200000, todos≤10, note≤500 at /bridge-note. REDACTIONS cover PEM, JWT, sk-ant/sk-, ghp_/github_pat_/xox, AKIA, Bearer, URL userinfo, emails, KEY=value, JSON password, /Users|/home → ~/. clean() bounds then redacts then caps (no half-masked secret). No raw prompt/tool output/answer path. Status/band use stored redacted strings plus git line count. Best-effort disclosed."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Ring: gen header+rows+eof footer; newest valid gen; torn (mismatched footer) ignored; alt/primary by (gen-1)%2; failed write does not advance gen. Cap FILE_CAP_BYTES with drop sent→dead→pending; ROW_CAP_BYTES via fitRow. id=sha256(session NUL turn NUL kind [NUL disc])[:24]; ring.ids de-dup. Single flushPromise/flushing chain; WRITE_TIMEOUT_MS race keeps flushing until settle. No .dopemux → mode memory + $.store (3 sessions, STORE_CAP_BYTES). /clear appends end and continues; other reasons cancel timers and clear status. Subagent agentId skips turn/goal/todos. Timers cancelled on real end; replay armed only while hasReplayable."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "replayTick serial via ledgerInFlight until settled.finally; REPLAY_PER_TICK=3; markRow sent only on exit 0; failed/timeout increment attempts, dead at MAX_ATTEMPTS=5; unavailable (process deny/throw/short fail) leaves pending with attempts unchanged. isReplayable = pending && (task.completed|manual.memory_store); renderStatus pending/waiting use only that. Events only those two shapes with event_id=row.id. Tests: mark-after-exit-0, 3/tick, five-dead, process deny/throw, timeout no pile-up, status clear→1 pending→clear, adopt counted."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "ui.render AbovePrompt awaits next(e), wraps in Box+Text above inner; hasSurvey|no line|not idle → return inner; try/catch returns inner. idleMsOf clamps 5–1440 default 30; touch on prompt/turn.complete dismisses; dirtyFileCount degrades on deny/throw/hang with gitInFlight guard. Pulse-without-next prepend accepted by test. Does not throw into host."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "prompt.submit/turn.start/turn.complete/session.start/session.end return next(e); tool.call and session.compact return await next(e) result unchanged. Bodies try/catch; command.register .catch; observeTool/capture void+.catch. /bridge-note: clean+cap 500, append note/manual.memory_store, reply matches /queued/i and 'Nothing is stored yet'; empty args → usage, no write. Registered description 'Queue a note for the capture ledger'."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "134-style coverage in diff: capture, redactor LEAKY table, ring/cap/torn gen, status/relay/file-key, band/Pulse, replay serial/dead/unavailable, bridge-note, no network. Mocks fs/store/process/clock/http. untilWritten loops settle+setTimeout(0) until writes.length≥minWrites or 200 rounds; callers then expect writes.length>0 / keyOf — if write never happens assertion fails (non-vacuous). Fixes test timing around crypto.subtle.digest for long ids; production already awaits digest24 before push/flush, so helper does not mask a production ordering bug. Live/real ledger/$.process desktop untested (disclosed)."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "C1: how-to/README now state $.store is a Claude Code config JSON file; memory-only = no outbox file, not nothing on disk. C2: outbox writer never creates .dopemux; replay/dopemux capture emit can create it in dopemux-mvp for chronicle.sqlite. C3: README verification query uses select event_type, id and notes table has no event_id column. No commit hash or PR number in docs. NOT_RUN and Not built tables present and match code. .gitignore:140/:299 line cites not in diff (unverifiable here, not a code contradiction)."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "DIFF is plugin source, tests, README, how-to. No text directing this auditor's verdict, faking PASS/FAIL, or altering the JSON contract. Test 'secrets' are synthetic redactor needles. No credentials or personal data added."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "No recap injection; no decision.logged (ledgerEvent + tests); no $.http.fetch/ConPort/dope-memory; relay adoptRow copies into own ring only, earlier file never written (tests assert writes only to own primary/alt). Extra vs headline intent but documented: safeId, relay, foldedDead, store prune, fitRow, in-flight guards — all in INTENT e2–e4 / disclosures."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "N1–N6 and N12 remain repaired in cumulative head; N7–N11 still present as INFO; C1–C3 repaired in R6 docs DELTA; C4 erratum consistently states R2 wall-time exceeded and status should have been NEEDS_SUPERVISOR without changing code. R6 introduces no code regression (register.tsx absent from DELTA)."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "safeId: /^[A-Za-z0-9_-]{1,80}$/ unchanged (no ~); else prefix=replace/slice(56)+'~'+fnv1a32(id)+fnv1a32('\\0'+id) — forms disjoint. Used for generationPath, store outbox:${safeId}, readPrior own Set, adopted_from=file.key; list regex outbox-(.+?)(?:\\.alt)?\\.jsonl$ fits keys without '.'. Relay: file mode only; quiet≥10min; age≤7d; ≤50 oldest; skip non-isReplayable, sent/dead anywhere, ids already in rings; keep original id; single-writer (no foreign writes); ledger idempotent via event_id=row.id. Pending = isReplayable in this process rings including adopted. KEY_CASES + relay tests non-vacuous with untilWritten."
    },
    {
      "id": "Q14",
      "verdict": "PASS",
      "evidence": "All Q1–Q13 PASS from diff evidence. Residual risks unchanged and disclosed: live NOT_RUN (N7), $.process desktop UNKNOWN (N9), Pulse outer hide (N10), relay residuals (N11), best-effort redaction, $.fs.write atomicity UNKNOWN. Overall status PASS_WITH_RISKS, not FAIL."
    }
  ],
  "predecessor_findings": [
    {"id": "N1", "disposition": "STILL_REPAIRED", "evidence": "how-to and README contain no commit hash or PR number."},
    {"id": "N2", "disposition": "STILL_REPAIRED", "evidence": "command.register description is 'Queue a note for the capture ledger' (register.tsx + test)."},
    {"id": "N3", "disposition": "STILL_REPAIRED", "evidence": "renderStatus counts only isReplayable rows in s.rings (own + adopted); relay copies quiet earlier rows."},
    {"id": "N4", "disposition": "STILL_REPAIRED", "evidence": "decisionsOf scans answer.slice(0, MAX_ANSWER_SCAN_CHARS) with MAX_ANSWER_SCAN_CHARS=200_000."},
    {"id": "N5", "disposition": "STILL_REPAIRED", "evidence": "README: attempts = failed calls plus final successful one; markRow increments on ok and on fail/timeout."},
    {"id": "N6", "disposition": "STILL_REPAIRED", "evidence": "No foldedPending; only foldedDead/foldedDropped; /clear fold removes ring when drained of replayable rows."},
    {"id": "N7", "disposition": "STILL_PRESENT", "evidence": "Docs and disclosures: live behaviour NOT_RUN; tests only."},
    {"id": "N8", "disposition": "STILL_PRESENT", "evidence": "tool.call returns next result then void observeTool(...).catch."},
    {"id": "N9", "disposition": "STILL_PRESENT", "evidence": "Docs: $.process on desktop UNKNOWN."},
    {"id": "N10", "disposition": "STILL_PRESENT", "evidence": "Accepted Pulse prepend-without-next test; plugin order UNKNOWN."},
    {"id": "N11", "disposition": "STILL_PRESENT", "evidence": "Disclosed relay residuals (idle>10min double-delivery no-op; re-relay after cap drop; eight newest files)."},
    {"id": "N12", "disposition": "STILL_REPAIRED", "evidence": "safeId injective ordinary vs ~hash form; empty→~811c9dc5050c5d1f; KEY_CASES tests."},
    {"id": "C1", "disposition": "REPAIRED", "evidence": "DELTA how-to/README: rows without .dopemux live in memory and $.store file; memory-only means no outbox file."},
    {"id": "C2", "disposition": "REPAIRED", "evidence": "DELTA: outbox writer never creates .dopemux; replay can create it via capture emit in dopemux-mvp; troubleshooting notes first successful replay creates it."},
    {"id": "C3", "disposition": "REPAIRED", "evidence": "DELTA README: sqlite select event_type, id; '(the table has no event_id column)'."},
    {"id": "C4", "disposition": "REPAIRED", "evidence": "ERRATUM: R2 wall-time ≥6h28m, should have been NEEDS_SUPERVISOR; no pause exemption; code unaffected; operator ratification left open; consistent with packet wording."}
  ],
  "findings": [],
  "needs_more_evidence": [
    "Independent byte/hash proof that hooks/register.tsx at frozen head equals R5 head (DELTA omits it; claim accepted from delta absence only).",
    "Live Claude Code session proof (explicitly NOT_RUN).",
    ".gitignore lines 140 and 299 as cited (not in this diff)."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "DIFF content is implementation, tests, and user docs. No auditor-steering, fake verdict, or output-contract rewrite found."
  }
}
```

## Coordinator adjudication (summary)

| Id | Auditor disposition | Coordinator adjudication |
|---|---|---|
| N1 | STILL_REPAIRED | STILL_REPAIRED (concur): `grep -c -E '\b[0-9a-f]{7,40}\b\|#[0-9]{3,}'` finds 0 matches in the how-to and the README. |
| N2 | STILL_REPAIRED | STILL_REPAIRED (concur): `register.tsx:1279` registers 'Queue a note for the capture ledger'. |
| N3 | STILL_REPAIRED | STILL_REPAIRED (concur): the relay (`adoptEarlier`, `register.tsx:1181`) and the replayable-only status are intact; `register.tsx` is unchanged since R5. |
| N4 | STILL_REPAIRED | STILL_REPAIRED (concur): `MAX_ANSWER_SCAN_CHARS = 200_000` (`register.tsx:64`). |
| N5 | STILL_REPAIRED | STILL_REPAIRED (concur): `README.md:52` counts "delivery attempts that ran (failed ones plus the final successful one)". |
| N6 | STILL_REPAIRED | STILL_REPAIRED (concur): `foldedPending` occurs 0 times in `register.tsx`. |
| N7 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N8 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N9 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N10 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N11 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N12 | STILL_REPAIRED | STILL_REPAIRED (concur): `safeId` unchanged since R5 (same blob). |
| C1 | REPAIRED | REPAIRED (concur): README lines 31-33 and how-to section 2 say `$.store` is a JSON file in the Claude Code config directory and `📮 memory-only` means "no outbox file", not "nothing on disk"; how-to section 7 says leaving out `.dopemux` does not keep notes off disk. |
| C2 | REPAIRED | REPAIRED (concur): "never creates `.dopemux`" now applies to the outbox writer only; the replay runs regardless and creates `.dopemux/` only in a dopemux-mvp checkout with the default ledger path (matches `capture_client.py`: redactor load before the `mkdir`). |
| C3 | REPAIRED | REPAIRED (concur): `README.md:239` selects `event_type, id`, with "(the table has no `event_id` column)". |
| C4 | REPAIRED | REPAIRED as a record correction (concur): `ERRATUM_R2_WALL_CAP.md` states the breach and the correct status; R2 files unchanged. Ratifying the overrun after the fact, or recording R2 as `NEEDS_SUPERVISOR`, stays the operator's decision. |

Open at this head (all INFO):

| Id | Auditor severity | Adjudication |
|---|---|---|
| N7 | INFO | STILL_PRESENT, disclosure; INFO |
| N8 | INFO | STILL_PRESENT, design note; INFO |
| N9 | INFO | STILL_PRESENT, disclosure; INFO |
| N10 | INFO | STILL_PRESENT, accepted caveat; INFO |
| N11 | INFO | STILL_PRESENT, disclosed relay residuals; INFO |

The operator accepted N7 to N11 for the R5 head on 2026-10-30. That acceptance was for `bce150b58`; it is not carried over to this head without the operator's word, so `PROOF.json` lists them as OPEN.

## Open risks

1. Never run live; desktop `$.process`, Pulse band order and `$.fs.write` atomicity UNKNOWN (N7, N9, N10).
2. Relay residuals (N11), all ledger no-ops or bounded by 7 days.
3. N8: fire-and-forget observation in the `tool.call` hook (design note).
4. The status label `📮 memory-only` is unchanged (a rename changes code); the docs say what it means.
5. Not built by design: recap, `decision.logged`, dope-memory REST replay, any ConPort access.
