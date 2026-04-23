# ADR — Adopt a Dopemux Adaptive Ingress Plane with Local Runtime Shims

## Status
Accepted

## Context
Dopemux is a service-dense workspace with split authority across PM, chronicle, structured context, retrieval, and execution. Agent runtimes expose divergent hook, MCP, wrapper, and watcher surfaces. Direct point-to-point integration does not scale, but repo truth also forbids collapsing adapters, memory, retrieval, and PM truth into one monolith.

## Decision
Implement one agent-facing gateway for ingress/control concerns only. Keep local runtime shims for lifecycle visibility that the gateway cannot observe remotely. Preserve Leantime, task-orchestrator, ConPort, dope-memory, dope-context, dopetask, and Repo-Truth-Extractor as separate authorities. Route all authoritative mutations through owned service interfaces. Use a canonical event envelope, capability registry, deterministic tool catalogs, async workers for non-critical processing, and feature-flagged migration.

## Consequences
### Positive
- One policy/auth/audit choke point
- Easier runtime onboarding
- Cleaner, more deterministic agent-visible surface
- Fewer exposed proxy/bridge layers

### Negative
- New gateway single-point-of-failure risk
- Shim maintenance burden
- Extra network hop
- Contract-testing burden across runtimes

### Constraint
The gateway may centralize ingress logic, but it may not centralize truth.

## Rejected alternatives

### A. Status quo + better hooks
Rejected as too fragmented, too drift-prone, and too weak on centralized policy enforcement.

### C. Monolithic Dopemux service
Rejected as a direct violation of repo-truth boundaries and a path to fake authority collapse.
