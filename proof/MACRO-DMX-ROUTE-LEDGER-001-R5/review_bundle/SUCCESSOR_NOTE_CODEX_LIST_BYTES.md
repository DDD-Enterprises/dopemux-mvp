# R5 successor note: Codex P2 x2 on 0b46b8755 (production change)

Additive. No other file in this bundle is edited. It changes the subject of any audit.

- Fix commit: `3d2af4b209dfc1fb703f82658a0c3a35cd804814`.
- Finding 1 (`rehydrate`): a failed `fs.list` was read as an empty directory, so `nextSeq` and `nextSegmentN` stayed 0 and the
  first write replaced the persisted `<stem>.jsonl`. Now a failed listing starts empty only if `fs.exists` reports the directory
  absent; if it exists, or `exists` itself fails, receipts are turned off (reason "could not list the receipt directory") and
  nothing is written.
- Finding 2 (`place`): segment size used `line.length` (UTF-16 units). With `recordDescription: true` and non-ASCII text a segment
  could pass the 4 MiB host limit before rolling, and a segment over the limit can never be written. Now UTF-8 bytes, by a hand-written
  `utf8Length` (no `TextEncoder`/`Buffer` assumed in the mod runtime). The 3.5 MB rollover threshold itself is unchanged.
- Tests written first and red against `0b46b8755` (99 pass / 5 fail; the absent-directory control passed already). After: 104 pass /
  0 fail, `claude plugin validate` exit 0, `tsc --noEmit` exit 0, `git diff --check` exit 0. A first typing error (`receiptDir` is
  `string | undefined`) was caught by `tsc` and fixed before the commit.
- Behaviour change to tell an auditor: a receipt directory that exists but cannot be listed now turns receipts OFF for the session,
  where before it silently risked overwriting. The `utf8Length` surrogate handling counts a lone surrogate as 3 bytes (what a UTF-8
  encoder emits as U+FFFD); `JSON.stringify` does not emit lone surrogates, so this is a bound, not a case seen.
- Not re-run: the 15-mutation check (its scratch harness no longer exists). No live-session check (N1). `markdownlint` NOT_RUN.
- Audit state unchanged: NOT_RUN. This is the third semantic change after R5's own repair (`13ceb5020` test-only, `61c371f28`, this
  one), so the audit subject must be the head after this note. Earlier notes still hold.
