# ConPort Authority Invariant Gaps

**Date:** 2026-03-12
**Purpose:** Identify invariants that are documented but not enforced in code.

---

## Documented Invariants

These invariants are stated in `docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md`
and related ADRs.

---

## Invariant 1: ConPort is canonical for decisions/progress/context

**Stated in:** ADR-ConPort, authority-invariants-and-dark-methods.md
**Status:** DOCUMENTED, PARTIALLY ENFORCED

**What is enforced:**
- REST endpoints are the sole write path for decisions/progress/context
- FastMCP and JSON-RPC wrappers delegate to REST (no bypass)
- dopecon-bridge KG proxy routes to ConPort (verified in TP4A)

**What is NOT enforced:**
- No auth gate prevents direct writes to ConPort from unauthorized callers
- No write audit log at the ConPort layer — writes are accepted without identity attribution
- No rate limiting on write endpoints
- Any caller that can reach port 3004 can write decisions/progress to any workspace_id

**Gap type:** Operational hardening gap (not a design gap)
**Risk:** Medium — contained by network boundary assumption
**Fix:** Add auth middleware + write audit at REST handler entry points

---

## Invariant 2: Projections/mirrors are non-canonical

**Stated in:** ADR-ConPort, PREFERRED_SURFACE_DECISION.md
**Status:** DOCUMENTED, NOT CODE-ENFORCED

**What is enforced:**
- FastMCP wrappers delegate to REST (no local state)
- JSON-RPC handler delegates to REST (no local state)
- dopecon-bridge DDG proxy routes to ConPort (no local DDG write)

**What is NOT enforced:**
- No code-level label on FastMCP/JSON-RPC responses marking them as `authoritative: false`
- No `lane: canonical` metadata in REST responses
- No response envelope distinguishing "canonical result" from "wrapper result"
- Callers must infer canonical authority from integration contract, not from response metadata

**Gap type:** Observability/provenance gap (not a correctness gap)
**Risk:** Low — correctness is maintained, provenance is not surfaced
**Fix:** Add `authority: "canonical"` and `source_surface: "rest"` fields to REST responses, or document that responses are implicitly canonical.

---

## Invariant 3: Custom_data is a ConPort capability, not a canonical PM-plane contract

**Stated in:** docs/systems/conport/authority-invariants-and-dark-methods.md
**Status:** DOCUMENTED, ENFORCED BY OMISSION

**What is enforced:**
- custom_data is REST-only (no MCP wrappers)
- Not listed in any PM-plane normalized tool surface

**What is NOT enforced:**
- No schema/contract defined for custom_data use cases
- No workspace-level access scope for custom_data categories
- No prohibition on unauthorized category/key creation

**Gap type:** Contract gap (capability exists, contract is undefined)
**Risk:** Low — capability is REST-only with no wrappers, limiting accidental misuse
**Fix:** Define allowed categories and key namespaces for PM-plane use if custom_data is to be sanctioned.

---

## Invariant 4: Dark methods are internal-only

**Stated in:** DARK_METHOD_INVENTORY.md, authority-invariants-and-dark-methods.md
**Status:** DOCUMENTED, NOT ENFORCED IN CODE

**What is enforced:**
- fork_instance, promote, promote_all are documented as admin-only

**What is NOT enforced:**
- No auth scope or role check distinguishes admin calls from normal calls
- These methods appear on all three surfaces (REST, JSON-RPC, FastMCP)
- They are discoverable via `tools/list` on JSON-RPC and FastMCP — any agent can call them

**Gap type:** Access control gap
**Risk:** Medium — well-meaning agents may call fork_instance/promote unexpectedly
**Fix:** Either add auth scope check (`admin_only: true` flag), remove from FastMCP/JSON-RPC tool discovery, or document prominently in all surface inventories.

---

## Invariant 5: AGE/ag_catalog dependency is available at runtime

**Stated in:** Implicit in graph operations in enhanced_server.py
**Status:** ASSUMED, NOT VALIDATED AT STARTUP

**What is enforced:**
- `init_connections()` attempts to create AGE extension and initialize graph

**What is NOT enforced:**
- No startup health gate fails the service if AGE is unavailable
- `ag_catalog` missing logs a warning but does not prevent service startup
- If AGE is missing, graph operations silently fail or return empty results

**Gap type:** Deployment assumption gap
**Risk:** Medium — ConPort may appear healthy while graph features are broken
**Fix:** Add explicit AGE availability check to `/health` endpoint; fail health check if AGE required and missing.

---

## Invariant Gap Summary

| Invariant | Documented | Code-Enforced | Gap Type | Risk |
|-----------|-----------|---------------|----------|------|
| ConPort is canonical for decisions/progress/context | YES | Partial | Auth hardening | Medium |
| Projections/mirrors are non-canonical | YES | Partial | Provenance/observability | Low |
| custom_data is not sanctioned PM-plane contract | YES | Enforced by omission | Contract definition | Low |
| Dark methods are internal-only | YES | NOT enforced | Access control | Medium |
| AGE dependency validated at startup | Implied | NOT enforced | Deployment assumption | Medium |

**Total open invariant gaps: 5**
**Critical gaps (would break PM-plane correctness): 0**
**Medium risk gaps (could cause confusion or silent failure): 3**
**Low risk gaps (documentation/provenance only): 2**
