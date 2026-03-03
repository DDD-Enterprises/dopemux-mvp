---
name: drain
description: "Drain the open PR queue: classify blockers, fix CI/conflicts/review comments, and merge (or mark MERGE_READY) with per-PR proof bundles."
user-invocable: true
allowed-tools:
  - bash
  - read_file
  - write_file
  - search_replace
  - grep
  - conport_*
  - serena_*
  - dope_context_*
  - pal_*
---

# /drain — PR Queue Drain Skill

## Purpose
Systematically drain the open PR queue in this repository. Each PR is
classified by its blockers, fixed with the minimal safe change, verified, then
merged (or marked `MERGE_READY` if merge permissions require human action).

---

## Step 0 — Gather run parameters

Ask the user for the following. Use defaults if no answer is provided within
one exchange:

| Parameter        | Default  | Notes                                    |
| ---------------- | -------- | ---------------------------------------- |
| Remote           | `origin` | The git remote to use                    |
| Base branch      | `main`   | Branch all PRs target                    |
| Max PRs this run | `3`      | Keep WIP cap low                         |
| Merge method     | `squash` | `squash` / `rebase` / `merge`            |
| Actually merge?  | `yes`    | `no` → only prepare MERGE_READY evidence |

Generate a `RUN_ID` = `drain-<YYYYMMDD-HHMM>` (use current local time).

---

## Step 1 — Tool Discovery Gate (G0)

Run each check. If ANY fails, write `proof/<RUN_ID>/FAILURE.md` and **STOP**.

```bash
# 1a. gh CLI + auth
gh auth status

# 1b. MCP namespaces — spot-check one tool per namespace
#     (Vibe will surface these as tool calls; if not available, note it)
# conport_*, pal_*, dope_context_*, serena_*
```

Log `RUN_START` to conport (or dope_context_write if conport unavailable):
- run_id, timestamp, repo, base_branch, max_prs, merge_method

---

## Step 2 — Queue Snapshot

```bash
gh pr list \
  --base <BASE_BRANCH> \
  --limit <MAX_PRS * 3> \
  --json number,title,author,updatedAt,mergeable,reviewDecision,\
statusCheckRollup,isDraft,additions,deletions \
  | tee proof/<RUN_ID>/QUEUE_SNAPSHOT.json
```

**Classify each PR** into one of:

| Class            | Condition                                          |
| ---------------- | -------------------------------------------------- |
| `READY`          | CI green + no conflicts + review satisfied         |
| `CI_ONLY`        | CI failing, no conflicts, no unresolved comments   |
| `CONFLICTS_ONLY` | Merge conflicts, CI would be green otherwise       |
| `COMMENTS_ONLY`  | Unresolved review comments, CI green, no conflicts |
| `MIXED`          | More than one of CI / conflicts / comments         |
| `BLOCKED`        | Missing info, external dep, draft, unclear         |

**Stable sort**: priority order above → `(additions+deletions) asc` → `updatedAt asc`.

Skip `BLOCKED` and `isDraft=true` PRs (note them in the report).

---

## Step 3 — Per-PR Loop (repeat for each PR up to cap)

### 3a — Intake

Write `proof/<RUN_ID>/PR_<num>/INTAKE.json`:
```json
{
  "number": <num>,
  "title": "...",
  "classification": "CI_ONLY",
  "diffstat": {"additions": 0, "deletions": 0},
  "ci_failing_jobs": [],
  "conflicts": false,
  "unresolved_comments": [],
  "review_decision": "..."
}
```

Write `proof/<RUN_ID>/PR_<num>/BLOCKERS.json` with specific failure details:
- For CI: job name, step name, first error line from logs
- For conflicts: conflicting files
- For comments: comment author, file, line, body

Log `PR_SELECTED` to conport.

### 3b — Worktree Setup

```bash
# Fetch PR head
gh pr checkout <num> --force

# Verify clean state (G9)
git status --porcelain
# If not empty: STOP

# Create fix branch
git checkout -b fix/pr-<num>-drain-<RUN_ID>
```

### 3c — Fix Loop (G3: minimal change only)

**If CI_ONLY:**
```bash
# Get failing job logs
gh run list --branch <PR_HEAD_BRANCH> --limit 1 --json databaseId
gh run view <run_id> --log-failed
# Apply minimum fix targeting the specific failure
# Commit: "ci-fix: <brief description> (drain/<RUN_ID>)"
```

**If CONFLICTS_ONLY:**
```bash
# Rebase base branch into PR branch
git fetch origin <BASE_BRANCH>
git rebase origin/<BASE_BRANCH>
# Resolve conflicts — prefer PR-branch intent, not base
# Run relevant tests to confirm resolution is correct
# Commit: "conflict-resolution: rebase on <BASE_BRANCH> (drain/<RUN_ID>)"
```

**If COMMENTS_ONLY:**
- Address comments one-by-one in file order
- For each comment: smallest change that satisfies the request
- Ask user if a comment is ambiguous (one question per blocker pass)
- Commit: `"review-response: address <N> comments (drain/<RUN_ID>)"`

**If MIXED:** apply fixes in order: conflicts → CI → comments.

Append every command (with stdout/stderr) to:
`proof/<RUN_ID>/PR_<num>/COMMANDS_RUN.txt`

### 3d — Validation (G4)

```bash
# Run tests relevant to changed files
# (use git diff --name-only to find changed files, then run their test suites)

# PAL precommit check (via MCP)
# Call pal_precommit tool or equivalent

# PAL challenge (via MCP)
# Call pal_challenge tool or equivalent
```

Write `proof/<RUN_ID>/PR_<num>/VALIDATION.md`:
- Test results (pass/fail counts, any failures)
- Precommit result
- Challenge result
- Overall: `PASS` or `FAIL`

If FAIL: write `proof/<RUN_ID>/PR_<num>/FAILURE.md` and move on to next PR
(do not push broken code).

Log `CI_GREEN` or `FIX_APPLIED` to conport.

### 3e — Push + PR Update

```bash
git push origin fix/pr-<num>-drain-<RUN_ID> --force-with-lease

# Update PR head to the fix branch (or push to original PR branch if preferred)
gh pr edit <num> --head fix/pr-<num>-drain-<RUN_ID>

# Request re-review if review comments were addressed
# gh pr review --request <reviewer> <num>
```

Wait for CI (up to `CI_WAIT_SECONDS=120` polling `gh run list`).
If CI times out: write `MERGE_READY` with note "CI pending" and move on.

### 3f — Merge Decision (G5)

Check all gates:
```bash
gh pr view <num> --json mergeable,reviewDecision,statusCheckRollup
```

**If all green AND `actually_merge=yes`:**
```bash
gh pr merge <num> --<merge_method> --delete-branch --auto
```
Log `MERGED` to conport.

**If not mergeable OR `actually_merge=no`:** write `MERGE_READY` evidence:
- Current CI status
- Review decision
- What still needs to happen (approvals needed, policy blockers)

Log `MERGE_READY` to conport.

### 3g — Proof Bundle

Write `proof/<RUN_ID>/PR_<num>/PROOF_BUNDLE.md`:

```markdown
# PR <num> Proof Bundle — <RUN_ID>

## Classification
<class> — <reason>

## Blockers Found
<list>

## Actions Taken
<commands from COMMANDS_RUN.txt, summarized>

## Validation
<PASS / FAIL + details>

## Outcome
MERGED | MERGE_READY | SKIPPED

## Evidence
- INTAKE.json: present
- BLOCKERS.json: present
- COMMANDS_RUN.txt: present
- CI_SUMMARY.md: present
- VALIDATION.md: present
```

---

## Step 4 — Final Report

Write `proof/<RUN_ID>/QUEUE_REPORT.md`:
```markdown
# PR Drain Report — <RUN_ID>

## Summary
- PRs processed: N
- Merged: N
- MERGE_READY: N
- Skipped/Blocked: N

## Top-3 Blocker Reasons
1. ...
2. ...
3. ...

## PRs Not Processed (over cap or BLOCKED)
- ...

## Next Actions
- ...
```

Log `RUN_COMPLETE` to conport.

Print the `QUEUE_REPORT.md` contents as the final response.

---

## Hard Stop Conditions

At any point, if you encounter:
- Missing required tool (gh, MCP namespace)
- `git status --porcelain` non-empty at a gate check
- Validation FAIL with no clear fix
- Ambiguous reviewer comment that would require a design decision

→ **Write `proof/<RUN_ID>/FAILURE.md`, emit STOP + reason, do not proceed.**

---

## Notes on MCP Tool Names

Based on the project's `.vibe/config.toml`, MCP server names and their tool
prefixes are:

| Server name in config | Tool prefix     |
| --------------------- | --------------- |
| `conport`             | `conport_`      |
| `serena`              | `serena_`       |
| `dope_context`        | `dope_context_` |
| `pal`                 | `pal_`          |

If a tool call fails with "Unknown tool", that MCP server is not reachable.
Treat as a G0 failure and log to `FAILURE.md`.
