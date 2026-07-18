# MCPINT ↔ SVCFEAT Reconciliation — the Serena/DopeCode seam

**Date**: 2026-07-17 · **Status**: **CONFIRMED by user 2026-07-17** (Option C applied to both trees: DEPLOY-001 `c14414ff` rescoped, IMP-ADHDINTEL-007 `e5984180` cancelled-terminal, moot deps dropped, ARCH-SERENA-003 narrowed to write-lane gating)
**Collision surface**: MCPINT gate G3 + IMP-ADHDINTEL-007 vs DMX-SVCFEAT DOPECODE-DEPLOY-001 (item `c14414ff`, tree `f64aa1a9`, PR #1072)

## 1. The collision, precisely

Two same-day directives, both carrying user authority, prescribe different shapes for
the same code (`services/serena`, the 46-tool in-repo engine):

| Directive | Session | Shape | Grounding |
|---|---|---|---|
| **MCPINT G3** ("Two surfaces, no overlap") | this session, answered AFTER the tool-delta analysis | Upstream serena stays (27 tools incl. the 22 candidate-lacks: memories, onboarding, editing suite, shell); the 41 candidate-only tools extracted to a `dope-adhd` surface on adhd-engine; 8 duplicates dropped | user constraint: "keep ALL features"; delta showed replacement loses 22 tools |
| **SVCFEAT DOPECODE-DEPLOY-001** (KEYSTONE) | sibling session, same day | "containerize services/serena engine + **repoint compose off upstream wrapper**" — i.e. the candidate REPLACES upstream; supersedes SVCFIN ARCH-SERENA-SURFACE-003 archive→deploy | user intent: deploy the stranded flagship engine as a product ("DopeCode") |

The literal SVCFEAT spec is G3's rejected "Promote candidate" option. But the two
*intents* are compatible: the user wants the engine's features LIVE (both agree) and
wants nothing lost (G3's delta-informed refinement). The conflict is only in the
deployment topology.

## 2. Recommended harmonization (Option C — "DopeCode as the extended surface")

**Deploy DopeCode as its OWN service** (own container, own name/port, own catalog
entry) — do NOT repoint the serena compose service:

1. **DOPECODE-DEPLOY-001 (modified)**: containerize `services/serena` as `dopecode`
   (new compose service + catalog entry, agents matrix per ADR-002). Upstream serena
   stays untouched — its 22 unique tools (memories/onboarding/editing/shell) survive,
   its write-lane gating still lands via the surface ADR.
2. **MCPINT-IMP-ADHDINTEL-007 is SUPERSEDED** by the modified DEPLOY-001: the 31-tool
   ship-list (F001, ADHD intelligence, analytics, nav-guidance, structural-graph)
   goes live *in place* on DopeCode — zero extraction/porting cost, which is strictly
   cheaper than the adhd-engine port and removes the dependency on engine ignition.
   The complexity-delegation sub-spec (G5: `analyze_complexity`/`get_unified_complexity`
   delegate to the complexity library) transfers onto DopeCode unchanged.
3. **The 8 upstream-duplicate tools** (`find_references`, `goto_definition`,
   `search_pattern`, `get_file_symbols`, `apply_patch`, `batch_apply_patch`,
   `create_file`, `write_file`) + `find_similar_code` (dope-context's plane): disable
   on the DopeCode surface or mark non-contractual in its catalog `tools:` pointer, so
   the no-overlap doctrine and the tool-granular drift gate stay coherent. DopeCode's
   own improvement packets (ROLLBACK-004, RENAME-006, LSP-007) may later justify
   promoting its write layer — that's a future surface-ADR amendment, not a default.
4. **Placement-map delta** (addendum added to tool-placement-map.md): `dope-adhd` on
   adhd-engine is CANCELLED as a surface; its planned tools live on `dopecode`.
   Plane-purity is trade-off-accepted: F001/focus/fatigue storage already lives inside
   this engine; adhd-engine still consumes DopeCode signals via events for
   notifications/recap (unchanged SVCFIN ADHDLOOP scope).
5. **Seam guards updated**: ARCH-SERENA-SURFACE-003 (SVCFIN) remains the owner of
   upstream write-lane gating ONLY (its archive question is moot — nothing archives);
   the MCPINT reconcile-notes on ADHDINTEL/root point here.

**Why not the literal SVCFEAT shape (replace upstream)?** It silently loses serena
memories (used by live agent sessions), onboarding/project-activation, and the
symbol-editing suite — the exact regression the user refused when shown the delta.
**Why not keep the MCPINT extraction?** It duplicates work DEPLOY-001 does for free,
adds an engine-ignition dependency, and would strand DopeCode's non-ADHD extras
(callers/callees/import-graph) in limbo.

## 3. Effects on loaded packets (no orchestrator mutations until user confirms)

| Item | Effect |
|---|---|
| SVCFEAT DOPECODE-DEPLOY-001 (`c14414ff`) | MODIFY summary: "repoint compose off upstream" → "deploy as new `dopecode` service alongside upstream; dupes disabled/non-contractual" |
| MCPINT IMP-ADHDINTEL-007 (`e5984180`) | CANCEL as superseded (spec note transfers: 31-tool list, complexity delegation, snapshot/catalog obligations) |
| Cross-tree dep ADHDLOOP-IGNITION → ADHDINTEL | DROP (no longer needed — DopeCode doesn't ride on adhd-engine) |
| SVCFIN ARCH-SERENA-SURFACE-003 (`9a96f47e`) | Scope narrows to upstream write-lane gating; archive question closed |
| MCPINT FND-DRIFTGATE-003 / DOC packets | Gain `dopecode` as a snapshot/catalog subject once deployed |
| adr-mcpint-001/002 | Minor amendments at acceptance: dopecode server entry + agents row; placement-map addendum referenced |

## 4. Confidence & authority

Authority: user G3 answer (delta-informed, this session) + SVCFEAT packet text (read
from the tree, not paraphrase) + tool-delta computed live 2026-07-16. Confidence:
high on the collision being real; the harmonization is a recommendation — final shape
is the user's call.
