---
id: TP-DMX-MCPPROF-001
title: Tp Dmx Mcpprof 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-23'
last_review: '2026-08-23'
next_review: '2026-11-21'
prelude: Tp Dmx Mcpprof 001 (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: TP-DMX-MCPPROF-001
## Profile-Selected MCP Tool Plane and Generic Repo-Domain Read Contract

**Status:** `DRAFT_READY_FOR_OPERATOR_REVIEW`
**Implementation authorized:** `false`
**Repository:** `DDD-Enterprises/dopemux-mvp`
**Series:** `SER-DMX-MCPPROF-001`
**Risk:** High
**Task class:** Architecture-sensitive, security-sensitive, API-sensitive
**Primary implementer:** Codex
**Fallback implementer:** Claude Code Sonnet
**Embedded auditor:** AGY/Antigravity Sonnet, then Claude Code Sonnet/Opus, then Gemini CLI
**Required final gate:** PR Steward

## 1. Objective

After operator acceptance of `ADR-DMX-MCPPROF-001`, implement deterministic profile-selected MCP generation and doctoring, official GitHub read profiles, Playwright CLI/MCP placement, locked tool inventories, and the generic repo-domain read-facade contract.

The packet must amend the existing accepted MCP integration architecture without creating a second catalog or weakening ADR-MCPINT-001, ADR-MCPINT-002, DCP facade, identity, actor-authentication, or proof gates.

## 2. Claim ledger

### OBSERVED

- `mcp_catalog.yaml` is the current MCP catalog authority.
- ADR-MCPINT-002 already decides generated agent exposure and the DCP read-only facade role.
- PAL HTTP is health-only and PAL stdio is the valid PAL MCP surface.
- Current catalog entries already carry scope, transport, plane, authority role, lifecycle, identity scope, agent matrix, and tool-snapshot metadata.

### PROPOSED

- Profiles become explicit projections inside the existing catalog.
- Generated configs require one named profile.
- The tool inventory/count/schema digest becomes checked-in evidence.
- `repo-domain-read` is a generic fixed-path local stdio extension, not arbitrary executable discovery.

### UNKNOWN

- Exact current renderer file set at execution time.
- Exact client compatibility for hosted versus local official GitHub MCP transport.
- Whether open PRs touch catalog/renderers/doctor surfaces.
- Whether the existing schema/tool-snapshot system can absorb profile digests without a new schema file.

### CONFLICTING

- Current human-facing docs may still describe PAL HTTP as available while catalog truth quarantines it.

## 3. Authority and precedence

1. Exact-head runtime code, config, tests, active entrypoints, open PRs, and GitHub state.
2. Current accepted ADRs, especially ADR-MCPINT-001/002 and DCP read-only exposure ADRs.
3. `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, system boundaries, service catalog.
4. MCP catalog/tool snapshots and generator docs.
5. This packet and proposed ADR.
6. Current official GitHub MCP, Playwright, Semgrep, and MCP SDK documentation.

If the proposed ADR conflicts with an accepted current ADR, stop with `BLOCKED_AUTHORITY_CONFLICT`.

## 4. Scope IN

- Add the proposed ADR and index entry.
- Extend the existing catalog model with explicit profiles.
- Add deterministic profile rendering and CLI selection.
- Emit visible tool inventory, counts, profile digest, and schema/tool digest.
- Add official GitHub MCP profile policy in read-only mode.
- Add Playwright, Context7, GPT Researcher, Semgrep, and PR Steward placement by profile without enabling global defaults.
- Add generic fixed-path `repo-domain-read` contract validation.
- Add profile-specific doctor and negative tests.
- Update current MCP profile/operator documentation.
- Produce proof and PR readiness artifacts.

## 5. Scope OUT

- Accepting the ADR on behalf of the operator.
- Exposing any new write-capable profile.
- Changing domain authority.
- Implementing dNh or adOps business tools.
- Remote/public ingress.
- Secrets, GitHub tokens, provider credentials, or populated private config.
- Rewriting ConPort, dope-memory, task-orchestrator, dope-context, Serena, PAL, or DCP facade internals.
- Opportunistic cleanup.
- Removing legacy config in external repos.

## 6. Invariants

1. `mcp_catalog.yaml` stays the catalog authority.
2. Every generated config selects an explicit profile.
3. There is no implicit/all fallback.
4. Profiles do not alter service authority.
5. Normal GitHub profiles are read-only.
6. PAL MCP resolves to stdio only.
7. Playwright MCP is absent from `core-*`.
8. Domain executable is fixed to `<repo-root>/scripts/mcp/domain-read`.
9. Domain manifest is fixed to `<repo-root>/mcp/domain-read-tools.json`.
10. Symlink/path escape, unknown repo identity, untracked executable, manifest mismatch, write/admin tool, or unknown side effect blocks exposure.
11. Tool inventory drift is explicit and deterministic.
12. Runtime write authorization and proof gates cannot be weakened.

## 7. Preflight and custody

Run from the primary checkout only to create a dedicated worktree:

```bash
set -euo pipefail
REPO=/Users/hue/code/dopemux-mvp
git -C "$REPO" fetch origin --prune
git -C "$REPO" status --short
git -C "$REPO" rev-parse --show-toplevel
git -C "$REPO" rev-parse origin/main
WT="$REPO/.worktrees/TP-DMX-MCPPROF-001"
BRANCH=feat/TP-DMX-MCPPROF-001-profiled-tool-plane
test ! -e "$WT"
git -C "$REPO" worktree add -b "$BRANCH" "$WT" origin/main
cd "$WT"
git status --short
git rev-parse HEAD
git rev-parse origin/main
```

Stop if the primary checkout is dirty in any path relevant to this packet, the worktree exists, branch exists unexpectedly, or HEAD does not equal the captured `origin/main` base.

Capture current open-PR state:

```bash
gh pr list --repo DDD-Enterprises/dopemux-mvp --state open --limit 100 \
  --json number,title,headRefName,baseRefName,headRefOid,updatedAt
```

For every open PR plausibly touching the allowlist, capture changed filenames before implementation. Stop if overlapping work is active and no explicit integration plan exists.

## 8. Required PAL chain

```text
apilookup
-> analyze
-> tracer (catalog -> renderer -> generated config -> doctor)
-> thinkdeep
-> challenge
-> planner
-> challenge
-> implementation in slices
-> testgen
-> secaudit
-> docgen after code stabilizes
-> codereview
-> precommit
-> challenge
```

No planner before MEDIUM confidence. No implementation before plan challenge. Final confidence must be VERIFIED.

## 9. Allowed paths

```text
docs/90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md
docs/90-adr/adr-index.md
mcp_catalog.yaml
src/dopemux/mcp/fleet_catalog.py
src/dopemux/commands/mcp_commands.py
src/dopemux/mcp/profile_policy.py
schemas/mcp-profile.schema.json
tests/unit/test_mcp_profile_policy.py
tests/unit/test_mcp_profile_rendering.py
tests/unit/test_mcp_profile_doctor.py
docs/02-how-to/mcp-profiles.md
.claude/mcp-system.md
task-packets/mcp-profiles/TP-DMX-MCPPROF-001.md
task-packets/mcp-profiles/TP-DMX-MCPPROF-001.json
proof/TP-DMX-MCPPROF-001/**
```

If exact-head tracing proves a different existing renderer or schema file must change, stop before editing and return `NEEDS_SUPERVISOR_ALLOWLIST_AMENDMENT` with the exact path and reason.

## 10. Commit-sized slices

### Slice 0: proposed ADR and collision audit

- Add the ADR as `proposed`.
- Update ADR index only.
- Prove it amends rather than duplicates ADR-MCPINT-001/002.
- No runtime/config changes.

**Gate:** operator acceptance is required before slice 1.

### Slice 1: profile contract and deterministic inventory

- Add profile schema/model inside the existing catalog flow.
- Add the initial profile definitions.
- Emit deterministic selected-server and visible-tool manifests with digests.
- Add unknown profile, duplicate tool, lifecycle-blocked server, and unexplained inventory drift negatives.

### Slice 2: renderer, CLI, and doctor

- Add explicit profile selection to generation/init surfaces.
- Add `profile list`, `profile show`, and profile-aware doctor output using the current CLI architecture.
- Ensure configs are generated, never hand edited.
- Default behavior must resolve to an explicitly named compatibility profile or fail with migration guidance; it must not expose all servers.

### Slice 3: official GitHub and specialized placement

- Use current official GitHub MCP documentation to select supported hosted or local transport per client.
- Enforce read-only and toolset allowlists for normal profiles.
- Place Playwright only in `ui-audit`.
- Place Context7 and GPT Researcher in separate research profiles.
- Place Semgrep/GitHub security reads in `security`.
- Place GitHub PR/review/thread/Actions reads in `pr-steward`.

### Slice 4: generic repo-domain-read contract

- Validate fixed executable and manifest paths.
- Verify repo identity, containment, regular/tracked file status, no symlink escape, tool schema digests, side-effect classifications, and result bounds.
- Omit/block the server when any check fails.
- Do not execute arbitrary repo-provided paths.

### Slice 5: docs, full validation, proof, audit, PR

- Align `.claude/mcp-system.md` with current catalog transport truth.
- Document profile selection, migration, and blocked states.
- Run full relevant tests and proof capture.
- Run embedded audit.
- Open/update PR and run PR Steward.

## 11. Exact validation commands

```bash
set -o pipefail
python -m json.tool schemas/mcp-profile.schema.json >/dev/null
uv run pytest -q \
  tests/unit/test_mcp_profile_policy.py \
  tests/unit/test_mcp_profile_rendering.py \
  tests/unit/test_mcp_profile_doctor.py
uv run pytest -q tests/unit -k 'mcp and (catalog or profile or render or doctor)'
uv run ruff check \
  src/dopemux/mcp/fleet_catalog.py \
  src/dopemux/mcp/profile_policy.py \
  src/dopemux/commands/mcp_commands.py \
  tests/unit/test_mcp_profile_policy.py \
  tests/unit/test_mcp_profile_rendering.py \
  tests/unit/test_mcp_profile_doctor.py
uv run mypy \
  src/dopemux/mcp/fleet_catalog.py \
  src/dopemux/mcp/profile_policy.py \
  src/dopemux/commands/mcp_commands.py
uv run dopemux mcp profile list
uv run dopemux mcp profile show core-code
uv run dopemux mcp profile show core-retrieval
uv run dopemux mcp doctor --profile core-code
uv run dopemux mcp doctor --profile ui-audit
pre-commit run --files \
  mcp_catalog.yaml \
  src/dopemux/mcp/fleet_catalog.py \
  src/dopemux/mcp/profile_policy.py \
  src/dopemux/commands/mcp_commands.py \
  schemas/mcp-profile.schema.json \
  tests/unit/test_mcp_profile_policy.py \
  tests/unit/test_mcp_profile_rendering.py \
  tests/unit/test_mcp_profile_doctor.py \
  docs/90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md \
  docs/02-how-to/mcp-profiles.md \
  .claude/mcp-system.md
git diff --check
git status --short
git diff --stat
git diff
```

Also execute a clean-room deterministic generation twice and byte-compare outputs. Use the exact current renderer command discovered during tracing; record it verbatim in proof before use.

## 12. Required negative validations

- unknown profile;
- profile without required lifecycle-active server;
- PAL HTTP selected as MCP;
- Playwright in `core-code`;
- GitHub write tool in a normal profile;
- ConPort admin tool in a non-admin profile;
- missing domain executable;
- untracked domain executable;
- symlink/path escape;
- malformed domain tool manifest;
- manifest tool classified write or unknown;
- tool digest mismatch;
- profile tool inventory increase without baseline update;
- attempted config generation with implicit `all`.

## 13. Proof requirements

Under `proof/TP-DMX-MCPPROF-001/` capture:

- `BASELINE.json`
- `FILES_INSPECTED.txt`
- `OPEN_PRS.json`
- `PAL_CHAIN.md`
- `PROFILE_INVENTORY.json`
- `PROFILE_DIGESTS.json`
- `NEGATIVE_TESTS.json`
- `COMMANDS.log`
- `EXIT_CODES.json`
- `TEST_RESULTS.txt`
- `LINT_TYPE_RESULTS.txt`
- `GIT_STATUS_BEFORE.txt`
- `GIT_STATUS_AFTER.txt`
- `GIT_DIFF_STAT.txt`
- `GIT_DIFF.patch`
- `AUDITOR_REPORT.json`
- `PROOF.json`
- `HANDOFF.json`
- `MERGE_READINESS.json` after PR Steward

Proof must conform to current proof and handoff contracts and be current to final head SHA.

## 14. Embedded audit

Required fields:

- `auditor_tool`
- `auditor_model`
- `invocation`
- `exit_code`
- `auditor_verdict`
- `auditor_findings`
- `fixes_applied_from_audit`
- `remaining_risks`
- `skip_reason`

Allowed verdicts: `PASS`, `PASS_WITH_RISKS`, `FAIL`, `NEEDS_SUPERVISOR`, `SKIPPED`. `SKIPPED`, `FAIL`, or `NEEDS_SUPERVISOR` blocks readiness.

Audit focus:

- profile/canonical-authority confusion;
- arbitrary executable/path injection;
- GitHub write leakage;
- profile/tool-count drift;
- renderer divergence;
- hidden all-tools fallback;
- Playwright or Desktop Commander exposure outside allowed profiles;
- PAL transport regression;
- stale proof.

## 15. PR Steward

PR Steward must harvest metadata, head SHA, changed files, commits, reviews, review comments, review threads, issue comments, bots, checks, and CI. Unknown reviewers/bots, unclassified items, unresolved blocking threads, failed/pending required checks, stale proof, or allowlist escape blocks `READY`.

## 16. Rollback

- Revert the packet commits in reverse slice order.
- Restore prior generated config behavior and catalog content.
- Remove new profile schema/model and docs.
- Regenerate the prior default config from the pre-packet base.
- Stop any profile-only test instance.
- Do not remove or alter existing MCP state stores.

## 17. Stop conditions

Stop immediately on:

- ADR not accepted before runtime slice;
- accepted ADR conflict;
- overlapping active PR without integration plan;
- required edit outside allowlist;
- secret or token material in diff/proof;
- arbitrary executable selection requirement;
- inability to prove GitHub read-only mode;
- profile generation nondeterminism;
- any write/admin tool in a normal profile;
- any durable side effect from a read-only validation;
- audit failure or PR Steward block.

## 18. Expected terminal response

Return:

1. objective status;
2. exact base and head SHA;
3. slices and commits;
4. files changed;
5. profile inventories and digests;
6. validation outputs and exit codes;
7. negative-test results;
8. audit report;
9. proof path;
10. PR URL;
11. PR Steward status;
12. remaining risks.
