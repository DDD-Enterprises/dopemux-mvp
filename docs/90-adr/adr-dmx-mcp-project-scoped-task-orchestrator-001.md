---
id: adr-dmx-mcp-project-scoped-task-orchestrator-001
title: 'ADR-DMX-MCP-PROJECT-SCOPED-TASK-ORCHESTRATOR-001: Project-Scoped Kotlin Task
  Orchestrator Instances on Leased Ports'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-28'
last_review: '2026-07-28'
next_review: '2026-10-26'
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
  - TP-DMX-MCP-PROJECT-SCOPED-TASK-ORCHESTRATOR-001
  - adr-dmx-mcp-peer-project-preflight-001
  - adr-mcpint-001
  - adr-task-orchestrator-as-workflow-authority
prelude: 'ADR-DMX-MCP-PROJECT-SCOPED-TASK-ORCHESTRATOR-001: Project-Scoped Kotlin Task
  Orchestrator Instances on Leased Ports (adr) for dopemux documentation and developer
  workflows.'
---
# ADR-DMX-MCP-PROJECT-SCOPED-TASK-ORCHESTRATOR-001

## Project-Scoped Kotlin Task Orchestrator Instances on Leased Ports

**Status:** PROPOSED
**Decision date:** 2026-07-28
**Owner:** Dopemux operator and MCP lifecycle authority
**Scope:** Kotlin Task Orchestrator jar (`ghcr.io/jpicklyk/task-orchestrator`), its wrapper scripts, `mcp_catalog.yaml`, the port lease registry, generated `.mcp.json` / `.envrc.dopemux-mcp`
**Governing design:** `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md` §1.2, §10.1 (supervisor ruling D1, 2026-07-28)
**Implementation packet:** P-24 (`TP-DMX-MCP-PROJECT-SCOPED-TASK-ORCHESTRATOR-001`)
**Does not cover:** the Python `:8000` compose service of the same name (design §10.2 / M11)

---

## 1. Decision summary

The Kotlin Task Orchestrator becomes **project-scoped**: exactly one jar per project, where "project" is the
git **common-dir**–derived root, shared by every worktree of that repo.

1. Runtime identity is aligned with the storage identity the jar already has (SQLite under
   `~/.local/share/dopemux-mission-control/task-orchestrator/<workspace_id>/current-tasks.db`).
2. Each project holds **one leased port** in the runtime lease registry. `7890` stops being a reserved singleton.
3. Each repo's `.mcp.json` endpoint is **generated from that project's lease**.
4. Starting project B must never kill, replace, adopt, or mutate project A's process, container, lease, data
   directory, or metadata.
5. `state_scope: multi_project_singleton` remains **NOT AUTHORIZED**. This ADR removes the *port* bottleneck,
   never the *authority* wall: sharing workflow authority inside one process stays banned.
6. `dopemux mcp switch-project` survives **only** as a transitional compatibility path, retired when this
   ADR's implementation lands.

---

## 2. Claim ledger

### OBSERVED

* Storage is already per-project: `task-orchestrator-current-stdio.sh:97-111` derives
  `workspace_id = slug(basename(project_root)) + "-" + sha256(project_root)[:16]` from
  `git rev-parse --git-common-dir` and roots `data_dir` at it.
* The HTTP wrapper hardcodes port `7890` and publishes `127.0.0.1:7890:7890`
  (`task-orchestrator-http-singleton.sh:150,183`), so one project is reachable at a time.
* Both wrappers **kill and replace** every container matching the container name *or* mounting the same
  `data_dir` (`...stdio.sh:186-203`, `...http-singleton.sh:265-273`), and both re-derive identity in bash
  rather than consuming `src/dopemux/mcp/project_identity.py:60-130`.
* `mcp_catalog.yaml:390-406`: `state_scope: single_active_project`, `port_policy: reserved_singleton`,
  `reserved_port: 7890`, `management_model: wrapper-singleton`.
* `port_allocator.py:33` makes TO the only `RESERVED_SINGLETON_IDENTITY_PREFIX` entry;
  `port_allocator.py:51-66` additionally recognises TO as reserved by a back-compat heuristic
  (`default_port_base == 7890` **and** `port_var == TASK_ORCHESTRATOR_HTTP_PORT`) even if the catalog changes.
  Reserved roles are never leased (`port_allocator.py:396-465`).
* `task_orchestrator_identity.py:277-290`: the upstream jar exposes **no** `/info` or `/health`. Project
  identity is provable only from Docker labels, the `/app/data` mount, and wrapper metadata.
* Live state 2026-07-28 (evidence §1): `task-orchestrator-dnh_crm-9a4e9aa8a329cdd5` holds `127.0.0.1:7890`;
  dopemux-mvp has no reachable orchestrator. PR #1086 was closed because it bundled an unapproved
  `multi_project_singleton` authority change with the peer-project preflight repair — a governance rejection,
  not a technical-safety finding (evidence §5).

### INFERRED

* `serverInfo.name` is a constant service-family string, so an MCP `initialize` probe proves *which service*
  answers a port, never *which project* owns it. Per-port ownership proof must come from `dopemux.*` labels
  and the `/app/data` mount source.
* Kill-and-replace is correct **within** a project (prevents two JVM writers on one SQLite file) and wrong
  **across** projects. The predicate is the defect, not the mechanism.
* Storage is already disjoint, so concurrent per-project jars add no shared state; today's only contended
  resource is the TCP port.

### UNKNOWN

* Whether external operator config (Codex global launcher, `.vibe/config.toml`, IDE settings) hardcodes
  `7890` outside this repo's generated artifacts — **OPEN**; a sweep is a precondition, not an assumption.
* Whether the jar behaves correctly on a non-7890 port and never persists the port in state — **OPEN**,
  resolved by the P-24 smoke test.
* Whether a future upstream release exposes an identity endpoint that would let a probe prove ownership
  without Docker inspection — **OPEN**; nothing here may depend on it.

---

## 3. Context

Task Orchestrator is the workflow authority. Its storage has always been per-project, but its runtime is
pinned to one fixed host port, so "who owns 7890" silently decides which repo's workflow truth an agent
reads. Today that answer is `dNh_CRM`: any Dopemux agent talking to `:7890` is answering from another repo's
database while every health check reports green.

`adr-dmx-mcp-peer-project-preflight-001` separated peer instances from ownership collisions for ConPort and
dope-memory and deliberately left TO under `single_active_project`, stating that a change required an
independent architecture decision. This ADR is that decision, and it does **not** revive
`multi_project_singleton`: one process per project keeps the authority wall where the storage wall already is.

---

## 4. Decision

### 4.1 Sharing class and identity

TO is `sharing_class: project` (design §1.1). Identity is computed by the canonical identity module
(`identity.py`, design P-02 / §2.2) and **consumed** by the wrappers, never re-derived:

| Field | Source | Note |
| --- | --- | --- |
| `project_root` | parent of `git rev-parse --git-common-dir` | identical for every worktree of a repo |
| `project_id` | `f"{canonical_slug(project_root.name)}-{sha256(project_root)[:16]}"` | container name, labels, lease |
| `workspace_id` | `project_id` | the jar's data-dir key; the two MUST NOT diverge |
| `worktree_root` | `git rev-parse --show-toplevel` | diagnostics only; never a scoping key |

Two derivation chains for one id is the defect class that already produced this repo's duplicate volume
pairs; it is not repeated. **Migration guard:** if the recomputed `workspace_id` differs from an existing
on-disk data-dir name, start FAILS with a named remedy. A silent recompute would orphan a task database.

### 4.2 Port model: leased, not reserved

`7890` ceases to be a reserved singleton. TO joins the **leased** tier (design §3.1) with
`default_port_base: 7890` as a *preferred candidate only*.

1. The lease key is the **project** (`scope: project`, keyed on `project_root`); all worktrees of a repo
   resolve to one lease.
2. First allocation prefers `7890`, then the standard span scan. The registry, not the formula, is authority.
3. The current `7890` holder keeps it by **adopting a lease for it**, not by privilege; afterwards `7890` is
   an ordinary leased port whose holder happens to be that project.
4. `reserved_port: 7890` is removed from the catalog **and** the back-compat heuristic at
   `port_allocator.py:51-66` is deleted. Leaving it would silently keep TO reserved after the catalog
   changed — a false-green of the exact kind this repo has been burned by.
5. `stop` releases the lease; `reconcile` (P-10) marks stale leases whose container is gone. Lease GC (P-09)
   is a hard prerequisite — otherwise every abandoned project leaks a port permanently.

### 4.3 Endpoint generation

Each repo's `.mcp.json` entry and `.envrc.dopemux-mcp` `TASK_ORCHESTRATOR_HTTP_PORT` are generated from that
project's lease through the existing `url_template`. No hand-written port, and **no `7890` fallback**: a
missing lease is a generation failure, not a silent default.

### 4.4 No cross-project mutation

Kill-and-replace becomes project-scoped. A container is eligible for `docker rm -f` only when *all* hold:
its `dopemux.project_id` equals this project's; its `/app/data` mount source equals this project's
`data_dir`; and it is not the healthy HTTP singleton this project is deferring to (existing stdio defer
path).

Any other container — foreign-labelled, unlabelled, or ambiguous — is never stopped, adopted, renamed,
relabelled, or reused; it is reported. Removing one stays an explicit operator action (`migrate --evict`,
design §7), never a side effect of `start`. A foreign container is also no longer a *blocker*, because this
project no longer needs its port; the peer-preflight ADR §4.2 port-collision rules apply unchanged to
whatever port this project's lease names.

### 4.5 Catalog changes

`mcp_catalog.yaml` (authority per ADR-MCPINT-001), service `task-orchestrator`:

| Key | From | To |
| --- | --- | --- |
| `state_scope` | `single_active_project` | `per_project` |
| `port_policy` | `reserved_singleton` | `leased` |
| `reserved_port` | `7890` | *(removed)* |
| `default_port_base` | `7890` | `7890` (preferred candidate only) |
| `management_model` | `wrapper-singleton` | `wrapper-project` |
| `sharing_class` | *(absent)* | `project` |
| `identity_scope` | `per-repo` | unchanged |

`management_model` must change: `wrapper-singleton` sets `fixed=True` in `build_role_requests`
(`port_allocator.py:164-171`), suppressing rebind. A leased service that cannot rebind is not leased.

### 4.6 Identity probing

* TO is **removed** from `RESERVED_SINGLETON_IDENTITY_PREFIX`; that map's remaining purpose (design §3.2) is
  host singletons, which TO no longer is. If TO is its last entry at implementation time, the constant is
  obsolete for this service and must not be retained "just in case".
* Verification becomes **per-leased-port**: (a) MCP `initialize` returns the expected `serverInfo.name`
  prefix — *service-family evidence only*; **and** (b) the container publishing that port carries this
  project's `dopemux.project_id` and `/app/data` mount. A pass on (a) alone never yields `owned`.
* `evaluate_fixed_port_state()` is generalised to take the leased port as a required argument;
  `DEFAULT_TO_PORT = 7890` survives only as a legacy-detection constant for migration and doctor, commented
  as such. Wrapper metadata keeps its refuse-to-overwrite-another-project guard
  (`task-orchestrator-http-singleton.sh:88-93`) and records the leased port.

### 4.7 Migration from today's single `7890` holder

Per-project and reversible; no data moves, because no data is shared.

| Step | Action | Failure posture |
| --- | --- | --- |
| M-TO-1 | Sweep for hardcoded `7890` outside generated artifacts (repo, `.vibe`, Codex launcher, agent files, docs) | any unresolved hit blocks the flip |
| M-TO-2 | Adopt a project lease for the live `7890` holder (dNh_CRM) with proof: labels + mount + `initialize` | no proof ⇒ no adoption; operator resolves manually |
| M-TO-3 | Start this project's jar on its leased port; regenerate `.mcp.json` + `.envrc.dopemux-mcp` atomically | partial write ⇒ both files left untouched |
| M-TO-4 | Verify both jars serve concurrently with disjoint SQLite files | failure ⇒ stop the new jar, revert generated config |
| M-TO-5 | Delete `switch-project` and its doc references | — |

Design step **M12** ("resolve 7890 ownership via `switch-project`") is superseded by M-TO-2/M-TO-3. Design
**M10** (repointing `.vibe/config.toml` off the `:8000` shadow twin) stays blocked until this implementation
lands and can supply a project-correct endpoint; a naked static `:7890` remains unsafe.

### 4.8 `switch-project` disposition

Transitional compatibility only: the documented remedy for a workspace_id mismatch *until* this ADR is
implemented, never the steady-state answer in any doc, agent file, or error string afterwards. Its command,
help text, and every doc reference are **deleted** as a P-24 acceptance criterion. Per AGENTS.md §12.6 it is
currently PLANNED, not implemented — if still unimplemented when P-24 lands, never implement it.

---

## 5. Non-goals

1. **No shared-authority TO.** `multi_project_singleton` is not authorized and may not return as an
   optimisation; one process serves exactly one project.
2. **No state merging between projects** — no cross-project queries, federated views, shared work-item ids,
   or migration combining two `current-tasks.db` files.
3. **No change to the Python `:8000` service** (design §10.2 / M11: rename, not retire).
4. **No worktree-scoped orchestrators** — that reintroduces the concurrent JVM writers kill-and-replace
   exists to prevent.
5. **No automatic stopping of foreign containers** (peer-preflight invariant 5) and **no partial-start
   semantics change** (peer-preflight §4.5).

---

## 6. Relationship to ADR-DMX-MCP-PEER-PROJECT-PREFLIGHT-001

**Superseded on acceptance:** §4.4 (TO remains single-active-project, incl. the `single_active_project` /
`reserved_port: 7890` block); invariant 4 (one active owner on 7890); validation requirements 6 and 9 (both
conditioned on the reserved-port model removed here); the consequence "Full `mcp up` can still block when
another project owns Task Orchestrator."

**Retained:** §4.1–4.3 peer-vs-collision classification, incl. `DOCKER_CONTAINER_WRONG_PROJECT` staying in
`BLOCKING_FINDING_CODES` — now evaluated against the *leased* port; §4.6 Docker-unavailability stays
fail-closed for mutations; invariants 1, 2, 3, 5, 6, 7, 9, 10; invariant 8 ("no shared Task Orchestrator
state"), reaffirmed verbatim; and §7's rejected alternative "Share Task Orchestrator across projects", which
this ADR does **not** overturn — parallel isolated instances are the opposite of sharing. That ADR remains
`PROPOSED`; this one does not alter its status.

---

## 7. Invariants

1. One TO process per project; never more, never shared.
2. Project identity is derived once, in `identity.py`, from the git common dir.
3. The data directory's `workspace_id` always equals the `project_id` used for container, labels, and lease.
4. A project's start path mutates only containers, leases, data dirs, and metadata whose project identity
   matches its own.
5. No generated artifact contains a TO port that did not come from a lease.
6. A live MCP handshake proves service family, never project ownership.
7. Two projects' SQLite databases are distinct files, never opened by one process.
8. Docker-unavailable never produces a positive ownership claim.
9. No config path selects another project's orchestrator without an explicit operator override naming it.

---

## 8. Validation requirements

Acceptance requires executed tests proving:

1. **Concurrency** — two repos run jars simultaneously; each answers `initialize` and serves its own items.
2. **SQLite separation** — distinct `<workspace_id>/current-tasks.db` mount sources per `docker inspect`,
   confirmed by on-disk path/inode comparison, not name resemblance.
3. **Non-interference** — starting B leaves A's container id, uptime, lease row, and data-dir mtime unchanged.
4. **Restart recovery** — killing A and re-running `start` restores A on its leased port without touching B.
5. **Worktree sharing** — two worktrees of one repo resolve to one `project_id`/lease/container; the second
   starts nothing new.
6. **Stale-lease reconciliation** — a TO lease whose container is gone is marked stale and its port reusable.
7. **Non-7890 operation** — a project on some other leased port is functional end to end (resolves §2 UNKNOWN).
8. **Endpoint generation** — generated artifacts carry the leased port; a missing lease fails generation.
9. **Foreign-container safety** — an unlabelled or foreign container on the preferred port is never removed;
   the project allocates elsewhere.
10. **No reserved-singleton residue** — TO absent from `RESERVED_SINGLETON_IDENTITY_PREFIX`, back-compat
    branch gone.
11. **Identity migration guard** — recomputed `workspace_id` ≠ existing data dir fails start with the remedy.
12. **`switch-project` absence** — grep guard over code, help output, and docs.

Prerequisites that must merge first: **P-02** (`identity.py`), **P-09** (lease GC), and **P-10**
(`mcp reconcile --reap`). Leased TO ports without lease GC create permanent per-project port leaks, and P-24
must not create leased TO instances before the implemented stale-lease cleanup path exists. Final completion requires executed tests, codereview,
precommit, embedded audit, proof artifacts, and current PR Steward readiness. Tool output alone is not proof.

---

## 9. Rollback

Revert plus restart; no data migration is authorized, so nothing must be un-migrated. P-10 is a required
precondition for this rollback path; P-24 must not land before `dopemux mcp reconcile --reap` exists. (1) Revert the
implementation commits — catalog fields, allocator changes, wrapper scripts, identity wiring. (2) `dopemux
mcp reconcile --reap` the TO leases created under this model; they are ordinary lease rows. (3) Stop the
per-project jars and restart a single jar on `7890` via the reverted wrapper. (4) Regenerate `.mcp.json` /
`.envrc.dopemux-mcp`, which return to the fixed-port template.

Each project's `current-tasks.db` is untouched by both the flip and the rollback — the databases were already
per-project before this ADR and remain so after. That is what makes the decision cheap to reverse.

---

## 10. Rejected alternatives

| Alternative | Why rejected |
| --- | --- |
| `multi_project_singleton` (one process, many projects) | Supervisor ruling: puts several projects' workflow authority behind one process boundary — a governance change, not a port fix. The direction PR #1086 was closed for. |
| Keep the reserved port, add `switch-project` | Makes "which repo is the orchestrator answering for" a mutable global. Today's live state (dNh_CRM on 7890 while Dopemux agents query it) is the demonstration. |
| Per-worktree orchestrators | Concurrent JVM writers on one SQLite file. |
| Reverse-proxy demultiplexer on 7890 routing by project header | A new always-on component plus an identity-forwarding contract to solve what the lease registry already solves. Reconsider only if a client proves unable to accept a variable port — **OPEN**. |
| Keep `7890` reserved for a "primary" project, lease the rest | A privileged project is a hidden global; every project must resolve its endpoint the same way. |

---

## 11. Consequences

**Positive.** Two projects operate concurrently without a port fight; "the orchestrator answered for the
wrong repo" becomes structurally impossible; runtime scope finally matches the storage scope the jar always
had; a whole tier of port policy (`reserved_singleton`) and a whole command (`switch-project`) disappear.

**Negative.** TO ports become variable, so anything holding a hardcoded `7890` breaks until swept (M-TO-1);
the fleet gains one long-lived container per active project; TO now depends on lease GC (P-09) being real,
where before it depended on nothing.

**Neutral.** No task data moves, no schema changes, no authority boundary moves. Docker remains the only
proof surface for TO ownership until upstream exposes an identity endpoint (§2 UNKNOWN).

---

## 12. Status transition

`PROPOSED` → `ACCEPTED` when: P-02, P-09, and P-10 are merged; the P-24 packet is approved and stays within this
ADR's scope; all §8 validations pass with executed evidence; the hardcoded-`7890` sweep (M-TO-1) returns no
unresolved hits; embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS` with PR Steward `READY`; and no
`multi_project_singleton` state scope appears anywhere in the change.
