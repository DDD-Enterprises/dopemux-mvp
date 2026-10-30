---
id: pulse-status-line
title: Pulse Status Line and Focus Clock
type: how-to
owner: '@hu3mann'
author: 'claude-code-agent (claude-haiku-5-5)'
date: '2026-10-21'
last_review: '2026-10-23'
next_review: '2027-01-19'
prelude: How to load the dopemux-pulse mod, read its status line and focus band, use the focus commands, and diagnose an unreachable ADHD engine.
---
# Pulse Status Line and Focus Clock

`dopemux-pulse` is a read-only Claude Code mod. It shows a status line under the
prompt, a focus clock driven by three slash commands, and a band above the prompt
while a focus block runs. Source: `plugins/dopemux-pulse/`.

This guide assumes Claude Code runs from the repo root and the Dopemux ADHD
engine is started, or you accept that the status line will report it unreachable.

## 1. Load the mod

From the repo root:

```bash
claude --plugin-dir plugins/dopemux-pulse
```

Nothing is installed and nothing is written to `~/.claude`. The mod lasts for
that session (`plugins/dopemux-pulse/README.md`, "Load it").

## 2. Read the status line

The status line refreshes every 60 seconds (`hooks/register.tsx`, `POLL_MS`).
Example:

```text
🎯 14/25 · ⚡ medium · 🧠 focused · ⏱ 37m
```

| Part | Meaning | Source |
|------|---------|--------|
| `🎯 14/25` | Minutes elapsed in the focus block / block length | `renderStatus` |
| `🎯 idle` | No focus block runs | `renderStatus` |
| `🎯 25/25 done` | Block time is up, not yet ended | `renderStatus` |
| `⚡ medium` | Engine `energy` (or `energy_level` alias) | `parseState` |
| `🧠 focused` | Engine `attention` (or `attention_state` alias) | `parseState` |
| `⏱ 37m` | Session minutes counted by the mod from session start | `session.start` handler |

The engine's `session_minutes` value is not used (see section 5).

If a field is missing from an otherwise valid answer, the mod shows `?` in its
place (for example `🧠 ?`).

## 3. Use the focus clock

| Command | Effect |
|---------|--------|
| `/pulse-focus [minutes]` | Start a block. Default 25; whole numbers 5-120 only. Starting while one runs restarts it. |
| `/break` | End the block and clear the continuous-focus count. |
| `/done` | Finish the block and also clear the continuous-focus count. Says `No focus block is running.` when none runs. |

Anything other than a whole number from 5 to 120 is refused with
`Focus minutes must be a whole number from 5-120 (default 25). Nothing started.`
Examples of refused input: `4`, `121`, `12.5`, `abc`.

The command is `/pulse-focus`, not `/focus`, which Claude Code ships and refuses.
If Claude Code refuses to register one of the three commands, a toast
`dopemux-pulse: /<name> could not be registered` is shown.

### What you see while a block runs

- **Band above the prompt:** `🎯 Focus: 15 min left of 25 · /break · /done`.
  It draws nothing when no block runs, and it yields when a survey is shown.
- **Limit toast:** at the block length, `🎯 Your 25-minute focus block is up.
  /break to rest, or /done to finish.` After the limit the band reads
  `🎯 Focus block done (+N min). ...`.
- **Continuous-focus nudge:** one toast at 90 minutes of continuous focus. The
  count starts at the first `/pulse-focus` and resets on `/break` or `/done`.
  Chained blocks do not reset it.

## 4. Configure the engine URL

The mod has one option, `engineUrl`, default `http://127.0.0.1:3025`. It must
start with `http://` or `https://`; a trailing slash is dropped. Any other value
shows `⚠ ADHD engine URL is not http(s)` and the mod fetches nothing. The README
says to set it under `pluginConfigs` in settings or in the `/config` menu.

Port `3025` is the adhd-engine host port in `services/registry.yaml`. Inside its
container the engine listens on `8095`.

## 5. Know what the engine data is

- **Endpoint:** the mod sends `GET <engineUrl>/api/v1/state` with a 2-second
  timeout. This is the only request it makes. It writes no files and runs no
  processes.
- **Keys:** the engine returns `energy`, `attention`, `session_minutes` and
  `user_id`. Its `/state` handler also returns `energy_level` and
  `attention_state`, with the same values. An older engine returns only `energy`
  and `attention`. The mod prefers the primary keys either way.
- **Energy and attention are proxy data.** The engine infers them from hook
  activity, not from measurements of the person. Treat them as a rough signal.
- **Fallback answers look healthy.** If the engine's handler raises, it still
  returns HTTP 200 with `medium` / `focused` (`services/adhd_engine/api/routes.py`,
  the `except` branch). The mod cannot tell that apart from real state.
- **`session_minutes` is always 0 today.** Only the `/state` handler reads
  `_session_start_times`, and nothing writes it. That is why the mod counts
  `⏱` itself.

## 6. Troubleshoot an unreachable engine

The status line text tells you which case applies:

| Status text | Meaning | What to check |
|-------------|---------|---------------|
| `🔌 ADHD engine unreachable` | Connection refused, timeout (over 2 s), or no answer | Is the engine running on the `engineUrl` port? Try `curl -s http://127.0.0.1:3025/api/v1/state` |
| `🔌 ADHD engine unreachable (HTTP 503)` | Engine answered with a non-2xx status | Check the engine's logs for that status |
| `⚠ ADHD engine state malformed` | Answer is not a JSON object, or has neither `energy` nor `attention` (or their aliases) | The URL may point at something other than the engine |
| `⚠ ADHD engine URL is not http(s)` | `engineUrl` is not an `http(s)://` URL | Fix the option; nothing is fetched until it is valid |
| `⏳ ADHD engine: connecting` | No poll has answered yet | Wait one poll (up to 60 s) |

Toasts fire on changes only. A toast appears once when a reachable engine goes
down (`ADHD engine unreachable` or `ADHD engine state malformed`), and once when
it comes back (`ADHD engine is back`). An engine that was never up shows only the
status line, with no toast.

Focus timers keep running while the engine is down. While a request is
outstanding the mod starts no other; a hung engine shows `unreachable` after 2
seconds, and polling resumes once the abandoned request settles. An engine that
never settles it keeps the status line on `unreachable`.

## 7. Verify the mod

```bash
claude plugin validate plugins/dopemux-pulse
claude plugin test plugins/dopemux-pulse
```

The tests run the hooks with a mocked clock and a mocked HTTP answer, so they
check the hooks' logic only.

## Not verified

- Live behaviour against a running adhd-engine has not been checked. The mocked
  tests do not cover real engine answers.
- The live paint of the status line and band, and `/pulse-focus` typeahead, have
  not been seen in a real session.
- `/clear` behaviour in a real session has not been observed. The test
  `session.end with reason clear` covers the mocked case only.
- Ending a session (any reason other than `clear`) is covered by tests only.
