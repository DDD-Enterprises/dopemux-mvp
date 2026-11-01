---
id: MEMORY-BRIDGE
title: Use the dopemux-memory-bridge mod
type: how-to
author: '@hu3mann'
owner: '@hu3mann'
date: '2026-10-23'
last_review: '2026-10-23'
next_review: '2026-12-23'
prelude: How to load the dopemux-memory-bridge Claude Code mod, read its status line and welcome-back band, replay tasks to the local capture ledger, and what it does not build.
---
# Use the dopemux-memory-bridge mod

The mod keeps a small local outbox per session, shows how many rows wait for the
local capture ledger, draws a welcome-back band after a break, and replays
completed todos and `/bridge-note` notes to that ledger. It makes no network call.
Source: `plugins/dopemux-memory-bridge/` (design notes in its `README.md`).

**Status:** live behaviour is **NOT_RUN**: no real session has loaded the mod yet.

## 1. Load the mod

```
claude --plugin-dir plugins/dopemux-memory-bridge
```

The desktop app reads `CLAUDE_CODE_PLUGIN_DIRS` instead (README). The hooks file
names one module, `hooks/register.tsx`.

## 2. Know where it writes

After each finished turn, on compaction, on `/clear` and at session end, the mod
appends one JSON row to:

```
<repo-root>/.dopemux/memory-bridge/outbox-<sessionId>.jsonl
```

`<repo-root>` is the nearest ancestor holding `.git` or `.dopemux`. The file key is the
session id if it has only letters, digits, `_` and `-` (max 80 characters); other ids get
a sanitized prefix, `~` and a 16-hex hash of the whole id, so sessions never share a file.
The outbox writer writes only when `<repo-root>/.dopemux` **already exists** and never creates
it. This repo ignores `.dopemux/` (`.gitignore` lines 140 and 299); other repos are unchecked.
Without the directory, rows stay in memory and in the plugin's `$.store`, a JSON file that
Claude Code keeps in your Claude Code config directory across sessions (the newest 3 sessions,
at most 256 KiB each); the status line shows `📮 memory-only`, which means "no outbox file",
not "nothing on disk". The replay (section 5) can still create `.dopemux/`; from the next
write on, rows go to the outbox file.

Rows hold derived fields only: a goal (160 characters), up to 30 relative file paths, up to 3
decisions and up to 10 completed todo titles. Raw prompts, tool output and answers are not
stored. Files are capped at 1 MiB and rows at 8 KB; over the cap the oldest `sent` rows go
first, then `dead`, then `pending`, and each drop shows as `+N dropped`.

## 3. Read the status line

| Shown | Meaning |
|---|---|
| `📮 N pending` | N `task` or `note` rows this session will deliver: its own, and relayed ones (section 5) |
| `📮 N pending (ledger unavailable)` | the last replay call did not succeed |
| `📮 clear` | nothing waits for the ledger |
| `📮 memory-only` | `.dopemux` is absent; rows live in memory and the plugin's `$.store` file (section 2), not in an outbox file |
| `⚠ outbox write failed` | a write failed or hung past 3 s; rows are kept and retried |
| `⚠ N undeliverable` | N rows hit five failed attempts and will not be retried |

Only `task` and `note` rows count as pending, and only those this session will
deliver. `turn`, `compact` and `end` rows are local history and are never sent.

## 4. Read the welcome-back band

After `idleMinutes` without a prompt or finished turn, one line shows above the
prompt:

```
Welcome back - you were on <last goal> - last decision <last decision> - <n> uncommitted files
```

The file count comes from `git status --porcelain` via `$.process.run`. The
decision segment appears only when one exists. `idleMinutes` defaults to 30 and
accepts 5 to 1440; set it in the plugin config or settings `pluginConfigs`.

Decisions are captured only from an answer line starting with `Decision:` or
`DECISION:` (optionally bold), in the first 200,000 characters of the answer.

**Pulse caveat:** if Pulse is the outer render hook, the band is hidden during a
Pulse focus block. Which is outer is UNKNOWN; accepted as a limit.

## 5. Replay tasks and notes to the local ledger

A completed todo and each `/bridge-note` are replayed by running
`dopemux capture emit --event <json> --mode plugin --repo-root <repo-root>`.
Only `task.completed` and `manual.memory_store` events are sent; the row id is the
`event_id`, which the ledger stores in the `id` primary key, so a resend does not duplicate.
Rows land in `<repo-root>/.dopemux/chronicle.sqlite`, table `raw_activity_events`. The replay
runs whether or not `.dopemux` exists: in a dopemux-mvp checkout or worktree with the default
ledger path, `dopemux capture emit` creates `<repo-root>/.dopemux/` for the ledger file. In any
other repo it fails before that, so nothing is created there.

- A timer runs once a minute, only while a row waits, and sends at most three rows.
- A row becomes `sent` only after exit 0. Any other result leaves it `pending`
  and counts one attempt; after five attempts it becomes `dead` and is not retried.
- If `$.process` cannot start, the row stays `pending` and no attempt is counted.

Relay: at session start, a session copies into its outbox the undelivered `task` and
`note` rows of earlier sessions in this repo whose file has been quiet for 10 minutes,
if the row is at most 7 days old (50 per start, oldest first). A copy keeps the row id
and gets `adopted_from`, so the ledger stores a row delivered twice once. The earlier file is never written; a live session's rows stay with that session.

Limits: CLI only; needs `dopemux` on `PATH` with a build that has `capture emit`;
works only where `services/working-memory-assistant` sits under the repo root
(elsewhere rows go `dead`); raw rows only, so they are not recallable yet.

## 6. Write a note with `/bridge-note`

```
/bridge-note <text>
```

The only slash command and the only user-triggered write. The text is redacted,
capped at 500 characters and queued as a `note` row. The reply says it is queued,
not stored. With no text it prints usage and writes nothing.

## 7. Privacy

- Stored strings are redacted first: API-key shapes, JWTs, `Bearer` values, URL
  userinfo, emails, `KEY=value` secrets, PEM blocks, and home-directory prefixes.
  Redaction is best effort, not a guarantee.
- Where rows rest on disk: the outbox file under `.dopemux/memory-bridge/`, or, without
  `.dopemux`, the plugin's `$.store` JSON file in your Claude Code config directory (newest
  3 sessions); after a replay, also `.dopemux/chronicle.sqlite`. Leaving out `.dopemux` does
  not keep notes and goals off disk.
- No network call. The only subprocesses are `git status --porcelain` and the
  `dopemux capture emit` replay. No ConPort, dope-memory or ADHD-engine access.

## 8. Desktop surface

The band exists on terminal and desktop only. `$.process` is documented as CLI
only; on the desktop app it is **UNKNOWN**. If it fails there, the file count is
omitted, the replay never runs, and the status line shows the ledger as
unavailable. The outbox and status line do not need `$.process`.

## 9. Troubleshooting

- `📮 memory-only`: create `.dopemux/` yourself in the repo root (in a dopemux-mvp checkout
  the first successful replay also creates it).
- `ledger unavailable` with rows `pending`: check `dopemux` is on `PATH` and
  `dopemux capture emit --help` exits 0.
- `⚠ outbox write failed`: the next append retries; rows stay in memory meanwhile.

## Verification status

- `claude plugin validate` and `claude plugin test` pass for the committed mod (advisory warnings only).
- Unit tests mock the clock, file system, store and process. Live proof: **NOT_RUN**.

## Not built

| Item | Why not | What clears it |
|---|---|---|
| Session-start recap | Identity is not fail-closed on base; `DMX-MEMSPINE-IDENTITY-005` has no implementing commit; P3 (workspace and instance identity) is unproven live | `DMX-MEMSPINE-IDENTITY-005` or an operator-accepted equivalent on main, plus a live P3 check |
| `decision.logged` | Repo doctrine logs decisions in ConPort only, and ConPort already emits this event | An operator change to the doctrine; until then decisions stay local for the band |
| dope-memory REST replay (`POST /tools/memory_store`) | Not idempotent (random source id per call), no authentication, `summary` and `reasoning` not redacted | Idempotency key, authentication and redaction on the service, then an operator ruling |
| Any ConPort read or write | `GET /api/context` inserts a row, so it is not read-only; the workspace must always be sent explicitly | An operator ruling limiting reads to `/api/decisions` and `/api/recent-activity` with an explicit workspace id |
