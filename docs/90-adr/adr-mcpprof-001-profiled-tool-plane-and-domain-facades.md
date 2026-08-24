---
id: ADR-DMX-MCPPROF-001
title: 'Profile-Selected MCP Tool Plane and Repo-Domain Read Facades'
type: adr
owner: '@hu3mann'
author: 'GPT-5.6 Thinking, draft for operator review'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
status: accepted
prelude: Adds profile-selected progressive disclosure, locked tool inventories, official GitHub read profiles, a Playwright CLI/MCP split, and a generic local repo-domain read-facade contract without changing domain authority.
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-mcpint-001
    - adr-mcpint-002
    - ADR-DCP-MCP-RO-0009
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR-DMX-MCPPROF-001: Profile-Selected MCP Tool Plane and Repo-Domain Read Facades

**Status:** Accepted
**Decision owner:** Operator
**Acceptance date:** 2026-07-26
**Operator acceptance phrase:** `ACCEPT AND EXECUTE TP-MCP-PROFILE-PROGRAM-001-R1`
**Supervisor packet:** `TP-MCP-PROFILE-PROGRAM-001-R1`
**Unlocks:** `TP-DMX-MCPPROF-001`
**Implementation gate:** Authorized for `TP-DMX-MCPPROF-001` only; does not accept repo-specific facade ADRs or write-capable profiles

## Context

Dopemux already has an accepted agent-exposure model:

- catalog-generated configuration rather than per-agent hand editing;
- the DCP read-only facade as the universal read plane for agents without attribution;
- runtime enforcement for writes rather than trusting config distribution;
- split authority across workflow, structured context, chronicle, retrieval, bridge, and operator-support systems.

The remaining problem is not the absence of MCP servers. It is excessive simultaneous exposure and repo-specific semantic gaps.

A coding agent frequently sees servers that are irrelevant to its current task. Several surfaces overlap in appearance while owning different authority slices. Browser and research servers carry large schemas and context payloads. Generic database servers would bypass application policies and proof contracts. Repo-specific agents still need concise domain reads that generic code and retrieval tools cannot provide safely.

The current accepted ADR-MCPINT-002 decides *which agents may reach which authority classes*. It does not define task-selected profiles, tool-inventory budgets, the CLI-versus-MCP browser split, or the contract for repo-native read facades. This ADR is a narrow amendment, not a replacement.

## Decision

### 1. `mcp_catalog.yaml` remains the exposure source of truth

Profiles are declared in or generated strictly from `mcp_catalog.yaml`. No second global profile catalog may become an independent authority.

Every generated client configuration must identify one explicit profile. There is no implicit `all` profile and no silent fallback to every available server.

Profiles are exposure projections. They do not change the authority of the services they expose.

### 2. Initial profile set

| Profile | Intended use | Initial server classes |
|---|---|---|
| `core-code` | Normal implementation and code navigation | GitHub read-only, ConPort, dope-memory, task-orchestrator, Serena |
| `core-retrieval` | Broad code/docs retrieval | GitHub read-only, ConPort, dope-memory, task-orchestrator, dope-context |
| `planning-audit` | Planning, challenge, audit | GitHub read-only, dope-context, PAL stdio |
| `ui-audit` | Exploratory UI and browser-state investigation | GitHub read-only, Playwright MCP, repo-domain-read |
| `research-docs` | Current library/vendor documentation | GitHub read-only, Context7 |
| `research-web` | Multi-source public research | GitHub read-only, GPT Researcher |
| `security` | Security review | GitHub security read toolsets, Semgrep |
| `pr-steward` | PR evidence intake | GitHub PR/review/thread/commit/Actions reads, proof/facade reads |

`core-code` and `core-retrieval` are alternatives, not cumulative defaults.

### 3. Tool inventories are locked and reviewed as evidence

Each generated profile emits:

- selected servers;
- visible tool names;
- visible tool count;
- tool-schema digest;
- profile digest;
- excluded write/admin tools;
- lifecycle and health state.

Any increase in visible tools or server count must be represented as an explicit checked-in manifest delta with rationale. CI blocks unexplained drift. This ADR does not establish a universal magic number; the checked-in baseline is the budget.

### 4. Official GitHub MCP, least privilege by profile

Dopemux uses GitHub's official MCP implementation or official hosted surface. Third-party clones do not satisfy this decision.

Normal profiles use read-only mode. Toolsets are allowlisted by profile:

- `core-*`: repositories, issues, pull requests, and narrowly required context reads;
- `security`: code security, secret protection, and advisory reads;
- `pr-steward`: pull requests, reviews, review threads, commits, statuses, and Actions reads.

GitHub writes are not authorized by this ADR. A later ADR must define an attributed write profile if one is needed.

### 5. Playwright CLI is default; Playwright MCP is specialized

Coding agents use Playwright CLI, committed tests, and repo scripts for routine browser automation and CI because this path avoids loading large MCP schemas and page trees into every task.

Playwright MCP is enabled only in `ui-audit` for persistent browser state, accessibility-tree inspection, exploratory diagnosis, screenshot/trace capture, and iterative UI reasoning.

Playwright MCP is not a posting, purchasing, credential-entry, or production-mutation authority.

### 6. Generic repo-domain read-facade contract

Dopemux supports one optional per-repo server slot named `repo-domain-read`.

The executable contract is fixed:

```text
<repo-root>/scripts/mcp/domain-read
```

The generator may expose it only when:

1. the resolved repo root matches the active project identity;
2. the executable is a tracked regular file under the repo root;
3. symlink and path-escape checks pass;
4. a repo-local tool manifest validates;
5. every tool is classified `READ_ONLY_NO_DURABLE_SIDE_EFFECT`;
6. negative discovery tests prove write/admin tools are absent;
7. the server uses stdio or loopback-only transport;
8. no secret values are embedded in generated config.

The fixed repo-local manifest path is:

```text
mcp/domain-read-tools.json
```

The manifest includes tool name, input schema digest, output schema digest, authority source, side-effect classification, sensitivity class, and maximum result bound.

### 7. Domain facades use application services, not generic databases

A domain facade may query canonical application services and deterministic projections. MCP handlers must not become an alternate SQL/HTTP implementation of business logic.

Direct generic SQLite, PostgreSQL, Qdrant, filesystem, memory, or arbitrary HTTP tools are forbidden in default profiles. A bounded sandbox exception requires a separate profile and explicit operator approval.

### 8. Reads with durable side effects are not read-only

A route that writes audit rows, refreshes an index, forks state, updates access timestamps, triggers sync, or performs any durable mutation is not eligible for `repo-domain-read`, even if its product label says “search” or “get.” It remains blocked until a pure application read exists.

### 9. Write and admin separation

The following remain absent from every profile created by this ADR:

- ConPort admin tools;
- workflow transitions;
- memory correction, reflection generation, or storage;
- indexing, sync, clear, or autonomous-control operations;
- shell/editor tools from code-intelligence servers;
- outbound communication;
- posting, purchase, captcha, or production browser mutation.

A config file cannot grant a write. Runtime identity, actor attribution, accepted authority, and proof gates remain mandatory.

### 10. Profile selection and failure behavior

The operator selects a profile through Dopemux CLI generation/startup surfaces. Unknown profile, unavailable required server, tool-manifest mismatch, digest drift, ambiguous repo identity, or lifecycle conflict fails closed.

No profile silently expands because a server is installed.

## Invariants

1. Existing authority boundaries remain unchanged.
2. `mcp_catalog.yaml` remains the global catalog authority.
3. Generated configs are derived; hand-edited agent configs are not authoritative.
4. PAL HTTP remains health-only unless a separate accepted decision changes it; PAL MCP uses stdio.
5. Bridges, retrieval outputs, caches, and facades remain non-authoritative projections.
6. Normal GitHub exposure is read-only.
7. The domain-facade contract cannot select arbitrary executables.
8. Unknown side effects block exposure.
9. Tool-count/schema drift is explicit and reviewable.
10. A profile cannot weaken runtime authorization or proof requirements.

## Alternatives considered

### Load all healthy servers

Rejected. Health proves reachability, not relevance, authority, or safe tool choice.

### Maintain bespoke configs per agent and repo

Rejected. This recreates the configuration divergence ADR-MCPINT-001 and ADR-MCPINT-002 were written to remove.

### Add generic database MCP servers

Rejected. They bypass application-layer policy, event contracts, redaction, approval, and proof.

### Put repo-specific business tools in Dopemux

Rejected. Dopemux owns control and coordination, not CRM or ad-operations business logic. The generic facade contract keeps domain code in its repo.

### Use Playwright MCP for all browser work

Rejected. Routine coding and CI benefit from CLI/test determinism and smaller context; MCP is reserved for stateful investigation.

## Consequences

### Positive

- smaller, task-relevant tool surfaces;
- explicit and diffable tool budgets;
- reduced authority ambiguity;
- repo semantics without generic database exposure;
- consistent GitHub least-privilege profiles;
- browser tooling matched to the actual task class.

### Costs

- profile generation and doctor logic become more complex;
- repo-domain facades require contracts, tests, and maintenance;
- some tasks require switching profiles rather than seeing every tool at once;
- blocked “read” routes may require application refactoring to become pure.

### Failure direction

When profile, identity, tool manifest, lifecycle, or side-effect truth is unknown, the server or tool is omitted and the profile reports `BLOCKED`. Missing convenience is preferred over accidental authority.

## Migration

1. Add proposed ADR and profile schema/tests without changing default generation.
2. Add profile rendering and inventory/digest output.
3. Add official GitHub read profiles and Playwright/Context7/GPT Researcher/Semgrep profile placement.
4. Add the generic `repo-domain-read` contract and negative validation.
5. Implement dNh and adOps facades in their own repositories.
6. Generate and smoke the repo profiles.
7. Remove or quarantine legacy hand-authored configs only after exact client-consumer proof.

## Verification

- schema validation for every profile;
- deterministic generation repeated twice with byte-identical output;
- exact visible tool inventory and digests;
- unknown profile fail-closed test;
- missing/unsafe domain executable negative tests;
- write/admin tool exclusion tests;
- GitHub read-only negative mutation test;
- Playwright absent from normal coding profiles;
- PAL HTTP absent as an MCP transport;
- profile-specific doctor output;
- full MCP generator and lifecycle regression suites;
- embedded independent audit and PR Steward readiness.

## Acceptance

**Accepted 2026-07-26** via operator phrase `ACCEPT AND EXECUTE TP-MCP-PROFILE-PROGRAM-001-R1` under supervisor packet `TP-MCP-PROFILE-PROGRAM-001-R1`.

Operator acceptance authorizes packet `TP-DMX-MCPPROF-001` only. It does not accept either repo-specific facade ADR and does not authorize any write-capable profile.
