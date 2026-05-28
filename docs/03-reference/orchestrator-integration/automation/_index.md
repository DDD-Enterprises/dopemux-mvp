---
id: orchestrator-automation-index
title: Automation Pilot Reference
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference detailing background queue-draining, daemon executors, and safety kill-switches.
related_packets:
  - TP-DMX-ORCH-016
  - TP-DMX-ORCH-016-DAEMON
---

# Automation Pilot & Daemon

The automation pilot operates background queue-draining, test isolation execution, and dependency resolution loops.

## Global Kill-Switch
A strict environment and configuration-level kill-switch (`ORCHESTRATOR_AUTO_PILOT=0`) instantly disables all daemon background processing and falls back to manual validation.
