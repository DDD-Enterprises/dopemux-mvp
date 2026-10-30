# dopemux-pulse

A read-only Claude Code function-hook mod (early-access plugin API) that puts
two things in a session:

- **Status line** (under the prompt), refreshed every 60 seconds:
  `🎯 14/25 · ⚡ medium · 🧠 focused · ⏱ 37m`
  - `🎯 14/25` is the running focus block (minutes elapsed / block length);
    `🎯 idle` when none runs, `🎯 25/25 done` once the block's time is up.
  - `⚡` and `🧠` are the Dopemux ADHD engine's `energy` and `attention`
    (falling back to `energy_level` / `attention_state`).
  - `⏱ 37m` is session minutes, counted by the mod from `session.start`
    (the engine's own `session_minutes` is not used).
  - If the engine is unreachable the line says `🔌 ADHD engine unreachable`
    (with the HTTP status for a non-2xx answer); if the answer is not usable it
    says `⚠ ADHD engine state malformed`. A toast fires once when a reachable
    engine goes down and once when it comes back; an engine that was never up
    only shows the status line.
- **Focus clock**, three commands:
  - `/pulse-focus [minutes]` starts a focus block (default 25, allowed 5-120;
    anything else is refused and nothing starts). Starting one while another
    runs restarts it.
  - `/break` ends the block and the continuous-focus count.
  - `/done` finishes the block and also ends the continuous-focus count (says
    so if none is running).
  - A band above the prompt shows `🎯 Focus: 15 min left of 25` while a block
    runs and draws nothing of its own when idle. A toast fires at the limit,
    and a gentler nudge after 90 minutes of continuous focus (the count starts
    at the first `/pulse-focus` and resets on `/break` or `/done`; chained
    blocks do not reset it).

`/focus` is a name Claude Code itself ships and `$.command.register` refuses it
(`claude plugin validate` reports it), so the focus command is `/pulse-focus`.
If Claude Code refuses to register one of the three commands, a toast
`dopemux-pulse: /<name> could not be registered` is shown.

## Load it

```bash
claude --plugin-dir plugins/dopemux-pulse
```

Nothing is installed or written to `~/.claude`; the mod lives for that session.

## Configuration

One option, `engineUrl` (`userConfig` in `plugin.json`), default
`http://127.0.0.1:3025`. It must be `http(s)://`; anything else shows
`⚠ ADHD engine URL is not http(s)` and nothing is fetched. Set it under
`pluginConfigs` in settings or in the `/config` menu.

## Engine dependency

The mod does one `GET <engineUrl>/api/v1/state` per minute (2 second timeout)
against the Dopemux ADHD engine. It needs the engine's `energy` and `attention`
keys; the `energy_level` / `attention_state` aliases are accepted too. Without a
running engine the focus clock still works and the status line says the engine
is unreachable.

While a request is outstanding the mod starts no other. A hung engine shows
`unreachable` after 2 seconds, and polling resumes once the abandoned request
settles; an engine that never settles it keeps the status line on `unreachable`.

## Limits

- **Energy and attention are proxy data.** The engine infers them from hook
  activity (prompts, tool use, timing), not from anything about the person. Read
  them as a rough signal.
- **Read-only.** HTTP GET to the one configured URL only; no process runs, no
  files written, no prompt rewriting, no tool hooks, no model calls, no
  credentials.
- **State is in memory.** A focus block does not survive the session. On a real
  end (`session.end` with any reason but `clear`) all timers are cancelled and
  the status line is cleared. A `/clear` also fires `session.end` (reason
  `clear`) but the process goes on and no `session.start` follows, so the mod
  ignores it: the status line, polling and any running focus block carry on.
- **Nothing else is sent.** The mod never sends anything except
  `GET <engineUrl>/api/v1/state`.
- The band and status line are drawn on the terminal and desktop surfaces.

## Tests

```bash
claude plugin validate plugins/dopemux-pulse
claude plugin test plugins/dopemux-pulse
```

The tests run the hooks against the engine's test kit with a mocked clock and a
mocked HTTP answer.

**Not verified:** behaviour in a real session against a running engine. The
tests prove the hooks' logic, not the live paint of the status line or band, the
`/pulse-focus` typeahead, or a real engine's responses.
