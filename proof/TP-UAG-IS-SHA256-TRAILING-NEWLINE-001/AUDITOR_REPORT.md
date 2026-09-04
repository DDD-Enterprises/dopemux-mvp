# Embedded Audit — TP-UAG-IS-SHA256-TRAILING-NEWLINE-001 (PR #1312)

- **Status:** PASS
- **Auditor tool:** agy
- **Auditor model:** gemini-3.1-pro-high
- **Exit code:** 0
- **Audited head:** `d40438603969a175201c6191c97bbb8a585163f2`
- **Audited span:** `328a31e9a4..d404386039` (src/dopemux/uag/primitives.py, tests/unit/uag/test_hardening.py)
- **Report path:** `proof/TP-UAG-IS-SHA256-TRAILING-NEWLINE-001/AUDITOR_REPORT.md`

## Summary

Independent `agy`/Gemini 3.1 Pro High session, invoked with real filesystem
tool access (`--add-dir`) to the mounted worktree, audited a standalone
follow-up fix to `is_sha256()`. The prior independent audit of PR #1309 (UAG
T1 semantic core, head `06d515dfd`, same-model-family claude-code-cli/sonnet)
had found finding `AUD-01`: `is_sha256` accepted a SHA-256 digest with a
trailing newline, because Python's `$` regex anchor matches just before a
trailing newline when combined with `.match()`. PR #1309 merged separately
before that finding was fixed; this PR closes it as a standalone change.

## Verified Closure

- **AUD-01** `src/dopemux/uag/primitives.py` — `_SHA256_RE` changed from
  `re.compile(r"^[a-f0-9]{64}$")` + `.match()` to an anchor-free
  `re.compile(r"[a-f0-9]{64}")` + `.fullmatch()`, which requires the entire
  string to match with no trailing-newline exception. The auditor confirmed
  this via direct reasoning about `re.fullmatch` semantics, not by trusting
  the candidate's framing.
- `tests/unit/uag/test_hardening.py::TestIsSha256RejectsPadding` was
  confirmed to import and exercise the real `is_sha256` (not a stale
  duplicate), and the auditor confirmed the trailing-`\n` negative case would
  have passed (incorrectly) under the OLD implementation — i.e. the test
  actually pins the regression.
- Both call sites (`DigestRef.__post_init__`, `Receipt.__post_init__`) were
  inspected; the fix is fully backwards-compatible for legitimate 64-char
  lowercase-hex inputs, so no valid input is newly rejected.

## Findings

| ID | Severity | Title | Status |
|----|----------|-------|--------|
| AUD-01 | LOW | `is_sha256` accepted a single trailing newline via `$` regex anchor | RESOLVED |

### AUD-01 — is_sha256 trailing-newline gap (LOW, RESOLVED)

Originally found by the independent audit of PR #1309 at head `06d515dfd`
(`proof/TP-UAG-T1-SEMANTIC-CORE-001/AUDITOR_REPORT.md`). PR #1309 merged to
`main` (commit `fe08a6efe`) before this finding was addressed. This PR closes
it as a standalone follow-up. Verified resolved by this audit.

## Independent Verification Performed

- Recomputed the SHA-256 of `src/dopemux/uag/primitives.py` at the audited
  head using its own tool access: `3d79cd0a66811524886f6e7c7c9898256c1b067b88f7081237530c5dc679c938` —
  cross-checked byte-exact against local `shasum -a 256`.
- Ran `git diff 328a31e9a4..HEAD` itself in the mounted worktree and confirmed
  the change is strictly the two declared files, no scope creep.
- Ran `python -m pytest -q tests/unit/uag`, `python -m pytest -q
  tests/contracts`, `ruff check src/dopemux/uag tests/unit/uag`, `git diff
  --check` itself: all PASS.
- Scanned the diff for instruction-like/prompt-injection content: none found.

## Remaining Risks

None identified.

## Trust Model Note

This is a genuinely independent audit (Gemini 3.1 Pro High via `agy`, not the
same model family as the implementer), with real filesystem/git tool access,
unlike the two prior same-model-family (claude-code-cli/sonnet) audits of the
parent PR #1309. The signed local attestation binds these verified bytes to
PR #1312 at head `d404386039` per `docs/ops/embedded-audit.md`'s "Local signed
attestation" route, used here because the trusted CI job's Tier-2
`pal-mcp-clink` route returned an infrastructure error ("Credit balance is too
low") rather than a real verdict.
