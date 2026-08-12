# Command Log — TP-DMX-TRUST-GATE-FAIL-CLOSED-001

## S0 — Custody (no mutation)

```
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short --branch
git fetch origin main --quiet
git rev-parse origin/main                      # -> 3e8fcc1c70c5b859dd651a1cd33c85eab837c93e
git merge-base --is-ancestor $H0 origin/main    # -> true, H0 is ancestor
git diff --stat $H0 origin/main -- <7 allowlisted source/test paths>   # -> empty (IDENTICAL)
gh pr list --repo DDD-Enterprises/dopemux-mvp --state open --json number,title,headRefName,files
  # -> no open PR overlaps the allowlisted paths
```

## Worktree setup (§12)

```
git worktree add -b tp/DMX-TRUST-GATE-FAIL-CLOSED-001 \
  /Users/hue/code/dopemux-mvp-worktrees/tp-trust-gate-fail-closed-001 origin/main
# HEAD is now at 3e8fcc1c70
```

## S1 — Reproduce F001/F002 (local temp fixtures, no network, before any source edit)

```
# F001: empty {} proof and head-only proof through RedLaneScanner.scan()
# result on parent 3e8fcc1c70: status=PASS, self_certification_status=NONE

# F002: control-snapshot generation with TP-DCP-0002 entirely absent
# result on parent 3e8fcc1c70: readiness.snapshot_status=READY, blocking_reasons=[]
```
Full before/after transcripts: `review_bundle/DEFECT_REPRODUCTION_BEFORE_AFTER.txt`.

## S2 — Regression tests added, confirmed failing pre-fix

```
python3.12 -m pytest -q tests/dcp/test_dcp_0005_red_lane_scanner.py tests/dcp/test_dcp_0004_control_snapshot.py
# -> 7 new scanner tests + 1 new snapshot test FAILED for the expected reason
#    (asserted non-PASS/non-READY, observed PASS/READY) prior to S3 implementation.
```

## S3 — Implementation

- `src/dopemux/dcp/red_lane_scanner.py`: split identity branch so `self_certification_status`
  is `NONE` only when both implementer and auditor identities are present and distinct,
  `UNKNOWN` when either is missing; added explicit `MALFORMED_PROOF` BLOCKER finding on
  JSON parse failure / non-dict root instead of silent `continue`.
- `src/dopemux/dcp/control_snapshot.py`: added `elif` branch in `_readiness()` blocking
  readiness when a prerequisite packet state is `UNKNOWN` or `CLAIMED`.

## S4 — Deterministic validation

```
python3.12 -m pytest -q tests/dcp/test_dcp_0003_proof_family_dispatch.py tests/dcp/test_dcp_0004_control_snapshot.py tests/dcp/test_dcp_0005_red_lane_scanner.py
# -> 69 passed

python3.12 -m pytest -q tests/dcp
# -> 1 failed (tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified),
#    rest passed. Confirmed pre-existing/out-of-scope: caused by origin/main's own history
#    (PR #1165 commit vs its parent), reproduces identically regardless of packet changes,
#    file outside this packet's allowlist.

git diff --check
# -> exit 0

pre-commit run --files <all 14 changed/added files>
# -> all applicable hooks Passed, rest Skipped (no matching files)

grep -rniE "(sk-[a-z0-9]{20,}|ghp_[a-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z]+ PRIVATE KEY-----)" <changed files>
# -> one match, pre-existing (not in packet diff), synthetic repeating-digit pattern in
#    existing test_secret_redaction test
```

Full transcript: `review_bundle/FINAL_VALIDATION_LOG.txt`.

## S5 — Freeze C1

```
git add <14 allowlisted files>
git commit -m "fix(dcp): fail closed on incomplete control evidence" ...
# repo preflight hook ran: repo_preflight, run-mode, jq-present, ledger-present,
# ledger-json, diff-whitespace, smoke-tests — all OK
# -> C1 = 352a3d888d1ce5116b9af65d696fe62373728a7c
```

## S6 — Independent audit

Spawned an independent Claude Code `quality-engineer` subagent with no prior conversation
context, given only the repo path, commit SHA, and task packet. Full verdict in
`AUDITOR_REPORT.md`. Verdict: `PASS_WITH_RISKS` (both risks non-blocking).

Deviation: packet-preferred AGY `gemini-3.1-pro-high` was not invocable in this session;
fallback route used per packet §9, recorded explicitly.
