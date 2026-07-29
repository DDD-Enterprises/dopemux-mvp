# 40_OPEN_PR_IMPACT_LEDGER

> This ledger is candidate-future-authority context only.
> No unmerged PR content is represented as current-main truth.

```yaml
captured_at: 2026-07-28T00:15:00Z
execution_base_sha: 5f862d36f5417801b9fe148fccbb439731627234
open_pr_count: 21
material_open_pr_count: 3
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
- Changed-file count: 2
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
- Changed-file count: 2
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
- Changed-file count: 1
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: 1 file changed (UI dashboard dependency consolidation), mergeStateStatus=BEHIND. No intersection with watched paths.
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
- Changed-file count: 1
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: 1 file changed (CI container build matrix), mergeStateStatus=BEHIND. No intersection with watched paths.
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
- Changed-file count: 16206
- **Classification: SUPERSEDED_OR_CONFLICTING**
- Evidence: mergeStateStatus=DIRTY. changedFiles=16206, additions=5,145,096, deletions=9,284 -- two to three orders of magnitude larger than any other open PR, consistent with prior session's durable finding (reference_rte_stranded_branch_2026_07_26.md) that this exact branch (claude/rte-audit-improvement-f4beb7) is 4146 commits ahead / 4221 behind main with a merge-base dated 2025-09-19, i.e. a long-diverged, effectively stranded lineage rather than a clean forward delta.
- Current-main effect: None; PR is unmerged and not a safe merge candidate in its current form.
- Action if merged: Not applicable in current form -- this branch would need to be rebased or its recoverable commits cherry-picked onto current main (per the prior session's recovery note: 160/193 of its changed paths are present on main) before any merge could be evaluated for source-set impact.
- Source slots affected: none
- Contradiction/overlap notes: Shares problem domain (RTE truth/audit remediation) with #1136, which is the actively-maintained, clean-lineage successor; #1136 should be treated as authoritative for that domain, not #1123.
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

### PR #1126 -- fix(dope-context): repair vector compatibility and collection migration

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1126
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `fix/dope-context-voyage4-repair-0002`
- Head SHA: `ba8a78fa1ed09dc0d7cbb9f2b2680508c6fa13a3`
- Merge-state status: DIRTY
- Updated: 2026-07-27T02:55:25Z
- Changed-file count: 36
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: mergeStateStatus=DIRTY. Touches docs/03-reference/systems/dope-context/vector-profiles-and-migration.md (adjacent doc, not the exact slot-20 file) plus substantial services/dope-context/** runtime changes (embeddings, indexing, MCP server, reranker) described at a high level by slot 20's system-dopecontext.md.
- Current-main effect: None; PR is unmerged.
- Action if merged: Re-verify slot 20 content against the new dope-context runtime behavior and regenerate if drift is found.
- Source slots affected: [20]
- Contradiction/overlap notes: mergeStateStatus=DIRTY indicates merge conflicts must be resolved before this can land; classification may need revisiting once conflicts are addressed.
- Confidence: medium
- Sample changed paths:
    - `docs/03-reference/systems/dope-context/vector-profiles-and-migration.md`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/AUDITOR_REPORT.md`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/AUDIT_INTAKE.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/COLLECTION_MIGRATION_REPORT.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/COMMAND_LOG.txt`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/HANDOFF.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/IMPLEMENTATION_REPORT.md`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/MANIFEST.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/PROOF.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/VALIDATION.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/VECTOR_COMPATIBILITY_MATRIX.json`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/agy_audit_raw.txt`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/claude_audit_raw.txt`
    - `proof/TP-DOPECONTEXT-VOYAGE4-REPAIR-0002/gemini_audit_raw.txt`
    - `proof/pr_merge/embedded-audit/pr-1126/PROOF.json`

### PR #1127 -- docs(ltaip): import full macro-packet series and load-plan artifacts

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1127
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `docs/ltaip-full-packet-import`
- Head SHA: `f9acb478ecbb5bb9609a85ff15db4c1c85fc5f75`
- Merge-state status: BEHIND
- Updated: 2026-07-27T00:44:05Z
- Changed-file count: 33
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: mergeStateStatus=BEHIND. All 33 changed files are under docs/ops/load-plans/**, reports/leantime-ai-parity/**, schemas/leantime-ai-parity/**, scripts/leantime-ai-parity/**, task-packets/leantime-ai-parity/**, and tests/prototypes/leantime-ai-parity/**. None intersect the 37 selected slots or the watched-path list.
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
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-001.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-001.md`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-002.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-002.md`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-003.json`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-003.md`
    - `task-packets/leantime-ai-parity/TP-LTAIP-H0-004.json`

### PR #1128 -- feat(mcp): profile-selected tool plane and repo-domain read contract

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1128
- State: OPEN (draft: False)
- Base branch: `main`
- Head branch: `feat/TP-DMX-MCPPROF-001-profiled-tool-plane`
- Head SHA: `e41d134b5b0f32b5475ab5f094274bfac2259601`
- Merge-state status: DIRTY
- Updated: 2026-07-27T00:49:18Z
- Changed-file count: 40
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: mergeStateStatus=DIRTY. Touches mcp_catalog.yaml, schemas/mcp/fleet-catalog.schema.json, src/dopemux/mcp/*, docs/90-adr/adr-index.md, docs/90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md (a different ADR from the Memory Trinity ADR in slot 11). None of these paths intersect the 37 selected slots.
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
- Head SHA: `bf1842e3d0b20396e6d222dccbe97257584849e2`
- Merge-state status: BEHIND
- Updated: 2026-07-27T21:27:43Z
- Changed-file count: 366
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: mergeStateStatus=BEHIND (rebasable, not conflicted). True changedFiles=366 (gh pr view's files connection caps display at 100; verified via --json changedFiles). Directly touches docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md (slot 23) plus extensive services/repo-truth-extractor/** runtime, config/pricing.yaml, and CI workflow changes.
- Current-main effect: None; PR is unmerged.
- Action if merged: Regenerate slot 23 from the new main tip; re-run all validation gates.
- Source slots affected: [23]
- Contradiction/overlap notes: Same problem domain (RTE truth/audit remediation) as #1123, but #1136 is the clean, rebasable, actively-updated branch while #1123 is a massively diverged, DIRTY, likely-abandoned predecessor lineage -- see #1123 classification.
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
- Changed-file count: 42
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
- Changed-file count: 63
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Draft PR, mergeStateStatus=BEHIND. Touches docs/03-reference/dcp/model-routing-series-map.json, docs/03-reference/dcp/model-routing-series-status.md, and proof/task-packets artifacts under DMX-DCP-MODEL-ROUTING-MVP-0000R/0000S. docs/03-reference/dcp/** is not in the watched-path list and does not intersect any of the 37 selected slots.
- Current-main effect: None.
- Action if merged: None required for this package.
- Source slots affected: none
- Contradiction/overlap notes: Overlaps in subject matter with #1137 (same DCP model-routing series, same base proof directory DMX-DCP-MODEL-ROUTING-MVP-0000R); both draft, both BEHIND, no conflict evidence found between them.
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
- Changed-file count: 18
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Touches docs/90-adr/adr-dmx-prsteward-soloowner-001.md and tools/pr_steward/solo_owner_security_release.py (18 files total). Slot 32 (docs/ops/pr-steward.md) was grep-checked for 'solo'/'org member'/'exact-head'/'authoriz' and contains no matching content describing this mechanic, so its accuracy is unaffected by this PR merging.
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
- Changed-file count: 1
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
- Changed-file count: 3
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
- Merge-state status: BLOCKED
- Updated: 2026-07-27T16:29:41Z
- Changed-file count: 3
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot python-minor-patch group bump (40 updates); 3 files, mergeStateStatus=BLOCKED. No intersection with watched paths.
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
- Merge-state status: UNSTABLE
- Updated: 2026-07-27T16:29:57Z
- Changed-file count: 2
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
- Merge-state status: UNSTABLE
- Updated: 2026-07-27T16:30:05Z
- Changed-file count: 1
- **Classification: NO_PROJECT_SOURCE_IMPACT**
- Evidence: Dependabot setuptools 82.0.1->83.0.0 bump; 1 file (uv lock/pyproject dep pin). No intersection with watched paths.
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
- Merge-state status: UNSTABLE
- Updated: 2026-07-28T16:06:45Z
- Changed-file count: 2
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
- Merge-state status: UNSTABLE
- Updated: 2026-07-28T16:07:48Z
- Changed-file count: 2
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
- Merge-state status: UNSTABLE
- Updated: 2026-07-28T23:25:37Z
- Changed-file count: 2
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
- State: OPEN (draft: True)
- Base branch: `main`
- Head branch: `claude/mcp-multi-instance-design-d706d6`
- Head SHA: `edb265c9634d43ad36c0e2f7a6e24dc59bea7d5b`
- Merge-state status: UNSTABLE
- Updated: 2026-07-28T23:52:54Z
- Changed-file count: 56
- **Classification: SOURCE_CONTENT_REFRESH_IF_MERGED**
- Evidence: Draft PR, mergeStateStatus=UNSTABLE. Changed-file list directly includes AGENTS.md, docs/03-reference/systems/dopemux/system-dopemux.md, and docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md -- exactly slots 01, 15, 17 of this package.
- Current-main effect: None; PR is unmerged and draft.
- Action if merged: Regenerate slots 01, 15, 17 from the new main tip and re-run all validation gates.
- Source slots affected: [1, 15, 17]
- Contradiction/overlap notes: None observed.
- Confidence: high
- Sample changed paths:
    - `.claude/claude.md`
    - `.claude/hooks/mcp_health_probe.py`
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
    - `docs/01-tutorials/quickstart.md`

## 4. Conservation Check

- Open PR inventory count: 21
- Ledger entry count: 21
- Every PR number appears exactly once above (enforced by the build script's fail-closed classification lookup).

