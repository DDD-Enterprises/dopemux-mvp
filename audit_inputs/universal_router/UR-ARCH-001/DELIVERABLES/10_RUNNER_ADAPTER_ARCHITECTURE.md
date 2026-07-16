# Runner Adapter Architecture

## Adapter principle

- **PROPOSED:** A runner adapter translates Universal Router contracts into runner-specific requests and observations. It does not own route policy, execution authority, provider proxying, proof, or release readiness.
- **PROPOSED:** Release one implements read-only capability and evidence adapters only. Execution methods are absent or hard-disabled.
- **PROPOSED:** Every adapter is versioned because containment, model identity, output schemas, and telemetry fields can change between runner versions.

## Adapter modes

```text
DESCRIBE_CAPABILITIES
IMPORT_CAPABILITY_SNAPSHOT
IMPORT_HEALTH_SNAPSHOT
VALIDATE_RECOMMENDATION
BUILD_EXECUTION_REQUEST      # future
EXECUTE                      # future, one certified adapter at a time
NORMALIZE_RESULT             # future
```

- **PROPOSED:** Release one permits the first four modes only.
- **PROPOSED:** `EXECUTE` must not exist behind a hidden flag in release one.

## Common adapter interface

| Label | Method | Input | Output | Side effects in release one |
|---|---|---|---|---|
| **PROPOSED** | `describe()` | runner/provider ID | static adapter metadata | none |
| **PROPOSED** | `collect_capability_snapshot()` | bounded local evidence source | `RunnerCapabilitySnapshot` | local reads only |
| **PROPOSED** | `collect_health_snapshot()` | existing subsystem health/ref | `ProviderHealthSnapshot` | no provider call by default |
| **PROPOSED** | `validate_candidate()` | TaskEnvelope, candidate, policy | validation findings | none |
| **PROPOSED** | `build_execution_request()` | accepted recommendation/handoff | `ExecutionRequest` | future only |
| **PROPOSED** | `execute()` | `ExecutionRequest` | raw runner result | future only |
| **PROPOSED** | `normalize_result()` | raw result + refs | `RunnerResult`, identity/usage refs | future only |

## Adapter evidence requirements

- **PROPOSED:** Adapter ID and version.
- **PROPOSED:** Supported runner versions or version range.
- **PROPOSED:** Exact invocation template when execution is eventually enabled.
- **PROPOSED:** Structured-output method and local validator.
- **PROPOSED:** Session persistence behavior.
- **PROPOSED:** Read/write/tool/MCP/network controls and enforcement sources.
- **PROPOSED:** Authentication path without credential values.
- **PROPOSED:** Identity fields and attestation level.
- **PROPOSED:** Usage/cost fields and exactness.
- **PROPOSED:** Failure classifier.
- **PROPOSED:** Redaction behavior.
- **PROPOSED:** Certification refs and revocation state.

## First-release adapters

### DCP adapter

- **OBSERVED:** DCP is a pure fail-closed classifier and does not dispatch runners.
- **PROPOSED:** Import `classify_route` output or an existing artifact into `DCPClassificationRef`.
- **PROPOSED:** Preserve deterministic route ID, red-lane, risk, authority, runtime-impact, proof/audit/escalation fields.
- **PROPOSED:** Reject any attempt to interpret backend recommendation as execution permission.

### Freeflow adapter

- **OBSERVED:** Freeflow owns quotas, cooldowns, paid caps, admission, route decisions, and estimated cost for its slice.
- **PROPOSED:** Use a stable public adapter to request/read an admission decision or snapshot.
- **PROPOSED:** Do not open or mutate Freeflow SQLite tables directly from router code.
- **PROPOSED:** Record `POLICY_BLOCKED`, cooldown, and admission separately from provider health.

### LiteLLM observation adapter

- **OBSERVED:** LiteLLM is provider proxy infrastructure; Dopemux has manager, config-generation, and trace surfaces.
- **PROPOSED:** Release one imports existing trace records and proxy config resolution only.
- **PROPOSED:** `proxy_reported_model` and provider fields are observations, not provider attestation by default.
- **PROPOSED:** Do not start, stop, repair, or reconfigure LiteLLM through `dopemux route`.

### RTE adapter

- **OBSERVED:** RTE owns extraction-specific route ladders, strict schema, provider locks, preflight, repair/sidefill, pricing, spend, and run proof.
- **PROPOSED:** The adapter detects extraction intent and emits an `RTE_SPECIALIZED` candidate.
- **PROPOSED:** It imports RTE route/run refs after an RTE system has acted.
- **PROPOSED:** It never maps RTE model ladders into a universal model pool.

### Task Orchestrator projection adapter

- **OBSERVED:** Task Orchestrator owns workflow views/transitions and separately has a narrow capability-family coordinator.
- **PROPOSED:** The router may create a read-only projection payload containing decision ID, task class, recommended runner family, blockers, and expiry.
- **PROPOSED:** Release one does not write that projection automatically.
- **PROPOSED:** The adapter has no workflow-transition method.

### Dopetask/handoff reference adapter

- **OBSERVED:** Dopetask owns execution after accepted handoff.
- **PROPOSED:** Release one validates existing handoff/proof refs and can explain missing prerequisites.
- **PROPOSED:** Future phases may build an additive handoff extension containing route decision, policy, containment, identity requirements, and snapshot refs.
- **PROPOSED:** The existing handoff schema remains canonical.

### Proof, audit, and PR Steward reference adapters

- **OBSERVED:** These systems own their own statuses and chain of custody.
- **PROPOSED:** Adapters validate ref shape, hash, head SHA/freshness, and status.
- **PROPOSED:** They cannot convert skipped audit to pass or blocked readiness to ready.

## Codex advisory adapter

- **OBSERVED:** Local Codex 0.144.1 proved non-interactive JSONL output, output-schema support, read-only sandbox selection, ephemeral sessions, and one successful contained smoke.
- **OBSERVED:** The smoke did not provide provider-attested actual model or plan-credit/cost data, and hard tool denial was not proven.
- **PROPOSED:** Release-one adapter capabilities:
  - import local version/help evidence;
  - import smoke refs;
  - validate whether a recommendation requests supported controls;
  - render a future invocation template without executing it;
  - mark actual identity, hard tool denial, and credits as `UNKNOWN`.
- **PROPOSED:** Execution remains disabled until a separate packet proves worktree containment, file/command allowlists, credential posture, identity/usage capture, proof linkage, and dopetask acceptance.

## Future execution adapters

### Codex execution adapter

- **PROPOSED:** First candidate because local non-interactive and structured-output behavior has the strongest successful smoke evidence.
- **PROPOSED:** Required before enablement: hard wrapper file/command allowlists, worktree verification, network posture, ephemeral session, bounded context manifest, output location, exact command capture, identity/usage normalization, and certification.
- **PROPOSED:** No subagent fanout in its first certification.

### Claude Code Sonnet adapter

- **OBSERVED:** Local help proves model/effort, print mode, JSON/schema output, no-session persistence, tool selection, budget cap, and agent listing.
- **UNKNOWN:** Safe authenticated contained execution and actual model identity remain unproven.
- **PROPOSED:** Use as implementation fallback after independent certification.
- **PROPOSED:** A Claude Code run cannot audit its own implementation session.

### Claude Code Opus adapter

- **PROPOSED:** High-complexity refactor/debug or deep audit fallback only.
- **PROPOSED:** Premium usage requires an explicit reason and cost/credit posture.
- **PROPOSED:** It is not a routine default.

### AGY/Sonnet audit adapter

- **CLAIMED:** Project operating policy prefers AGY/Sonnet as embedded auditor where safely available.
- **OBSERVED:** Local AGY help proves model/session selection and print mode, but structured output, hard containment, usage, identity, and auth were not proven.
- **PROPOSED:** Candidate remains ineligible for independent audit until a fresh capability snapshot proves required controls.
- **PROPOSED:** Safe availability, not preference, controls eligibility.

### Gemini CLI audit adapter

- **OBSERVED:** Local help proves model selection, headless prompt, and JSON/stream JSON output.
- **UNKNOWN:** No-tool/no-persistence containment, reasoning control, identity, usage, cost, and subagent inheritance are not locally proven.
- **PROPOSED:** Use for broad-context contradiction audits only after wrapper/OS containment is certified.
- **PROPOSED:** It does not become a default implementation route merely because it can read large contexts.

### Direct API adapter

- **PROPOSED:** One provider-specific adapter per provider family, not one generic trust adapter.
- **PROPOSED:** Each adapter defines request metadata, structured output, provider identity evidence, usage/cost fields, retry semantics, and redaction.
- **PROPOSED:** LiteLLM can remain the proxy path, but provider attestation still requires provider-controlled evidence meeting the identity contract.

### Desktop/manual advisory adapter

- **PROPOSED:** Import transcript/export refs, operator identity, requested model/picker claim, redaction report, and hashes.
- **PROPOSED:** Output is advisory and cannot satisfy machine execution, provider attestation, independent audit, or release approval alone.

## Subagent and delegation rule

- **PROPOSED:** Release one uses `subagent_pattern=NONE` for all candidates.
- **PROPOSED:** Future adapters may support `SEQUENTIAL_SINGLE_DELEGATE` only after model inheritance, permissions, identity, context, usage, and session isolation are proven.
- **PROPOSED:** `PARALLEL_FANOUT` remains prohibited until a separate architecture and certification decision.
- **PROPOSED:** Task Orchestrator capability-family assignment remains separate from runner-native subagents.

## Adapter certification tuple

```text
runner_id
runner_version
provider_path_id
requested_model
reasoning_mapping
adapter_id
adapter_version
containment_profile
network_posture
policy_hash
benchmark_corpus_version
```

- **PROPOSED:** Any change to the tuple invalidates certification until replayed.
- **PROPOSED:** Revoked adapters remain readable for historical replay but cannot generate eligible candidates.
