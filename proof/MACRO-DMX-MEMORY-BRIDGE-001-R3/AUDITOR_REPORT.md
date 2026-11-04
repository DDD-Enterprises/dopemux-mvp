# Auditor Report - MACRO-DMX-MEMORY-BRIDGE-001-R3

**Subject**: repaired content head `c71e7c1f436349f477037d28ce479218c63a53a4` on branch `claude/memory-bridge-001-b349d8`, base `93050d135ffc2592000c1d0edef82b2912935525`, cumulative diff of 6 content files (5 commits), sha256 `131d964c352700a859bd9c195c186a39154ae444128b708b63bf08506feeb31a`. Proof-only commits follow it. This is the re-audit after the first audit (`proof/MACRO-DMX-MEMORY-BRIDGE-001-R2/AUDITOR_REPORT.md`, content head `52855fb35ea40f420bdacdcab9e092f8d15292c6`, accepted by the operator on 2026-10-24); that record is unchanged.
**Verdict**: `PASS_WITH_RISKS`. Tool `grok-cli`, model `grok-4.5` (self-reported `grok-4.7`).
**Route**: the operator's verbatim line `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R3_AUDIT_ROUTE=grok-cli:grok-4.5:ONE_ATTEMPT`; tool-less recipe reused from the first audit; `init.tools == []` in the probe and in the real run, zero `tool_use` blocks; machine evidence in `review_bundle/GROK_AUDIT_STREAM.txt` and `review_bundle/GROK_PROBE_STREAM.txt`.
**Run record**: `review_bundle/GROK_RUN_RECORD.md`. **Coordinator adjudication**: `review_bundle/GROK_ADJUDICATION.md`.
**Signature**: none. Signing is an operator step. `audit_identity.independence` is unattested.

## Auditor response (verbatim)

```json
{
  "model_self_reported": "grok-4.7",
  "tools_used": "none",
  "status": "PASS_WITH_RISKS",
  "questions": [
    {
      "id": "Q1",
      "verdict": "PASS",
      "evidence": "Cumulative diff is exactly six new files: docs/02-how-to/memory-bridge.md, plugins/dopemux-memory-bridge/.claude-plugin/plugin.json, README.md, hooks/hooks.json, hooks/register.test.ts, hooks/register.tsx. No other hosts, paths, or smuggled content files."
    },
    {
      "id": "Q2",
      "verdict": "PASS",
      "evidence": "Only subprocess argv surfaces are fixed arrays: ['git','status','--porcelain'] (dirtyFileCount) and ['dopemux','capture','emit','--event', JSON.stringify(event), '--mode','plugin','--repo-root', root] (emitOnce). No shell. safeId strips session ids to [A-Za-z0-9_-]{,80}. Outbox paths are outboxDir(root)/outbox-${key}(.alt).jsonl under normalizePath(root). relativeTo drops paths outside root. Event JSON is built from structured LedgerEvent fields after clean(); user text is payload data, not argv structure. findRoot walks at most MAX_ROOT_WALK=40 ancestors for .git/.dopemux."
    },
    {
      "id": "Q3",
      "verdict": "PASS",
      "evidence": "Outbox/store hold derived fields only (goal≤160, ≤30 paths, ≤3 decisions≤200, ≤10 titles, note≤500 from /bridge-note) after redact+cap; intended_event only task.completed|manual.memory_store|null. No raw tool output; answer text only via marker lines. Status/band show counts or already-cleaned goal/decision. Redactor covers PEM, JWT, sk-/sk-ant-, ghp/github_pat/Slack, AKIA/ASIA, Bearer, URL userinfo, emails, KEY=value, JSON secret keys, /Users|/home prefixes. clean() pre-bounds before regex (chars*4+200). Residual: decisionsOf(answer) has no pre-bound (N4); redaction best-effort as disclosed."
    },
    {
      "id": "Q4",
      "verdict": "PASS",
      "evidence": "Ring: header meta=gen, rows, footer meta=eof with matching gen/rows; newest valid gen wins; failed write does not advance gen (retry same target). Cap FILE_CAP_BYTES with drop order sent→dead→pending; ROW_CAP_BYTES via fitRow. Ids digest24(session NUL turn NUL kind [NUL disc]); duplicate id ignored. One flush chain with flushing flag; write raced WRITE_TIMEOUT_MS but flag held until settle. Absent .dopemux → memory+$.store (STORE_CAP_BYTES, prune to 3). /clear appends end and continues; other reasons set isEnded and cancel timers. Subagent turns/todos/goal skipped; Edit/Write/NotebookEdit from subagents still count on parent. Logic matches tests; N6 dead fold branch remains harmless."
    },
    {
      "id": "Q5",
      "verdict": "PASS",
      "evidence": "replayTick serial, REPLAY_PER_TICK=3, ledgerInFlight held until settled.finally; mark sent only on outcome==='ok' after exit 0; attempts++ on ok/fail/timeout; dead at MAX_ATTEMPTS=5; unavailable (no process / quick reject) does not spend attempts. Only ledgerEvent for task.completed and manual.memory_store. isReplayable requires pending+those intended_events; status pending counts only those (plus folded prior). Tests: clear→1 pending→clear after send; turn-only stays clear; other sessions counted not emitted. event_id=row.id."
    },
    {
      "id": "Q6",
      "verdict": "PASS",
      "evidence": "ui.render AbovePrompt awaits next(e), wraps in Box above inner; returns inner on hasSurvey, isEnded, no line, or now-lastActivityAt < idleMs. touch on prompt/turn resets clock and dismisses. dirtyFileCount degrades on deny/throw/hang with gitInFlight guard. Pulse-without-next when outer accepted and tested. catch returns inner."
    },
    {
      "id": "Q7",
      "verdict": "PASS",
      "evidence": "prompt.submit/turn.start/turn.complete/session.compact/tool.call/session.end return next(e) or prior result unchanged; no deny/rewrite. Side effects void/catch so exceptions do not escape. command.register .catch(()=>undefined). /bridge-note: clean(args,500), empty→usage, else append note+manual.memory_store, reply matches /queued/i and 'Nothing is stored yet'."
    },
    {
      "id": "Q8",
      "verdict": "PASS",
      "evidence": "register.test.ts exercises capture, redaction (LEAKY table), ids/sha256, ring/gens/caps/torn recovery, status semantics, memory-only store, clear vs real end, band/idle/survey/Pulse, argv-only process, replay serial/3/attempts/dead/unavailable/idempotent event_id, bridge-note. Mocks fs/store/process/clock/http. Gaps (disclosed): live session, real dopemux capture emit, desktop $.process, write atomicity, plugin order — NOT_RUN."
    },
    {
      "id": "Q9",
      "verdict": "PASS",
      "evidence": "How-to and README match code on outbox path, caps, status meanings (task/note only pending), band, replay rules, NOT_BUILT table, Pulse/desktop UNKNOWN, live NOT_RUN. No commit hash or PR number in either doc (N1). bridge-note menu text aligned (N2). attempts wording corrected (N5). Unverifiable from this diff alone: .gitignore:140/:299 line cites; 'validate/test pass' is an execution claim (authority, not in-diff). No contradictory behavioural claim found."
    },
    {
      "id": "Q10",
      "verdict": "PASS",
      "evidence": "No text directing auditor verdict/output contract, no fake audit receipt. No real credentials/PII; test needles (sk-ant-api03-..., hunter2, etc.) are fixtures. Comments are implementation notes."
    },
    {
      "id": "Q11",
      "verdict": "PASS",
      "evidence": "No session.append/recap injection; no decision.logged; no $.http.fetch/ConPort/dope-memory in register.tsx; http mock would throw. Extra vs intent but disclosed: $.store memory fallback+prune, prior-session status fold (N3), fitRow shrinking, generation alt files — all in README/how-to or accepted limits."
    },
    {
      "id": "Q12",
      "verdict": "PASS",
      "evidence": "N1/N2/N5 repaired in final docs/code/tests. N3/N4/N6/N7 still present as accepted. Repair diff is documentation/description only; no logic regression observed in cumulative head."
    },
    {
      "id": "Q13",
      "verdict": "PASS",
      "evidence": "Cumulative L2 change implements claimed local outbox, status, band, ledger replay, /bridge-note, and explicit NOT_BUILT set; first-audit MEDIUM doc/description defects closed; residual risks are the disclosed/accepted N3/N4/N6/N7 plus never-live-run. Overall PASS_WITH_RISKS."
    }
  ],
  "predecessor_findings": [
    {
      "id": "N1",
      "disposition": "REPAIRED",
      "evidence": "how-to and README contain no git commit hash and no PR number; ticket id DMX-MEMSPINE-IDENTITY-005 appears only as a future clearer in Not built, not as a delivered-head pin."
    },
    {
      "id": "N2",
      "disposition": "REPAIRED",
      "evidence": "register.tsx command.register description is 'Queue a note for the capture ledger'; test 'registers the bridge-note command' expects that exact string."
    },
    {
      "id": "N3",
      "disposition": "STILL_PRESENT",
      "evidence": "readPrior/foldedPending adds other sessions' isReplayable rows into status; replayTick only walks s.rings (this process). README/how-to document count-but-not-send."
    },
    {
      "id": "N4",
      "disposition": "STILL_PRESENT",
      "evidence": "decisionsOf runs DECISION_LINE.matchAll on the full answer string with no size pre-bound (unlike clean())."
    },
    {
      "id": "N5",
      "disposition": "REPAIRED",
      "evidence": "README row field table: 'a counter of delivery attempts that ran (failed ones plus the final successful one)'; code increments attempts on both ok and failed/timeout paths."
    },
    {
      "id": "N6",
      "disposition": "STILL_PRESENT",
      "evidence": "session.end clear fold enters only when !entries.some(isReplayable), yet the loop still has if (isReplayable) foldedPending += 1 — unreachable."
    },
    {
      "id": "N7",
      "disposition": "STILL_PRESENT",
      "evidence": "How-to/README Verification: live behaviour NOT_RUN; no real session, real emit, or desktop $.process in the change set."
    }
  ],
  "findings": [
    {
      "id": "N3",
      "severity": "LOW",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Status pending includes other sessions' replayable rows that this mod never sends, so 📮 N pending may not clear for those N.",
      "evidence": "readPrior counts isReplayable into foldedPending; nextReplayable only iterates s.rings. Accepted follow-up.",
      "status": "OPEN"
    },
    {
      "id": "N4",
      "severity": "LOW",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Decision regex runs on unbounded assistant answer text.",
      "evidence": "decisionsOf(answer) → answer.matchAll(DECISION_LINE) with no slice/pre-bound. Accepted follow-up.",
      "status": "OPEN"
    },
    {
      "id": "N6",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Dead branch in /clear fold increments foldedPending for isReplayable inside a block that requires none.",
      "evidence": "session.end reason==='clear' guard !ring.entries.some(isReplayable) then loop if (isReplayable) foldedPending += 1. Harmless. Accepted.",
      "status": "OPEN"
    },
    {
      "id": "N7",
      "severity": "INFO",
      "file": "docs/02-how-to/memory-bridge.md",
      "summary": "Mod has never run in a real Claude Code session; proof is test-kit only.",
      "evidence": "Disclosed NOT_RUN in how-to, README, and authority limitations (i)(iv).",
      "status": "OPEN"
    },
    {
      "id": "N8",
      "severity": "INFO",
      "file": "plugins/dopemux-memory-bridge/hooks/register.tsx",
      "summary": "Observing tool.call intentionally does not await observeTool before returning, relying on host microtask ordering so turn digests stay complete.",
      "evidence": "on('tool.call') awaits next then void observeTool(...).captureTurn snapshots s.files/s.todosDone synchronously when later invoked. Tests pass under mock settle; production interleaving UNKNOWN. Design trades await-delay for hook non-blocking.",
      "status": "OPEN"
    }
  ],
  "needs_more_evidence": [
    "Live Claude Code session with plugin loaded (outbox file, status line, band, /bridge-note).",
    "Real $.process.run for git status and dopemux capture emit on CLI and desktop surfaces.",
    "Confirmation of $.fs.write atomicity / torn-write behaviour on the target FS.",
    "Installed plugin order relative to dopemux-pulse (which is outer).",
    "Independent re-run receipts for claude plugin test (105) / tsc / validate (authority-claimed, not in this message's diff)."
  ],
  "instruction_like_content": {
    "detected": false,
    "notes": "Diff is implementation, tests, README and how-to. No auditor-steering, fake verdict, or output-contract override. NOT_RUN and Not built sections are descriptive limits, not instructions to this auditor."
  }
}
```

## Coordinator adjudication (summary)

First-audit findings:

| Id | Auditor disposition | Coordinator adjudication |
|---|---|---|
| N1 | REPAIRED | REPAIRED (concur) |
| N2 | REPAIRED | REPAIRED (concur) |
| N3 | STILL_PRESENT | STILL_PRESENT, accepted follow-up; severity LOW stands |
| N4 | STILL_PRESENT | STILL_PRESENT, accepted follow-up; severity LOW; no ReDoS |
| N5 | REPAIRED | REPAIRED (concur) |
| N6 | STILL_PRESENT | STILL_PRESENT, accepted follow-up; INFO |
| N7 | STILL_PRESENT | STILL_PRESENT, disclosure; INFO |

Findings open at this head:

| Id | Auditor severity | Adjudication |
|---|---|---|
| N3 | LOW | STILL_PRESENT, accepted follow-up; severity LOW stands |
| N4 | LOW | STILL_PRESENT, accepted follow-up; severity LOW; no ReDoS |
| N6 | INFO | STILL_PRESENT, accepted follow-up; INFO |
| N7 | INFO | STILL_PRESENT, disclosure; INFO |
| N8 | INFO | CONFIRMED as a design note; severity INFO; no defect shown |

Full reasoning: `review_bundle/GROK_ADJUDICATION.md`.

## Open risks

1. Never run live (NOT_RUN); `$.process` on the desktop surface UNKNOWN; Pulse can hide the band; `$.fs.write` atomicity UNKNOWN.
2. N3: the status line counts other sessions' never-replayed rows as pending (documented limit, unrepaired).
3. N4: no size pre-bound on the answer text before decision matching (linear cost); N6 dead code; N8 fire-and-forget observation in the `tool.call` hook (design note).
4. Replay writes raw ledger rows only; it needs the dopemux service tree under the repo root and `dopemux` on PATH.
5. Not built by design: recap, `decision.logged`, dope-memory REST replay, any ConPort access.
