## Task: Implement Constrained Dynamic Loading (Revised Track 3)
- **ID**: 20250906-185622
- **Priority**: Medium
- **Status**: IN-PROGRESS
- **Context**: taskmaster_migration
- **Dependencies**: None

### Description
Add selective, pattern-based MCP server activation with strict constraints: pre-approved registry, synchronous execution, mandatory health checks, automatic cleanup, and admin override capability. Target 15-25% token reduction through intelligent server loading. Update to leverage available MCP tools (Serena, Claude-context, Task-master, Exa) and integrate with the existing MCP controller architecture for code analysis, symbol management, orchestration, and testing.

### Implementation Details
Scope and goals:
- Replace any basic file-operation based discovery/activation with MCP-native tooling: Serena for code analysis and symbol graph, Exa for pattern-based capability/server discovery, Task-master for synchronous orchestration and lifecycle, Claude-context for token accounting and context packing.
- Integrate with the existing MCP controller architecture (controller registry, adapters, lifecycle hooks, health-check protocol) to perform constrained dynamic loading of MCP servers and tools.
- Maintain strict constraints: pre-approved registry allowlist, synchronous activation, mandatory health checks, automatic cleanup/teardown, and admin override with audit logging. Achieve 15-25% reduction in token usage by only loading necessary servers/tools and trimming context via Claude-context.

Architecture integration:
- Implement ConstrainedDynamicLoader in src/mcp/controller/dynamic_loader.py. Expose an interface IDynamicLoader used by the MCP controller to request tool/server activation.
- Use the controller's registry for the pre-approved allowlist. Patterns may include tool name regex, capability tags, and symbol namespaces.
- Discovery and selection:
  1) Use Exa to perform query-based discovery against known MCP server manifests and capability indexes (local repo + remote registry APIs). Map request patterns to candidate servers.
  2) Use Serena's symbol index to confirm which server exposes the requested tools/symbols and to resolve version/namespace ambiguities. Persist a lightweight cache in the controller's store (no direct file I/O; rely on tool APIs and controller storage abstractions).
- Orchestration (synchronous):
  - Use Task-master to run the activation pipeline single-flight per capability key with timeouts, CPU/memory quotas, and cancellation propagation. All activation steps run synchronously relative to the requesting flow, with progress surfaced via controller events.
- Health checks:
  - Before exposing a dynamically loaded server, perform MCP-standard health probes (handshake/ping, tool list introspection, optional no-op tool invocation). Require success within timeouts; otherwise reject and emit telemetry.
- Automatic cleanup:
  - Use Task-master finalizers to ensure teardown of ephemeral sessions, temporary resources, and symbol cache entries on completion, error, or timeout. Implement idle TTL and reference counting to unload safely when no longer needed.
- Admin override:
  - Add RBAC-aware override (role: admin) that can bypass pattern restrictions and load non-allowlisted servers temporarily. All overrides must be tagged, time-bounded, and audit-logged in controller telemetry.
- Token optimization:
  - Use Claude-context to estimate predicted token cost of candidate activations and to pack only necessary context/tool manifests. Gate activation on budget policies to reach 15-25% token reductions vs. baseline greedy loading. Record pre/post token usage metrics to validate savings.
- Observability:
  - Emit structured events for discovery decisions, health outcomes, activation timings, token deltas, cleanup results, and override usage. Provide counters and traces for SLOs.
- Configuration:
  - Loader policies support: allowlist entries, pattern rules (regex/capability tags), timeouts, quotas, token budget thresholds, and admin roles. Keep configuration static at startup and read via existing controller config interfaces. When Task 33 (ConfigManager) lands, wire policies to its schemas without changing this loader’s public API.
- Security and safety:
  - Enforce allowlist first, then pattern matching, then health checks. Deny by default. No direct filesystem access from the loader; use MCP tool APIs and controller storage abstractions only. Comprehensive audit logging for overrides and failures.

Non-goals:
- Do not implement dynamic runtime config reloading. Do not add new external dependencies outside the MCP toolchain and existing controller interfaces.

### Test Strategy
Unit tests:
- Policy enforcement: verify allowlist and pattern rules deny/allow correctly, including edge cases and malformed patterns.
- Discovery and selection: mock Exa to return candidate manifests and Serena to return symbol graphs; ensure the selector picks correct servers and rejects mismatches.
- Orchestration: simulate Task-master single-flight behavior, timeouts, and cancellations; verify synchronous behavior and proper error propagation.
- Health checks: mock MCP handshake, tool list introspection, and no-op tool calls; assert mandatory health checks gate activation.
- Token accounting: mock Claude-context estimates and verify activation gating on token budgets and recorded token deltas.
- Cleanup: verify finalizers always run and resources are released on success, error, and timeout.
- Admin override: RBAC checks and audit log emission; ensure overrides bypass pattern restrictions but still require health checks.

Integration tests:
- End-to-end activation: from request pattern to active tool with Serena and Exa running in test mode; assert telemetry events, health results, and loader state transitions.
- Failure injection: discovery returns stale or conflicting candidates; health probe failures; Task-master timeout; ensure graceful denial and cleanup.
- Token reduction validation: run a representative scenario set with baseline greedy loading vs. constrained loader using Claude-context accounting; assert 15-25% reduction median across scenarios, with per-scenario metrics persisted.
- Concurrency: multiple simultaneous requests for the same and different capabilities; assert single-flight behavior, no duplicate loads, correct reference counting, and teardown after idle TTL.

Tooling and harness:
- Provide mocks/fakes for Serena, Exa, Task-master, and Claude-context where direct invocation is not feasible. Include contract tests against real tool endpoints in CI optional jobs.
- Snapshot and golden tests for selection decisions and audit logs to detect regressions.
- Performance tests to measure activation latency and overhead. Security tests to ensure no activation for non-allowlisted servers and that override use is fully logged.

### Migration Notes
- Originally Task ID: 48
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: medium
- Status mapping: in-progress
- Dependencies: []

### Related Files
- Original: .taskmaster/tasks/tasks.json
