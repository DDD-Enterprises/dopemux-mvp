# COMMAND_LOG

Key commands executed during this packet's implementation, in order. All exit
codes recorded in `EXIT_CODES.json`.

## Preflight
- `git rev-parse --show-toplevel`, `git remote -v`, `git status --short`, `git fetch origin --prune`
- `git rev-parse origin/main` -> `5f862d36f5417801b9fe148fccbb439731627234` (EXECUTION_BASE_SHA)
- `git rev-parse HEAD` (confirmed dedicated worktree already at EXECUTION_BASE_SHA)
- `test -f .dopetaskroot`, `test -f pyproject.toml`, `gh repo view --json nameWithOwner,defaultBranchRef`
- `python3 --version` (3.12.13), `git --version` (2.54.0), `gh --version` (2.95.0)

## Evidence capture
- `gh pr list --repo DDD-Enterprises/dopemux-mvp --state open --limit 200 --json ...` -> `OPEN_PRS_INITIAL.json` (21 PRs)
- `gh pr view <N> --json ... > open-pr-<N>.json` for all 21 open PRs
- `gh pr view <N> --json changedFiles,additions,deletions` for all 21 PRs (gh's `.files` connection caps display at 100; used to get true changed-file counts for #1123 [16206] and #1136 [366])

## Source resolution
- `git cat-file -e <EXECUTION_BASE_SHA>:<path>` / `git rev-parse <EXECUTION_BASE_SHA>:<path>` / `git cat-file -s <blob>` for every one of ~50 candidate paths across the 37 required slots
- `git show <EXECUTION_BASE_SHA>:<path> | head` for conflict adjudication (ARCHITECTURE.md, PM_PLANE.md, doc-trust-map.md, model-routing.policy.yaml)
- `grep -n -i -E "solo|org.member|exact.head|authoriz" docs/ops/pr-steward.md` (confirmed no overlap with PR #1140)

## Build and validate (run 3 times: initial, post-PR-#1150-drift-refresh, post-audit-fix)
- `python3 -m py_compile scripts/project_sources/*.py`
- `python3 scripts/project_sources/build_chatgpt_project_sources.py --repo-root . --execution-base-sha <sha> --open-pr-dir proof/... --output-dir out/... --generated-at <ts>`
- `python3 scripts/project_sources/validate_chatgpt_project_sources.py --repo-root . --execution-base-sha <sha> --package-dir out/... --open-pr-dir proof/...` -> all 9 gates pass every run
- Reproducibility check: rebuilt into a second directory with identical args, `diff -rq` against the committed UPLOAD_FILES -> zero differences
- ZIP reproducibility check: rebuilt the ZIP twice from identical inputs, `shasum -a 256` identical both times

## Schema / runtime checks
- `python3 -c "import jsonschema, yaml"` (both available)
- `python3 -c "... jsonschema.validators.validator_for(s).check_schema(s) ..."` for slots 25, 31, 33 (all valid schema documents)
- `python3 -m jsonschema -i task-packets/generated/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (failed once with `execution.agent: "claude"` not in enum; fixed to `"shell"`, then passed)
- `python3 scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static` -> `status=passed failures=0`

## Packaging
- ZIP built with a Python `zipfile` script (sorted member order, normalized `date_time`), `unzip -t`, `shasum -a 256` + sidecar

## Allowlist / diff
- `git status --short`, `git diff --check`, `git diff --cached --stat`
- Removed a stray `out/chatgpt-project-upload-set/.claude/.activity-heartbeat-cache.json` (a harness hook side-effect from an incidental `cd` into that directory, not part of this packet's allowlist)

## Commit / push / PR
- `git add` (allowlisted paths only) + `git add -f` for the gitignored `.zip`/`.zip.sha256`
- `git commit`, `git push -u origin claude/chatgpt-40-source-refresh-f84dfc`
- `gh pr create` -> PR #1152

## PR drift gates (run twice: pre-audit and post-audit)
- `git fetch origin --prune`, `git rev-parse origin/main` (unchanged both times)
- `gh pr list ... --json number,headRefOid` diffed against captured evidence -> PR #1150 head SHA changed once (refreshed and rebuilt); no other drift affecting `origin/main` or classifications

## Embedded audit
- Dispatched an independent `general-purpose` subagent (separate session, no implementer context) per packet section 20 / directive route 2 ("Claude Code CLI Sonnet in a separate non-implementer session")
- Auditor independently re-ran `git cat-file`/`git show`/`diff`, the validator script, a from-scratch rebuild diffed against committed output, `unzip -t`, `shasum -a 256 -c`, a secret grep, and live `gh pr view`/`gh pr list` spot-checks
- Verdict: `PASS_WITH_RISKS` -- 2 findings addressed (see `AUDITOR_REPORT.md`, `AUDIT_VERDICT.json`), package rebuilt a third time to incorporate the fixes, all gates re-verified pass
