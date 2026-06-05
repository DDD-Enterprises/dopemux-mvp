---
id: dcp-mcp-readonly-registry-contract
title: DCP Read-Only MCP Facade — Multi-Project Registry Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Multi-project registry and resolver contract for the read-only MCP evidence facade for dopemux documentation and developer workflows.
---

# Multi-Project Registry Contract

> **Status.** Schema/resolver shape remains `PROPOSED` design. The `dopemux init` marker / workspace-identity contract is now **`OBSERVED`** — resolved by the static inspection in TP-DCP-MCP-RO-0003 (see [`DOPEMUX_INIT_REGISTRY_DISCOVERY.md`](DOPEMUX_INIT_REGISTRY_DISCOVERY.md)) and reflected in §2/§4/§5 below. Concrete registry file location and load mechanics are implemented in TP-DCP-MCP-RO-0004.

## 1. Purpose

The registry is the facade's **trust boundary**. It is the single source of truth for *which* projects are exposed to ChatGPT and *what* each project's backend bindings are. ChatGPT never names a path, URL, or port — only a `project_id` that the registry resolves.

## 2. Eligibility vs Exposure (core invariant)

- **Eligibility**: a workspace that has been `dopemux init`-ialized is *eligible* to be registered. `OBSERVED` (§1 of the discovery doc): the init marker is the **`.dopemux/` directory** (`src/dopemux/project_init.py:167`; checked at `cli.py:770`).
- **Exposure**: a workspace is only *exposed* when an operator adds an explicit, `enabled: true` entry to the facade's own registry.

`dopemux init` is **eligibility, not consent.** Initializing a workspace must never auto-expose it. This is fail-closed: absent a registry entry, a project does not exist as far as the facade is concerned. In particular, the facade **must not** derive exposure from dopemux's global workspace registry (`~/.dopemux/config.json`, `src/dopemux/global_config.py:24`), which records *every workspace the user has ever opened* — that is eligibility, not exposure.

## 3. Registry Schema (`PROPOSED`)

```yaml
# registry.yaml (location TBD in 0004; NOT committed with secrets)
projects:
  - project_id: "dopemux-mvp"          # opaque caller-facing id
    workspace_path: "/abs/path/..."     # resolved + validated at load
    enabled: true                       # exposure switch; default false
    service_profiles:                   # per-backend bindings
      conport:
        workspace_id: "<conport-workspace-id>"
        base_url: "http://127.0.0.1:3004"
      dope_memory:
        profile: "<memory-profile>"
        base_url: "http://127.0.0.1:3020"
      dope_context:
        base_url: "http://127.0.0.1:3010"  # MCP transport
      task_orchestrator:
        project_id: "<to-project-id>"
        base_url: "http://127.0.0.1:8000"
```

Field notes:
- `project_id` is the **only** project handle a caller may supply.
- `workspace_path`, `workspace_id`, `base_url`, ports, and routes are **registry-owned**; callers cannot set or override them.
- `enabled` defaults to `false`; omission means not exposed.
- `service_profiles` may be partial — a project missing a profile reports that capability as unavailable (see [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md) and `get_project_capabilities`), returning `PARTIAL`/`BLOCKED`, never guessed data.

## 4. Validation Rules (fail closed)

1. Every project-scoped tool requires a `project_id`; only `list_projects` is exempt.
2. A `project_id` not present in the registry → `BLOCKED` (unknown project).
3. A `project_id` present but `enabled: false` → `BLOCKED` (disabled project).
4. `workspace_path` must resolve (canonical, symlink-followed) to a path **contained within an approved root**. Escape → `BLOCKED`.
5. **Eligibility validation (`OBSERVED`-backed):** the resolved workspace must (a) validate as a real workspace via `validate_workspace()` / `get_workspace_root()` (`src/dopemux/workspace_detection.py:222`/`:82`, git-toplevel based); (b) contain a **`.dopemux/`** directory (init marker); (c) carry a **`.repo_id`** identity whose `project`/`owner` match the registry entry (`.repo_id` is the canonical identity marker per `schemas/dcp/dcp_project_resource_map.schema.json`). Any miss → `BLOCKED`.
6. No caller-supplied path, URL, port, backend route, `workspace_id`, SQL, or shell is ever accepted.
7. Registry load itself fails closed: a malformed entry disables that project rather than exposing it loosely.

## 5. Resolver Flow (`PROPOSED`)

```
project_id
  → registry lookup            (unknown → BLOCKED)
  → enabled check              (disabled → BLOCKED)
  → workspace_path → realpath  (resolve symlinks; get_workspace_root semantics)
  → containment check          (escapes approved root → BLOCKED)
  → eligibility check          (.dopemux/ present + validate_workspace() ok → else BLOCKED)
  → identity check             (.repo_id project/owner matches registry → else BLOCKED)
  → bind service_profiles      (missing profile → capability unavailable / PARTIAL)
  → canonical path + bindings  → adapter
```

## 6. Symlink-Escape Prevention

The resolver canonicalizes `workspace_path` (e.g. `realpath`) **before** the containment check, so a symlink pointing outside the approved root is rejected. Proof-file and code reads performed under a resolved root must re-apply containment on the final target path (no `..` traversal, no symlink jailbreak).

## 7. Capability Model

Each project advertises capabilities derived from its `service_profiles` (which backends are bound and reachable). `get_project_capabilities` returns this set so a caller knows, before issuing a tool call, whether e.g. chronicle search is available for that project. An unbound or unreachable backend yields a `PARTIAL`/`BLOCKED` envelope — the facade never fabricates a capability.

## 8. Open Questions / UNKNOWNs

- ~~`UNKNOWN`: the concrete `dopemux init` marker(s) and workspace-identity fields~~ → **RESOLVED** in TP-DCP-MCP-RO-0003: init marker = `.dopemux/`; identity = `.repo_id`; detection = `get_workspace_root()`/`validate_workspace()`. See [`DOPEMUX_INIT_REGISTRY_DISCOVERY.md`](DOPEMUX_INIT_REGISTRY_DISCOVERY.md).
- ~~`UNKNOWN`: whether dopemux already exposes a project list/registry primitive~~ → **RESOLVED**: no `list_projects` CLI; the global `~/.dopemux/config.json` is an opened-workspaces cache (eligibility, not exposure); the facade keeps its own explicit allowlist. (Discovery §4.)
- `CONFLICTING` (operator decision, repo-wide): repo-root marker fragmentation — `.repo_id` vs `.dopetaskroot` (`operator_workflows.py:141`) vs the **absent** `.n` (referenced by some task packets). The facade adopts `.repo_id` for identity per `dcp_project_resource_map.schema.json`; repo-wide unification is out of facade scope.
- `PROPOSED`: exact location and load mechanics of the facade registry file (TP-DCP-MCP-RO-0004).
