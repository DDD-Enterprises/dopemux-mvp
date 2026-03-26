---
id: agent-leasing-contract
title: Agent Leasing Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-26'
last_review: '2026-03-26'
next_review: '2026-06-24'
prelude: Agent Leasing Contract (explanation) for dopemux documentation and developer
  workflows.
---
# Agent Leasing Contract: Execution Plane Rules of Engagement

## 1. Overview
The **Execution Plane** provides formal provenance and safety for all automated and human actions within the `dopemux` ecosystem. To prevent race conditions, duplicated effort, and unverified changes, all agents MUST adhere to this leasing contract.

## 2. Rules of Engagement

### 2.1 Lease Requirement
No tool execution, file modification, or git operations are permitted unless a valid `ACTIVE` lease is held for the current Task Packet (`ExecutionPacket`).
*   Agents must call `checkout(packet_id, agent_id)` to acquire a lease.
*   The `agent_id` must uniquely identify the acting entity.

### 2.2 Heartbeat Obligation
Leases are time-bound to prevent "zombie" locks if an agent crashes.
*   Agents MUST pulse the `heartbeat(lease_id)` tool at least once every 5 minutes.
*   If a heartbeat is missed beyond the TTL, the lease state transitions to `EXPIRED`.
*   An `EXPIRED` lease results in immediate revocation of execution privileges.
*   Any work performed under an expired lease is considered invalid and subject to automated rollback.

### 2.3 Handoff Semantics
Work is only considered "done" when it is formally handed off.
*   Upon completion, the agent MUST call `release(lease_id, final_state=PROOF_GENERATED)`.
*   The transition to `PROOF_GENERATED` signals that the work is ready for auditing.
*   Agents must ensure all proof artifacts (logs, diffs, test results) are linked in the packet's `proof_bundle` before release.

## 3. Enforcement
The Task Orchestrator and individual MCP servers enforce these rules. MCP tools will verify lease validity before performing destructive or state-changing operations.
