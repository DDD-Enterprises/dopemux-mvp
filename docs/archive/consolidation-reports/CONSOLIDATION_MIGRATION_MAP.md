---
id: CONSOLIDATION_MIGRATION_MAP
title: Consolidation_Migration_Map
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Consolidation_Migration_Map (explanation) for dopemux documentation and developer
  workflows.
---
# Documentation Consolidation Migration Map

**Date**: 2026-02-02
**Status**: Ready for execution
**Script**: `/Users/hue/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/comprehensive_consolidation.py`

## Overview

This consolidation reorganizes scattered documentation files into a clean Diátaxis-based structure, removing duplicate directories and archiving historical documents.

## Execution

Run the consolidation script:

```bash
cd /Users/hue/code/dopemux-mvp
python3 /Users/hue/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/comprehensive_consolidation.py
```

Or use the simpler script for just the first phase:

```bash
python3 /Users/hue/code/dopemux-mvp/move_docs.py
```

## What Stays at Root

### Approved Root Files
- README.md
- CHANGELOG.md
- INSTALL.md
- QUICK_START.md
- TODO.md
- AGENTS.md
- Any LLM-focused files (claude.md, llms.txt, etc.)

### Service/Component READMEs
- All README.md files in services/, components/, and subdirectories remain in place
- These will be reviewed and slimmed down separately

## Migration Details

### Phase 1: Historical Docs → archive/implementation-history/

| Source | Destination |
|--------|-------------|
| DOPESMUX_ULTRA_UI_MVP_COMPLETION.md | archive/implementation-history/ |
| PHASE1_SERVICES_INTEGRATION_COMPLETED.md | archive/implementation-history/ |
| PHASE_3_NEXT_STEPS_PLANNING.md | archive/implementation-history/ |
| REORGANIZATION-2025-10-29.md | archive/implementation-history/ |
| RELEASE_NOTES_v0.1.0.md | archive/implementation-history/ |
| pm-integration-changes.md | archive/implementation-history/ |
| 94-architecture/CONPORT_KG_2.0_EXECUTIVE_SUMMARY.md | archive/implementation-history/ |
| 94-architecture/CONPORT_KG_2.0_MASTER_PLAN.md | archive/implementation-history/ |
| 94-architecture/INTEGRATION_COMPLETE_SUMMARY.md | archive/implementation-history/ |
| 94-architecture/PHASE_2_COMPLETION_SUMMARY.md | archive/implementation-history/ |

### Phase 2: Deprecated/Planning Docs → archive/deprecated/

| Source | Destination |
|--------|-------------|
| claude-code-tools-integration-plan.md | archive/deprecated/ |
| conport_enhancement_decisions.json | archive/deprecated/ |
| deployment/overview.md | archive/deprecated/ |

### Phase 3: How-To Guides → 02-how-to/

| Source | Destination |
|--------|-------------|
| TERMINAL_SETUP.md | 02-how-to/terminal-setup.md |
| WEBSOCKET_QUICK_START.md | 02-how-to/websocket-quickstart.md |
| tmux-setup.md | 02-how-to/tmux-setup.md |
| troubleshooting-playbook.md | 02-how-to/troubleshooting.md |
| deployment/DEPLOYMENT-CHECKLIST.md | 02-how-to/deployment-checklist.md |
| deployment/DEPLOYMENT-INSTRUCTIONS.md | 02-how-to/deployment-instructions.md |
| deployment/DEPLOYMENT-WORKTREE-INSTRUCTIONS.md | 02-how-to/deployment-worktree.md |
| deployment/PRODUCTION_DEPLOYMENT_CHECKLIST.md | 02-how-to/production-deployment-checklist.md |
| operations/adhd-engine-rollout-runbook.md | 02-how-to/operations/adhd-engine-rollout.md |

### Phase 4: Reference Docs → 03-reference/

| Source | Destination |
|--------|-------------|
| security-overview.md | 03-reference/security.md |
| ai-agents.md | 03-reference/ai-agents.md |
| DOCUMENTATION-CATALOG.md | 03-reference/documentation-catalog.md |
| engineering/service_env_contract.md | 03-reference/service-env-contract.md |

### Phase 5: Explanation Docs → 04-explanation/

| Source | Destination |
|--------|-------------|
| dopemux-ultra-ui-mvp-summary.md | 04-explanation/dopemux-ultra-ui-mvp.md |
| dopemux-overview.md | 04-explanation/dopemux-overview.md |
| metrics-dashboards-for-tmux.md | 04-explanation/metrics-dashboards.md |

### Phase 6: Architecture Consolidation → 04-explanation/architecture/

All architecture docs from `architecture/` and `94-architecture/` directories consolidate into `04-explanation/architecture/`:

| Source | Destination |
|--------|-------------|
| architecture/PROFILE_SYSTEM_ARCHITECTURE.md | 04-explanation/architecture/profile-system.md |
| architecture/working-memory-assistant-design.md | 04-explanation/architecture/working-memory-assistant.md |
| architecture/working-memory-assistant-interfaces.md | 04-explanation/architecture/working-memory-interfaces.md |
| 94-architecture/AGENT_INTEGRATION_GUIDE.md | 04-explanation/architecture/agent-integration-guide.md |
| 94-architecture/conport-kg-project-summary.md | 04-explanation/architecture/conport-kg-project-summary.md |
| 94-architecture/multi-instance-implementation.md | 04-explanation/architecture/multi-instance-implementation.md |
| 94-architecture/serena-v2-architecture-analysis.md | 04-explanation/architecture/serena-v2-architecture.md |
| 94-architecture/system-bible.md | 04-explanation/architecture/system-bible.md |
| 94-architecture/unified-architecture-guide.md | 04-explanation/architecture/unified-architecture-guide.md |

### Phase 7: Guides Consolidation → 01-tutorials/

| Source | Destination |
|--------|-------------|
| guides/PROFILE_MIGRATION_GUIDE.md | 01-tutorials/profile-migration-guide.md |
| guides/PROFILE_USER_GUIDE.md | 01-tutorials/profile-user-guide.md |

## Directories to be Removed (After Emptying)

After consolidation, these empty directories will be removed:

- `docs/architecture/` (merged into 04-explanation/architecture/)
- `docs/94-architecture/` (merged into 04-explanation/architecture/)
- `docs/guides/` (merged into 01-tutorials/)
- `docs/deployment/` (merged into 02-how-to/)
- `docs/engineering/` (merged into 03-reference/)
- `docs/operations/` (merged into 02-how-to/operations/)
- `docs/user-guides/` (if empty)
- `docs/development/` (to be reviewed separately)
- `docs/synergies/` (to be reviewed separately)
- `docs/audit/` (to be reviewed separately)
- `docs/services/` (to be reviewed separately)
- `docs/mcp-servers/` (to be reviewed separately)
- `docs/systems/` (to be reviewed separately)

## Final Structure

```
docs/
├── 00-MASTER-INDEX.md              # Main navigation
├── docs_index.yaml                 # Machine-readable index
│
├── 01-tutorials/                   # Learning-oriented
├── 02-how-to/                      # Problem-solving
│   └── operations/                 # Operations runbooks
├── 03-reference/                   # Technical specs
├── 04-explanation/                 # Understanding-oriented
│   └── architecture/               # All architecture docs
│
├── 05-audit-reports/               # Kept as-is
├── 06-research/                    # Kept as-is
├── 90-adr/                         # Architecture Decision Records
├── 91-rfc/                         # Request for Comments
│
└── archive/                        # Historical documents
    ├── implementation-history/     # Phase completions, progress
    ├── deprecated/                 # Old planning docs
    ├── session-notes/              # Session summaries
    └── completed-projects/         # Existing archive
```

## Post-Consolidation Tasks

1. **Update 00-MASTER-INDEX.md**: Reflect new structure and paths
2. **Update docs_index.yaml**: Update file paths in machine-readable index
3. **Review remaining directories**: Check development/, synergies/, audit/, services/, mcp-servers/, systems/
4. **Service README audit**: Ensure service READMEs are brief, extract detailed docs to docs/03-reference/services/
5. **Verify links**: Update any internal documentation links to new paths
6. **Update .gitignore**: Ensure archived directories are tracked

## Notes

- All moves preserve file content - nothing is deleted
- Historical docs remain accessible in archive/
- Diátaxis structure (tutorials/how-to/reference/explanation) is preserved and strengthened
- All service READMEs remain in their original locations
- Root-level LLM files (AGENTS.md, TODO.md, etc.) remain at root

## Rollback

If needed, the consolidation can be partially rolled back by moving files back from their destinations to sources using git:

```bash
git log --name-status | grep -A5 "consolidation"
git checkout HEAD~1 -- docs/
```
