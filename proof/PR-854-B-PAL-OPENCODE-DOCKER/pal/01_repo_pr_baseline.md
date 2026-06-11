# PAL-1 — Repo / PR Baseline

## stage
PAL-1 Repo/PR Baseline

## tool_or_mode
UNAVAILABLE_MANUAL_STAGE (Claude Sonnet — PAL MCP not available)

## model
claude-sonnet-4-6

## inputs_read
- git branch, rev-parse, status
- gh pr view 854 (full JSON)
- gh pr checks 854
- gh pr view 862 (summary)

---

## current_branch
OBSERVED: `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`

## local_head
OBSERVED: `15f235b8c60c473c301713f6e2f6251a449d07cf`

## pr_854_head
OBSERVED: `15f235b8c60c473c301713f6e2f6251a449d07cf`

## head_lock
OBSERVED: LOCAL_HEAD == PR_HEAD → **PASS**

## pr_state
OBSERVED: OPEN, NOT draft, MERGEABLE

## changed_files
OBSERVED: 102

## base_branch
OBSERVED: main

## pr_title
OBSERVED: "feat(dcp): DMX-DCP-MODEL-ROUTING-MVP-0001 domain model, OpenCode integration, and predecessor routing packets"

## pr_url
https://github.com/DDD-Enterprises/dopemux-mvp/pull/854

---

## pr_body_scope_assessment
OBSERVED: PR body explicitly states **combined scope**:
- DMX-DCP-MODEL-ROUTING-MVP-0001 domain model (9 schemas, 15 test fixtures)
- OpenCode integration + PAL stdio (B work): opencode.jsonc, start-pal.sh, verify-pal.sh, .opencode/agents/
- Predecessor routing packets (0000 through 0000I)
- Infra + security: .gitignore, compose.yml, .mcp.json, mcp_catalog.yaml, litellm CVE fix (d5e09bf3e)

OBSERVED: PR body explicitly states "Clean 0001 extracted to #862" — PR #862 is the clean 0001 carve.

OBSERVED: PR body notes runtime/security proofs for all 5 B items (described but not freshly captured via attached logs in current proof/ tree — that is what this packet repairs).

OBSERVED: PR body already states `merge_readiness: BLOCKED_NOT_REQUESTED`.

---

## ci_check_state (at head 15f235b8c)

### FAILING
| Check | Status | Note |
|---|---|---|
| `review / review` | **FAIL** | 3m54s — https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/27319152783/job/80706295934 |

### PASSING
| Check | Status |
|---|---|
| Analyze (js/ts/python/ruby) | PASS |
| Build adhd-engine, claude-brain, conport, dope-memory, dopecon-bridge, dopemux-backend, litellm, task-orchestrator, webhook-receiver | ALL PASS |
| Scout adhd-engine/claude-brain/conport/dope-memory/dopecon-bridge/dopemux-backend/litellm/task-orchestrator/webhook-receiver | ALL PASS |
| CodeQL | PASS |
| advisory check-only intake | PASS |
| checks | PASS |
| independent embedded audit | PASS |
| 🤖 Claude Code Security Analysis | PASS |
| 📊 ADHD-Friendly Security Summary | PASS |
| 💅 Code Quality & Linting | PASS |
| 🗺️ Model Routing Consistency | PASS |
| 🧪 Extractor Full/Smoke | PASS |

### SKIPPING
| Check | Status |
|---|---|
| debugger, review (orchestrator), invoke, plan-execute, dispatch (orchestrator) | SKIPPING |
| 📊 Scoped Coverage | SKIPPING |

---

## pr_862_reference
OBSERVED: PR #862 is OPEN (draft), MERGEABLE, on branch `dcp/model-routing-0001` at `a83f8e252`
Title: "DMX-DCP-MODEL-ROUTING-MVP-0001 domain model + dual independent audit (clean carve from #854)"
This confirms PR #862 is the clean 0001 carve reference.

---

## evidence_ledger
- branch: OBSERVED (git)
- local_head: OBSERVED (git rev-parse)
- pr_854_head: OBSERVED (gh pr view)
- mergeability: OBSERVED (gh pr view — MERGEABLE)
- draft_state: OBSERVED (gh pr view — isDraft=false)
- changed_files: OBSERVED (gh pr view — 102)
- pr_body_scope: OBSERVED (body text)
- failing_checks: OBSERVED (gh pr checks — review/review FAIL)
- pr_862_reference: OBSERVED (gh pr view 862)

---

## risks
- `review / review` check is FAILING at current head — this must be investigated and noted in proof
- PR body claims runtime proofs but no captured log files exist yet in proof/ for this head
- 102 changed files is a large mixed-scope PR — clean 0001 is in #862

## confidence
high

## next_action
Proceed to PAL-2 (evidence inventory) — investigate what files exist, verify-pal structure, Dockerfile paths

## verdict
BASELINE_CAPTURED — one failing check (review/review) noted, all Scout/Build PASS
