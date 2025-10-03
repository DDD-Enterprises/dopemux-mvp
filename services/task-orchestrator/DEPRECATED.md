# ⚠️ DEPRECATED - DO NOT USE

**This service has been replaced as part of Path C Migration (Decision #140).**

## Replacement Systems

This task-orchestrator service has been **decomposed and migrated** to:

### 1. ADHD Engine Service
**Location**: `services/adhd_engine/`
**Replaces**: `adhd_engine.py` (962 lines)
**Purpose**: ADHD accommodation intelligence (energy tracking, attention monitoring, break management)
**Access**: HTTP API on port 8095 or Docker: `dopemux-adhd-engine`

### 2. ConPort Task Storage
**Location**: `services/conport/` (SQLite database)
**Replaces**: Task orchestration, task storage, dependency tracking
**Purpose**: Single source of truth for all tasks and decisions
**Access**: ConPort MCP tools in Claude Code

### 3. SuperClaude Commands
**Location**: `.claude/commands/dx/`
**Replaces**: CLI task management, session workflows
**Purpose**: ADHD-optimized development commands
**Access**: `/dx:implement`, `/dx:session/*`, `/dx:prd-parse`, etc.

## Migration Completed

**Date**: October 2025
**Timeline**: Weeks 1-2 of Path C migration

## What Happened to Each Component

| Old File | New Location | Status |
|----------|--------------|--------|
| adhd_engine.py | services/adhd_engine/engine.py | Extracted & Enhanced |
| enhanced_orchestrator.py | ConPort + Integration Bridge | Functionality Distributed |
| sync_engine.py | Deferred to Week 8+ (Leantime sync) | Not Currently Needed |
| event_coordinator.py | Integration Bridge | Pattern Reused |
| automation_workflows.py | SuperClaude commands | Replaced |
| claude_context_manager.py | ConPort active_context | Pattern Reused |
| multi_team_coordination.py | Not migrated | Future Enhancement |
| predictive_risk_assessment.py | Not migrated | Future Enhancement |
| external_dependency_integration.py | Not migrated | Future Enhancement |
| deployment_orchestration.py | Not migrated | Future Enhancement |
| performance_optimizer.py | Not migrated | Future Enhancement |
| orchestrator_integration_test.py | Archived | Tests Replaced |

## Preserved Until

**2025-11-01** - This directory will be removed one month after migration completion.

Until then, code is preserved for reference but should NOT be used in production.

## Documentation

- **Migration ADR**: `docs/90-adr/ADR-XXXX-path-c-migration.md`
- **Decision Log**: ConPort Decisions #140, #141, #147, #148, #150, #152
- **New Architecture**: See `.claude/CLAUDE.md`

## For Developers

If you need functionality from this service:
1. Check if it exists in `services/adhd_engine/` (most ADHD features)
2. Check ConPort MCP tools (task storage, decisions)
3. Check SuperClaude `/dx:` commands (workflows)
4. If not found, it may be planned for future enhancement

Contact: See ConPort decisions for migration rationale and future plans.
