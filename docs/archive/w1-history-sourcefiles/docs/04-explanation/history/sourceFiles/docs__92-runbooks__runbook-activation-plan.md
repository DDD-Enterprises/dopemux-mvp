---
id: runbook-activation-plan
title: Runbook — Dopemux Activation Plan
type: runbook
owner: @hu3mann
last_review: 2025-09-24
next_review: 2025-12-24
tags: [adhd, activation, planning, execution]
related: [runbook-project-analysis-backup, runbook-extended-roadmap]
---

# Dopemux Integration Activation Plan

## Planning Session Details
- **Date**: 2025-09-24
- **Analysis Tool**: zen thinkdeep (gemini-2.5-pro)
- **Planning Tool**: zen planner (gpt-5-mini)
- **Continuation ID**: 1f3a6262-13a8-405a-938f-97ffc2f34640

## Executive Summary

**BREAKTHROUGH DISCOVERY:** Project has solid, comprehensive infrastructure that needs activation, NOT rebuilding. This plan transforms operational issues into systematic activation workflow.

## Key Finding: Infrastructure Status = SOLID

**Existing Components Found:**
- Complete ADHD system components: context_manager.py, task_decomposer.py, attention_monitor.py
- Comprehensive MCP infrastructure: session_manager.py, broker.py, observability.py, roles.py
- Existing integration bridges: leantime_bridge.py, taskmaster_bridge.py
- Mature Python package with proper dependencies and dev tooling

**Issue Type:** Integration Activation (NOT Architectural Chaos)

## Implementation Phases

### PHASE 1: QUICK WINS (Week 1) - Build Momentum

1. **Session Persistence Testing (25 min)**
   - File: `src/dopemux/mcp/session_manager.py`
   - Goal: Identify specific failure points in save/restore
   - Success: Clear error diagnosis OR working session functionality

2. **Documentation System Audit (25 min)**
   - Directories: `./docs/`, `./CCDOCS/`, `./dopemux-docuXtractor/`
   - Goal: Map content distribution and identify conflicts
   - Output: Documentation audit report

3. **ADHD System Status Check (25 min)**
   - Files: `context_manager.py`, `task_decomposer.py`, `attention_monitor.py`
   - Goal: Verify individual component functionality
   - Success: All 3 systems import and basic functions work

### PHASE 2: INTEGRATION ACTIVATION (Week 2) - Core Connections

1. **Leantime Bridge Testing (25 min)**
   - File: `src/integrations/leantime_bridge.py`
   - Test connection and data flow

2. **Taskmaster Bridge Testing (25 min)**
   - File: `src/integrations/taskmaster_bridge.py`
   - Verify integration functionality

3. **MCP Role System Debug (25 min)**
   - File: `src/dopemux/mcp/roles.py`
   - Fix metamcp optimization issues

4. **Session-ADHD Integration (25 min)**
   - Connect session persistence with ADHD systems
   - Test cross-component communication

### PHASE 3: DOCUMENTATION CONSOLIDATION (Week 3) - Structure

1. **Unified Hierarchy Design (25 min)**
   - Create enforced structure with metadata/linking
   - Define file types and naming conventions

2. **Migration Automation (25 min)**
   - Script to consolidate 3 documentation systems
   - Preserve content while enforcing structure

3. **docuXtractor Integration Decision (25 min)**
   - Evaluate: Integrate with core OR maintain as separate tool
   - Implement chosen approach

## ADHD-Optimized Work Session Structure

**SESSION TEMPLATE (30 minutes total):**
- **Pre-Session (5 min)**: Review specific file/goal, set timer, clear context switch
- **Deep Work (20 min)**: Single task focus, no context switching, clear success criteria
- **Post-Session (5 min)**: Document findings, update progress, plan next step

## Immediate Next Actions

### START TODAY:
**Session Manager Testing (25 min)**
- **File**: `src/dopemux/mcp/session_manager.py`
- **Approach**: Test with simple session data, check logs/error output
- **Success**: Clear error diagnosis OR working session save/restore

## Contingency Plans

- **If Session Manager is Broken**: Skip to ADHD system testing, revisit later
- **If ADHD Systems Don't Import**: Check dependencies, verify environment setup
- **If Documentation Conflicts Severe**: Create new unified structure, migrate incrementally
- **If Integration Bridges Non-Functional**: Focus on core stability first

## Success Indicators

- **Week 1**: At least 2 of 3 core systems showing progress
- **Week 2**: First working integration between any two systems
- **Week 3**: Unified documentation system operational
- **Month 1**: Core Dopemux functionality activated and usable

## ROI Analysis

**Activation vs Rebuild:**
- **Estimated Savings**: Months of development time
- **Risk Reduction**: Building on proven architecture
- **ADHD Benefit**: Maintains existing mental models and context

---
*Generated: 2025-09-24 via systematic analysis and ADHD-optimized planning*