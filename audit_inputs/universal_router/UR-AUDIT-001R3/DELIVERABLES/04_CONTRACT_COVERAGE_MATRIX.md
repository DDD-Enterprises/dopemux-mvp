# 04 — Contract Coverage Matrix (26 required contracts)

Source: `07_CONTRACT_CATALOG.md` (+ `12`, `13`, `08`, `10`). Completeness scale:
`COMPLETE_MODEL` = owner/authority/refs/invariants/relationships fully specified, field typing to be finalized in schema;
`INCOMPLETE` = prose-only with unresolved semantics per the prompt;
Cross-contract consistency checked (relationship-constraints section, `07`).

Global note (finding UR-AUDIT-R3-003, P2): every router-owned contract is given as a "minimal fields"
list without exhaustive types/required-optional/closed enums; strict JSON schemas + valid/invalid/unknown/
conflicting fixtures are the explicit deliverable and gate of UR-TP-001. Authority/ownership/refs/invariants
are complete, so implementation does not require *authority* guessing.

| Contract | Owner | Creation authority | Mutation | UNKNOWN/CONFLICT behavior | Dup risk | Completeness |
|---|---|---|---|---|---|---|
| SubsystemDecisionRef | Router (ref) | on import | append-only superseding | ref validity never upgrades authority | none (ref) | COMPLETE_MODEL |
| TaskEnvelope | Router intake | intake | ephemeral/journaled, no exec permission | privacy UNKNOWN fails closed | vs dopetask packet — kept separate | COMPLETE_MODEL (type finalize in TP-001) |
| DCPClassificationRef | DCP (underlying) | import verbatim | immutable | fields not rewritten; backend rec ≠ exec | vs RiskPrivacy — separate | COMPLETE_MODEL |
| RiskPrivacyClassification | Router (route-specific) | synthesis | append-only | UNKNOWN fails closed for net/write/security/audit/release | vs DCP — references, not replaces | COMPLETE_MODEL |
| RunnerCapabilitySnapshot | Router snapshot store | import/probe | append-only, TTL | installed ≠ authenticated; unsupported ≠ untested | vs registry — separate | COMPLETE_MODEL |
| ProviderHealthSnapshot | Router store (source subsystem health) | import | append-only, TTL | ENVIRONMENT/POLICY_BLOCKED ≠ unhealth; stale→STALE | vs Freeflow — refs cooldown/admission | COMPLETE_MODEL |
| ModelCapabilityRecord | Executable policy registry | policy | versioned | capability ≠ availability | vs RTE map — not promoted globally | COMPLETE_MODEL |
| RoutePolicy | Router | reviewed activation | immutable after activation | cannot weaken hard invariants | single owner | COMPLETE_MODEL |
| RouteCandidate | Router | engine | ephemeral/journaled | score can't override hard block; eligibility enum incl STALE/UNKNOWN | none | COMPLETE_MODEL |
| UniversalRouteDecision | Router | engine | append-only | unknowns[]/conflicts[] preserved; status enum | central record | COMPLETE_MODEL |
| ExecutionRecommendation | Router presentation | engine | expires; re-recommend on drift | expiry/drift → re-recommend | none | COMPLETE_MODEL |
| ExecutionRequest | Future caller / dopetask boundary | future only | n/a release-one | release-one emits none; needs accepted handoff | none | COMPLETE_MODEL (future) |
| RunnerResult | Runner adapter (future) | future | normalized observation | success ≠ validation/audit pass | none | COMPLETE_MODEL (future) |
| ModelIdentityObservation | Identity adapter | normalize | append-only | insufficient → attested_actual_model=UNKNOWN; conflicts[] | single | COMPLETE_MODEL |
| UsageObservation | Usage adapter | normalize | append-only correction | missing≠zero; no derived credits/overhead | vs Freeflow/RTE — refs, not copy | COMPLETE_MODEL |
| ContainmentDeclaration | Route decision (enforcement external) | route | per-control enforcement_source | PROMPT_REQUESTED can't satisfy enforcement; UNVERIFIED/CONFLICTING | none | COMPLETE_MODEL |
| NetworkPosture | Route decision | route | — | UNKNOWN blocks net routes; provider ≠ general web | none | COMPLETE_MODEL |
| ValidationResult | Validator (underlying) | import ref | superseding | skipped ≠ passed | vs test system — ref | COMPLETE_MODEL |
| EscalationDecision | Router | engine | append-only | env failure can't RAISE_MODEL_TIER | none | COMPLETE_MODEL |
| AuditAssignment | Route rec (authority external) | route | — | same runner/session ≠ independent | vs audit system — assignment intent only | COMPLETE_MODEL |
| AuditResultRef | Audit/proof (underlying) | import | superseding | skipped never pass; state enum incl NEEDS_SUPERVISOR | vs internal — ref | COMPLETE_MODEL |
| HumanApprovalRef | External governance | import | — | router cannot self-issue | vs OPERATOR_ACCEPTED — separate | COMPLETE_MODEL (issuer UR-OQ-018 open) |
| BenchmarkCertification | Benchmark system (ref) | import | invalidated on tuple change | any tuple change invalidates | none | COMPLETE_MODEL — **tuple omits identity_confidence, task_class, containment, network (UR-AUDIT-R3-002, P2)** |
| ProofBundleRef | Existing proof contract | import | superseding | no duplicate proof body/schema | tracked canonical exists (provenance) | COMPLETE_MODEL |
| DopetaskHandoffRef | Existing handoff/dopetask | import | superseding | execution needs accepted handoff | tracked canonical exists | COMPLETE_MODEL |
| PRStewardReadinessRef | PR Steward | import | superseding | cannot convert non-ready→ready | canonical command UR-OQ-006 open | COMPLETE_MODEL (cmd unknown, UR-AUDIT-R3-004) |

## Cross-contract consistency (relationship constraints, `07`)
- One TaskEnvelope → many decision attempts; one attempt → exactly one policy hash + one DCP ref. **Consistent.**
- One decision with status `RECOMMENDED` → exactly one selected candidate. **Consistent.**
- One ExecutionRequest → one accepted recommendation + one accepted handoff. **Consistent** (future).
- Validation/audit/proof/PR readiness independently versioned; supersede without mutating the route decision. **Consistent** with append-only journal.
- Identity/Usage/Containment/Network invariants align with artifacts `12`,`13`,`11` (no contradictions found).

## Verdict
No contract is UNSUPPORTED or internally contradictory. All 26 are COMPLETE at the authority/semantic MODEL
level. The single substantive contract defect is BenchmarkCertification's incomplete scope tuple
(UR-AUDIT-R3-002, P2, gates automatic routing). Schema-typing completeness is deferred to UR-TP-001 by design
(UR-AUDIT-R3-003, P2, gates UR-TP-001 completion) — this is the packet's stated work, not an authority gap.
