# 40_OPEN_PR_IMPACT_LEDGER

> This ledger is candidate-future-authority context only.
> No unmerged PR content is represented as current-main truth.

```yaml
captured_at: 2026-07-29T08:30:00Z
execution_base_sha: 414c7ac7f998d6eaec7cf7ae9ab431c0fac6476d
open_pr_count: 32
material_open_pr_count: 8
regeneration_required_if_any_material_pr_merges: true
```

## 1. Repository

`DDD-Enterprises/dopemux-mvp`, default branch `main`.

## 2. Watched Path Families

A PR is presumptively material if it touches any of:

```text
AGENTS.md
RULES.md
PROJECT.md
ARCHITECTURE.md
PM_PLANE.md
SERVICE_CATALOG.md
TRUTH_*.md
SYSTEM_*.md
docs/03-reference/governance/**
docs/03-reference/truth/**
docs/03-reference/systems/**
docs/03-reference/planes/**
docs/03-reference/spec/dopetask/**
docs/ops/embedded-audit.md
docs/ops/pr-steward.md
schemas/proof/**
schemas/pr_steward/**
config/runtime_authority_manifest.json
scripts/verify_runtime_authority.py
config/ai/model-routing.policy.yaml
docs/90-adr/**
tools/pr_steward/**
src/dopemux_pr_merge_specialist/**
src/dopemux/dcp/**
src/dopemux/mcp/**
mcp_catalog.yaml
schemas/mcp/**
services/repo-truth-extractor/**
services/dope-context/**
services/task-orchestrator/**
services/dopecon-bridge/**
services/working-memory-assistant/**
src/conport/**
```

Touching a watched path is a trigger for review, not automatic proof of impact.

## 3. Per-PR Ledger

### PR #1113 -- deps(deps): bump next from 15.5.18 to 15.5.21

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1113
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/npm_and_yarn/next-15.5.21`
- Head SHA: `bf6cf155d1ad764f8a9479f0988bc3066a5ceb24`
- Merge-state status: BEHIND
- Updated: 2026-07-26T11:27:34Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot next.js 15.5.18->15.5.21 patch bump; 2 files. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `package-lock.json`
    - `package.json`

### PR #1115 -- fix(security): bump pyasn1 to 0.6.4 (recreates #1090 on current main)

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1115
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `fix/security-pyasn1-0.6.4-current-main`
- Head SHA: `396c32013ea91552d08677b245c1b5739b2d2264`
- Merge-state status: BEHIND
- Updated: 2026-07-26T11:27:18Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot pyasn1 0.6.4 security bump; 2 files. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `docker/mcp-servers-source/pal/pal-mcp-server/uv.lock`
    - `uv.lock`

### PR #1117 -- fix(deps): consolidate safe UI patch dependencies (#1094, #1108, #1109)

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1117
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `fix/ui-dashboard-deps-consolidation`
- Head SHA: `350123f5bb058e5f195349f0197a128416392201`
- Merge-state status: BEHIND
- Updated: 2026-07-26T11:27:14Z
- Changed-file count: 1 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: 1 file changed (UI dashboard dependency consolidation), mergeStateStatus=UNKNOWN/BEHIND. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `ui-dashboard/package-lock.json`

### PR #1118 -- fix(ci): align container build matrix for adhd-dashboard (recreates #1107)

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1118
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `fix/container-ci-matrix-adhd-dashboard`
- Head SHA: `d13b4aacc9765384e598ef950bb4c9acd9954697`
- Merge-state status: BEHIND
- Updated: 2026-07-26T11:27:08Z
- Changed-file count: 1 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: 1 file changed (CI container build matrix), mergeStateStatus=UNKNOWN/BEHIND. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `.github/workflows/containers.yml`

### PR #1123 -- fix(rte): R3-009/R3-010 F-30 boundary + F-23 residual closure (v5)

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1123
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `claude/rte-audit-improvement-f4beb7`
- Head SHA: `0181fc9e8bd79b208a1f25cf56db757b90a080a4`
- Merge-state status: DIRTY
- Updated: 2026-07-26T22:03:05Z
- Changed-file count: 16206 (capture_complete: False)
- **Classification: SUPERSEDED_OR_CONFLICTING**
- Evidence: mergeStateStatus=DIRTY. changedFiles=16206, additions=5,145,096, deletions=9,284 -- two to three orders of magnitude larger than any other open PR, consistent with a prior session's durable finding (reference_rte_stranded_branch_2026_07_26.md) that this exact branch (claude/rte-audit-improvement-f4beb7) is 4146 commits ahead / 4221 behind main with a merge-base dated 2025-09-19, i.e. a long-diverged, effectively stranded lineage rather than a clean forward delta. Full path-level file capture was NOT attempted for this PR (capture_complete=false, disclosed) -- classification rests on these aggregate scale/state metrics, not path intersection, since re-litigating the stranded-branch finding from scratch is out of this packet's scope.
- Current-main effect: None; PR is unmerged and not a safe merge candidate in its current form.
- Action if merged: Not applicable in current form -- this branch would need to be rebased or its recoverable commits cherry-picked onto current main (per the prior session's recovery note: 160/193 of its changed paths are present on main) before any merge could be evaluated for source-set impact.
- Source slots affected: none
- Contradiction/overlap notes: Shares problem domain (RTE truth/audit remediation) with #1136 and #1155, which are the actively-maintained, clean-lineage successors; #1136/#1155 should be treated as authoritative for that domain, not #1123.
- Confidence: high
- Sample changed paths:
    - `.Jules/palette.md`
    - `.antigravitycli/8045acdf-ddc1-4770-9e5f-66a542feed87.json`
    - `.antigravitycli/c1be0ae4-af24-4184-9a66-bb7ce6372872.json`
    - `.backup_location`
    - `.claude.json`
    - `.claude.json.template`
    - `.claude/AGENT_ARCHITECTURE.md`
    - `.claude/MULTI_LANGUAGE_SUPPORT.md`
    - `.claude/PRIMER.md`
    - `.claude/PROJECT_INSTRUCTIONS.md`
    - `.claude/README.md`
    - `.claude/SESSION_STATE_MCP_ORCHESTRATOR.md`
    - `.claude/SYNERGISTIC_WORKFLOWS.md`
    - `.claude/WORKTREE_MCP_SETUP.md`
    - `.claude/agents/_index.md`

### PR #1127 -- docs(ltaip): import full macro-packet series and load-plan artifacts

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1127
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `docs/ltaip-full-packet-import`
- Head SHA: `5bcadcb59427a5f1094d3bc0ed0e94de9ed9a74f`
- Merge-state status: BEHIND
- Updated: 2026-07-29T06:04:19Z
- Changed-file count: 34 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: mergeStateStatus=UNKNOWN/BEHIND. All 33 changed files are under docs/ops/load-plans/**, reports/leantime-ai-parity/**, schemas/leantime-ai-parity/**, scripts/leantime-ai-parity/**, task-packets/leantime-ai-parity/**, and tests/prototypes/leantime-ai-parity/**. None intersect the 37 selected slots or the watched-path list.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `docs/ops/load-plans/load_plan-LTAIP-H0.json`
    - `docs/ops/load-plans/ltaip-h0-load-instructions.md`
    - `docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json`
    - `docs/ops/load-plans/task_orchestrator_task_tree-LTAIP-H0.json`
    - `docs/ops/load-plans/task_orchestrator_v3_advisory-LTAIP-H0.json`
    - `reports/leantime-ai-parity/task-orchestrator-load-receipts.json`
    - `schemas/leantime-ai-parity/task-orchestrator-rest-epics.schema.json`
    - `scripts/leantime-ai-parity/load_task_orchestrator.py`
    - `task-packets/generated/TP-PR1127-CI-001.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-001.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-001.md`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-002.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-002.md`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-003.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-003.md`

### PR #1128 -- feat(mcp): profile-selected tool plane and repo-domain read contract

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1128
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `feat/TP-DMX-MCPPROF-001-profiled-tool-plane`
- Head SHA: `e41d134b5b0f32b5475ab5f094274bfac2259601`
- Merge-state status: DIRTY
- Updated: 2026-07-27T00:49:18Z
- Changed-file count: 40 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: mergeStateStatus=DIRTY/UNKNOWN across captures. Touches mcp_catalog.yaml, schemas/mcp/fleet-catalog.schema.json, src/dopemux/mcp/*, docs/90-adr/adr-index.md, docs/90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md (a different ADR from the Memory Trinity ADR in slot 11). None of these paths intersect the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `.claude/mcp-system.md`
    - `docs/02-how-to/mcp-profiles.md`
    - `docs/90-adr/adr-index.md`
    - `docs/90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md`
    - `mcp_catalog.yaml`
    - `mcp_tool_surfaces.json`
    - `proof/TP-DMX-MCPPROF-001/AUDITOR_REPORT.json`
    - `proof/TP-DMX-MCPPROF-001/AUDITOR_REPORT.md`
    - `proof/TP-DMX-MCPPROF-001/BASELINE.json`
    - `proof/TP-DMX-MCPPROF-001/COMMANDS.log`
    - `proof/TP-DMX-MCPPROF-001/EXIT_CODES.json`
    - `proof/TP-DMX-MCPPROF-001/FILES_INSPECTED.txt`
    - `proof/TP-DMX-MCPPROF-001/GIT_DIFF.patch`
    - `proof/TP-DMX-MCPPROF-001/GIT_DIFF_STAT.txt`
    - `proof/TP-DMX-MCPPROF-001/GIT_STATUS_AFTER.txt`

### PR #1136 -- refactor(rte): RTE-TRUTH audit + remediation waves R0/R1/R3/R4

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1136
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `claude/rte-truth-program`
- Head SHA: `5f52cad52275c563567201d6377a750b8475baa3`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:46:50Z
- Changed-file count: 366 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: mergeStateStatus=BEHIND (rebasable, not conflicted). Full paginated changedFiles=366 (captured via `gh api .../pulls/1136/files --paginate`, not the 100-file-capped `gh pr view --json files`; capture count verified to equal the PR's own reported changedFiles=366 exactly). Directly touches docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md (slot 23) plus extensive services/repo-truth-extractor/** runtime, config/pricing.yaml, and CI workflow changes.
- Current-main effect: None; PR is unmerged.
- Action if merged: Regenerate slot 23 from the new main tip; re-run all validation gates.
- Source slots affected: [23]
- Contradiction/overlap notes: Same problem domain (RTE truth/audit remediation) as #1123 and the narrower #1155, but #1136 is the clean, rebasable, actively-updated branch while #1123 is a massively diverged, DIRTY, likely-abandoned predecessor lineage -- see #1123 classification.
- Confidence: high
- Sample changed paths:
    - `.github/workflows/ci-complete.yml`
    - `.gitignore`
    - `.pre-commit-config.yaml`
    - `claudedocs/rte-truth-program-2026-07/A1-architecture.md`
    - `claudedocs/rte-truth-program-2026-07/A2-cost-truthfulness.md`
    - `claudedocs/rte-truth-program-2026-07/A3a-prompts-ABC.md`
    - `claudedocs/rte-truth-program-2026-07/A3b-prompts-DEGHM.md`
    - `claudedocs/rte-truth-program-2026-07/A3c-prompts-QRST.md`
    - `claudedocs/rte-truth-program-2026-07/A3d-prompts-WXZ-promptgen.md`
    - `claudedocs/rte-truth-program-2026-07/A4-cli-ux-docs.md`
    - `claudedocs/rte-truth-program-2026-07/A5-ops-gates-proof.md`
    - `claudedocs/rte-truth-program-2026-07/A6-fresh-eyes.md`
    - `claudedocs/rte-truth-program-2026-07/A7-legacy-refgraph.md`
    - `claudedocs/rte-truth-program-2026-07/CONSOLIDATED-FINDINGS.md`
    - `config/pricing.yaml`

### PR #1137 -- DMX-DCP-MODEL-ROUTING-MVP-0000R: Current-Main Runtime and Toolchain Reconciliation

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1137
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0000r-runtime-reconcile`
- Head SHA: `5de3f0ef56dfcf8545c395418b4a3d424b1bc249`
- Merge-state status: BEHIND
- Updated: 2026-07-27T03:19:24Z
- Changed-file count: 42 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft PR, mergeStateStatus=BEHIND. Touches docs/03-reference/dcp/current-main-runtime-reconciliation.{json,md} and proof/task-packets artifacts. docs/03-reference/dcp/** is not in the watched-path list and does not intersect any of the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Predecessor/companion of #1138 in the same DCP model-routing series lineage.
- Confidence: high
- Sample changed paths:
    - `docs/03-reference/dcp/current-main-runtime-reconciliation.json`
    - `docs/03-reference/dcp/current-main-runtime-reconciliation.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.attempt1.incomplete.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.raw.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.stderr.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/CURRENT_MAIN_RUNTIME_RECONCILIATION.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/CURRENT_MAIN_RUNTIME_RECONCILIATION.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/FINAL_STATUS_PORCELAIN.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/HANDOFF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/HANDOFF.md`

### PR #1138 -- DMX-DCP-MODEL-ROUTING-MVP-0000S: Series lineage and authority map

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1138
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0000s-series-lineage`
- Head SHA: `3ce0db080527d64eeb3849e88786528422885333`
- Merge-state status: BEHIND
- Updated: 2026-07-27T03:23:41Z
- Changed-file count: 63 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft PR, mergeStateStatus=UNKNOWN/BEHIND across captures. Touches docs/03-reference/dcp/model-routing-series-map.json, docs/03-reference/dcp/model-routing-series-status.md, and proof/task-packets artifacts under DMX-DCP-MODEL-ROUTING-MVP-0000R/0000S. docs/03-reference/dcp/** is not in the watched-path list and does not intersect any of the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Overlaps in subject matter with #1137 (same DCP model-routing series, same base proof directory DMX-DCP-MODEL-ROUTING-MVP-0000R); both draft, no conflict evidence found between them.
- Confidence: high
- Sample changed paths:
    - `docs/03-reference/dcp/current-main-runtime-reconciliation.json`
    - `docs/03-reference/dcp/current-main-runtime-reconciliation.md`
    - `docs/03-reference/dcp/model-routing-series-map.json`
    - `docs/03-reference/dcp/model-routing-series-status.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.attempt1.incomplete.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.raw.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/AUDITOR_REPORT.stderr.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/CURRENT_MAIN_RUNTIME_RECONCILIATION.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/CURRENT_MAIN_RUNTIME_RECONCILIATION.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0000R/FINAL_STATUS_PORCELAIN.txt`

### PR #1140 -- fix(pr-steward): support solo org members in exact-head authorization

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1140
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `fix/pr-steward-solo-owner-org-member`
- Head SHA: `232fb713fbb927ead17ba2ead2cd1136ad3a5deb`
- Merge-state status: BEHIND
- Updated: 2026-07-27T04:43:23Z
- Changed-file count: 18 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Touches docs/90-adr/adr-dmx-prsteward-soloowner-001.md and tools/pr_steward/solo_owner_security_release.py (18 files total). The touched ADR falls under the ledger's own watched docs/90-adr/** family but is confirmed to be a different file from the Memory Trinity ADR selected as slot 11 (docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md) -- it is not itself a candidate for any of the 37 selected slots. Slot 32 (docs/ops/pr-steward.md) was grep-checked for 'solo'/'org member'/'exact-head'/'authoriz' and contains no matching content describing this mechanic, so its accuracy is unaffected by this PR merging.
- Current-main effect: None.
- Action if merged: None required for the selected 37-source set; re-check docs/ops/pr-steward.md wording only if a future edit adds solo-owner authorization language.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: medium
- Sample changed paths:
    - `docs/90-adr/adr-dmx-prsteward-soloowner-001.md`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/AUDITOR_REPORT.md`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/BASELINE_HEAD.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/BRANCH.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/EXIT_CODES.json`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/FILES_CHANGED.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/GIT_DIFF.patch`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/GIT_DIFF_STAT.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/GIT_STATUS_BEFORE.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/PROOF.json`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/review_bundle/AGY_AUDIT_RAW.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/review_bundle/AUDIT_INPUT.md`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/review_bundle/CLAUDE_AUDIT_RAW.txt`
    - `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/review_bundle/GEMINI_AUDIT_RAW.txt`
    - `task-packets/pr-steward/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001.md`

### PR #1142 -- deps(deps-dev): bump postcss from 8.5.15 to 8.5.18

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1142
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/npm_and_yarn/postcss-8.5.18`
- Head SHA: `5126f254275adce3621a1d9c5b24288678e8b95e`
- Merge-state status: BEHIND
- Updated: 2026-07-27T07:31:28Z
- Changed-file count: 1 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot postcss 8.5.15->8.5.18 bump; 1 file. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `package-lock.json`

### PR #1143 -- chore(deps): bump the npm_and_yarn group across 1 directory with 3 updates

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1143
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/npm_and_yarn/ui-dashboard/npm_and_yarn-d3bc4254df`
- Head SHA: `8147bf929910592088df771d1f92a782d8a5ad62`
- Merge-state status: BEHIND
- Updated: 2026-07-27T07:32:02Z
- Changed-file count: 3 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot npm_and_yarn group bump for ui-dashboard (3 updates); 3 files. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `ui-dashboard/package-lock.json`
    - `ui-dashboard/package.json`
    - `ui-dashboard/pnpm-lock.yaml`

### PR #1144 -- deps(deps): bump the python-minor-patch group with 40 updates

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1144
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/uv/python-minor-patch-2b653c8b3a`
- Head SHA: `cd1689667ff50fd32979dd7a4fc9212f54eb2042`
- Merge-state status: BEHIND
- Updated: 2026-07-27T16:29:41Z
- Changed-file count: 3 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot python-minor-patch group bump (40 updates); 3 files. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `pyproject.toml`
    - `ui-dashboard-backend/requirements.txt`
    - `uv.lock`

### PR #1145 -- deps(deps): bump google-genai from 1.69.0 to 2.14.0

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1145
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/uv/google-genai-2.14.0`
- Head SHA: `b6e686757fdb23b78861586c49adb42c4a3ce262`
- Merge-state status: BEHIND
- Updated: 2026-07-27T16:29:57Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot google-genai 1.69.0->2.14.0 bump; 2 files. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `pyproject.toml`
    - `uv.lock`

### PR #1146 -- deps(deps-dev): bump setuptools from 82.0.1 to 83.0.0

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1146
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/uv/setuptools-83.0.0`
- Head SHA: `eb2bfdce946995fff025831bc499fae33fe686cc`
- Merge-state status: BEHIND
- Updated: 2026-07-27T16:30:05Z
- Changed-file count: 1 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot setuptools 82.0.1->83.0.0 bump; 1 file. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `pyproject.toml`

### PR #1147 -- deps(deps): bump the javascript-minor-patch group with 9 updates

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1147
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/npm_and_yarn/javascript-minor-patch-6ddac0c4e4`
- Head SHA: `abbf2e7e3a58386c44232e594b5329de59392e4b`
- Merge-state status: BEHIND
- Updated: 2026-07-28T16:06:45Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot javascript-minor-patch group bump (9 updates); 2 files. No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `package-lock.json`
    - `package.json`

### PR #1148 -- deps(deps): bump next from 15.5.18 to 16.2.12

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1148
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `dependabot/npm_and_yarn/next-16.2.12`
- Head SHA: `6c37e3515541af3479fcf901675b28c05aef50c2`
- Merge-state status: BEHIND
- Updated: 2026-07-28T16:07:48Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot next.js 15.5.18->16.2.12 bump; 2 files (package manifest/lock). No intersection with watched paths.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `package-lock.json`
    - `package.json`

### PR #1149 -- 🎨 Palette: Add descriptive tooltip to task start button

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1149
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `jules-10223693338927440299-c662ce23`
- Head SHA: `9f2f089dd5e43387ba029c8f5c9de312899dceb3`
- Merge-state status: BEHIND
- Updated: 2026-07-28T23:25:37Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: 2 changed files, UI palette tooltip copy change (jules-authored). No intersection with watched paths or selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: None.
- Confidence: high
- Sample changed paths:
    - `ui-dashboard/src/components/TaskSequencer.tsx`
    - `ui-dashboard/src/components/__tests__/Accessibility.test.tsx`

### PR #1150 -- MCP fleet: multi-instance design (supervisor-ruled) + P-22/P-23 safe-subset implementation

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1150
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `claude/mcp-multi-instance-design-d706d6`
- Head SHA: `ad1fe43ed7dca30e3f9af7fa555b87b4406bce30`
- Merge-state status: CLEAN
- Updated: 2026-07-29T08:25:16Z
- Changed-file count: 77 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Draft PR, mergeStateStatus=BEHIND (was UNSTABLE at earlier capture; state has since changed but content intersection is unchanged). Refreshed changed-file list (59 files, was 56/56 at two earlier captures) still directly includes AGENTS.md, docs/03-reference/systems/dopemux/system-dopemux.md, and docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md -- exactly slots 01, 15, 17 of this package.
- Current-main effect: None; PR is unmerged and draft.
- Action if merged: Regenerate slots 01, 15, 17 from the new main tip and re-run all validation gates.
- Source slots affected: [1, 15, 17]
- Contradiction/overlap notes: None observed.
- Confidence: high
- Sample changed paths:
    - `.claude/claude.md`
    - `.claude/hooks/mcp_health_probe.py`
    - `.github/copilot-instructions.md`
    - `.vibe/config.toml`
    - `AGENTS.md`
    - `INSTALL.md`
    - `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md`
    - `claudedocs/mcp-fleet-multi-instance-evidence-2026-07-28.md`
    - `claudedocs/mcp-legacy-launch-path-worklist-2026-07-28.md`
    - `compose/legacy/conport-kg-docker-compose.yml`
    - `compose/legacy/leantime-overlay-docker-compose.yml`
    - `docker/mcp-servers-source/SERVER_REGISTRY.md`
    - `docker/mcp-servers-source/setup-task-orchestrator.sh`
    - `docker/mcp-servers-source/start-all-mcp-servers.sh`
    - `docker/mcp-servers-source/start-profile.sh`

### PR #1151 -- feat(dcp): trusted input capability boundary — DMX-DCP-MODEL-ROUTING-MVP-0007I

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1151
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0007i-trusted-input`
- Head SHA: `e36dda5cc51afe663150ada6bfae28e1c35c4f7f`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:05:38Z
- Changed-file count: 17 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft, mergeStateStatus=BEHIND. Touches src/dopemux/dcp/__init__.py, input_adapters.py (17 files total) -- DCP trusted-input capability boundary feature work; no intersection with the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: First PR in the DCP model-routing-0007/0008/0009 series (0007I, followed by 0007T/#1153, 0007A/#1154, 0008/#1156, 0009/#1157).
- Confidence: high
- Sample changed paths:
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/FINAL_STATUS_PORCELAIN.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/HANDOFF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/HANDOFF.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/PAL_CHAIN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/PROOF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/SECURITY_BOUNDARY_REVIEW.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/TRUSTED_INPUT_DESIGN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/TRUSTED_INPUT_TEST_MATRIX.json`
    - `src/dopemux/dcp/__init__.py`
    - `src/dopemux/dcp/input_adapters.py`

### PR #1153 -- test(dcp): trusted-input adversarial corpus — 0007T

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1153
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0007t-adversarial-tests`
- Head SHA: `dfa01bf12f01b924cd96d2ea483f166b81f73d1d`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:06:46Z
- Changed-file count: 34 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft, mergeStateStatus=BEHIND. Touches src/dopemux/dcp/__init__.py, input_adapters.py (34 files total, mostly test corpus) -- DCP trusted-input adversarial test corpus; no intersection with the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Companion test PR for #1151 in the same DCP model-routing-0007 series.
- Confidence: high
- Sample changed paths:
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/FINAL_STATUS_PORCELAIN.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/HANDOFF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/HANDOFF.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/PAL_CHAIN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/PROOF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/SECURITY_BOUNDARY_REVIEW.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/TRUSTED_INPUT_DESIGN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/TRUSTED_INPUT_TEST_MATRIX.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007T/ADVERSARIAL_CORPUS.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007T/AUDITOR_REPORT.md`

### PR #1154 -- feat(dcp): trusted adapter registry (disabled) — 0007A

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1154
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0007a-adapter-registry`
- Head SHA: `ca487efd253e0399ffee28ec2aa39d07c4335a5b`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:07:53Z
- Changed-file count: 50 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft, mergeStateStatus=BEHIND. Touches src/dopemux/dcp/__init__.py, input_adapters.py, trusted_adapter_registry.py (50 files total) -- DCP trusted-adapter-registry (disabled) feature work; no intersection with the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Part of the same DCP model-routing-0007 series as #1151/#1153/#1156/#1157.
- Confidence: high
- Sample changed paths:
    - `config/dcp/trusted_input_adapters.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/ADAPTER_REGISTRY_POLICY.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/FINAL_STATUS_PORCELAIN.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/HANDOFF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/HANDOFF.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/PAL_CHAIN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/PROOF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/DIFF_NAME_ONLY.txt`

### PR #1155 -- fix(rte): surface tree-sitter degraded mode

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1155
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `codex/tp-rte-truth-r0-005-tree-sitter-degraded`
- Head SHA: `c05d8c062a40b2d3a1a9485ef239b433b659650b`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:08:54Z
- Changed-file count: 7 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Draft, mergeStateStatus=BEHIND. Touches services/repo-truth-extractor/lib/prescan/code_intelligence_report.py, code_prescan.py, engine.py, and tests/test_code_prescan_truthfulness.py (7 files) -- a narrower RTE prescan fix (tree-sitter degraded-mode surfacing) in the same runtime family slot 23 (system-repotruthextractor.md) describes.
- Current-main effect: None; PR is unmerged.
- Action if merged: Re-verify slot 23 content against the new RTE prescan behavior and regenerate if drift is found.
- Source slots affected: [23]
- Contradiction/overlap notes: Same RTE runtime family as #1136 (broader remediation program) and #1123 (superseded predecessor); this one is narrowly scoped to tree-sitter degraded-mode handling specifically.
- Confidence: medium
- Sample changed paths:
    - `proof/TP-RTE-TRUTH-R0-005/AUDITOR_REPORT.md`
    - `proof/TP-RTE-TRUTH-R0-005/PROOF.json`
    - `services/repo-truth-extractor/lib/prescan/code_intelligence_report.py`
    - `services/repo-truth-extractor/lib/prescan/code_prescan.py`
    - `services/repo-truth-extractor/lib/prescan/engine.py`
    - `services/repo-truth-extractor/tests/test_code_prescan_truthfulness.py`
    - `task-packets/TP-RTE-TRUTH-R0-005.json`

### PR #1156 -- feat(dcp): inert backend runner contract — 0008

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1156
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0008-runner-contract`
- Head SHA: `b0e8b750874be1a4146aa15cbff2e0fc62c02192`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:09:14Z
- Changed-file count: 66 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft, mergeStateStatus=BEHIND. Touches src/dopemux/dcp/__init__.py, input_adapters.py, runner_contract.py, trusted_adapter_registry.py (66 files total) -- DCP inert-backend-runner-contract feature work; no intersection with the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Predecessor of #1157 in the same DCP series.
- Confidence: high
- Sample changed paths:
    - `config/dcp/trusted_input_adapters.json`
    - `docs/03-reference/dcp/backend-runner-contract.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/ADAPTER_REGISTRY_POLICY.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/FINAL_STATUS_PORCELAIN.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/HANDOFF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/HANDOFF.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/PAL_CHAIN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/PROOF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007I/COMMAND_LOG.md`

### PR #1157 -- feat(dcp): runner capability registry (invocation disabled) — 0009

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1157
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `dcp/model-routing-0009-runner-capabilities`
- Head SHA: `40224403cba6411ea79156572710b8b13b5e5cb9`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:11:21Z
- Changed-file count: 84 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft, mergeStateStatus=BEHIND. Touches src/dopemux/dcp/__init__.py, input_adapters.py, runner_capability_registry.py, runner_contract.py, trusted_adapter_registry.py (84 files total) -- DCP runner-capability-registry feature work; src/dopemux/dcp/** is a watched-path family but none of the 37 selected slots is a DCP source file.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Part of the same DCP model-routing-0007/0008/0009 series as #1151/#1153/#1154/#1156.
- Confidence: high
- Sample changed paths:
    - `config/dcp/runner_capabilities.json`
    - `config/dcp/trusted_input_adapters.json`
    - `docs/03-reference/dcp/backend-runner-contract.md`
    - `docs/03-reference/dcp/runner-capability-matrix.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/ADAPTER_REGISTRY_POLICY.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/AUDITOR_REPORT.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/COMMAND_LOG.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/DIFF_NAME_ONLY.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/DIFF_STAT.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/EVIDENCE_LEDGER.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/FINAL_STATUS_PORCELAIN.txt`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/HANDOFF.json`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/HANDOFF.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/PAL_CHAIN.md`
    - `proof/DMX-DCP-MODEL-ROUTING-MVP-0007A/PROOF.json`

### PR #1159 -- feat(dopetask): add "claude" to execution.agent enum

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1159
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `claude/distracted-brahmagupta-6b0743`
- Head SHA: `3a6cda08047776bf62259eb350e79a6840a56892`
- Merge-state status: BEHIND
- Updated: 2026-07-29T00:36:42Z
- Changed-file count: 2 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: mergeStateStatus=BEHIND, not draft. Directly touches docs/03-reference/spec/dopetask/dopetask-canonical-spec.json (slot 25) plus docs/03-reference/governance/codex-macro-packet-blueprint.md. Title: 'feat(dopetask): add "claude" to execution.agent enum' -- this is the exact follow-up this packet itself flagged (see task-packets/generated/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.json's execution.agent invariant note) after discovering the canonical schema's execution.agent enum lacked a 'claude' value.
- Current-main effect: None; PR is unmerged.
- Action if merged: Regenerate slot 25 from the new main tip; also revisit this packet's own task-packets/generated/TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH.json execution.agent value (currently the 'shell' fallback) since a native 'claude' enum value would then exist.
- Source slots affected: [25]
- Contradiction/overlap notes: Directly resolves a gap this packet itself discovered and flagged as a follow-up task.
- Confidence: high
- Sample changed paths:
    - `docs/03-reference/governance/codex-macro-packet-blueprint.md`
    - `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`

### PR #1161 -- MCP fleet follow-ups: LOW audit findings, M11 consumer sweep, P-24 ADR

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1161
- State: OPEN (draft: True)
- Base branch: `claude/mcp-multi-instance-design-d706d6`
- Head branch: `claude/mcp-fleet-followups`
- Head SHA: `8f3a10b93a158f78194850995bd781e79f59b70b`
- Merge-state status: UNSTABLE
- Updated: 2026-07-29T04:37:32Z
- Changed-file count: 10 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Draft MCP/task-orchestrator follow-up touching the task-orchestrator Leantime follow-up document and a project-scoped task-orchestrator ADR. These changes can alter context for slot 17's Task Orchestrator system description.
- Current-main effect: None; PR is unmerged.
- Action if merged: Re-verify slot 17 and regenerate if the current system description drifts.
- Source slots affected: [17]
- Contradiction/overlap notes: No exact selected slot path is edited; classification is conservative because the changed ADR and follow-up document concern the same system plane.
- Confidence: medium
- Sample changed paths:
    - `.claude/skills/pr-docgen-sync/scripts/pr_docgen_sync_workflow.py`
    - `.github/copilot-instructions.md`
    - `.github/skills/pr-docgen-sync/scripts/pr_docgen_sync_workflow.py`
    - `claudedocs/m11-workflow-api-rename-consumer-sweep-2026-07-29.md`
    - `docs/03-reference/planes/pm/task-orchestrator-leantime-followups.md`
    - `docs/90-adr/adr-dmx-mcp-project-scoped-task-orchestrator-001.md`
    - `docs/planes/pm/task-orchestrator-leantime-followups.md`
    - `templates/skills/pr-docgen-sync/scripts/pr_docgen_sync_workflow.py`
    - `tests/test_cli_mcp_startup.py`
    - `tests/test_mcp_health_probe.py`

### PR #1162 -- fix(pr-steward): paginate the changed-files completeness cross-check past 100 files

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1162
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `fix/pr-steward-changed-files-pagination`
- Head SHA: `77e26075f31d9675fc385c4f6698e0ddf7292a38`
- Merge-state status: BLOCKED
- Updated: 2026-07-29T04:47:31Z
- Changed-file count: 3 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Touches tools/pr_steward/collector.py and pagination/release-approval tests. Changed-file completeness is a documented PR Steward readiness behavior represented by slot 32.
- Current-main effect: None; PR is unmerged.
- Action if merged: Re-verify slot 32 against the new changed-file completeness behavior and regenerate if drift is found.
- Source slots affected: [32]
- Contradiction/overlap notes: This is the isolated follow-up for the Steward pagination repair reverted from PR #1152.
- Confidence: medium
- Sample changed paths:
    - `tests/pr_steward/test_collector_changed_files_pagination_check.py`
    - `tests/pr_steward/test_collector_security_release_approval.py`
    - `tools/pr_steward/collector.py`

### PR #1163 -- draft(research): preregister LTAIP H0 segment study [BLOCKED_EVIDENCE]

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1163
- State: OPEN (draft: True)
- Base branch: `docs/ltaip-full-packet-import`
- Head branch: `research/TP-LTAIP-H0-001-segment-workflow-lock`
- Head SHA: `08e4bfe7ce41c6802f4b1f424d8f107a81b99e41`
- Merge-state status: UNSTABLE
- Updated: 2026-07-29T05:55:29Z
- Changed-file count: 7 (capture_complete: True)
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft research-registration PR touching docs/06-research, proof, reports, and participant evidence only. No selected slot or watched runtime family intersects its seven changed paths.
- Current-main effect: None; PR is unmerged.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Targets a non-main base branch and is marked BLOCKED_EVIDENCE in its title.
- Confidence: high
- Sample changed paths:
    - `docs/06-research/leantime-ai-parity/h0/segment-lock/interview-guide.md`
    - `docs/06-research/leantime-ai-parity/h0/segment-lock/recruitment-and-consent.md`
    - `docs/06-research/leantime-ai-parity/h0/segment-lock/research-protocol.md`
    - `proof/leantime-ai-parity/TP-LTAIP-H0-001/COMMAND_LOG.md`
    - `proof/leantime-ai-parity/TP-LTAIP-H0-001/GIT_STATUS_BEFORE.txt`
    - `reports/leantime-ai-parity/h0/segment-lock/participant-register.redacted.json`
    - `reports/leantime-ai-parity/h0/segment-lock/session-evidence.jsonl`

### PR #1164 -- fix(task-orchestrator): repair bridge-backed ConPort persistence wiring

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1164
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `codex/to-conport-persistence-repair`
- Head SHA: `c78c45b0e06a729d51f329e510f0a8069c46fca6`
- Merge-state status: UNSTABLE
- Updated: 2026-07-29T06:25:29Z
- Changed-file count: 11 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Draft, mergeStateStatus=UNSTABLE. Touches services/task-orchestrator/app/services/workflow_service.py and compose.yml, changing Task Orchestrator persistence behavior described by slot 17.
- Current-main effect: None; PR is unmerged.
- Action if merged: Re-verify slot 17 against the persisted workflow behavior and regenerate if drift is found.
- Source slots affected: [17]
- Contradiction/overlap notes: Implementation repair is accompanied by task packet and contract tests; no selected source file is directly edited.
- Confidence: medium
- Sample changed paths:
    - `compose.yml`
    - `services/task-orchestrator/app/services/workflow_service.py`
    - `task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-implementation-notes.md`
    - `task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-plan-review.md`
    - `task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-plan.md`
    - `task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-research-review.md`
    - `task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001-research.md`
    - `task-packets/TP-DMX-TO-CONPORT-PERSISTENCE-REPAIR-001.json`
    - `tests/arch/test_task_orchestrator_conport_persistence_contract.py`
    - `tests/unit/test_task_orchestrator_workflow_route_certification.py`
    - `tests/unit/test_task_orchestrator_workflow_store.py`

### PR #1165 -- audit: approve AGY Gemini 3.1 Pro exact model

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1165
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `codex/approve-agy-gemini-3-1-pro-audit`
- Head SHA: `8f2c009c35309c4aad371d17568528b61b84523d`
- Merge-state status: UNSTABLE
- Updated: 2026-07-29T07:53:00Z
- Changed-file count: 6 (capture_complete: True)
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Draft, mergeStateStatus=UNSTABLE. Directly touches docs/ops/embedded-audit.md (slot 30) and schemas/proof/embedded_audit.schema.json (slot 31), plus the related proof-model test.
- Current-main effect: None; PR is unmerged.
- Action if merged: Regenerate slots 30 and 31 from the new main tip and re-run package validation.
- Source slots affected: [30, 31]
- Contradiction/overlap notes: Directly affects the embedded-audit contract carried by this package.
- Confidence: high
- Sample changed paths:
    - `docs/ops/embedded-audit-proof.md`
    - `docs/ops/embedded-audit.md`
    - `proof/TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001/implementation-notes.md`
    - `schemas/proof/embedded_audit.schema.json`
    - `task-packets/TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001.json`
    - `tests/audit/test_agy_gemini31_model.py`

## 4. Conservation Check

- Open PR inventory count: 32
- Ledger entry count: 32
- Every PR number appears exactly once above (enforced by the build script's fail-closed classification lookup).
