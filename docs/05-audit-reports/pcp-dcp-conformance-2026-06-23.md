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

**Audit basis:** External auditor reviewed PCP/DCP at `517e6dd4a` (GitHub API only). Local re-verification performed via 3 Explore agents + direct reads + greps + a real wheel build/clean-venv install. PAL multi-model validation: gpt-5.2, gpt-5.5 (neutral 8/10), gemini-2.5-pro (adversarial 9/10, conceded all facts). Operator + supervisor issued the final classification.

**PR:** `claude/pcp-conformance-repair-0001` (TP-DMX-PCP-CONFORMANCE-REPAIR-0001)

---

## Finding Classification Table

| Item | Classification | Status |
|---|---|---|
| **A4** `dopemux.pcp` packaging | MUST_FIX | **PARTIAL in PR1** — packaging declared; installed-wheel *import* still blocked (see A4 below) |
| **A2** DCP proof family | MUST_FIX | **MAPPING DELIVERED in PR1** (authority modeling + exporter-consumption tracked as follow-ups) |
| **A3** "only selected_provider+selected_model" | REJECTED_WITH_REASON | **NOT IN SCOPE** |
| **Red Line #15** forbidden writer wiring | PASS_WITH_GUARD | **GUARD ADDED in PR1** |
| A3 narrow residual: `selected_provider:"unknown"` for `SELECTED` | ROUTING_POLICY_RESIDUAL | **Tracked: `#968/#967`** |
| **A1** unsigned READY gate | ACTIVATION_SCOPED | **Deferred** |

---

## A4 — MUST_FIX: `dopemux.pcp` Packaging (PARTIAL — packaging declared, wheel-import deferred)

**Evidence:** `pyproject.toml` explicit package allowlist (lines 148–218) omitted `dopemux.pcp` and `dopemux.pcp.bridge` despite the source tree existing at `src/dopemux/pcp/`. Tests passed only via `pythonpath=["src"]` (pytest config line 298), masking a wheel/install failure.

**Fix shipped in PR1:** `dopemux.pcp` and `dopemux.pcp.bridge` added to the `[tool.setuptools]` packages list immediately after `dopemux.orchestrator.validation`; `dopemux-pcp = "dopemux.pcp.cli:pcp"` added to `[project.scripts]`.

**Proven (wheel contents):** A built wheel now contains all 8 `dopemux/pcp/*` modules (incl. `bridge/fastapi_bridge.py`) and the `dopemux-pcp` console-script entry point — all absent before the fix. **PASS.**

**NOT yet fixed (discovered by the clean-venv install gate):** Four PCP modules load repo-root schema JSON **at import time** via a source-tree-relative path (`_REPO_ROOT = parents[4]` → `schemas/project_control_plane/*.json`):
- `bridge/fastapi_bridge.py` → `live_write_ready.schema.json`
- `exporter.py` → `project_evidence_export.schema.json`
- `negative_cases.py` → `negative_case_result.schema.json` + `project_evidence_export.schema.json`
- `pr_steward.py` → `merge_readiness.schema.json`

The repo-root `schemas/` directory is **not bundled** in the wheel (`[tool.setuptools.package-data]` covers only `dopemux.templates`), and `parents[4]` resolves to the wrong location once installed. Result: `import dopemux.pcp.*` (and the `dopemux-pcp` CLI) **crashes from an installed wheel** with `FileNotFoundError`. The packages-allowlist fix is **necessary but not sufficient** for clean installed-wheel activation — the audit's A4 framing missed this layer.

**Operator ruling:** ship the surgical packaging fix; track the wheel-safety fix separately (do not expand PR1 into a packaging refactor of the generic exporter).

**Follow-up (tracked):** *PCP wheel-safe schema loading* — bundle the `schemas/project_control_plane` JSON as package data and make the 4 loaders wheel-safe (`importlib.resources` or src-tree/installed dual-path), then the clean-venv import gate passes.

**Tests:** `tests/project_control_plane/test_packaging.py` — 2 tests, PASS.

---

## A2 — MUST_FIX: DCP Proof-Family Mapping (MAPPING DELIVERED)

**Evidence:** `schemas/dcp_extension/extension_manifest.dcp.json` had `proof_status_mappings: []`. Invariant pin existed but no proof-root → PCP-pointer mapping.

**Deliverables in PR1 (contract level):**
- Created `schemas/dcp_extension/proof_status_map.dcp.json` — maps Dopemux proof roots (`PROOF.json`, `SUMMARY.md`) to `pcp.proof_pointer.v0` entries with honest `UNKNOWN` states. Honesty rule: pointers declare the mapping with `freshness_state/validation_status/auditor_verdict = "UNKNOWN"` and an `unknowns` note ("resolved at export time by the exporter-consumption follow-up").
- `extension_manifest.dcp.json` `capabilities.proof_status_mappings`: `[]` → `["schemas/dcp_extension/proof_status_map.dcp.json"]`.

**Dropped from PR1 (operator ruling DROP_FROM_PR1 — preserve Packet-5 scope-lock):** A `proof.dopemux_family` authority-map entry was initially added but collided with the Packet-5 scope-lock (`tests/dcp_extension/test_dcp_extension_mapping.py`: authority owners ≡ manifest `adapter_mappings` ≡ `EXPECTED_SYSTEMS`, all MCP-system adapters). Registering `"dopemux"` as a pseudo-adapter to satisfy the lock blurs adapter-ownership vs proof-family-ownership. The entry, its test, and the `adapter_mappings`/`EXPECTED_SYSTEMS` bumps were reverted; the Packet-5 scope-lock is unchanged.

**Follow-ups (NOT in PR1):**
1. *Proof-family authority modeling* — model `proof.*` ownership cleanly (a plane distinct from MCP adapter mappings) rather than forcing it into the Packet-5 adapter set.
2. *Exporter-consumption* — an extension-aware seam (NOT the generic `exporter.py`) resolving the proof_status_map at export time (head-SHA + freshness → real CURRENT/STALE/PASS, fail-closed on missing). Until then proof pointers remain honest-UNKNOWN. PR1 must NOT be reported as "proof family fully wired."

**Tests:** `tests/dcp_extension/test_proof_status_map.py` — 2 tests (manifest declares mapping; pointers validate against `proof_pointer.schema.json`), PASS. Pre-existing manifest/authority schema + Packet-5 scope-lock tests: PASS (unchanged).

---

## A3 — REJECTED_WITH_REASON: "only selected_provider+selected_model"

**Claim (auditor):** The DCP extension route-decision schema is thin and effectively requires only `selected_provider` + `selected_model`.

**Rejection evidence:**
- The extension schema has **19 required fields** spanning privacy, risk, access path, proof, audit, human-gate, benchmark, and more.
- `live_write_runner_selected: const false` — the live-write runner is pinned off.
- Richer `schemas/dcp/*` (runtime) and `contracts/openclaw-dcp-routing/*` (policy) families exist alongside it.

**Operator + supervisor ruling:** REJECTED. **No change** to `schemas/dcp_extension/routing/route_decision.schema.json`. **Do not merge stale `#974`.**

---

## Red Line #15 — PASS_WITH_GUARD

**Evidence:** `src/dopemux/pcp/**` contains zero forbidden merge-writer references (`queue_drain`, `batch_resolve_and_merge`, `pr_merge_specialist`). Bridge registry defaults inert (`writer_registry=None`); both factories default to no writer.

**Guard added:** `tests/project_control_plane/test_red_line_15.py` — 3 tests (forbidden-token scan of `src/dopemux/pcp/**`; both factories default `writer_registry=None`; `route_mutation` with `execute=True` and no writer returns `executed=False, permitted=False`). All PASS.

---

## Routing Residual → `#968/#967`

**Finding:** `selected_provider:"unknown"` is permitted for the `SELECTED` routing branch (the schema forbids `null` but allows the `"unknown"` string). Contracts-only; no runtime consumer.

**Classification:** ROUTING_POLICY_RESIDUAL — tracked under `#968/#967`. **Supervisor recommendation:** CONTEXTUAL now (`"unknown"` permissible for public/read-only/manual lanes); STRICT before runtime routing activation (private/high-risk/security/release/structured-output → block or escalate).

---

## A1 — Activation-Scoped: Unsigned READY Gate (Deferred)

**Finding:** The `LIVE_WRITE_READY` gate enforces schema shape + internal consistency + TTL + operation binding, but not cryptographic signing / authenticated issuer provenance. Gate truth-booleans are unsigned (verified out-of-band per the ops doc).

**Classification:** ACTIVATION_SCOPED — fail-closed in commit-default/in-tree wiring; only exploitable once a real writer is registered (bridge inert today).

**Deferred work (not PR1):** signed/authenticated READY issuer, endpoint authN/Z, cross-process atomic dedup + lease, gate-verifier dependency, tz-aware-strict `_parse_iso8601`, generic `WRITER_RAISED` code, `_canonical_digest allow_nan=False`.

---

## PAL Validation

- **gpt-5.2** (neutral): validated the finding set + classification + A3 rejection; sharpened the A3 residual to a contract-integrity concern; confirmed bridge fail-closed.
- **gpt-5.5** (neutral, 8/10): corroborated; narrowed A1 to "commit-default state"; flagged A2 faithful-fix > exporter wiring.
- **gemini-2.5-pro** (adversarial, 9/10): conceded all facts; pushed severity/scope (A2 needs authority + integrity; dedup-before-writer DoS).
- (grok-4, claude-opus-4.5, gemini-3-pro-preview adversaries were unavailable — provider credit/decommission — and are NOT counted.)

---

## Validation Buckets (PR1)

| Bucket | Result |
|---|---|
| `tests/project_control_plane/test_packaging.py` (2) | PASS |
| `tests/dcp_extension/test_proof_status_map.py` (2) | PASS |
| `tests/project_control_plane/test_red_line_15.py` (3) | PASS |
| Full `tests/project_control_plane` + `tests/dcp_extension` (incl. Packet-5 scope-lock + schema-validation) | PASS |
| Wheel build + **contents** (`dopemux/pcp/*` 8 modules + `dopemux-pcp` script present) | PASS |
| Clean-venv **install + import** of `dopemux.pcp.*` | **FAIL (known)** — repo-root schema loaded at import time; deferred to the *PCP wheel-safe schema loading* follow-up |
| `rg "queue_drain\|batch_resolve_and_merge\|pr_merge_specialist" src/dopemux/pcp` | PASS (empty) |

**NOT claimed:** SOUND_FOR_ACTIVATION — requires A4 wheel-safety, A2 authority modeling + exporter-consumption, the A1 signing/auth family, and the routing residual to all close first.

---

## Tracked Follow-ups (out of PR1)

1. **PCP wheel-safe schema loading** (A4 completion) — bundle `schemas/project_control_plane` as package data + `importlib.resources`/dual-path loaders for `fastapi_bridge.py`, `exporter.py`, `negative_cases.py`, `pr_steward.py`. Closes the clean-venv import gate.
2. **A2 proof-family authority modeling** — clean `proof.*` ownership plane (not the MCP adapter set).
3. **A2 exporter-consumption** — extension-aware seam resolving proof_status_map at export time.
4. **Routing residual `#968/#967`** — `selected_provider:"unknown"` policy (CONTEXTUAL → STRICT).
5. **A1 activation-security family** — signing/auth/dedup-lease/etc.
