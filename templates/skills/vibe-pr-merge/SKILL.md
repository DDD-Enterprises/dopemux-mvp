# Skill: Vibe PR Merge Specialist

## Purpose
Deterministic, policy-governed PR remediation and queue management with advanced throughput optimization, integrated with Vibe guardrails.

## When to Use
- **`dopemux vibe pr-merge flight`**: Real-time queue visualization and manual control.
- **`dopemux vibe pr-merge flight --auto-pilot`**: Supervised, automated remediation of the PR queue.
- **`dopemux vibe pr-merge queue-drain`**: Fully autonomous, headless queue processing.

## When NOT to Use
- Architectural design from scratch.
- Bypassing mandatory human security reviews.

## Key Subsystems & Workflow
1.  **State Analyzer**: Ingests PR state via GraphQL, including review threads and CI statuses.
2.  **Predictive Queue Scorer**: Ranks PRs using a DAG-based topological sort with **WSEMT (Weighted Shortest Expected Merge Time)** scoring to prioritize high-value, low-risk changes.
3.  **Remediation Engine**:
    *   **Conflict Classifier**: Uses `git rerere` for known conflicts and escalates unsafe semantic conflicts.
    *   **Thread Handler**: Resolves discussions programmatically via GraphQL `resolveReviewThread` mutations.
    *   **Verification Engine**: Executes local validation steps defined in policy.
4.  **Orchestrator**: Manages the state machine, advancing PRs through their lifecycle (`Verify -> Patch -> Implement`) and enabling GitHub Auto-Merge when appropriate.

## Core Mandates & Constraints
- **Throughput over Latency**: Optimize global repository velocity, not just single PR merge time.
- **DAG Dependency Awareness**: Process PR stacks in the correct topological order.
- **Semantic Safety**: Escalate high-risk conflicts in `auth/`, `secrets/`, etc., to humans.
- **Evidence-Based Automation**: All automated actions must be logged and auditable.
- Ambiguity = Human Escalation.
- High-Risk Conflict = No Auto-Resolution.
