# W01 return (MACRO-DMX-PULSE-002-R2) — child report saved verbatim as received

**Requested route**: `claude-code-agent`, `claude-sonnet-5-5` (Agent tool, subagent type `developer`), effort `UNKNOWN`.
**Observed model**: `UNKNOWN` (no runtime receipt). Self-report below: "Sonnet 5.5 (claude-sonnet-5-5)".
**Measured by the harness**: 88,095 subagent tokens, 32 tool uses, duration 196,474 ms (about 3.3 minutes).
**Supervisor re-verification before commit C1 `abd128393eddf68830afd4e2c3637feefd10c467`**: `claude plugin validate` exit 0; `claude plugin test` exit 0, 29 pass / 0 fail; `git diff --check` exit 0; diff names equal the two allowlisted files; supervisor's own mutation (drop `|| s.isFetching` from `poll`) made T1, T2, T3 fail (26 pass / 3 fail) and was restored byte-identical (`cmp`); `tsc` clean with an out-of-repo tsconfig (exit 0).

---

STATUS: READY_FOR_AUDIT (F1 and F6 both complete; nothing committed). Self-reported model: Sonnet 5.5 (claude-sonnet-5-5), effort UNKNOWN. This is a self-report, not a runtime receipt.

Start state was as required: HEAD f4115046484ed0dc580cc4337bb8c7cf55d39af7, porcelain showed only the two untracked task-packets dirs. I did not open the findings files (GROK_ADJUDICATION.md, GROK_AUDIT_RESPONSE.txt). I took F1/F6 from the packet text and confirmed them against the source.

## Per-file summary (diff: 2 files, +151/-21)
- `plugins/dopemux-pulse/hooks/register.tsx`
  - **F1:**
    - Added `isFetching` to the `Pulse` state.
    - `fetchState` creates the `$.http.fetch(...)` promise with its fulfil and reject handlers attached at creation. The reject handler maps to `down`, and the fulfil handler is try/catch-wrapped.
    - A trailing `.then` clears `isFetching` only when the underlying fetch settles.
    - The race against the 2 s `$.clock.after` is unchanged, so `down` still shows after 2 s. `timer?.cancel()` stays in the `finally`.
    - `poll` now returns early on `s.isEnded || s.isPolling || s.isFetching`.
    - The late answer of an abandoned request is never read, so nothing is written to the view and nothing is toasted.
    - The trade-off comment is above `fetchState`.
  - **F6:** a top-level helper `registerCommand($, spec)` awaits `$.command.register`. On rejection it toasts the fixed text `dopemux-pulse: /<name> could not be registered`, using only the literal name, inside its own try/catch. The three registrations in `session.start` now use it. Registration of the other commands and the poll start are unchanged.
  - Helpers remain top-level and take `$` and the state as arguments. No new constants, no `$.process`/`$.fs`, no new network target.
- `plugins/dopemux-pulse/hooks/register.test.ts`
  - Harness additions: a `slow-then-deny` behaviour (sleeps 10 min, then returns `{ deny }`) and an optional 4th argument `denyCommand` that makes `command.register` refuse that one name.
  - New tests T1-T5. All 24 existing tests are unmodified.

## Fail-then-pass (final test text run against `git show HEAD:` register.tsx, then the new one)
Unmodified module: 25 pass / 4 fail. New module: 29 pass / 0 fail.

| Test | Unmodified module | New module | Failing assertion before |
|---|---|---|---|
| T1 | FAIL | PASS | `urls` expected length 1, received 6 |
| T2 | FAIL | PASS | `urls` expected length 1 at the 9-minute checkpoint, received 8 |
| T3 | FAIL | PASS | `urls.length <= 2` expected, received 11 |
| T4 | PASS | PASS | none (see below) |
| T5 | FAIL | PASS | toasts expected `["dopemux-pulse: /break could not be registered"]`, received `[]` |

- T2: recovery is asserted with `urls.length >= 2` and a healthy status, no exact count. No `malformed` status was ever written. The only toast is `ADHD engine is back`, which is correct because `wasUp` was already false after the timeout.
- T3: it also asserts that the status count is unchanged and there are no toasts.
- T4 passes on the old module too, so it is a regression guard, not a fail-before test. I report that honestly.
- T5: registered commands are exactly `['pulse-focus','done']`, the toast is the only one, and the poll still ran with status `⚡ medium · 🧠 focused`.

## Mutation checks (each restored byte-identical, verified with `cmp`)
- **M1, drop `|| s.isFetching` from `poll`:** T1, T2, T3 FAIL (26 pass / 3 fail). Result PASS (mutation caught).
- **M3, release the guard at race end (in the `finally`) instead of at settle:** T1, T2, T3 FAIL. Result PASS (mutation caught).
- **M2, remove only the rejection handler:**
  - T3 did NOT fail. Two existing tests ('engine is down...' and 'toasts once...') did.
  - The runner does observe unhandled rejections: a probe produced "the file ran to its end: a rejection nothing handled". But `Promise.race` itself subscribes to the loser, so removing the handler raises no unhandled rejection here.
  - So T3's rejection claim is covered by inspection plus the runner's file-level rejection check, not by a mutation-sensitive assertion. The `process`-based hook I first wrote in T3 was dead (`process` is undefined in the sandbox), so I removed it and left a comment.
  - Result for M2: T3 not mutation-sensitive.
- After restore: 29 pass / 0 fail.

## Gates
- `claude plugin validate plugins/dopemux-pulse`: PASS, exit 0 ("Validation passed with warnings"). The only advice is the README install line (baseline).
- `claude plugin test plugins/dopemux-pulse`: PASS, exit 0, 29 pass / 0 fail (baseline was 24 pass / 0 fail).
- `tsc -p plugins/dopemux-pulse`: NOT_RUN. `plugins/dopemux-pulse/.claude-plugin/` contains only `plugin.json`, with no `types/` directory laid by the engine.
- `git diff --check`: PASS, exit 0.
- `git diff --name-only | sort`: exactly `plugins/dopemux-pulse/hooks/register.test.ts` and `plugins/dopemux-pulse/hooks/register.tsx`.
- Porcelain: the two modified files plus the two untracked task-packets dirs.

## Declaration check
The supplied claude-code.d.ts documents no timeout or abort option for `$.http.fetch`. `HttpInit` (line 5363) has only `method`, `headers`, `body`, `auth` and `socketPath`, and the `fetch` doc (line 3568) lists the same five. `signal` and `timeoutMs` exist only on `$.model.complete` and `$.process.run`, and `signal` on `$.clock.sleep`. This confirms the supervisor's observation. Nothing was adopted.

## Host-never-settles trade-off
`$.http.fetch` cannot be cancelled, and the abandoned request is NOT cancelled. If the host never settles an abandoned request, polling pauses and the status line stays `🔌 ADHD engine unreachable` until it does. The host's own network timeout is UNKNOWN. The same text is in the code comment above `fetchState`.

## Other notes
- At the exact settle instant (10 min), tick-versus-settle ordering is mock-clock dependent. T3 tolerates at most one new post-settle request, and T2 pins no exact count.
- No live session was run: runtime behaviour is NOT_RUN, and only the mock-clock tests ran. I did not install the plugin, enable hot reload, or write under ~/.claude.
- advisor_calls: 0.
- Nothing was committed or pushed.
- files_written (repo): `/Users/hue/code/dopemux-mvp/.claude/worktrees/pulse-f1-001-5a321f/plugins/dopemux-pulse/hooks/register.tsx` and `/Users/hue/code/dopemux-mvp/.claude/worktrees/pulse-f1-001-5a321f/plugins/dopemux-pulse/hooks/register.test.ts`.
- Scratch copies for restore and mutation work are in the supervisor scratchpad: `register.new.tsx` and `register.test.new.ts`. Neither is in the repo.
