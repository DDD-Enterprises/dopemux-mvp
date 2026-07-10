---
id: dcp-mcp-readonly-registry-v2-contract
title: DCP Read-Only MCP Facade — Exposure Target Registry v2 Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-09'
last_review: '2026-07-09'
next_review: '2026-10-07'
prelude: Registry v2 (opaque target_id, 9-family allowlist, static ADR resolution-class/posture table, deterministic content-hash generation) and pure resolver-core contract for the read-only MCP evidence facade, per ADR-DCP-MCP-RO-0009.
---

# Registry v2 Contract

> **Status.** `OBSERVED` / implemented in TP-DCP-MCP-RO-0010:
> `services/dcp-readonly-facade/src/dcp_facade/registry_v2.py`,
> `resolver_core.py`, `capability.py`,
> `services/dcp-readonly-facade/schema/registry_v2.schema.json`. v1
> (`registry.py` / `resolver.py`, see
> [`MULTI_PROJECT_REGISTRY_CONTRACT.md`](MULTI_PROJECT_REGISTRY_CONTRACT.md))
> is **kept, unmodified, alongside** v2 — this packet does not remove or
> rewrite v1. Runtime instance registry join, canonical MCP catalog join,
> candidate discovery, live protocol verification, ownership evidence
> adjudication, and the read-only backend adapter gate remain out of scope
> and are covered by later packets in the `DCP-MCP-RO` series.

## 1. Why v2

ADR-DCP-MCP-RO-0009 tightens the v1 contract in four ways that registry v2
implements:

1. The caller-facing handle is renamed `project_id` → **`target_id`** — an
   opaque exposure-consent identifier, never a filesystem path, worktree
   hash, runtime instance ID, or backend workspace ID.
2. Service bindings are renamed `service_profiles` (free-form,
   caller-adjacent connection detail) → **`service_policies`** (a `family ->
   {enabled}` map). The registry no longer carries `base_url` / ports /
   workspace IDs for a family — those become operational-runtime-registry
   concerns in later packets. Registry v2 declares **consent + policy**
   only: whether a family is present and policy-enabled for a target.
3. Service family identifiers are restricted to **exactly the 9** families
   required by ADR-DCP-MCP-RO-0009 §"Required Service Families". The bare,
   unqualified name `task-orchestrator` is explicitly **forbidden** — it is
   split into `to_mcp_wrapper` (host-singleton MCP wrapper, single active
   project) and `to_compose_rest` (host-singleton REST, project-routed).
4. A registry-wide **generation id** — a deterministic content hash, never a
   timestamp or random value — is exposed for future cache-key and
   resolution-receipt use (ADR §"Caching and Resolution Receipts").

## 2. Registry v2 Schema

Machine-checkable schema:
[`services/dcp-readonly-facade/schema/registry_v2.schema.json`](../../../../services/dcp-readonly-facade/schema/registry_v2.schema.json)
(JSON Schema draft-07). Example:
[`services/dcp-readonly-facade/registry.example.yaml`](../../../../services/dcp-readonly-facade/registry.example.yaml).

```yaml
approved_roots:
  - /abs/approved/root

targets:
  - target_id: "dopemux-main"             # opaque caller-facing handle (the ONLY handle ChatGPT may supply)
    workspace_path: "/abs/approved/root/dopemux-mvp"
    enabled: true                          # exposure switch; default false
    binding_mode: "PRIMARY_CHECKOUT_ONLY"  # default AND only supported value
    identity:                              # matched against the workspace's .repo_id
      project: "dopemux-mvp"               # REQUIRED; must equal .repo_id `project=`
      owner: "hu3mann"                     # OPTIONAL; enforced only when present
    service_policies:                      # family -> { enabled } — family MUST be one of the 9 ADR-0009 names
      conport:
        enabled: true                      # "configured": declared + policy-enabled — NOT proof of live/callable
      dope_memory:
        enabled: true
```

### 2.1 Field notes

| Field | Notes |
| --- | --- |
| `target_id` | The **only** handle a caller (ChatGPT) may supply. Required, non-empty string. |
| `workspace_path`, `approved_roots` | Registry-owned; callers cannot set or override them. |
| `enabled` | Defaults to `false`; omission means not exposed. Eligibility (`dopemux init`) is not exposure — see §2 of [`MULTI_PROJECT_REGISTRY_CONTRACT.md`](MULTI_PROJECT_REGISTRY_CONTRACT.md), unchanged in v2. |
| `binding_mode` | Defaults to, and in this packet **only accepts**, `PRIMARY_CHECKOUT_ONLY` (ADR §"Default Worktree Exposure Policy"). A target binds to exactly one operator-approved workspace; the resolver never enumerates, scans, or auto-selects sibling/newest/most-recent worktrees. Any other value is rejected fail-closed at parse time — this packet implements no other binding mode. |
| `identity.project` | Required; matched against the workspace's `.repo_id` `project=` value. |
| `identity.owner` | Optional; when present, matched against `.repo_id` `owner=`. Absent → owner check is skipped, never blocked for a field the registry didn't declare. |
| `service_policies.<family>.enabled` | Defaults to `false`. `configured` (as reported by `capability.py`) is exactly `family present AND enabled: true`. See §5. |

### 2.2 Allowed service families (exactly 9)

Per ADR-DCP-MCP-RO-0009 §"Required Service Families" — enforced by both the
JSON Schema (`additionalProperties: false` under `service_policies`) and the
Python parser (`registry_v2.ALLOWED_SERVICE_FAMILIES` /
`FORBIDDEN_FAMILY_NAMES`):

| Family | Resolution class | ChatGPT posture |
| --- | --- | --- |
| `conport` | `per_worktree_runtime` | `conditional_read_only` |
| `dope_memory` | `per_worktree_runtime` | `conditional_read_only` |
| `to_compose_rest` | `host_singleton_project_routed` | `conditional_get_only` |
| `to_mcp_wrapper` | `host_singleton_single_active_project` | `blocked` |
| `dope_context` | `singleton_per_call_workspace` | `blocked_until_read_bridge` |
| `serena` | `singleton_per_call_workspace` | `blocked_until_inventory` |
| `pal` | `host_singleton` | `blocked` |
| `docker_mcp_gateway` | `host_singleton` | `blocked` |
| `desktop_commander` | `host_singleton` | `blocked` |

This table is a **module constant**
(`registry_v2.FAMILY_POLICY_TABLE`) — static ADR data, not derived from any
live probe. The bare, unqualified name `task-orchestrator` is rejected at
both layers: the schema has no such property under `service_policies`
(`additionalProperties: false`), and the parser rejects it explicitly via
`FORBIDDEN_FAMILY_NAMES` even if some future schema revision were looser.

## 3. Fail-Closed Parsing Rules

Mirrors v1's fail-closed posture (`registry.py` §4), extended for v2:

1. A malformed target entry (missing `target_id`/`workspace_path`/
   `identity`/`identity.project`; wrong field types; unsupported
   `binding_mode`; forbidden/unknown service family; malformed
   `service_policies` entry) is **dropped** — recorded in `warnings`, never
   exposed loosely. **The whole target is dropped**, not just the offending
   family — a target with one bad family entry is not partially trusted.
2. `enabled` defaults to `false` when omitted.
3. A duplicate `target_id` within one registry document: the **later**
   entry is dropped (first-registered wins), recorded in `warnings`.
4. A registry root that is not a mapping, or whose `targets`/
   `approved_roots` are not lists, is treated as empty (with a warning) —
   never partially trusted.
5. `load_registry_v2` on a missing file returns an empty registry with a
   recorded warning (never raises to the caller).

## 4. v1 → v2 Migration

**v1 documents are never silently coerced.** If a document is v1-shaped
(top-level `projects` list, no `targets` key), `parse_registry_v2` fails
closed: it returns an **empty** registry with **one explicit, actionable
warning** naming the field rename (`project_id` → `target_id`, `projects` →
`targets`) and pointing at this document. No targets are loaded from a
v1-shaped document under `parse_registry_v2` — an operator must migrate the
file (or keep running it through v1's `registry.load_registry` /
`resolver.resolve`, which remain fully supported and unmodified) before it
is recognized by v2.

Rationale: v1's `service_profiles` shape (per-family `base_url` / port /
workspace-id detail) is a materially different trust surface from v2's
`service_policies` (family present + policy-enabled only, no connection
detail). Coercing one into the other automatically would either silently
drop operator-configured connection detail or silently invent
registry-v2-shaped consent the operator never declared. Both are exposure
risks; fail-closed with clear guidance is the safer default (ADR
§"Registry Authority Split": the exposure policy registry is operator
consent authority — it must never guess).

Migration steps for an operator upgrading a registry file:

1. Rename the top-level `projects:` key to `targets:`.
2. Rename each entry's `project_id:` field to `target_id:`.
3. Replace each entry's `service_profiles:` block (which carried `base_url`
   / port / workspace-id detail) with a `service_policies:` block
   (`family: {enabled: true|false}` only — no connection detail). Family
   names must be exactly one of the 9 in §2.2 (`task_orchestrator` in v1
   examples splits into `to_mcp_wrapper` and/or `to_compose_rest`).
4. Optionally add `binding_mode: "PRIMARY_CHECKOUT_ONLY"` (this is already
   the default).
5. Point `$DCP_FACADE_REGISTRY_V2` (not the v1 `$DCP_FACADE_REGISTRY`) at
   the migrated file.
6. Validate against
   `services/dcp-readonly-facade/schema/registry_v2.schema.json` before
   deploying.

## 5. Capability Separation: Configured vs Live vs Callable

ADR-DCP-MCP-RO-0009 §"Capability Reporting" requires that "configured,
discovered, or listening must never imply callable." This packet
implements exactly the **configured** half of that separation:

- **`configured`** (`registry_v2.ServicePolicy.configured`,
  `capability.capability_report()`'s `configured` field): `True` iff the
  family is present in the target's `service_policies` **and** that entry
  declares `enabled: true`. This is registry-declared consent + policy
  only — a purely local, deterministic fact derived from the registry file.
- **`live`**: always reported as the literal string `"UNKNOWN"` in this
  packet. Determining whether a runtime is actually live requires a
  socket/backend/container call — out of scope here (see ADR gates
  `RUNTIME_CANDIDATE_FOUND` onward).
- **`callable`**: always `False` in this packet. No backend call is ever
  made by `registry_v2.py`, `resolver_core.py`, or `capability.py`.

`capability_report(resolved: ResolvedTarget) -> list[dict]` returns one
entry per family bound to the resolved target:

```json
{
  "family": "conport",
  "configured": true,
  "resolution_class": "per_worktree_runtime",
  "chatgpt_posture": "conditional_read_only",
  "live": "UNKNOWN",
  "callable": false
}
```

A later packet in the `DCP-MCP-RO` series (runtime instance registry join +
live protocol verification + ownership evidence) is required before `live`
or `callable` can ever become anything other than `"UNKNOWN"` / `false`.

## 6. Resolver-Core Flow

`resolver_core.resolve_target(registry, target_id) -> (ResolvedTarget |
None, reason | None)` — pure, deterministic, no network/socket/external-
process/container calls:

```
target_id
  -> registry lookup            (unknown -> blocked)
  -> enabled check               (disabled -> blocked)
  -> workspace_path -> realpath  (unresolvable -> blocked)
  -> approved-roots containment  (escape -> blocked; symlink-followed BEFORE the check)
  -> eligibility check            (.dopemux/ present + validate_workspace() ok -> else blocked)
  -> identity check                (.repo_id project == identity.project; owner == identity.owner if declared -> else blocked)
  -> .git-derived root split       (see §7 -> no .git -> blocked)
  -> bind service_policies        (already resolved at registry-parse time)
  -> ResolvedTarget
```

Every failure returns a short, **opaque** block reason — never a leaked
absolute path, port, or URL (`target_id` itself is caller-supplied and
opaque already, so it is safe to echo back in reasons like `unknown target:
<target_id>`). This is a stricter posture than v1's `resolver.py`, which
forwards `validate_workspace()`'s raw error string (that string can contain
an absolute path, e.g. `"Path does not exist: <path>"`); `resolver_core.py`
deliberately does not forward it, using a fixed generic message instead.

## 7. `project_root` vs `worktree_root` Derivation

Derived **deterministically from local `.git` metadata only** — no `git`
process is ever spawned by `resolver_core.py`:

- **Primary checkout** (`.git` is a directory): `project_root ==
  worktree_root == workspace`.
- **Linked worktree** (`.git` is a file containing `gitdir: <path>`):
  1. Read the `gitdir:` line → `<main>/.git/worktrees/<name>`.
  2. Read that directory's `commondir` file (typically `../..`, relative to
     itself unless absolute) → resolves to the **common** `.git` directory.
  3. `project_root` = the common `.git` directory's **parent**.
  4. `worktree_root` = `workspace` (the resolved target workspace itself).
- **No `.git` at all** (neither directory nor file): unresolvable —
  **blocked fail-closed** (`"workspace has no resolvable git root"`). A
  target's `workspace_path` MUST point at a real git checkout (primary or
  linked worktree); a non-git directory is never a valid resolution target
  even if it happens to pass eligibility via another marker (e.g.
  `pyproject.toml`).

Both shapes are exercised by real temporary git repositories/worktrees in
`services/dcp-readonly-facade/tests/test_resolver_core.py` (not mocked) — a
linked worktree is built with `git worktree add --detach` in the test
fixture only; `resolver_core.py` itself never invokes `git`.

## 8. Out of Scope (this packet)

Per TP-DCP-MCP-RO-0010 and ADR-DCP-MCP-RO-0009: runtime instance registry
join, canonical MCP catalog join, candidate discovery, Docker/container
inspection, port leases, TCP probes, MCP `initialize`/REST fingerprints,
ownership adjudication, backend calls, tunnel, and authentication. Whether
any runtime is live, owned, or reachable is explicitly **not** determined
here — see §5.

## 9. Related

- ADR:
  [`adr-dcp-mcp-ro-0009-chatgpt-mcp-exposure-targets-runtime-resolution-ownership-evidence.md`](../../../90-adr/adr-dcp-mcp-ro-0009-chatgpt-mcp-exposure-targets-runtime-resolution-ownership-evidence.md)
- v1 contract (kept, unmodified):
  [`MULTI_PROJECT_REGISTRY_CONTRACT.md`](MULTI_PROJECT_REGISTRY_CONTRACT.md)
- Schema:
  [`services/dcp-readonly-facade/schema/registry_v2.schema.json`](../../../../services/dcp-readonly-facade/schema/registry_v2.schema.json)
- Example:
  [`services/dcp-readonly-facade/registry.example.yaml`](../../../../services/dcp-readonly-facade/registry.example.yaml)
