---
id: task-orchestrator
title: Task Orchestrator
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Task Orchestrator (reference) for dopemux documentation and developer workflows.
---
# Task Orchestrator

**Extracted from**: DOPESMUX_ULTRA_UI_MVP_COMPLETION.md
**Date**: 2026-02-02

## Task Orchestrator Features (from Ultra UI MVP)

### ConPort Adapter
- Bidirectional task transformations (OrchestrationTask ↔ ConPort progress_entry)
- ADHD metadata preservation (energy, complexity, priority tags)
- Real-time sync with retry logic and error handling
- Cross-plane queries for decision enrichment
- Dependency relationship linking

### Task Coordinator
- ADHD-aware task orchestration with cognitive load assessment
- Task batching based on cognitive capacity limits
- Dependency resolution across task sequences
- Context switching detection with break recommendations
- ConPort state synchronization
- 25-minute focus session management
- Energy-aware task sequencing
- Break scheduling optimization

### Cognitive Load Balancer
- Real-time cognitive load calculation using research-backed formula
- Load classification: LOW/OPTIMAL/HIGH/CRITICAL with actionable recommendations
- Background monitoring every 10 seconds
- Caching system for performance optimization
- Proactive task complexity adjustment based on current load
- Energy-aware task sequencing
- Attention span prediction (18-25 minutes)
- Break scheduling optimization
- Task sequence optimization for cognitive flow

**Formula**: Load = 0.4 × task_complexity + 0.2 × (decision_count ÷ 10) + 0.2 × (context_switches ÷ 5) + 0.1 × (time_since_break ÷ 60) + 0.1 × interruption_score

### ADHD Engine Features
**6 API Endpoints**:
- POST /api/v1/assess-task - Task complexity assessment
- GET /api/v1/energy-level/{user_id} - Energy level tracking
- GET /api/v1/attention-state/{user_id} - Attention monitoring
- POST /api/v1/recommend-break - Break suggestions
- POST /api/v1/user-profile - User profile management
- PUT /api/v1/activity/{user_id} - Activity updates

**6 Background Monitors**:
- Energy level tracking
- Attention state monitoring
- Cognitive load assessment
- Break suggestion engine
- Hyperfocus detection
- Context switching tracker

**Integration**:
- Redis persistence for user profiles and state
- ConPort MCP client integration
- Docker containerization

### Service Ports
- ADHD Engine: 8095, 8097
- Task Orchestrator: 3014
- ConPort: 3010
- Leantime: 8080
