# 08 — State-Store, Evaluation & Certification Audit

## A. State store (`05`, `04`, `17`)
Proposed: single workspace SQLite `<repo_root>/.dopemux/universal-router/router.sqlite3` with tables
`schema_migrations, journal_events, route_decisions, capability_snapshots, provider_health_snapshots,
policy_activations, reference_index`. `journal_events` is the replay spine; domain tables are append-only
projections.

| Aspect | Verdict | Notes |
|---|---|---|
| SQLite vs JSONL vs hybrid | SUPPORTED | SQLite (indexed reads) with JSON event spine is reasonable; not a new general event store (explicitly forbidden) |
| Append-only enforcement | SUPPORTED_WITH_RISK | BEFORE UPDATE/DELETE abort triggers = process-local; **not tamper-evidence** (UR-AUDIT-R3-005, P3) |
| WAL / locks / concurrency | SUPPORTED | WAL single-writer + advisory lock + busy timeout + idempotency keys + expected-parent (T14) |
| Repo/worktree identity | SUPPORTED_WITH_RISK | workspace-bound; per-worktree fragmentation across ~31 worktrees (UR-AUDIT-R3-006, P3) |
| Migrations / replay / corruption | SUPPORTED | forward-only checksummed migrations; failure → READ_ONLY_DEGRADED preserving DB; replay by sequence_id |
| Redaction / secret leakage | SUPPORTED | store presence/hash/refs only; no raw prompts/responses/secrets/proof bodies/full diffs |
| Snapshot expiry / policy refs / immutable refs | SUPPORTED | TTL table; refs+hashes only |
| Rollback / disablement / cleanup | SUPPORTED | kill switches; policy pointer rollback; journal never deleted; retention by explicit maintenance |
| Test isolation | SUPPORTED | UR-TP-003 concurrency/migration/replay fixtures required |
| Separation of journal / capability / health / policy-obs / operator-acceptance | SUPPORTED | distinct tables + event types even in one DB |
| New general event store? | AVOIDED | scope-OUT + decommission condition if it becomes one |

**Gitignore confirmation:** journal path is gitignored → append-only writes are workspace-local, not tracked
repo writes (supports READ_ONLY). Store design is **safe for first release**; two P3 hardening items only.

## B. Evaluation plan (`15`)
- Layers (contract conformance → historical replay → adversarial fixtures → shadow → manual acceptance →
  adapter cert → bounded live → automatic-routing cert) are correctly staged; execution-adjacent metrics
  (unnecessary diff, allowlist escape) explicitly deferred until an execution adapter exists.
- Corpus: ≥200 reviewed tasks, per-class minima, ≥20% hard-negatives, ≥15% contradictions, time/family split to
  avoid train/test leakage. Gold labels are **sets/constraints** (not single strings), two-reviewer for
  security/authority/release/contradiction, unresolved disagreements excluded from accuracy but kept in
  contradiction suite. **Circular labels avoided** ("do not infer model quality from PR merge or CI success alone").
- Metrics separate exact/estimated/session/unavailable; **coverage is itself a metric**; aggregate scores never
  erase class-level failures; severe-failure rate defined concretely (secret exposure, unauthorized execution
  recommendation, wrong authority, release bypass, fabricated identity/cost/credits, env-driven premium escalation).
- Impossible telemetry rejected ("do not penalize a route for a vendor measurement it does not expose").
- Shadow protocol S0–S6 with S4–S6 future-gated; thresholds (100% hard-constraint, 100% block/escalation recall,
  zero severe failures, ≥85% top-1 / ≥95% top-3, ≥98% explanation grounding, 100% deterministic replay) are
  demanding and appropriate.
- **Open corpus reality:** UR-OQ-017 (labelable task count) correctly gates UR-TP-008/policy promotion; the plan
  refuses to lower thresholds for corpus scarcity.

## C. Certification scope tuple (`15`, `10`, `07`) — **defect**
Prompt requires certification scoped to at least: `policy_version, runner_adapter_version, runner, provider_path,
configured_model, identity_confidence, reasoning_setting, network_posture, containment_posture, task_class,
corpus_version`.

Architecture tuple (`15`): `policy_hash + engine_version + adapter_version_set + capability_registry_hash +
runner + provider_path + configured_model + reasoning_level + containment_profile + network_posture`.
Adapter tuple (`10`) adds `benchmark_corpus_version`. BenchmarkCertification (`07`) route tuple:
`runner + provider path + model + reasoning + adapter + policy + corpus_version`.

**Missing from the certification tuples: `identity_confidence` and `task_class`** (and BenchmarkCertification
omits containment/network posture). → **UR-AUDIT-R3-002 (P2)**: a certification could be reused across differing
identity-confidence levels or task classes. Repair before certification-driven automatic routing (UR-TP-008/012).
Revocation/suspension criteria (`15`) are otherwise strong (immediate revoke on secret exposure/identity fraud/
proof fabrication/audit-independence violation/release bypass).

## D. Verdict
State store is safe for first release (2× P3 hardening). Evaluation plan is rigorous and non-circular. The single
substantive certification defect is the incomplete scope tuple (P2, future-phase blocking). No P0/P1.
