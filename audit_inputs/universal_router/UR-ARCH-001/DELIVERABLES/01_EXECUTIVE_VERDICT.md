# UR-ARCH-001 Executive Verdict

## Evidence posture

- **OBSERVED:** The static runtime census was taken at repository commit `b176747b339685e781de04268c46b7ae123abfbf` and found active, separate routing slices in Dopemux, Freeflow, LiteLLM, Repo Truth Extractor, and Task Orchestrator.
- **OBSERVED:** UR-INV-003 and UR-INV-004 carry explicit limitations and are not `VERIFIED`.
- **OBSERVED:** UR-REV-004 accepted architecture synthesis with carried unknowns and required an exact in-process location, a first-release CLI surface, an executable policy owner, strict model-identity separation, and isolation of dormant agent families.
- **CONFLICTING:** The supplied authority bundle includes exact-name authority copies, while the inspected commit evidence says several exact root files were absent. This architecture uses the runtime census and tracked-path evidence as higher authority and preserves the provenance conflict in `03_CONTRADICTION_LEDGER.md`.

## Executive decision

- **PROPOSED:** Implement the Universal Multi-Model Execution Router as an in-process Dopemux package at `src/dopemux/universal_router/`.
- **PROPOSED:** Register one new operator command group, `dopemux route`, with `explain`, `recommend`, `inspect`, and `validate` subcommands.
- **PROPOSED:** Do not create a network service, daemon, proxy, quota ledger, execution engine, workflow engine, proof schema, handoff schema, or release gate.
- **PROPOSED:** The first release is deterministic, read-only, advisory, operator-invoked, append-only for its own evidence, and incapable of automatic execution or automatic policy promotion.
- **PROPOSED:** The Universal Router owns only four things: the cross-subsystem orchestration decision, a minimal append-only decision journal, imported capability/provider-health snapshots, and the executable routing-policy contract.
- **PROPOSED:** The Universal Router references, but does not own, DCP classification, Freeflow admission, LiteLLM proxy observations, RTE specialized route decisions, dopetask handoff acceptance, validation, independent audit, proof bundles, human approval, and PR Steward readiness.

## Smallest canonical shape

| Label | Decision | Result |
|---|---|---|
| **PROPOSED** | Package | `src/dopemux/universal_router/` |
| **PROPOSED** | CLI integration | `src/dopemux/universal_router/cli.py`, registered from `src/dopemux/cli.py` as `route` |
| **PROPOSED** | Service or daemon | None |
| **PROPOSED** | Workspace state | `<repo_root>/.dopemux/universal-router/router.sqlite3` |
| **PROPOSED** | Tracked executable policy | `config/universal-router/policies/<policy_id>.yaml` plus `config/universal-router/active-policy.json` |
| **PROPOSED** | Policy schema | `schemas/universal-router/route-policy.schema.json` |
| **PROPOSED** | Snapshot ownership | Universal Router, append-only and time-bounded |
| **PROPOSED** | Quota/cooldown/cap ownership | Freeflow only |
| **PROPOSED** | Provider proxy ownership | LiteLLM only |
| **PROPOSED** | Extraction routing ownership | RTE only |
| **PROPOSED** | Workflow authority | Task Orchestrator only |
| **PROPOSED** | Execution after accepted handoff | dopetask only |
| **PROPOSED** | First-release terminal state | `ROUTE_RECOMMENDED` or `OPERATOR_ACCEPTED` |
| **PROPOSED** | First-release delegation | `NONE`; no subagent fanout |

## Required first-release posture

```text
READ_ONLY
ADVISORY
IN_PROCESS
OPERATOR_INVOKED
APPEND_ONLY_EVIDENCE
NO_AUTOMATIC_EXECUTION
NO_AUTOMATIC_POLICY_PROMOTION
NO_SUBAGENT_FANOUT
```

## Core safety rulings

- **PROPOSED:** `attested_actual_model` remains `UNKNOWN` unless provider-controlled metadata explicitly identifies the served model and is tied to the request through a versioned identity adapter.
- **PROPOSED:** Unknown actual model identity blocks pinned-model certification, benchmark certification, independent-audit claims that depend on model separation, and release-sensitive routes.
- **PROPOSED:** A provider request ID alone is not attestation. A model-generated identity claim is always untrusted. A proxy observation is not automatically provider attestation.
- **PROPOSED:** Estimated cost, actual API cost, plan credits, token counts, and session-level usage remain separate observations. No token-to-credit conversion is invented.
- **PROPOSED:** Every containment control records its enforcement source. Prompt text is never represented as runner, wrapper, or operating-system enforcement.
- **PROPOSED:** Sandbox network denial is classified as an environment condition, not provider unhealth.
- **PROPOSED:** Environment failure never promotes a task to a more expensive model. It yields same-tier retry, same-tier alternative, repair recommendation, escalation, or block.
- **PROPOSED:** A same-runner challenge is not independent. `SKIPPED_WITH_REASON` is not `PASS`.

## Architecture readiness

- **OBSERVED:** The source evidence is sufficient to select the authority boundary, package location, CLI shape, state-store design, policy owner, contract references, state machine, first-release scope, and migration sequence.
- **UNKNOWN:** Provider-attested identity support, local runner containment, plan-credit conversion, live provider health, and benchmark results remain unavailable for some routes.
- **PROPOSED:** Those unknowns block later execution, certification, or release-sensitive phases where relevant. They do not block independent review of this architecture.

## Final verdict

`READY_FOR_INDEPENDENT_AUDIT`
