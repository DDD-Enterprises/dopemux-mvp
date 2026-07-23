# Independent Audit Report — PR #1084 (security/release approval gate)

**Auditor tool**: agy (Antigravity CLI) — read-only `--mode plan`
**Audited head**: `7fa80333cd5998bdf8db22e04c1f8517dc7c7c91`
**Not self-audited**: implementing agent (Claude Sonnet 5) did not perform this audit.

## Audit trail

Two prior independent-audit attempts on this PR were exhausted before this run:
1. Claude `security-engineer` subagent (early round) — found bidirectional bot-login
   normalization bug (roster entry `"foo[bot]"` matching bare login `"foo"`). Fixed;
   regression tests added (`tests/pr_steward/test_known_author_bot_normalization.py`).
2. Grok CLI (headless, `--always-approve --deny edit:*,write:*,...`), audited head
   `7b7690fe8c25fc154fd1816d115098904262ac65` — found MEDIUM trust-boundary defect:
   changed-file classification was destination-path-only, so a rename could move a
   protected path (e.g. `tools/pr_steward/**`, `.github/workflows/**`, `CODEOWNERS`)
   out of scope without ever tripping the security/release approval gate. Fixed via
   migration to paginated REST `pulls/{n}/files` (carries `status`/`previous_filename`)
   and classification of `changed_paths + renamed_from_paths` together
   (`tools/pr_steward/collector.py::_fetch_changed_files_rest`,
   `tools/pr_steward/classifier.py::build_artifacts`).
3. Grok CLI account balance exhausted (402 Payment Required) before the required
   fresh audit against the fix commit could run.
4. Gemini CLI rejected authentication (`IneligibleTierError` — free tier retired,
   migrated to Antigravity).
5. **agy (Antigravity CLI)**, `--mode plan` (read-only), ran to completion in two
   passes (first hit a 5-minute print-timeout mid-analysis; re-run with 15-minute
   timeout and a pointer to the partial findings completed the audit).

## agy's independent verification (this run)

- Confirmed the rename-source fix: `_fetch_changed_files_rest` captures
  `previous_filename` from the REST API; `build_artifacts` feeds
  `changed_paths + renamed_from_paths` into `classify_security_release_paths`.
- Traced the fail-closed chain end-to-end: a renamed entry missing
  `previous_filename` is dropped and an error appended →
  `harvest_errors` non-empty → `harvest_complete = False` →
  `HARVEST_INCOMPLETE` blocker in `build_artifacts`. Confirmed correct.
- Investigated (and resolved as a non-issue) whether `gh api --paginate -q '.'`
  emits pretty-printed multi-line JSON per page, which would break the
  line-by-line parser in `_fetch_changed_files_rest`. Empirically confirmed
  `gh api -q '.'` emits **compact single-line** JSON per page (unlike standalone
  `jq .`, which pretty-prints) — the parser is correct as written.
- Investigated multi-hop renames within a single PR (`A -> B -> C`). Confirmed
  GitHub's PR-level files API collapses this to a single `previous_filename: A`,
  `filename: C` entry — the fix correctly captures the original protected path
  in this case.
- Ran the full `tests/pr_steward` suite in an isolated `git worktree` checked
  out at the audited head (no mutation of the working tree under audit):
  **174 passed, 0 failed, 0 errors** (`python3 -m pytest -v tests/pr_steward`,
  Python 3.12.13).

## Verdict

```text
AUDITED_HEAD: 7fa80333cd5998bdf8db22e04c1f8517dc7c7c91
VERDICT: PASS
BLOCKING: 0
HIGH: 0
MEDIUM (trust-boundary, open): 0
```

## Findings (non-blocking, INFO only)

1. **INFO** — `_fetch_changed_files_rest`'s `try/except json.JSONDecodeError`
   wraps the entire page-accumulation loop, so a malformed trailing page
   discards all previously-accumulated pages' entries and returns
   `([], [error])`. This is fail-closed (`HARVEST_INCOMPLETE`), not a security
   bypass — flagged only as a possible source of a spurious incomplete-harvest
   signal on a large multi-page PR. Accepted as-is; no trust-boundary impact.
2. **INFO** — `_changed_files()` in `classifier.py` does not itself guard
   `isinstance(item, dict)` before calling `.get()`. Pre-existing condition,
   present in the parent commit before this PR; the REST normalizer upstream
   already validates dict-type entries before they reach this function. No
   regression introduced by this fix.

## Remaining risks

None identified beyond the two INFO items above. All claimed fixes verified
end-to-end against the exact audited head; pagination and multi-hop-rename
behavior confirmed empirically, not merely by reading the code.
