# R5 successor note: CodeQL alert 272 (test-only fix)

This note is additive. It does not edit or replace any other file in this bundle.

- Subject of the R5 bundle: repair commit `26414fef53df4970e39269a3ba9ed93afd6b8f32`, bundle commit `94a78bce1`.
- Trigger: CodeQL alert #272, `js/incomplete-sanitization`, at `plugins/dopemux-route-ledger/hooks/register.test.ts:1197` on head `94a78bce1`.
- Fix commit: `13ceb5020d0c251f25de13844b00a9a40ae7f942`. One line, test file only:
  `expect(text).toMatch(new RegExp(FILE.replace(/[.]/g, '\\.')))` became `expect(text).toContain(FILE)`.
- Unchanged by the fix: `register.tsx`, `plugin.json`, `receipt.schema.json`, the README and the how-to doc. `REPAIR.diff` in this bundle therefore still describes the production and doc changes exactly; only the test-file part of it differs by that one line.
- Measured on the fix commit: `claude plugin test` 95 pass / 0 fail; `claude plugin validate` exit 0; `tsc -p ... --noEmit` exit 0; `git diff --check` exit 0. With the expectation deliberately broken (`FILE + "-nope"`) the test failed (94 pass, 1 fail), so the new assertion is not vacuous. The mutation was reverted before committing.
- Not changed by this note: the audit state. The independent audit is still NOT_RUN for the repaired code; `audit_not_executed` and `audit_provenance_missing` on the audit check, and the PR Steward readiness failure that follows from them, are expected and are not code problems. No audit evidence, signing or gate file was touched. A later semantic change would invalidate any audit of this head; this change is test-only.
