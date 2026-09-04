# Review Bundle — TP-UAG-IS-SHA256-TRAILING-NEWLINE-001

Independent AGY/Gemini (`gemini-3.1-pro-high`) embedded-audit evidence for the
standalone `is_sha256` digest-validation fix at HEAD
`d40438603969a175201c6191c97bbb8a585163f2` (PR #1312, base `328a31e9a4`).

## Contents

| File | Purpose |
|------|---------|
| `audit_prompt.txt` | The independent auditor prompt (trusted task + authority framing, repo/head binding, required challenge list, `--add-dir` real tool access). |
| `auditor_raw_output.txt` | Raw structured JSON output of the independent `agy --model gemini-3.1-pro-high` session: verdict PASS, 0 risks, independently recomputed `primitives.py` SHA-256 matched local `shasum` byte-exact. |
| `audit_diff.txt` | Unified diff of the audited surface (`src/dopemux/uag/primitives.py`, `tests/unit/uag/test_hardening.py`) between base and audited head. |
| `changed_files.txt` | List of changed source files in the audit scope. |
| `instruction_like_scan.json` | Prompt-injection-style content scan result (`detected: false`). |
| `README.md` | This index. |

## Notes

- The audit was performed via `agy` (Google Antigravity CLI, Gemini 3.1 Pro
  High) — a genuinely different model family from the implementer, unlike the
  two prior same-model-family (claude-code-cli/sonnet) audits of the parent
  PR #1309 this fix follows up on. Tier-1 route #1 per `docs/ops/embedded-audit.md`.
- The auditor was invoked with `--add-dir` (real filesystem/git tool access to
  the mounted worktree), so hash recomputation and diff/test execution were
  performed by the auditor itself, not asserted by the candidate.
- Verdict is **PASS** with 0 findings/risks: the fix correctly replaces
  `re.compile(r"^[a-f0-9]{64}$")` + `.match()` (which admits a trailing
  newline because Python's `$` matches just before one) with an anchor-free
  pattern plus `.fullmatch()`, closing finding `AUD-01` from the prior
  independent audit of PR #1309 at head `06d515dfd`.
- Local `python -m pytest -q tests/unit/uag` (79 passed), `python -m pytest -q
  tests/contracts` (187 passed), `ruff check`, and `git diff --check` were run
  by the implementer; the auditor separately re-ran the same commands itself
  via its own tool access and reported PASS for each.
