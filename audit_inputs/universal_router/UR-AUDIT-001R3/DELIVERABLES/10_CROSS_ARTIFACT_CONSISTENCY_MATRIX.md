# 10 — Cross-Artifact Consistency Matrix

Comparison of the 20 deliverables on the load-bearing dimensions. "Consistent" = the value/claim is stated
identically or compatibly wherever it appears. Semantic mismatches are called out explicitly.

| Dimension | Canonical value | Artifacts asserting it | Consistency |
|---|---|---|---|
| Package path | `src/dopemux/universal_router/` | 01,04,05,18,19 | Consistent |
| CLI noun/surface | `dopemux route explain/recommend/inspect/validate` | 01,04,05,06,16,19 | Consistent |
| Service/daemon | None | 01,04,05,16 | Consistent |
| State-store path | `<repo_root>/.dopemux/universal-router/router.sqlite3` | 01,04,05,14,16,18,19 | Consistent |
| Policy schema path | `schemas/universal-router/route-policy.schema.json` | 01,05,14,19 | Consistent |
| Active policy pointer | `config/universal-router/active-policy.json` | 01,05,14,19 | Consistent |
| Policy files | `config/universal-router/policies/ur-policy-<semver>.yaml` | 01,05,14,19 | Consistent |
| States (14) | INTAKE…BLOCKED | 08,16,18 | Consistent |
| Terminal states | COMPLETED/BLOCKED/ESCALATED (+R1 stops ROUTE_RECOMMENDED/OPERATOR_ACCEPTED) | 08,16,18 | Consistent |
| First-release limit | stop at ROUTE_RECOMMENDED / OPERATOR_ACCEPTED | 01,04,05,08,16,18,19 | Consistent |
| First-release posture | READ_ONLY/ADVISORY/IN_PROCESS/OPERATOR_INVOKED/APPEND_ONLY/NO_AUTO_EXEC/NO_AUTO_PROMO/NO_FANOUT | 01,04,17 | Consistent |
| Ownership (Freeflow/LiteLLM/RTE/TO/dopetask/DCP/PR Steward) | references only | 02,04,05,06,10,16,17 | Consistent |
| Snapshot expiry TTLs | version 7d, containment 7d, auth 15m, pos-health 5m, transient 60s, vendor 24h, benchmark ≤30d | 05,20(UR-OQ-014) | Consistent |
| Audit states | NOT_REQUIRED…NEEDS_SUPERVISOR | 07,08,10,17 | Consistent |
| Network postures (6) | OFFLINE…UNKNOWN | 07,11 | Consistent |
| Containment enforcement sources (6) | PROMPT_REQUESTED…UNVERIFIED | 07,11,17 | Consistent |
| Identity fields (10) | requested…identity_adapter_version | 07,12,17 | Consistent |
| Usage fields (12) | visible_prompt_tokens…pricing_version | 07,13,15,17 | Consistent |
| Route classes | cheap read…audit failure | 09,11,15 | Consistent |
| Escalation budget | ≤1 reasoning + ≤1 model tier | 08,09,17,18 | Consistent |
| Environment failure → premium | forbidden | 01,04,06,08,09,11,13,14,17,19 | Consistent |
| Human override | external scoped expiring HumanApprovalRef | 08,11,12,14 | Consistent |
| Rollback | kill switch + active-pointer revert to certified hash; journal preserved | 05,14,16 | Consistent |
| Certification tuple | route-tuple + versions | 06(implicit),10,15,07 | **Minor mismatch** — tuple members differ across 15/10/07 and omit identity_confidence & task_class (UR-AUDIT-R3-002) |
| Packet ordering | 001…012 = roadmap Steps 1…12 | 16,18,19 | Consistent |
| Final verdict | READY_FOR_INDEPENDENT_AUDIT | 01,20 | Consistent |
| Provenance conflict | preserved (archive names ≠ tracked root authority) | 01,03(C-001),20(UR-OQ-001) | Consistent (verified in `13`) |

## Semantic mismatches recorded
1. **Certification scope tuple** is expressed with slightly different member sets in `15` (evaluation),
   `10` (adapter tuple), and `07` (BenchmarkCertification), and none includes `identity_confidence` or
   `task_class`. → UR-AUDIT-R3-002 (P2). Not a first-release blocker (future certification phase).
2. **Open-questions summary partition** (`20`: 11 first-release / 9 future) is a *bucket-by-earliest-phase*
   partition; several of the 11 also block future phases. Reproduced and found **consistent** under that
   interpretation (11 questions touch ≥1 first-release phase; the other 9 are future-only). No defect.
3. **PM_PLANE.md / AGENTS.md** bundle copies are stale vs current tracked root versions (provenance artifact,
   not an inter-deliverable inconsistency) — see `13`.

No load-bearing inconsistency (package/CLI/store/state/first-release/ownership/identity/usage/network/
containment) was found across the 20 artifacts. The design is internally coherent.
