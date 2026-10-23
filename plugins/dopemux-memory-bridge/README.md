# dopemux-memory-bridge

A Claude Code mod that keeps a small, local memory outbox for each session, shows
how many rows are waiting in the status line, and draws a one-line
"welcome back" band after a break.

This revision is the no-store core: it makes **no network call**, runs **no
`dopemux` command**, and never talks to ConPort, dope-memory or the ADHD engine.
The only subprocess it can start is `git status --porcelain`, and only for the
band. Sending rows anywhere (ledger replay, recap) is not part of this
revision.

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
| `kind` | `turn`, `compact`, `end`, `task` (and `note`, reserved for a later slash command) |
| `goal` | the first 160 characters of the user's text, redacted |
| `files_touched` | up to 30 unique repo-relative paths from Edit, Write and NotebookEdit calls this turn (paths outside the repo are skipped) |
| `decisions` | marker-detected, see below; up to 3, 200 characters each |
| `todos_completed` | up to 10 titles of TodoWrite items that newly became `completed` |
| `intended_event` | `task.completed` on a `task` row, otherwise `null` (`manual.memory_store` is reserved) |
| `state`, `attempts` | `pending` / `sent` / `dead`, and a counter; this revision only writes `pending` / `0` |

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

One line, beside Pulse's: `📮 N pending`, `📮 clear`, `📮 memory-only`,
`⚠ outbox write failed`, each with a ` +N dropped` suffix after a cap drop. `N`
counts pending rows in this session plus those found in the newest eight other
sessions' files at start.

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

## Known limits

- **Pulse.** The mod wraps `next(e)` and draws its line above whatever the rest
  draws. `dopemux-pulse` draws its own `Box` without `next(e)` while a focus block
  runs, so when Pulse is the outer hook the welcome-back band is hidden during
  focus (accepted). Which of two user-tier plugins is outer is UNKNOWN.
- **Surfaces.** The band exists on the terminal and desktop surfaces only
  (`AbovePrompt`). `$.process` is documented CLI-only; on the desktop app it may
  be absent or refuse, in which case the band simply omits the uncommitted-files
  segment. The outbox and status line need neither.
- Windows-style paths are not handled (POSIX `/` paths only).
- `$.fs.write` atomicity is UNKNOWN; the generation scheme is the mitigation.

## Tests and live proof

```
claude plugin validate plugins/dopemux-memory-bridge
claude plugin test plugins/dopemux-memory-bridge
```

The tests run against the mod kit with a mocked clock, file system, store and
process. **Live proof is NOT_RUN**: no real session has loaded this mod. To see it
yourself, start a session with the mod loaded from disk (`claude --plugin-dir
<path>/plugins/dopemux-memory-bridge`, or `CLAUDE_CODE_PLUGIN_DIRS` for the
desktop app) in a repo whose `.dopemux/` exists; finish one turn and look for
`📮 1 pending` and the new file under `.dopemux/memory-bridge/`; set
`idleMinutes` to 5, wait, and look for the band.
