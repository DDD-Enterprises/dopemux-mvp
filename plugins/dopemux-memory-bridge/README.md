# dopemux-memory-bridge

A Claude Code mod that keeps a small, local memory outbox for each session, shows
how many rows are waiting in the status line, draws a one-line "welcome back"
band after a break, and replays completed todos and `/bridge-note` notes to the
**local capture ledger**.

It makes **no network call** and never talks to ConPort, dope-memory or the ADHD
engine. It starts exactly two kinds of subprocess: `git status --porcelain` (the
band) and `dopemux capture emit` (the ledger replay, below). Everything else in
the original idea is listed under [Not built](#not-built).

## What it records, and where

After each finished main-loop turn (and on compaction, on `/clear` and at the
end of a session) it appends one JSON row to

```
<repo-root>/.dopemux/memory-bridge/outbox-<sessionId>.jsonl
```

`<repo-root>` is the nearest ancestor of the session's working directory that
holds a `.git` or a `.dopemux` (the same upward walk as
`src/dopemux/memory/capture_client.py`; in a worktree that is the worktree, not
the main checkout). The mod writes only when `<repo-root>/.dopemux` **already
exists** (this repo ignores it: `.gitignore:140` and `:299`; other repos are
unchecked) and never creates `.dopemux`. Without it, rows stay in memory plus the
plugin's `$.store`, and the status line says `📮 memory-only`.

A row holds derived fields only, never a raw prompt, tool output or answer:

| field | content |
|---|---|
| `v`, `id` | `1`; first 24 hex digits of `sha256(session_id NUL turn_id NUL kind)` (a `task`, `compact` or `end` row also hashes a discriminator after another NUL), so a repeat is ignored |
| `ts`, `session_id`, `cwd_rel` | ISO time, the session id, the working directory relative to the repo root |
| `kind` | `turn`, `compact`, `end`, `task` (a completed todo), `note` (a `/bridge-note`) |
| `goal` | the first 160 characters of the user's text, redacted |
| `files_touched` | up to 30 unique repo-relative paths from Edit, Write and NotebookEdit calls this turn (paths outside the repo are skipped) |
| `decisions` | marker-detected, see below; up to 3, 200 characters each |
| `todos_completed` | up to 10 titles of TodoWrite items that newly became `completed` |
| `note` | `note` rows only: the user's own text, redacted, at most 500 characters |
| `intended_event` | `task.completed` on a `task` row, `manual.memory_store` on a `note` row, otherwise `null` |
| `state`, `attempts` | `pending` / `sent` / `dead`, and a counter of failed delivery attempts |

Subagent loops (`agentId` set) never write a `turn` row, change the goal, or count
todos. File edits made inside a subagent count toward the turn that spawned it.

### Decision marker rule

A decision is captured only from a line of the assistant's answer that **starts**
with `Decision:` or `DECISION:` (optionally bold: `**Decision:**`,
`**DECISION**:`). Nothing else is inferred. Decisions stay in the outbox for the
band. `decision.logged` is **never emitted**: repo doctrine logs decisions in
ConPort only.

### Redaction

Every string is masked and capped before it is written: `sk-` and `sk-ant-` keys,
`ghp_`/`github_pat_`/Slack tokens, AWS key ids, JWTs, `Bearer` values, URL
userinfo (`https://user:pw@host`), email addresses, `KEY=value` pairs for
`DATABASE_URL`, `password`, `token`, `secret`, `*_KEY`, `*_URL` and similar,
JSON `"password": "..."` pairs, PEM blocks, and `/Users/<name>/` or
`/home/<name>/` prefixes (to `~/`). It is a deterministic in-module list; it adds
the four shapes the repo's own redactor misses (sk-ant keys, URL userinfo, emails,
`DATABASE_URL=`). It is best effort, not a guarantee that no secret can slip
through.

## Ledger replay (`dopemux capture emit`)

`task` and `note` rows are replayed to the local capture ledger
(`<repo-root>/.dopemux/chronicle.sqlite`, table `raw_activity_events`) by running

```
dopemux capture emit --event <json> --mode plugin --repo-root <repo-root>
```

through `$.process.run` with `timeoutMs: 15000`. The event is exactly

```
task.completed      { event_type, payload: { title }, ts_utc, session_id, event_id }
manual.memory_store { event_type, payload: { category: "implementation",
                      entry_type: "manual_note", summary }, ts_utc, session_id, event_id }
```

`event_id` is the row id, so a resend is a no-op in the ledger (`INSERT OR
IGNORE`). Those two types are the only ones ever emitted. The rules:

- **One minute, three rows.** A timer ticks every 60 s, and only while a row is
  waiting; each tick sends at most 3 rows, one at a time (a call costs about
  2.8 s). Rows with the fewest attempts go first.
- **Sent only on exit 0.** A row is rewritten as `sent` only after the command
  exits 0. A non-zero exit or a timeout leaves it `pending`, counts one attempt
  and shows `📮 N pending (ledger unavailable)`.
- **Dead after five.** After 5 failed attempts the row becomes `dead`, is never
  retried, stays in the file, and the status line shows `⚠ N undeliverable`. A
  `task`/`note` row that cannot make a complete event (no title or text) is dead
  at once.
- **`$.process` unavailable is not a failed attempt.** `$.process` is documented
  CLI only; on the desktop app it may be absent or refuse (UNKNOWN). A call that
  cannot start leaves the row `pending` with no attempt counted and the status
  line says the ledger is unavailable; nothing is dropped and nothing throws.
- **One call at a time, even when one hangs.** A call is raced against a 16 s
  timer, but a raced call is not cancelled: a flag stays set until it really
  settles, and no new call starts before then.
- **Scope.** Only this session's own outbox file is replayed (one writer per
  file). Pending rows left by other sessions' files are counted but not sent. A
  session that ends within a minute of a completed todo leaves that row
  `pending` in its file.

What the route is and is not (W01 Q5): CLI only; it writes `raw_activity_events`
only and nothing local promotes those rows into the work log; it loads the
redactor and schema from `services/working-memory-assistant` under the repo
root, so it works in dopemux-mvp checkouts and worktrees and **fails closed in any
other repo** (rows then go `dead` after five tries); the `dopemux` on `PATH` must
be a build that has `capture emit`.

## `/bridge-note <text>`

The one slash command, registered in `session.start`. It redacts the text, caps it
at 500 characters and appends a `note` row (`manual.memory_store`), then answers
that the note is **queued**, not stored; the replay above delivers it. With no
text it prints usage and appends nothing. It is the only user-triggered write.

## The ring

`$.fs.write` replaces a whole file (no append, delete or rename), so the outbox
is a rewrite-in-place ring:

- One writer per file: one in-module flush loop, at most one write in flight per
  session. A hung write is raced against a 3 s timer (the status line shows
  `⚠ outbox write failed`) but is never joined by a second write.
- **1 MiB per file, 8 KB per row.** Over the cap the oldest `sent` rows go first,
  then `dead`, then the oldest `pending`; each drop is counted and shown as
  `+N dropped`.
- **Two alternating generation files** for torn-write safety:
  `outbox-<id>.jsonl` (generations 1, 3, 5...) and `outbox-<id>.alt.jsonl`
  (2, 4, 6...). Each is a header line `{"v":1,"meta":"gen","gen":N,...}`, the rows,
  and a footer `{"v":1,"meta":"eof","gen":N,"rows":R}`. A file without a matching
  footer is torn and ignored. **A reader takes the highest valid generation.** A
  failed write does not advance the generation, so the retry overwrites the same
  (broken) file and spares the intact one.
- Files are never deleted; a drained file would be overwritten empty.

## Status line

One line, beside Pulse's: `📮 N pending`, `📮 N pending (ledger unavailable)`,
`📮 clear`, `📮 memory-only`, `⚠ outbox write failed`, each with a ` +N dropped`
suffix after a cap drop, and `⚠ N undeliverable` (with the pending part after a
` · `) when dead rows exist. **Pending means waiting for the ledger**: `N` counts
`task` and `note` rows still `pending` in this session, plus those found in the
newest eight other sessions' files at start. A `turn`, `compact` or `end` row is
local history for the band: it is never sent, so it is not counted (it keeps
`state: pending` in the file, which only means "not delivered"). A session with
only turns shows `📮 clear`; a completed todo makes it `📮 1 pending`, and it goes
back to `📮 clear` once that row is `sent`.

## Welcome-back band

While at least `idleMinutes` have passed since your last prompt or finished turn,
the band above the prompt shows one line:

```
Welcome back - you were on <last goal> - last decision <last decision> - <n> uncommitted files
```

built from the newest rows in this repo's outbox files and `git status
--porcelain` (via `$.process.run`; that segment is left out when `$.process` is
unavailable or fails, and so is the decision segment when there is none). Your
next prompt dismisses it. It stays hidden while a survey is up. A fresh session
started after a break shows it straight away, using the last turn time found in
the outbox.

`idleMinutes` (plugin option, default 30, allowed 5-1440) is set in the plugin's
config row or in settings `pluginConfigs`.

## Not built

| Item | Why not |
|---|---|
| Any HTTP call, dope-memory `POST /tools/memory_store` | W01 NO_GO: not idempotent (random `source_event_id`), unauthenticated, summary and reasoning are not redacted, identity keys unresolved |
| ConPort in any form | W01: reads are limited to two routes and need an operator ruling; ConPort is the single home for decisions |
| `decision.logged` | W01 NOT_BUILT: ConPort already emits it, and doctrine says decisions are logged in ConPort only. Marker-detected decisions stay local, for the band |
| Recap / injection into the session | W01 NO_GO until `DMX-MEMSPINE-IDENTITY-005` (or an operator-accepted equivalent) is on main |
| Replay of other sessions' pending rows | Needs a safe adoption rule for another writer's file; not designed |

## Known limits

- **Pulse.** The mod wraps `next(e)` and draws its line above whatever the rest
  draws. `dopemux-pulse` draws its own `Box` without `next(e)` while a focus block
  runs, so when Pulse is the outer hook the welcome-back band is hidden during
  focus (accepted). Which of two user-tier plugins is outer is UNKNOWN.
- **Surfaces.** The band exists on the terminal and desktop surfaces only
  (`AbovePrompt`). `$.process` is documented CLI-only; on the desktop app it may
  be absent or refuse, in which case the band omits the uncommitted-files segment
  and the ledger replay never runs (rows stay `pending`, the status line says the
  ledger is unavailable). The outbox and status line need neither.
- **Ledger rows are raw.** Nothing local turns `raw_activity_events` into the
  work log, so a replayed row is stored, not yet recallable.
- Windows-style paths are not handled (POSIX `/` paths only).
- `$.fs.write` atomicity is UNKNOWN; the generation scheme is the mitigation.

## Tests and live proof

```
claude plugin validate plugins/dopemux-memory-bridge
claude plugin test plugins/dopemux-memory-bridge
```

The tests run against the mod kit with a mocked clock, file system, store and
process (`process.run` is mocked: no test starts a real subprocess or touches a
real ledger). **Live proof is NOT_RUN**: no real session has loaded this mod. To
see it yourself, start a session with the mod loaded from disk (`claude
--plugin-dir <path>/plugins/dopemux-memory-bridge`, or `CLAUDE_CODE_PLUGIN_DIRS`
for the desktop app) in a repo whose `.dopemux/` exists; finish one turn and look
for the new file under `.dopemux/memory-bridge/` (the status line stays `📮 clear`
until a todo is completed or a note queued); set
`idleMinutes` to 5, wait, and look for the band.

To see the replay, use a dopemux-mvp checkout or worktree with `dopemux` on
`PATH`, complete a todo (TodoWrite) or run `/bridge-note hello`, and wait about a
minute: the row's `state` in the outbox file turns `sent`, and
`sqlite3 .dopemux/chronicle.sqlite "select event_type, event_id from
raw_activity_events order by created_at_utc desc limit 3"` shows the event with
the row's `id`. That writes the real ledger. If the row stays `pending` and the
status line says `ledger unavailable`, `$.process` is probably unavailable on
your surface (on the desktop app this is UNKNOWN until you try).
