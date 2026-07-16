# 05 — Authority Boundaries & Coexistence Audit

All boundaries below were confirmed against **current runtime/Git state at HEAD == census `b176747`**,
which is authority tier 1. Existence checks via `git cat-file -e b176747:<path>` and `git ls-tree`.

## Hard system boundaries (confirm/reject each)

| Boundary claim | Verdict | Evidence |
|---|---|---|
| `dopemux` remains operator control | CONFIRMED | `src/dopemux/cli.py` command groups; `route` added, not replacing |
| `dopetask` remains execution authority after accepted handoff | CONFIRMED | `scripts/dopetask` present; router stops pre-handoff (state machine, hard invariant) |
| Task Orchestrator = workflow-transition/view authority | CONFIRMED | `services/task-orchestrator/.../agents/__init__.py` present; router projection-only |
| LiteLLM = provider proxy infrastructure | CONFIRMED | `routing_config.py` + litellm_* surfaces present; router observation-only |
| Freeflow = quota/cooldown/paid-cap/route-admission | CONFIRMED | `src/dopemux/freeflow.py` present (SQLite subsystem, UR-INV-004) |
| RTE = specialized extraction-runtime authority | CONFIRMED | `services/repo-truth-extractor/run_extraction_v5.py`, `rte_config.py` present |
| DopeconBridge = adapter/proxy/event transport only | CONFIRMED (doc-grounded) | authority docs (`AGENTS.md`); router does not touch DopeconBridge; not independently runtime-inspected |
| Human approval external to automatic route selection | CONFIRMED | `HumanApprovalRef` external; distinct from OPERATOR_ACCEPTED |
| PR Steward = review-intake/merge-readiness evidence | CONFIRMED | referenced-only; canonical command unresolved (UR-OQ-006, finding -004) |
| `services/task-router` is NOT revived | CONFIRMED | `git ls-tree -r b176747 -- services/task-router` = **0 entries** (no tracked source) |
| `src/dopemux/agent_orchestrator.py` NOT promoted to authority | CONFIRMED | file present but classified LEAVE_ISOLATED; no router dependency on it |
| `services/agents/**` NOT promoted to authority | CONFIRMED | 16 tracked entries present; LEAVE_ISOLATED; router does not route through them |

### The router must not create a second: (all CONFIRMED — negative checks)
provider proxy · quota ledger · proof schema · handoff schema · execution engine · workflow engine ·
release gate · canonical task store · provider-health authority · model-attestation authority.
- `config/universal-router`, `schemas/universal-router`, `src/dopemux/universal_router`,
  `tests/universal_router` all have **0 entries at census** → no pre-existing duplicate; proposed records
  are *references/observations*, not new authorities. Hard invariants in `14` forbid each duplication;
  packet common scope-OUT (`19`) forbids new proxy/ledger/proof/handoff/engine/gate and `services/task-router` revival.

## Canonical writer/reader/adapter/decision-owner/evidence per domain

| Domain | Canonical writer | Reader | Router adapter | Decision owner | Evidence source |
|---|---|---|---|---|---|
| task-intent classification | DCP (narrow) | DCP consumers | DCP ref adapter | DCP | `routing_classifier.py` |
| privacy/risk | DCP inputs; canonical owner UNKNOWN | proof/audit | RiskPrivacy synthesis | DCP + router route-scope | `12`/`07` + UR-OQ-002 |
| model capability registry | RTE (its lane) | RTE runtime | registry projection | policy registry | `rte_config.py`; UR-INV-004 |
| runner capability snapshots | (none) → router | router | snapshot adapter | router (append-only) | UR-INV-003 artifacts |
| provider availability | subsystem-local | diagnostics | health snapshot adapter | router snapshot (scoped) | C-014, INV-003 sandbox denial |
| route admission/quota | Freeflow ledger | Freeflow router | Freeflow read adapter | Freeflow | `freeflow.py` |
| provider proxying | LiteLLM | trace JSONL | LiteLLM obs adapter | LiteLLM | `routing_config.py`/litellm_* |
| extraction routing | RTE | RTE proof | RTE ref adapter | RTE | `run_extraction_v5.py` |
| workflow transitions | Task Orchestrator | coordinator status | projection adapter | Task Orchestrator | task-orchestrator agents |
| execution dispatch | dopetask (post-handoff) | adapter result | handoff ref adapter | dopetask | `scripts/dopetask` |
| proof/handoff normalization | proof/handoff contracts | proof readers | additive ref adapter | proof/handoff systems | tracked `docs/governance/*` (provenance matrix) |
| benchmark certification | benchmark system | RTE proof | cert ref | benchmark authority | `15` (tuple gap: finding -002) |
| audit independence | audit runner | proof bundle | audit ref | external auditor | `08`/T11 |
| human approval/release | operator/governance | PR Steward readiness | HumanApprovalRef/PRSteward refs | external | UR-OQ-018/006 |

## Coexistence & covert-rewrite check (`16` compatibility matrix)
- Each existing surface is dispositioned as remain / adapter / specialized / ignore / deprecate / forbidden-from-promotion.
- **No covert rewrite disguised as migration was found.** The router adds the `route` noun beside the
  existing `routing` noun (verified: `routing_cli.py:588`), does not alias/redirect legacy commands, and
  does not migrate any subsystem state into router storage (`16` Data migration: "no migration of Freeflow,
  LiteLLM, RTE, workflow, proof, handoff, or PR Steward state").
- Advisory `config/ai/model-routing.policy.yaml` (present, no runtime reader — C-003) is kept ADVISORY and
  migrated only rule-by-rule through a disposition matrix (`14`) — not renamed into authority (decision 33).

## Authority verdict
Authority boundaries are **coherent, minimal, and grounded in current runtime truth**. No authority
absorption, no revived dead router, no duplicated canonical subsystem, and no covert migration rewrite.
The DopeconBridge boundary is accepted on authority-doc grounds (not independently runtime-inspected), which
is non-blocking because the router only references it. This domain contributes **no P0/P1 findings**.
