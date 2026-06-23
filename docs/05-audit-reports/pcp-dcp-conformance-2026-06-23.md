---
id: AUD-PCP-DCP-CONFORMANCE-2026-06-23
title: PCP/DCP Conformance Audit Classification — 2026-06-23
type: audit-report
owner: '@hu3mann'
author: claude
date: '2026-06-23'
last_review: '2026-06-23'
next_review: '2026-09-23'
prelude: Classification of PCP/DCP conformance findings from external audit + local re-verification, with PAL multi-model validation and operator/supervisor rulings.
---

# PCP/DCP Conformance Audit Classification — 2026-06-23

**Audit basis:** External auditor reviewed PCP/DCP at `517e6dd4a` (GitHub API). Local re-verification performed via 3 Explore agents + direct reads + greps. PAL multi-model validation: gpt-5.2, gpt-5.5 (neutral 8/10), gemini-2.5-pro (adversarial 9/10, conceded all facts). Operator + supervisor issued final classification.

**PR closed by:** `claude/pcp-conformance-repair-0001` (TP-DMX-PCP-CONFORMANCE-REPAIR-0001)

---

## Finding Classification Table

| Item | Classification | Status |
|---|---|---|
| **A4** `dopemux.pcp` packaging | MUST_FIX | **FIXED in PR1** |
| **A2** DCP proof family | MUST_FIX | **MAPPING DELIVERED in PR1** (exporter-consumption tracked as follow-up) |
| **A3** "only selected_provider+selected_model" | REJECTED_WITH_REASON | **NOT IN SCOPE** |
| **Red Line #15** forbidden writer wiring | PASS_WITH_GUARD | **GUARD ADDED in PR1** |
| A3 narrow residual: `selected_provider:"unknown"` for `SELECTED` | ROUTING_POLICY_RESIDUAL | **Tracked: `#968/#967`** |
| **A1** unsigned READY gate | ACTIVATION_SCOPED | **Deferred** |

---

## A4 — MUST_FIX: `dopemux.pcp` Packaging (FIXED)

**Evidence:** `pyproject.toml` explicit package allowlist (lines 148–218) omitted `dopemux.pcp` and `dopemux.pcp.bridge` despite the source tree existing at `src/dopemux/pcp/`. Tests passed only via `pythonpath=["src"]` (pytest config line 298), masking a wheel/install failure that would surface on any real install.

**Fix:** `dopemux.pcp` and `dopemux.pcp.bridge` added to the `[tool.setuptools]` packages list immediately after `dopemux.orchestrator.validation`. `dopemux-pcp = "dopemux.pcp.cli:pcp"` added to `[project.scripts]`.

**Tests:** `tests/project_control_plane/test_packaging.py` — 2 tests, PASS.

---

## A2 — MUST_FIX: DCP Proof-Family Mapping (MAPPING DELIVERED)

**Evidence:** `schemas/dcp_extension/extension_manifest.dcp.json` had `proof_status_mappings: []`. Invariant pin existed but no proof-root → PCP-pointer mapping. `authority_map.dcp.json` had no `proof` domain entry.

**Deliverables in PR1 (contract level):**
- Created `schemas/dcp_extension/proof_status_map.dcp.json` — maps Dopemux proof roots (`PROOF.json`, `SUMMARY.md`) to `pcp.proof_pointer.v0` entries with honest `UNKNOWN` states. Honesty rule: pointers declare the mapping with `freshness_state/validation_status/auditor_verdict = "UNKNOWN"` and an `unknowns` note ("resolved at export time by the exporter-consumption follow-up").
- `extension_manifest.dcp.json` `capabilities.proof_status_mappings` updated: `[]` → `["schemas/dcp_extension/proof_status_map.dcp.json"]`.
- `authority_map.dcp.json` new entry: `proof.dopemux_family` / action `read` / `canonical_authority_owner: "dopemux"` / `surface_class: "ADAPTER"` / `live_write_allowed: false` / `canonical_writer: null` / `unknown_behavior: "BLOCK_OR_ESCALATE"`.
- Manifest `adapter_mappings` updated to include `"dopemux"` (required by the scope-sync test `test_manifest_adapter_mappings_match_authority_owners`).

**Follow-up (NOT in PR1):** Exporter-consumption — wire an extension-aware seam (NOT the generic `exporter.py`) to resolve the proof_status_map at export time (head-SHA + freshness → real CURRENT/STALE/PASS states, fail-closed on missing). Until then proof pointers remain honest-UNKNOWN. PR1 must NOT be reported as "proof family fully wired."

**Tests:** `tests/dcp_extension/test_proof_status_map.py` — 3 tests, PASS. Existing schema tests for extension_manifest and authority_map: PASS (all 84 schema-validation tests).

---

## A3 — REJECTED_WITH_REASON: "only selected_provider+selected_model"

**Claim (auditor):** The DCP extension schema should expose only `selected_provider` + `selected_model` fields.

**Rejection evidence:**
- The extension schema has **19 required fields** spanning privacy, risk, access, proof, audit, human-review, benchmark, and more.
- The schema has `live_write_runner_selected: const false` — the live-write runner is pinned off.
- Richer `schemas/dcp/*` families exist alongside OpenClaw families.

**Operator + supervisor ruling:** REJECTED. No change to `schemas/dcp_extension/routing/route_decision.schema.json`.

**Do not merge stale `#974`.**

---

## Red Line #15 — PASS_WITH_GUARD

**Evidence:** `src/dopemux/pcp/**` contains zero forbidden merge-writer references (`queue_drain`, `batch_resolve_and_merge`, `pr_merge_specialist`). The bridge registry defaults inert (`writer_registry=None`). Both factory functions (`create_bridge_router`, `create_bridge_app`) default to no writer.

**Guard added:** `tests/project_control_plane/test_red_line_15.py` — 3 tests:
1. `test_no_forbidden_writer_wiring_in_pcp` — scans all `*.py` under `src/dopemux/pcp/` for forbidden tokens.
2. `test_bridge_factories_default_no_writer` — asserts `writer_registry` parameter default is `None` for both factories.
3. `test_execute_without_writer_is_rejected` — asserts `route_mutation` with `execute=True` and no writer returns `executed=False, permitted=False`.

All 3: PASS.

---

## Routing Residual → `#968/#967`

**Finding:** `selected_provider:"unknown"` is permitted for the `SELECTED` routing branch. The extension schema forbids `null` but allows the `"unknown"` string for `selected_provider`.

**Classification:** ROUTING_POLICY_RESIDUAL — tracked under `#968/#967`.

**Supervisor recommendation:** CONTEXTUAL now (`"unknown"` permissible for public/read-only/manual lanes); STRICT before runtime routing activation (private/high-risk/security/release/structured-output lanes must block or escalate).

---

## A1 — Activation-Scoped: Unsigned READY Gate (Deferred)

**Finding:** The `LIVE_WRITE_READY` gate does not enforce cryptographic signing or authenticated assertion provenance. Gate truth-booleans are unsigned.

**Classification:** ACTIVATION_SCOPED — fail-closed in commit-default/in-tree wiring. Gate truth-booleans unsigned but bridge is inert (no registered writer). This only matters once a writer is registered.

**Deferred work (not PR1):** Signed/authenticated READY issuer, endpoint authN/Z, cross-process atomic dedup + lease, gate-verifier dependency, tz-aware-strict `_parse_iso8601`, generic `WRITER_RAISED`, `_canonical_digest allow_nan=False`.

**Operator ruling:** Scoped this work to A4/A2/Red-Line in PR1; A1 family deferred until a writer is registered for activation.

---

## PAL Validation

- **gpt-5.2**: Validated conformance finding set, classification, and rejection of A3. PASS_WITH_RISKS (acknowledged full-suite NOT_RUN).
- **gpt-5.5**: Neutral assessment 8/10. Conceded A3 rejection evidence.
- **gemini-2.5-pro**: Adversarial review 9/10. Conceded all fact assertions.

---

## Validation Buckets (PR1)

| Bucket | Result |
|---|---|
| `tests/project_control_plane/test_packaging.py` (2 tests) | PASS |
| `tests/dcp_extension/test_proof_status_map.py` (3 tests) | PASS |
| `tests/project_control_plane/test_red_line_15.py` (3 tests) | PASS |
| `tests/project_control_plane test_extension_manifest_schema.py` (42 tests) | PASS |
| `tests/project_control_plane test_authority_map_schema.py` (42 tests) | PASS |
| Full `tests/project_control_plane tests/dcp_extension` (all) | PASS |
| Wheel build + install | NOT_RUN (run after PR merges per supervisor spec) |
| `rg -n "queue_drain\|batch_resolve_and_merge\|pr_merge_specialist" src/dopemux/pcp` | PASS (empty — confirmed clean) |

**NOT claimed:** SOUND_FOR_ACTIVATION — A4+A2+signing/auth+routing residual must all close and the exporter-consumption follow-up must be completed first.
