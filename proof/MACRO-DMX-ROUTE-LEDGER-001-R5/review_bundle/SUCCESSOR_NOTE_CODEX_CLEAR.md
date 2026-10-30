# R5 successor note: Codex P2 on /clear (production change)

Additive. No other file in this bundle is edited. This note supersedes two statements in
`VERIFY_NOTES.md` and changes the subject of any audit.

- Trigger: Codex review of `c4a98f99d`, P2 on `plugins/dopemux-route-ledger/hooks/register.tsx` (the `/clear` reset): a failed
  write leaves the segment dirty, `await s.chain` still succeeds, and the unconditional reset then discarded the only copy.
  This is the behaviour `VERIFY_NOTES.md` recorded as "Accepted" under the child deviations. That acceptance was wrong.
- Fix commit: `61c371f282363255b508dbcc20face5d379ce158`. `/clear` now uses `flushAtEnd` (one more awaited try). If anything is
  still unwritten it sets `clearPending` and keeps the session state; `ensureReady` calls `finishClear`, which flushes directly
  (it runs inside the serialized chain, so it must not await `s.chain`) and resets only once nothing is dirty. Receipts recorded
  in between carry the old session id. README and the how-to were updated.
- Superseded statements in `VERIFY_NOTES.md`: (1) "On `/clear` the pending flush is attempted once with no D4-style retry ... a
  dirty tail that fails at `/clear` is counted and then dropped by the reset" is no longer true; (2) "95 plugin tests" is now 98.
- Tests: three new D8 tests, written first and red against `c4a98f99d` (95 pass / 3 fail): unchanged id continues the file;
  changed id writes the old tail to its own file and starts fresh; writes that keep failing drop nothing and land after
  recovery. After the fix: 98 pass / 0 fail; `claude plugin validate`, `tsc --noEmit` and `git diff --check` exit 0.
- A first implementation awaited `s.chain` inside `finishClear` and deadlocked silently (record paths run inside `enqueue`);
  the tests caught it, and it was fixed before the commit.
- Not re-run: the 15-mutation sanity check (its scratch harness no longer exists), so the mutation claims in `VERIFY_NOTES.md`
  describe `26414fef5`, not this head. No live-session check (N1). `markdownlint` NOT_RUN.
- Audit state unchanged: NOT_RUN. This is a semantic change, so the subject for the independent audit is the head after this
  note, and nothing audited earlier covers it. The CodeQL fix note (`SUCCESSOR_NOTE_CODEQL.md`) still holds.
