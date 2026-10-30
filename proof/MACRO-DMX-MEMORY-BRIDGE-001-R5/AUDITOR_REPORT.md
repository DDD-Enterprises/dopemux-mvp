# Auditor Report - MACRO-DMX-MEMORY-BRIDGE-001-R5

**Subject**: content head `bce150b5858528bfb26b3b15e3248cb1294a65e5` on branch `claude/memory-bridge-001-b349d8`, base `93050d135ffc2592000c1d0edef82b2912935525`, cumulative diff of 6 content files (9 commits), sha256 `c9ad11865273be83e396378aad537b8ac7e1d9950ab9836ebdf853195f4d8a7b`. Proof-only commits follow it. Fourth audit of this mod (R2, R3, R4 at `88e7b7de3a43b50b4c4cdac7fc340f21bda03e40`: all PASS_WITH_RISKS; their records are unchanged).
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli`, model `grok-4.5` (self-reported `grok-4`).
**Route**: the operator's verbatim line `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R5_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`; tool-less recipe; `init.tools == []` in probe and run, zero `tool_use` blocks.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.
**Signature**: none (operator step). `audit_identity.independence` unattested.

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
      "evidence": "Cumulative diff adds exactly six paths: docs/02-how-to/memory-bridge.md, plugins/dopemux-memory-bridge/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.test.ts, hooks/register.tsx. No other hosts, services, hidden writes, or unrelated trees."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Only subprocesses are $.process.run(['git','status','--porcelain'], {cwd, timeoutMs}) and argv ['dopemux','capture','emit','--event', JSON.stringify(event), '--mode','plugin','--repo-root', root] (register.tsx emitOnce / dirtyFileCount). Array argv, no shell. Paths under normalizePath(root)/.dopemux/memory-bridge/outbox-<safeId>.jsonl|.alt.jsonl; .dopemux never created; findRoot walks at most 40 ancestors; relativeTo drops paths outside root; event payload is a closed LedgerEvent shape; session id reaches the filesystem only via safeId."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Outbox/store hold derived fields only (goal≤160, ≤30 rel paths, ≤3 decisions≤200, ≤10 todo titles, note from /bridge-note ≤500 after clean). Status/band show counts or already-cleaned goal/decision text. REDACTIONS cover PEM, JWT, sk-/sk-ant-, ghp/github_pat/xox, AKIA/ASIA, Bearer, URL userinfo, emails, KEY=value, JSON secret keys, /Users|/home → ~/. clean() trims to chars*4+200 before regexes then redacts then caps (secret-before-truncation). Decision scan sliced to 200_000 chars. No raw prompt/tool output/answer path. Redaction remains best-effort as disclosed."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Ring: header meta=gen + rows + footer meta=eof with matching gen/rows; torn files lack footer and are ignored; newest valid gen wins; alternate primary/alt by gen parity; failed write does not advance gen. Cap 1 MiB / 8 KB with drop order sent→dead→pending and +N dropped. Ids = first 24 hex of sha256(sid NUL turnId NUL kind [NUL disc]); de-dup via ring.ids. Single flushPromise/flushing chain; write raced 3s but flushing held until settle. Absent .dopemux → memory+$.store. /clear appends end and continues; other end reasons cancel timers and clear status. Subagent turns/todos/goal ignored. No unbounded timer: replay/idle armed only while needed."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "replayTick serial, ≤3/tick, mark sent only on exit 0, attempts++ on fail/timeout, dead at 5, unavailable (no process / early reject) does not attempt; ledgerInFlight held until settled.finally. Only task.completed and manual.memory_store via ledgerEvent. isReplayable = pending && (task.completed|manual.memory_store); turn/compact/end never counted. Tests: clear→1 pending→clear after send; adopted quiet tasks count; prior turns alone show clear."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "ui.render AbovePrompt awaits next(e), wraps in Box above inner; returns inner on hasSurvey, ended, no line, or idle not elapsed; try/catch returns inner. Idle via lastActivityAt+idleMs; prompt/turn.complete call touch. git status degrade/deny/throw/hang → omit files segment; gitInFlight prevents pile-up. Pulse outer-without-next accepted and tested."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "prompt.submit/turn.start/turn.complete return next(e); tool.call/session.compact await next then return that result; observers are void/catch. session.start/command.register failures caught. /bridge-note: clean(args,500), empty→usage no write, else queue note+manual.memory_store and reply 'Queued'/'Nothing is stored yet'."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "Tests are behavioral (status counts, adoption rules, key injectivity, redactor needles, serial ledger, hung write/git/ledger caps, band wrap/survey/Pulse). Mocks cover clock/fs/store/process/http. Untested/live: real Claude session, real dopemux capture emit, real chronicle.sqlite, desktop $.process, fs.write atomicity, two live concurrent sessions — all disclosed NOT_RUN."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "How-to and README match code on outbox path, safeId rule, caps, status semantics, band, replay argv/rules, relay (10m/7d/50, no write to earlier file), /bridge-note, privacy, Not built table, NOT_RUN. No commit hash or PR number cited. Unverifiable from this message only: exact .gitignore line numbers 140/299 (external to the six-file diff); not a code contradiction."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No auditor-steering directives, planted verdicts, or output-contract overrides in the six files. No real secrets/credentials/PII added; LEAKY fixtures are synthetic redactor needles."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "No session-start recap/injection, no decision.logged (intended_event only task.completed|manual.memory_store|null; test asserts absence), no $.http.fetch/ConPort/dope-memory. Relay readPrior/adoptEarlier only read earlier files; writes restricted to own generationPath. Extra but intent-aligned: store prune to 3, foldedDead/Dropped, fitRow shrink steps, MAX_SESSIONS_READ=8, INIT/END timeouts."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "N12 repaired by injective safeId (e3). N1–N6 remain present in cumulative code (scan bound, relay, in-flight guards, pending-only status, etc.). N7–N11 deliberately unchanged. No regression or new BLOCKING/HIGH defect found in the file-key change; residuals stay INFO as disclosed."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "safeId: /^[A-Za-z0-9_-]{1,80}$/ → identity (no ~); else prefix≤56 + '~' + fnv1a32(id)+fnv1a32('\\0'+id) (16 hex). Ordinary keys unchanged; forms cannot meet. Used consistently for generationPath, store outbox:${safeId}, readPrior own-set map(safeId), adopted_from=file.key; list regex ^outbox-(.+?)(?:\\.alt)?\\.jsonl$. Relay: copy keeps id/ts/session_id/attempts, sets adopted_from, state pending; skips non-isReplayable (no turn/compact/end), quiet≥10m, age≤7d, ≤50 oldest, skips sent/dead anywhere and ids already in rings; earlier file never written; ledger idempotent via event_id=row.id. Pending counts only this process's replayable rows. Tests for keys/adoption non-vacuous. Disclosed residuals (idle live session dual-delivery no-op; re-relay after cap-drop of sent copy) remain."
    },
    {
      "id": "Q14",
      "verdict": "PASS",
      "evidence": "Cumulative L2 change implements (a)–(f)/(e2)/(e3) as coded and tested; N12 closed; prior repairs hold; open items are disclosed INFO limits (never live-run, desktop $.process UNKNOWN, Pulse ordering, relay residuals). Overall status PASS_WITH_RISKS, not FAIL."
    }
  ],
  "predecessor_findings": [
    {
      "id": "N1",
      "disposition": "STILL_REPAIRED",
      "evidence": "R3 repair still in cumulative head (outbox/status/replay structure intact; no reintroduction of the earlier defect class)."
    },
    {
      "id": "N2",
      "disposition": "STILL_REPAIRED",
      "evidence": "R3 repair still present in register.tsx ring/flush/status paths."
    },
    {
      "id": "N3",
      "disposition": "STILL_REPAIRED",
      "evidence": "Relay (e2) present: adoptEarlier/readPrior, quiet 10m, age 7d, cap 50, adopted_from, no write to earlier file; covered by tests."
    },
    {
      "id": "N4",
      "disposition": "STILL_REPAIRED",
      "evidence": "MAX_ANSWER_SCAN_CHARS=200_000; decisionsOf slices answer before matchAll; tests for inside/beyond/huge answer."
    },
    {
      "id": "N5",
      "disposition": "STILL_REPAIRED",
      "evidence": "R3 repair still present (in-flight / status semantics retained)."
    },
    {
      "id": "N6",
      "disposition": "STILL_REPAIRED",
      "evidence": "Dead-branch removal from R4 remains; ledgerEvent only builds the two allowed types; stray intended_event rows stay pending and unemitted."
    },
    {
      "id": "N7",
      "disposition": "STILL_PRESENT",
      "evidence": "Docs and DISCLOSED LIMITATIONS: live Claude Code session NOT_RUN; tests only."
    },
    {
      "id": "N8",
      "disposition": "STILL_PRESENT",
      "evidence": "tool.call still awaits next(e), then void observeTool(...); intentional non-blocking observe."
    },
    {
      "id": "N9",
      "disposition": "STILL_PRESENT",
      "evidence": "$.process desktop availability still UNKNOWN; code treats deny/throw as unavailable without spending attempts."
    },
    {
      "id": "N10",
      "disposition": "STILL_PRESENT",
      "evidence": "Outer plugin drawing AbovePrompt without next(e) still hides the band; accepted; test pulseLike('prepend')."
    },
    {
      "id": "N11",
      "disposition": "STILL_PRESENT",
      "evidence": "Relay residuals unchanged: idle>10m live session can be dual-delivered (ledger no-op); sent copy dropped by 1 MiB cap may be re-adopted while source among eight newest; bounded by 7-day age."
    },
    {
      "id": "N12",
      "disposition": "REPAIRED",
      "evidence": "Old safeId collapsed distinct ids via replace-to-_ and truncate-80 (empty→unknown). New safeId keeps ordinary [A-Za-z0-9_-]{1,80} unchanged; others get prefix~64-bit FNV of whole id; empty→~811c9dc5050c5d1f; tests KEY_CASES / no collision / odd-id reload / odd-id relay."
    }
  ],
  "findings": [
    {
      "id": "N7",
      "severity": "INFO",
      "file": "docs/02-how-to/memory-bridge.md",
      "summary": "Mod has never run in a real Claude Code session; proof is test-kit only.",
      "evidence": "How-to Status/Verification and README Tests and live proof state live behaviour NOT_RUN; DISCLOSED LIMITATIONS (i).",
      "status": "OPEN"
    },
    {
      "id": "N8",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "tool.call observes with void after next(e) returns; observation is async fire-and-forget.",
      "evidence": "on('tool.call'): const result = await next(e); void observeTool(...); return result;",
      "status": "OPEN"
    },
    {
      "id": "N9",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "$.process on the desktop surface remains UNKNOWN; git segment and ledger replay depend on it.",
      "evidence": "emitOnce/dirtyFileCount degrade to unavailable/omit; docs Desktop surface section.",
      "status": "OPEN"
    },
    {
      "id": "N10",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "An outer AbovePrompt hook that omits next(e) (e.g. Pulse focus) hides the welcome-back band; plugin order UNKNOWN.",
      "evidence": "Accepted Pulse caveat in docs; test 'an outer plugin that draws without next hides the band'.",
      "status": "OPEN"
    },
    {
      "id": "N11",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Relay residuals: possible dual delivery (ledger no-op) and bounded re-relay after cap-drop of a sent copy; only eight newest earlier files scanned.",
      "evidence": "adoptEarlier + MAX_SESSIONS_READ=8; DISCLOSED LIMITATIONS (v).",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session load of plugins/dopemux-memory-bridge (NOT_RUN).",
    "Real dopemux capture emit against a checkout with services/working-memory-assistant (NOT_RUN).",
    "Whether $.process.run exists and succeeds on the desktop surface (UNKNOWN).",
    "Installed plugin order vs dopemux-pulse for AbovePrompt (UNKNOWN).",
    "Atomicity of $.fs.write (UNKNOWN; generation scheme is the mitigation).",
    "Exact .gitignore lines 140 and 299 cited in docs (not in this six-file diff)."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "README/how-to are operator and assistant how-tos describing behaviour and Not-built limits. No text attempts to dictate this auditor's verdict, fake PASS/FAIL, or alter the output contract. Test fixtures use synthetic secret shapes only."
  }
}
```

## Coordinator adjudication (summary)

| Id | Auditor disposition | Coordinator adjudication |
|---|---|---|
| N1 | STILL_REPAIRED | STILL_REPAIRED, re-verified by the coordinator (the auditor's evidence describes the wrong finding): a grep finds no commit hash or PR number in the how-to or README. |
| N2 | STILL_REPAIRED | STILL_REPAIRED, re-verified by the coordinator (the auditor's evidence is generic): `register.tsx:1279` registers 'Queue a note for the capture ledger'; no 'Store a note' remains. |
| N3 | STILL_REPAIRED | STILL_REPAIRED (concur): the relay (`adoptEarlier`, `register.tsx:1181`) and the replayable-only status are intact. |
| N4 | STILL_REPAIRED | STILL_REPAIRED (concur): `MAX_ANSWER_SCAN_CHARS = 200_000` (`register.tsx:64`). |
| N5 | STILL_REPAIRED | STILL_REPAIRED, re-verified by the coordinator (the auditor's evidence describes the wrong finding): `README.md:46` describes attempts as attempts that ran, failed ones plus the final successful one. |
| N6 | STILL_REPAIRED | STILL_REPAIRED, re-verified by the coordinator (the auditor's evidence describes the wrong finding): `foldedPending` occurs 0 times in `register.tsx`, so the dead `/clear` branch is gone. |
| N7 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N8 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N9 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N10 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N11 | STILL_PRESENT | STILL_PRESENT by decision (concur). |
| N12 | REPAIRED | REPAIRED (concur): `safeId` keeps `[A-Za-z0-9_-]{1,80}` ids unchanged and maps any other id to a sanitized prefix of up to 56 characters, `~`, and two FNV-1a passes over the whole id (16 hex); the forms cannot meet; the empty id is `~811c9dc5050c5d1f`. Every caller uses it; 11 new tests, failing first. Coordinator re-read the 13-line code diff. |

Open at this head (all INFO):

| Id | Auditor severity | Adjudication |
|---|---|---|
| N7 | INFO | STILL_PRESENT, disclosure; INFO |
| N8 | INFO | STILL_PRESENT, design note; INFO |
| N9 | INFO | STILL_PRESENT, disclosure; INFO |
| N10 | INFO | STILL_PRESENT, accepted caveat; INFO |
| N11 | INFO | STILL_PRESENT, disclosed relay residuals; INFO |

## Open risks

1. Never run live; desktop `$.process`, Pulse band order and `$.fs.write` atomicity UNKNOWN (N7, N9, N10).
2. Relay residuals (N11), all ledger no-ops or bounded by 7 days.
3. N8: fire-and-forget observation in the `tool.call` hook (design note).
4. Not built by design: recap, `decision.logged`, dope-memory REST replay, any ConPort access.
