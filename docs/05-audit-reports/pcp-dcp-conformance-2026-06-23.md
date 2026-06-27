---
id: AUD-PCP-DCP-CONFORMANCE-2026-06-23
title: "PCP/DCP Conformance Audit Classification \u2014 2026-06-23"
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-23'
last_review: '2026-06-23'
next_review: '2026-09-23'
prelude: Classification of PCP/DCP conformance findings from external audit + local
  re-verification, with PAL multi-model validation and operator/supervisor rulings.
---
# PCP/DCP Conformance Audit Classification — 2026-06-23

**Audit basis:** External auditor reviewed PCP/DCP at `517e6dd4a` (GitHub API only). Local re-verification performed via 3 Explore agents + direct reads + greps + real wheel build/clean-venv install. PAL multi-model validation: gpt-5.2, gpt-5.5 (neutral 8/10), gemini-2.5-pro (adversarial 9/10, conceded all facts). Operator + supervisor issued the final classification.

**PR:** `claude/pcp-conformance-repair-0001` (TP-DMX-PCP-CONFORMANCE-REPAIR-0001). The A4 wheel-safety completion was delivered by **#978** (schema bundling), folded into this branch and independently re-verified.

---

## Finding Classification Table

| Item | Classification | Status |
|---|---|---|
| **A4** `dopemux.pcp` packaging | MUST_FIX | **FIXED** — packaging declared (#977) + wheel-safe schema loading (#978, folded in) |
| **A2** DCP proof family | MUST_FIX | **MAPPING DELIVERED in #977** (authority modeling + exporter-consumption tracked as follow-ups) |
| **A3** "only selected_provider+selected_model" | REJECTED_WITH_REASON | **NOT IN SCOPE** |
| **Red Line #15** forbidden writer wiring | PASS_WITH_GUARD | **GUARD ADDED in #977** |
| A3 narrow residual: `selected_provider:"unknown"` for `SELECTED` | ROUTING_POLICY_RESIDUAL | **Tracked: `#968/#967`** |
| **A1** unsigned READY gate | ACTIVATION_SCOPED | **Deferred** |

---

## A4 — MUST_FIX: `dopemux.pcp` Packaging (FIXED, two steps)

**Evidence:** `pyproject.toml` explicit package allowlist omitted `dopemux.pcp` and `dopemux.pcp.bridge` despite the source tree existing at `src/dopemux/pcp/`. Tests passed only via `pythonpath=["src"]` (pytest config), masking a wheel/install failure.

**Step 1 — packaging declared (#977):** added `dopemux.pcp` + `dopemux.pcp.bridge` to the `[tool.setuptools]` packages list + `dopemux-pcp = "dopemux.pcp.cli:pcp"` console script. The built wheel ships all 8 `dopemux/pcp/*` modules + the script.

**Step 2 — wheel-safe schema loading (#978, folded in):** the clean-venv install gate (added in this work) caught that 4 PCP modules (`bridge/fastapi_bridge.py`, `exporter.py`, `negative_cases.py`, `pr_steward.py`) loaded repo-root schema JSON **at import time** via a source-tree-relative path (`parents[N]`), so `import dopemux.pcp.*` crashed from an installed wheel (`FileNotFoundError`). #978:
- Vendors the 4 loaded schemas under `dopemux/pcp/_schemas/` + a `load_schema()` shim using `importlib.resources` (resolves identically from source tree and installed wheel — single path, no repo-root assumption).
- Repoints the 4 loaders at `load_schema(...)`; drops the now-dead `json`/`pathlib` imports.
- Adds `dopemux.pcp._schemas` to `packages` + `package-data = ["*.json"]`.
- Adds a parity test asserting the vendored copies stay byte-identical to canonical `schemas/project_control_plane/` (drift would ship a stale contract).
- Declares `jsonschema>=4.20.0` as a **core** dependency (previously only transitive via litellm), so the import chain can't break.

**Re-verified (merged #977 @ the #978 squash):** wheel bundles all 4 schemas + the loader shim; `jsonschema` appears unconditionally in core `Requires-Dist`; a **clean-venv install + import of all 6 `dopemux.pcp.*` modules + the CLI succeeds from the installed location** (not the repo). The previously-FAILing clean-venv import gate now **PASSES**.

**Tests:** `tests/project_control_plane/test_packaging.py` (2) + `tests/project_control_plane/test_schema_bundle_parity.py` (parity) — PASS.

---

## A2 — MUST_FIX: DCP Proof-Family Mapping (MAPPING DELIVERED)

**Evidence:** `schemas/dcp_extension/extension_manifest.dcp.json` had `proof_status_mappings: []`. Invariant pin existed but no proof-root → PCP-pointer mapping.

**Deliverables in #977 (contract level):**
- Created `schemas/dcp_extension/proof_status_map.dcp.json` — maps Dopemux proof roots (`PROOF.json`, `SUMMARY.md`) to `pcp.proof_pointer.v0` entries with honest `UNKNOWN` states (resolved at export time by the exporter-consumption follow-up).
- `extension_manifest.dcp.json` `capabilities.proof_status_mappings`: `[]` → `["schemas/dcp_extension/proof_status_map.dcp.json"]`.

**Dropped from #977 (operator ruling DROP_FROM_PR1 — preserve Packet-5 scope-lock):** a `proof.dopemux_family` authority-map entry collided with the Packet-5 scope-lock (authority owners ≡ manifest `adapter_mappings` ≡ `EXPECTED_SYSTEMS`, all MCP-system adapters). Registering `"dopemux"` as a pseudo-adapter blurs adapter-ownership vs proof-family-ownership. Reverted; scope-lock unchanged.

**Follow-ups (NOT in #977):**
1. *Proof-family authority modeling* — model `proof.*` ownership cleanly (distinct plane from MCP adapter mappings).
2. *Exporter-consumption* — extension-aware seam (NOT the generic `exporter.py`) resolving the proof_status_map at export time (head-SHA + freshness → real CURRENT/STALE/PASS, fail-closed on missing). Until then proof pointers remain honest-UNKNOWN.

**Tests:** `tests/dcp_extension/test_proof_status_map.py` (2) + pre-existing manifest/authority schema + Packet-5 scope-lock tests — PASS.

---

## A3 — REJECTED_WITH_REASON: "only selected_provider+selected_model"

**Claim (auditor):** the DCP extension route-decision schema is thin and effectively requires only `selected_provider` + `selected_model`.

**Rejection evidence:** the extension schema has **19 required fields** (privacy, risk, access path, proof, audit, human-gate, benchmark, …); `live_write_runner_selected: const false`; richer `schemas/dcp/*` (runtime) and `contracts/openclaw-dcp-routing/*` (policy) families exist.

**Operator + supervisor ruling:** REJECTED. **No change** to `schemas/dcp_extension/routing/route_decision.schema.json`. **Do not merge stale `#974`.**

---

## Red Line #15 — PASS_WITH_GUARD

**Evidence:** `src/dopemux/pcp/**` contains zero forbidden merge-writer references (`queue_drain`, `batch_resolve_and_merge`, `pr_merge_specialist`). Bridge registry defaults inert (`writer_registry=None`); both factories default to no writer.

**Guard added:** `tests/project_control_plane/test_red_line_15.py` — 3 tests (forbidden-token scan; both factories default `writer_registry=None`; `route_mutation` `execute=True` + no writer → `executed=False, permitted=False`). PASS.

---

## Routing Residual → `#968/#967`

**Finding:** `selected_provider:"unknown"` is permitted for the `SELECTED` routing branch (schema forbids `null` but allows the `"unknown"` string). Contracts-only; no runtime consumer.

**Classification:** ROUTING_POLICY_RESIDUAL — tracked under `#968/#967`. **Supervisor recommendation:** CONTEXTUAL now (`"unknown"` permissible for public/read-only/manual lanes); STRICT before runtime routing activation (private/high-risk/security/release/structured-output → block or escalate).

---

## A1 — Activation-Scoped: Unsigned READY Gate (Deferred)

**Finding:** the `LIVE_WRITE_READY` gate enforces schema shape + internal consistency + TTL + operation binding, but not cryptographic signing / authenticated issuer provenance.

**Classification:** ACTIVATION_SCOPED — fail-closed in commit-default/in-tree wiring; only exploitable once a real writer is registered (bridge inert today).

**Deferred work:** signed/authenticated READY issuer, endpoint authN/Z, cross-process atomic dedup + lease, gate-verifier dependency, tz-aware-strict `_parse_iso8601`, generic `WRITER_RAISED` code, `_canonical_digest allow_nan=False`.

---

## PAL Validation

- **gpt-5.2** (neutral): validated the finding set + classification + A3 rejection; sharpened the A3 residual; confirmed bridge fail-closed.
- **gpt-5.5** (neutral, 8/10): corroborated; narrowed A1 to "commit-default state"; flagged A2 faithful-fix > exporter wiring.
- **gemini-2.5-pro** (adversarial, 9/10): conceded all facts; pushed severity/scope.
- (grok-4, claude-opus-4.5, gemini-3-pro-preview adversaries were unavailable — provider credit/decommission — and are NOT counted.)

---

## Validation Buckets

| Bucket | Result |
|---|---|
| `tests/project_control_plane` + `tests/dcp_extension` (full, incl. Packet-5 scope-lock + schema-bundle parity) | **PASS** (0 failures) |
| Wheel **contents** (`dopemux/pcp/*` modules + `dopemux-pcp` script + 4 vendored `_schemas/*.json` + loader shim) | **PASS** |
| `jsonschema` in core `Requires-Dist` (unconditional) | **PASS** |
| Clean-venv **install + import** of all 6 `dopemux.pcp.*` modules + CLI from installed wheel | **PASS** (was FAIL before #978; re-verified on merged branch) |
| `rg "queue_drain\|batch_resolve_and_merge\|pr_merge_specialist" src/dopemux/pcp` | **PASS** (empty) |

**NOT claimed:** SOUND_FOR_ACTIVATION — requires A2 authority modeling + exporter-consumption, the A1 signing/auth family, and the routing residual to all close first.

---

## Tracked Follow-ups (out of this PR)

1. **A2 proof-family authority modeling** — clean `proof.*` ownership plane (not the MCP adapter set).
2. **A2 exporter-consumption** — extension-aware seam resolving proof_status_map at export time.
3. **Routing residual `#968/#967`** — `selected_provider:"unknown"` policy (CONTEXTUAL → STRICT).
4. **A1 activation-security family** — signing/auth/dedup-lease/etc.

*(A4 wheel-safe schema loading — formerly follow-up #1 — was completed by #978.)*
