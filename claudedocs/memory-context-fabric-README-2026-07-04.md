# Memory Context Fabric — Design Doc Set (index)

**Date**: 2026-07-04 · **Status**: DESIGN (fold-in-ready) · **Branch**: `claude/memory-context-fabric`
**What this is**: the complete design documentation for the **Memory Context Fabric** — the subsystem that makes dopemux "keep track of everything and inject the needed context at all times, including conversation history." Generated for folding into a larger dopemux architecture design. **No implementation** is included; these are design + contract artifacts.

---

## The documents (read in this order)

| # | Doc | Purpose |
|---|---|---|
| 1 | **`memory-context-fabric-design-2026-07-04.md`** (v3) | The design spec — architecture (Context Fabric over the Memory Trinity), authority model, capture pipeline, memory model, retrieval + injection, governance, and the evidence-gated TP-MCF-001…009 phasing. Twice externally audited (CONDITIONAL-GO). |
| 2 | **`tp-mcf-001-authority-map-2026-07-04.md`** | Current-runtime truth — the file:line authority map for capture / promotion / ConPort / dope-context / hooks / bridge, with dead surfaces and painted sockets marked. Distinguishes *what exists* from *what the design targets*. |
| 3 | **`memory-context-fabric-interfaces-2026-07-04.md`** | Interfaces & data contracts — the Fabric's public surface (`context.recall`/`context.recap`), the `CaptureEnvelope`/`PromotedEntry`/`ContextBundle` schemas, plane-interaction contracts, and the invariants (contract tests). Defines the Fabric as a **bounded subsystem** with clear boundaries. |

**Supporting context** (separate initiatives, referenced by the above):
- `mcp-fleet-canonical-audit-and-target-design-2026-07-03.md` — the MCP fleet target-state (on `main`); the Fabric's plane dependencies live here.
- `mcp-fleet-forgotten-features-addendum-2026-07-04.md` — dormant-capability archaeology (on the `claude/mcp-fleet-audit-complete` branch); the semantic-memory / graph-traversal / ADHD-intelligence pieces the Fabric would resurrect.

---

## How it folds into a larger architecture

The Memory Context Fabric is **one subsystem** of the dopemux architecture, defined by three boundaries:

1. **Above it** — agent sessions (Claude Code / Codex) that *emit events and receive context*. They do not orchestrate memory.
2. **Below it** — the Memory Trinity planes (dope-memory / ConPort / dope-context) as canonical stores, plus Redis transport and the native-hook substrate. The Fabric is a *client* of these, never their owner.
3. **Beside it** — the **DCP read-only facade** (outbound projection to external LLMs) is the mirror-image sibling: the Fabric is *inbound + local*, DCP is *outbound + read-only*. Both use the same "orchestrate, don't own" + provenance/trust model, so they compose cleanly in a larger design.

**Invariant that makes it composable**: the Fabric owns no truth — no storage, no decision/graph/PM/retrieval authority, no fourth datastore. That is what lets it be dropped into a larger architecture without violating the Memory Trinity split-authority ADRs or the fleet governance model.

**Maturity for fold-in**: architecture + contracts are design-complete and audit-corrected; current-state is verified (doc 2); implementation is decomposed into gated packets (TP-MCF-001 done as a no-code audit; TP-MCF-002+ pending) but **not built** — so the larger architecture can treat this as a specified-but-unbuilt subsystem with a known build path.

---

## Governance footer

**Validation**: design/analysis only — **no code changed, live behavior NOT_RUN.** All runtime claims are file:line-grounded in doc 2; unbuilt/dead surfaces (`memory_{hash}`, `graph.neighbors`, transcript ingest, `context.recall`) are marked as such. **Rollback**: delete the four docs on this branch.
