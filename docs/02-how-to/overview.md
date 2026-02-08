---
id: README
title: Readme
type: how-to
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme (how-to) for dopemux documentation and developer workflows.
---
# How-To Guides - Problem-Solving Instructions

**How-to guides are goal-oriented directions** that take you through the steps to solve a real-world problem. These assume you have basic familiarity with Dopemux.

## Quick Navigation

- [Deployment](#deployment)
- [Integrations](#integrations)
- [Operations](#operations)

---

## Deployment

Step-by-step guides for deploying Dopemux in various environments.

### Production Deployment
- **[Production Deployment Guide](deployment-guide.md)** - Deploy to production environment
- **[Deployment Checklist](deployment-guide.md#pre-deployment-checklist)** - Pre-flight checklist and verification
- **[Worktree Deployment](deployment-worktree.md)** - Deploy using git worktrees

### Development Environment
- **[Instance State Persistence](instance-state-persistence.md)** - Maintain state across restarts
- **[Multi-Instance Workflow](multi-instance-workflow.md)** - Run multiple Dopemux instances

---

## Integrations

Connect Dopemux with external tools and services.

### Project Management
- **[Leantime Setup](integrations/leantime-integration-guide.md#quick-setup-5-minutes)** - Basic Leantime integration
- **[Leantime API Configuration](integrations/leantime-integration-guide.md#api-configuration)** - Advanced API setup
- **[Leantime Deployment](integrations/leantime-integration-guide.md#deployment-strategy)** - Deployment recommendations

### MCP Servers
- **[MCP Service Discovery Guide](mcp-service-discovery-guide.md)** - Discover and verify active MCP services
- **[MCP Tools Overview](../03-reference/mcp-tools-overview.md)** - Tool catalog and usage patterns

---

## Operations

Day-to-day operational tasks and workflows.

### Workflow Management
- **[Role Switching Quickstart](role-switching-quickstart.md)** - Switch between development roles
- **[Instance Slash Commands](instance-slash-commands.md)** - Command reference

### ADHD Engine
- **[Serena V2 Deployment](serena-v2-production-deployment.md#-quick-start---production-deployment)** - Deploy ADHD intelligence
- **[Serena V2 Production Guide](serena-v2-production-deployment.md#-integration-architecture)** - Integration and production architecture

---

## How-To Guide Principles

Guides in this section:
- **Are goal-oriented** - Solve specific problems
- **Show how to do something** - Practical steps
- **Are flexible** - Adapt to your situation
- **Are reliable** - Tested and verified

## Not What You're Looking For?

- **New to Dopemux?** → See [Tutorials](../01-tutorials/)
- **Need technical specs?** → See [Reference](../03-reference/)
- **Want to understand why?** → See [Explanation](../04-explanation/)

## Contributing

When adding how-to guides:
1. Start with a clear goal/problem statement
2. List prerequisites
3. Provide clear, numbered steps
4. Include verification steps
5. Troubleshoot common issues

---

**Part of:** [Diátaxis Documentation Framework](https://diataxis.fr/)
