---
id: DOC_CORPUS_SUMMARY
title: Doc Corpus Summary
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Doc Corpus Summary (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux Documentation Corpus Summary

**Generated:** 2026-02-15  
**Total Markdown Files:** ~2,585

## Primary Documentation Directories

### Core Project Docs
- **`docs/**`** - Main project documentation
- **`.claude/docs/**`** - Claude-specific MCP and statusline docs

### Service-Specific Docs
- **`services/adhd_engine/docs/**`** - ADHD Engine service documentation
- **`services/task-orchestrator/docs/**`** - Task Orchestrator service documentation
- **`services/working-memory-assistant/docs/**`** - Working Memory Assistant service documentation

### Infrastructure Docs
- **`docker/mcp-servers/docs/**`** - MCP server documentation

### Audit & Analysis Outputs
- **`_audit_out/**/*.md`** - Audit outputs and analysis reports
- **`scripts/docs_audit/**`** - Documentation audit scripts and results

### Archived/Quarantined Docs
- **`quarantine/2026-02-04/docs/**`** - Quarantined documentation from 2026-02-04
- **`quarantine/2026-02-04/.claude/docs/**`** - Quarantined Claude docs
- **`quarantine/2026-02-04/.claude/personas/**`** - Archived personas
- **`quarantine/2026-02-04/.claude/scratch/**`** - Archived scratch/session notes
- **`quarantine/2026-02-04/.claude/commands/**`** - Archived command definitions

### Test Resources
- **`tests/resources/test_docs/**`** - Test documentation fixtures

## Exclusions for Extraction

The following directories should be **EXCLUDED** from doc extraction (dependencies, not project docs):

- `node_modules/**` - Node.js dependencies
- `.venv/**` - Python virtual environment
- `.taskx_venv/**` - TaskX virtual environment
- `.git/**` - Git metadata
- `ui-dashboard/node_modules/**` - UI dashboard dependencies
- `SYSTEM_ARCHIVE/**` - System archives

## Doc Types Found

Based on sample inspection:
- **MCP Documentation** - Server configurations, tool definitions
- **Statusline Documentation** - Statusline examples and quickrefs
- **Session Logs** - Claude session summaries and handoffs
- **Architecture Docs** - System design, RFCs, boundaries
- **Workflow Docs** - Step-by-step procedures
- **Personas** - Agent persona definitions
- **Commands** - Slash command definitions
- **Audit Reports** - Memory surface analysis, gap analysis

## Recommended Extraction Strategy

For **Prompt G (Docs Deep Extraction)**, use these glob patterns:

### Include Patterns:
```
/Users/hue/code/dopemux-mvp/docs/**/*.md
/Users/hue/code/dopemux-mvp/.claude/docs/**/*.md
/Users/hue/code/dopemux-mvp/services/*/docs/**/*.md
/Users/hue/code/dopemux-mvp/docker/mcp-servers/docs/**/*.md
/Users/hue/code/dopemux-mvp/_audit_out/**/*.md
/Users/hue/code/dopemux-mvp/quarantine/2026-02-04/docs/**/*.md
/Users/hue/code/dopemux-mvp/quarantine/2026-02-04/.claude/**/*.md
/Users/hue/code/dopemux-mvp/scripts/docs_audit/**/*.md
```

### Exclude Patterns:
```
**/node_modules/**
**/.venv/**
**/.taskx_venv/**
**/.git/**
**/SYSTEM_ARCHIVE/**
```

## Expected Extraction Volume

| Category                | Estimated Files |
| ----------------------- | --------------- |
| Core docs               | ~200            |
| Service docs            | ~50             |
| Audit outputs           | ~30             |
| Quarantined docs        | ~2,000          |
| Claude sessions/scratch | ~200            |
| MCP/Infrastructure      | ~50             |
| Test fixtures           | ~10             |
| **Total**               | **~2,585**      |

## Notes

- The quarantine directory contains a large volume of archived documentation from 2026-02-04
- Many session logs and scratch files exist in `.claude/scratch/archive/`
- MCP server documentation is distributed across multiple locations
- Some docs may contain supersession chains (check for "supersedes", "deprecated" markers)
