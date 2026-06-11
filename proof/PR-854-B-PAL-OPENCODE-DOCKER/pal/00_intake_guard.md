# PAL-0 — Intake Guard

## stage
PAL-0 Intake Guard

## tool_or_mode
UNAVAILABLE_MANUAL_STAGE (Claude Sonnet — PAL MCP not available in this session)

## model
claude-sonnet-4-6

## inputs_read
- Task packet: DMX-DCP-PR854-B-PROOF-STEWARDSHIP-001-CC (user-provided)
- Preflight result: PASS (LOCAL_HEAD == PR_HEAD == 15f235b8c60c473c301713f6e2f6251a449d07cf)

## summary
This packet is PROOF REPAIR + RUNTIME EVIDENCE CAPTURE for PR #854.
It is NOT implementation, NOT runtime routing, NOT merge work.
All five B items must be proven or blocked by evidence collected from a live repo
checkout of the PR branch. No source/config edits are permitted.

## allowed_files
```
proof/PR-854-B-PAL-OPENCODE-DOCKER/**
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/COMMAND_LOG.md
proof/DMX-DCP-MODEL-ROUTING-MVP-0001/HANDOFF.md
```

## forbidden_files
```
.github/**
src/**
docker/**
services/**
scripts/**
config/**
.opencode/**
.claude/**
compose.yml
opencode.jsonc
AGENTS.md
mcp_catalog.yaml
Dockerfile (root-level)
```

## hard_stops
1. LOCAL_HEAD != PR_HEAD → BLOCKED (already passed preflight)
2. verify-pal.sh fails to fully pass → BLOCKED_VERIFY_PAL_FAIL
3. pal-stdio image fails to build → BLOCKED
4. stdin-attached test exits before 5 seconds → BLOCKED_PAL_STDIO_WITH_STDIN_FAIL
5. compose restart_count > 0 → BLOCKED_RESTART_LOOP
6. Critical/high CVEs not classified → BLOCKED
7. Forbidden file appears in diff → BLOCKED
8. Secret/env value printed → BLOCKED
9. Any merge/branch-protection command attempted → BLOCKED
10. dope-memory branch used as proof authority → BLOCKED_NEEDS_BRANCH_SEPARATION

## expected_proof_outputs
- COMMAND_LOG.md
- VERIFY_PAL.log
- PAL_STDIO_BUILD.log
- PAL_STDIO_WITH_STDIN.log
- PAL_STDIO_NO_STDIN.log
- PAL_STDIO_COMPOSE_RESTART_TEST.log
- DOCKER_SCOUT_CLASSIFICATION.md
- PR_STEWARD_LATEST_HEAD.md
- PROOF.json (PR-854-B dir)
- PAL_CHAIN.md
- pal/01_repo_pr_baseline.md through pal/08_final_handoff.md
- Updated proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json

## assumptions
- Docker is available and the pal-stdio Dockerfile path is correct
- gh CLI is authenticated
- No secrets are printed; all env lookups are structural only
- dope-memory MCP branch is NOT used as proof authority

## risks
- Docker Scout CLI may not be installed locally; will fall back to PR comment evidence
- compose pal-stdio may restart-loop if proxy exits on no stdin
- verify-pal.sh checks are structural (config wiring), not full runtime execution
- PAL MCP unavailable means challenge stage is same-tool (non-independent)

## confidence
high (preflight PASS, branch correctly checked out, all files inspectable)

## next_action
Proceed to PAL-1 (repo/PR baseline) — no hard stops triggered

## verdict
PASS
