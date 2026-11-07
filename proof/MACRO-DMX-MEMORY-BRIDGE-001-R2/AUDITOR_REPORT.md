# Auditor Report - MACRO-DMX-MEMORY-BRIDGE-001-R2

**Subject**: content head `52855fb35ea40f420bdacdcab9e092f8d15292c6` on branch `claude/memory-bridge-001-b349d8`, base `93050d135ffc2592000c1d0edef82b2912935525`, cumulative diff of 6 content files (3 commits), sha256 `575b241961879971e51ba908b4ecc19cd35125877832971a1a9a336a0d1b7856`. Proof-only commits follow it.
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli` 1.0.67, model `grok-4.5` (self-reported `grok-4`).
**Route**: the operator-approved route "grok-cli grok-4.5 final audit ... one attempt each, zero retries, no fallback" (relayed by the commissioning session, truncated mid-word; see `review_bundle/GROK_RUN_RECORD.md`). Tool-less recipe reused from `MACRO-DMX-PULSE-002-R2`; `init.tools == []` in the probe and in the real run, zero `tool_use` blocks; machine evidence in `review_bundle/GROK_AUDIT_STREAM.txt` and `review_bundle/GROK_PROBE_STREAM.txt`.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.
**Signature**: none. Signing is an operator step. `audit_identity.independence` is unattested.

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
      "evidence": "Cumulative diff adds exactly six paths: docs/02-how-to/memory-bridge.md, plugins/dopemux-memory-bridge/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.tsx, hooks/register.test.ts. No other hosts, services, hidden writes, or unrelated trees appear. Subprocess surfaces in register.tsx are only git status --porcelain (dirtyFileCount) and the fixed dopemux capture emit argv (emitOnce)."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Both process calls use argv arrays (no shell): ['git','status','--porcelain'] and ['dopemux','capture','emit','--event', JSON.stringify(event), '--mode','plugin','--repo-root', root]. Event payload fields are built only from cleaned row title/summary/session_id/id/ts. safeId strips session ids to [A-Za-z0-9_-]{,80}. normalizePath/relativeTo reject paths outside the resolved root; outbox paths are only under <root>/.dopemux/memory-bridge/outbox-<safeId>(.alt).jsonl and only after .dopemux exists. findRoot walks at most MAX_ROOT_WALK=40. JSON.stringify escapes note/title content so it cannot split argv. Residual: Windows paths explicitly unsupported (README); $.fs.write parent-dir creation behaviour UNKNOWN from this diff."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Outbox/store keep derived fields only (goal≤160, ≤30 rel paths, ≤3 decisions≤200, ≤10 titles, note via clean). Status line is counts/flags only. Band shows redacted goal/decision plus dirty count. REDACTIONS cover PEM, JWT, sk-/sk-ant-, ghp_/github_pat_/xox, AKIA/ASIA, Bearer, URL userinfo, emails, KEY=value secret shapes, JSON password-like keys, /Users|/home prefixes. clean() bounds input then redacts then caps (secret-before-truncate). No raw tool output path; answer text only via Decision:/DECISION: extraction. Tests assert needles absent and REDACTED present. Residual risks: decisionsOf(answer) runs matchAll on unbounded answer (ReDoS/CPU); home redaction requires trailing slash; redaction best-effort as disclosed; truncated-but-still-sensitive non-matching shapes can survive."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Ring: header meta=gen + rows + footer meta=eof with matching gen/rows; primary/alt alternate by gen; newest valid gen wins; torn (no matching footer) ignored; failed write does not advance gen (persistOnce sets gen only after successful write). Cap FILE_CAP_BYTES/STORE_CAP_BYTES drop sent→dead→pending with dropped counter. Ids = first 24 hex of sha256(sid NUL turnId NUL kind [NUL disc]); ring.ids dedupes. Single flushPromise/flushing chain; write Promise.race 3s but flushing held until settle (maxActive=1 tested). Absent .dopemux → memory+$.store, never mkdir .dopemux. /clear appends end and continues; other end reasons cancel timers and clear status. Subagent turns/todos/goal skipped; Edit/Write from subagents still recorded. Multi-session: prior files counted not written. Growth capped; timers cancelled on real end. Minor: enforceCap does not remove dropped ids from ring.ids (same-session re-append of dropped id impossible by design); clear-fold isReplayable branch is dead code."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "replayTick serial via replaying + ledgerInFlight; ≤3 rows/tick; mark sent only after outcome==='ok'; failed/timeout increment attempts and dead at 5; unavailable (no process/deny/throw/short fail) does not increment; ledgerInFlight cleared in settled.finally so hung emit cannot overlap; timeout breaks tick and re-arms; isEnded cancels further work; event_id=row.id; only task.completed and manual.memory_store from ledgerEvent. isReplayable requires pending AND those intended_events — turn/compact/end excluded. Tests: clear→1 pending→clear after send; prior turn-only files stay clear; undeliverable/dead; process deny/throw attempts stay 0; other session files not emitted. Status '(ledger unavailable)' when ledgerDown && waiting>0. Note: success path also sets attempts=row.attempts+1 (tested as 1); other sessions' pending folded into status forever (documented, never sent)."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "ui.render awaits next(e), wraps in Box above inner; hasSurvey or !idle or no line returns inner unchanged. Idle: lastActivityAt from prompt/turn.complete; armIdle(idleMs); config clamped 5–1440 default 30. Prompt touch redraws so band hides while lastActivityAt fresh without clearing bandLine. dirtyFileCount raced 3s with gitInFlight until settle; deny/throw/hang omit files segment. Pulse prepend-without-next hides band (accepted, tested). Render try/catch returns inner — does not throw into host."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "prompt.submit, turn.start, turn.complete, session.start, session.end return next(e). tool.call and session.compact await next then observe, return that result unchanged (no deny/rewrite). Fire-and-forget work uses void …catch; bodies wrapped in try/catch. command.register .catch(()=>undefined). /bridge-note: clean(args,500); empty→usage nothing queued; else append note+manual.memory_store and reply contains 'queued' / 'Nothing is stored yet'. No $.http.fetch, no $.session.append, no tool/agent registration beyond bridge-note."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "register.test.ts is non-vacuous: pass-through, redaction needles, ring gens/torn recovery, cap drop order, status replayable-only, clear vs real end, band wrap/survey/Pulse, emit argv/event shape, 3/tick, serial in-flight, attempts/dead/unavailable, bridge-note wording, no network. Mocks model fs/store/clock/process/command/ui. Gaps untested here: live Claude Code session, real dopemux capture emit/ledger, desktop $.process, fs.write atomicity/parent mkdir, huge-answer ReDoS, Windows paths, exact 105 count (claimed, not recounted from this message alone)."
    },
    {
      "id": "Q9",
      "verdict": "FAIL",
      "evidence": "How-to states Status/Verification HEAD `1ce149a76` and 105 tests at that commit; audit subject frozen content head is `52855fb35ea40f420bdacdcab9e092f8d15292c6` — citation does not match delivery head. Diff cannot support: `.gitignore` lines 140/299, chronicle.sqlite/raw_activity_events behaviour, capture_client idempotency, validate/test exit codes. Honest/complete: NOT_RUN live session; Not built table (recap, decision.logged, dope-memory REST, ConPort, other-session replay); Pulse/desktop $.process UNKNOWN; best-effort redaction. README aligns with register.tsx on ring/replay/band/subprocess scope. No PR numbers cited."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No text steering this auditor, faking a verdict, or altering the output contract. Operator how-to/README are documentation, not auditor directives. Test fixtures use synthetic secrets (sk-ant-api03-ABCDEFG…, hunter2, alice.smith@example.org) and placeholder names alice/bob — not live credentials or personal data. No real API keys/tokens added."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "Diff has no session-start recap injection, no decision.logged intended_event/emit, no $.http.fetch, no ConPort/dope-memory calls, no other-session replay (readPrior counts only). Extra vs terse intent (still mostly documented): $.store memory-only outbox + prune to 3 sessions; fold other-session pending/dead into status; fitRow shrink ladder; success increments attempts; /clear ring retention while replayable; command description 'Store a note in the capture ledger' while reply insists queued/not stored."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "Cumulative L2 change matches stated local-outbox / status / band / ledger-replay design with strong unit coverage and hook safety. Residual risks (never live-run; desktop $.process UNKNOWN; Pulse ordering; status counts other sessions' never-sent rows; how-to HEAD hash stale vs frozen head; slash description 'Store' vs queued semantics) are disclosed or non-blocking for merge-as-code, hence overall PASS_WITH_RISKS rather than FAIL."
    }
  ],
  "findings": [
    {
      "id": "N1",
      "severity": "MEDIUM",
      "file": "docs/02-how-to/memory-bridge.md",
      "summary": "How-to claims code HEAD `1ce149a76` and verification at that commit; frozen audit head is `52855fb35ea40f420bdacdcab9e092f8d15292c6`.",
      "evidence": "Lines: 'code committed at HEAD `1ce149a76`' and Verification 'At commit `1ce149a76`…105 tests'. Subject identifies frozen content head 52855fb… (3 commits from base). Stale or wrong HEAD citation for the delivered tree.",
      "status": "OPEN"
    },
    {
      "id": "N2",
      "severity": "MEDIUM",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Slash command description says 'Store a note in the capture ledger' while the command reply and intent require queued-not-stored messaging.",
      "evidence": "session.start registers description: 'Store a note in the capture ledger'; command.run returns text with 'Queued' and 'Nothing is stored yet'. Menu copy overclaims persistence relative to replay semantics.",
      "status": "OPEN"
    },
    {
      "id": "N3",
      "severity": "LOW",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Status pending includes other sessions' replayable rows that this mod will never send, so 📮 N pending can stick until those files change outside this process.",
      "evidence": "readPrior adds isReplayable counts into foldedPending; replay only walks s.rings (this process). README documents counting newest eight other files; intent (e) says other-session replay not built. Misleading 'waiting' semantics.",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "LOW",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "decisionsOf runs RegExp matchAll on the full unbounded assistant answer before any size bound.",
      "evidence": "decisionsOf(answer) has no pre-trim; clean() bounds only matched capture groups. A multi-megabyte answer could cost CPU on every turn.complete (privacy still OK — answer not stored).",
      "status": "OPEN"
    },
    {
      "id": "N5",
      "severity": "LOW",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Successful ledger emit increments attempts; docs describe attempts as failed-delivery counters.",
      "evidence": "markRow on outcome==='ok' sets attempts: row.attempts + 1; test expects attempts===1 after success. README emphasizes attempts on non-zero/timeout only.",
      "status": "OPEN"
    },
    {
      "id": "N6",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "On /clear, fold path that increments foldedPending from isReplayable is unreachable.",
      "evidence": "Ring is deleted only when !entries.some(isReplayable); the following loop still branches on isReplayable. Dead code; behaviour still correct because replayable rings are retained.",
      "status": "OPEN"
    },
    {
      "id": "N7",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/README.md",
      "summary": "Live behaviour, real ledger emit, desktop $.process, fs.write atomicity, and pre-commit hooks remain NOT_RUN / UNKNOWN as disclosed.",
      "evidence": "README/how-to Verification and Known limits; implementer authority facts. Unit kit only. Acceptable disclosure for L2 but residual operational risk.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Whether commit 1ce149a76 is identical to, ancestor of, or unrelated to frozen head 52855fb35ea40f420bdacdcab9e092f8d15292c6",
    "Exact claude plugin test count and validate output at the frozen head (claimed 105 / exit 0)",
    "Live Claude Code session load of the mod (terminal and desktop)",
    "Real dopemux capture emit against a checkout with services/working-memory-assistant and resulting chronicle.sqlite rows",
    "Whether $.process.run exists and is argv-no-shell on the desktop surface",
    "Whether $.fs.write creates missing parent dirs (memory-bridge) or fails closed",
    "Confirmation of .gitignore lines 140 and 299 ignoring .dopemux/"
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "Operator how-to and README contain procedural guidance for humans/assistants loading the mod; no text attempts to dictate this auditor's verdict, forge PASS/FAIL, or rewrite the JSON output contract. W01/GO_REDUCED narrative is design provenance, treated as claims under test."
  }
}
```

## Coordinator adjudication (summary)

| Id | Auditor severity | Adjudication |
|---|---|---|
| N1 | MEDIUM | CONFIRMED as a documentation defect; severity LOW, not MEDIUM |
| N2 | MEDIUM | CONFIRMED; severity LOW; the wording is a packet defect |
| N3 | LOW | CONFIRMED and disclosed; severity LOW stands; candidate for an accepted-risk ruling |
| N4 | LOW | PARTIALLY CONFIRMED; severity INFO; the ReDoS framing is not substantiated |
| N5 | LOW | CONFIRMED as a documentation inaccuracy; severity LOW |
| N6 | INFO | CONFIRMED; severity INFO |
| N7 | INFO | CONFIRMED; disclosure, not a defect; severity INFO |

Full reasoning per finding: `review_bundle/GROK_ADJUDICATION.md`.

## Open risks

1. Never run live (NOT_RUN); `$.process` on the desktop surface UNKNOWN; Pulse can hide the band; `$.fs.write` atomicity UNKNOWN.
2. Docs: the how-to cites a pinned commit SHA (N1) and the README misdescribes `attempts` (N5).
3. The `/bridge-note` menu description says `Store` (N2); the status line counts other sessions' never-replayed rows as pending (N3).
4. Replay writes raw ledger rows only; it needs the dopemux service tree under the repo root and `dopemux` on PATH.
5. Not built by design: recap, `decision.logged`, dope-memory REST replay, any ConPort access.
