---
id: SERVICE_WORKSPACE_ANALYSIS
title: Service_Workspace_Analysis
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Service_Workspace_Analysis (explanation) for dopemux documentation and developer
  workflows.
---
# Service Workspace Analysis

## Services by Workspace Dependency

### ✅ NEEDS Multi-Workspace (File/Code Operations)
1. **dope-context** - DONE ✅
2. **serena** - Code graph analysis
3. **conport_kg** - Knowledge graph (workspace-scoped contexts)
4. **workspace-watcher** - Different use case (detects active workspace)

### ⚠️ WORKSPACE-AWARE (Route by workspace)
1. **mcp-integration-bridge** - Routes requests with workspace context
2. **orchestrator** - Coordinates services with workspace context
3. **task-orchestrator** - Tasks associated with workspaces
4. **session_intelligence** - Sessions per workspace

### 🤷 WORKSPACE-AGNOSTIC (No file operations)
1. **adhd_engine** - Energy/attention (user-focused, not workspace)
2. **activity-capture** - Logs events (workspace is metadata)
3. **context-switch-tracker** - Tracks switches (workspace is data)
4. **intelligence** - AI coordination (workspace-agnostic)

## Implementation Priority

### HIGH PRIORITY (Direct file/code operations)
1. ✅ dope-context - Search/index code/docs
2. 🔄 serena - Code graph, LSP operations
3. 🔄 conport_kg - Context storage per workspace

### MEDIUM PRIORITY (Workspace routing/context)
1. 🔄 mcp-integration-bridge - Forward workspace in requests
2. 🔄 task-orchestrator - Tag tasks with workspace
3. 🔄 session_intelligence - Track sessions per workspace

### LOW PRIORITY (Workspace as metadata)
1. 🔄 orchestrator - Include workspace in service calls
2. 🔄 adhd_engine - Tag metrics with workspace
3. 🔄 activity-capture - Tag events with workspace

### NOT NEEDED (Workspace-agnostic)
1. ❌ workspace-watcher - Different use case
2. ❌ context-switch-tracker - Workspace is the data being tracked
3. ❌ intelligence - Workspace-agnostic AI routing

## Revised Implementation Plan

### Phase 1: Core Services (File Operations)
- serena (3-4 hours) - Complex, LSP clients per workspace
- conport_kg (2-3 hours) - Workspace-scoped graphs

### Phase 2: Routing & Coordination (Quick wins)
- mcp-integration-bridge (30 min) - Just forward workspace params
- task-orchestrator (1 hour) - Tag tasks with workspace
- session_intelligence (1 hour) - Session tracking

### Phase 3: Metadata Enhancement (Optional)
- orchestrator (30 min) - Pass workspace context
- adhd_engine (30 min) - Tag metrics
- activity-capture (30 min) - Tag events

**Estimated Total**: 8-12 hours for all critical services
