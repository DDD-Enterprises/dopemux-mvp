# 13 — Bundle-01 Provenance Resolution

Audit: `UR-AUDIT-001R3` · Auditor: Claude Opus in Claude Code (runner-configured, not provider-attested)
Repository: `DDD-Enterprises/dopemux-mvp` · HEAD = census commit `b176747b339685e781de04268c46b7ae123abfbf`

## Method

For every bundle-01 authority/contract/doctrine file I computed the Git blob object id
(`sha1("blob <len>\0"+content)`) and matched it against the **full census tree**
(`git ls-tree -r b176747`, 16,058 tracked blobs). A blob-id match proves a *byte-identical*
tracked file exists at that path at the census commit. For non-matches I checked root-path
existence with `git cat-file -e <commit>:<path>` and compared against the tracked variants that
UR-INV-004 named, using line/diff deltas to gauge semantic equivalence. Archive names were **not**
treated as proof of tracked root paths (mandatory correction 4).

Census commit equals current HEAD, so census and current-repo provenance are the same object graph.

## Headline result

- 32 bundle-01 payload files examined (excludes `MANIFEST.json`, `START_HERE.md`).
- **23 are byte-identical to at least one tracked path at census; 9 have no byte-identical tracked file.**
- The bundle is a *promoted upload set*: many files match `out/chatgpt-project-upload-set/…` copies
  and/or `docs/research/mcp-customization/dopemux-constraints/…` copies. Several also match genuine
  tracked reference docs (`docs/03-reference/systems/…`, `docs/governance/…`) or tracked **root**
  authority files.
- The upload assigns exact-authority names (`RULES.md`, `TRUTH_*`, `SYSTEM_*`, `system-boundaries.md`)
  by prefix, but for the highest-authority *root* names these frequently correspond to **absent root
  paths** or **research-tier copies** — exactly the C-001 / UR-OQ-001 conflict.

This **independently confirms** UR-ARCH-001's disposition (C-001, UR-OQ-001, `01_EXECUTIVE_VERDICT`
"CONFLICTING") and UR-INV-004 `BASELINE_DRIFT_CHECK` "Authority-Document Availability", and confirms
UR-REV-004 carried-unknown "Exact root authority filenames were absent at the inspected commit".

## Provenance matrix (bundle-01 → census tree)

Legend — Tier: `ROOT_AUTHORITY` = byte-identical tracked file at repo root; `REF_DOC` = byte-identical
tracked `docs/03-reference|02-how-to|governance` reference doc; `RESEARCH_ONLY` = byte-identical only to
`docs/research/…` (UR-INV-004 lower authority) and/or `out/…upload-set/…`; `UPLOAD_ONLY` = byte-identical
only to an `out/…upload-set/…` copy; `NO_MATCH` = no byte-identical tracked blob (semantic variant may exist).

| Bundle path | Git blob | Byte-identical tracked path(s) at census | Tier | Root name present at census? |
|---|---|---|---|---|
| authority/01_RULES.md | 75f22158 | (none) — semantic variant `docs/03-reference/governance/rules.md` differs (+YAML front-matter, 29 changed lines) | NO_MATCH | `RULES.md` **ABSENT** |
| authority/02_PROJECT.md | 29670dd2 | `PROJECT.md` (+upload copy) | ROOT_AUTHORITY | `PROJECT.md` PRESENT (identical) |
| authority/03_ARCHITECTURE.md | 34438d5e | `ARCHITECTURE.md` (+upload copy) | ROOT_AUTHORITY | `ARCHITECTURE.md` PRESENT (identical) |
| authority/04_system-boundaries.md | 05b02cff | (none) — semantic variant `docs/03-reference/systems/system-boundaries.md` differs (6 lines) | NO_MATCH | `SYSTEM_BOUNDARIES.md`/`system-boundaries.md` **ABSENT** at root |
| authority/05_TRUTH_SCOPE.md | ab7c31b9 | (none) | NO_MATCH | `TRUTH_SCOPE.md` **ABSENT** |
| authority/06_TRUTH_SYSTEMS.md | f0e11cbe | `docs/research/mcp-customization/dopemux-constraints/TRUTH_SYSTEMS.md` | RESEARCH_ONLY | absent at root |
| authority/07_TRUTH_INTERFACES.md | e8a30e3e | `docs/research/…/TRUTH_INTERFACES.md` | RESEARCH_ONLY | absent at root |
| authority/08_TRUTH_DATA_EVENTS.md | f4e0747c | `docs/research/…/TRUTH_DATA_EVENTS.md` | RESEARCH_ONLY | absent at root |
| authority/09_TRUTH_CANONICALS.md | eeba102c | `docs/research/…/TRUTH_CANONICALS.md` | RESEARCH_ONLY | absent at root |
| authority/10_TRUTH_GAPS.md | dd8ea45b | `docs/research/…/TRUTH_GAPS.md` | RESEARCH_ONLY | absent at root |
| authority/11_SERVICE_CATALOG.md | 3bd21022 | `SERVICE_CATALOG.md` (+upload copy) | ROOT_AUTHORITY | `SERVICE_CATALOG.md` PRESENT (identical) |
| authority/12_PM_PLANE.md | 3fd5fa11 | `out/…upload-set/…/05_PM_PLANE.md` only — **root `PM_PLANE.md` blob is `7725d672`, differs** | UPLOAD_ONLY | `PM_PLANE.md` PRESENT but **NOT identical** (bundle stale) |
| authority/13_SYSTEM_Dopemux.md | 6b538875 | `docs/research/…/SYSTEM_Dopemux.md` | RESEARCH_ONLY | absent at root |
| authority/14_SYSTEM_Dopetask.md | 4c52e38c | `docs/03-reference/systems/dopetask/system-dopetask.md` (+upload copy) | REF_DOC | absent at root (canonical is docs ref) |
| authority/15_SYSTEM_TaskOrchestrator.md | bdda10e5 | (none) | NO_MATCH | absent at root |
| authority/16_SYSTEM_ConPort.md | fddf579a | `docs/03-reference/systems/conport/system-conport.md` (+research +upload) | REF_DOC | absent at root |
| authority/17_SYSTEM_DopeMemory.md | abbf361d | `docs/research/…/SYSTEM_DopeMemory.md` (+upload) | RESEARCH_ONLY | absent at root |
| authority/18_SYSTEM_DopeContext.md | 475ecbd3 | `docs/03-reference/systems/dope-context/system-dopecontext.md` (+research +upload) | REF_DOC | absent at root |
| authority/19_SYSTEM_DopeconBridge.md | cf40bb83 | `docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md` (+research +upload) | REF_DOC | absent at root |
| authority/20_SYSTEM_ADHDEngine.md | 5f696339 | `docs/03-reference/systems/adhd-engine/system-adhdengine.md` (+research +upload) | REF_DOC | absent at root |
| authority/21_SYSTEM_RepoTruthExtractor.md | 77926375 | `docs/research/…/SYSTEM_RepoTruthExtractor.md` | RESEARCH_ONLY | absent at root |
| authority/22_AGENTS.md | 020793c3 | (none) — **root `AGENTS.md` blob is `b7bbdac1`, differs (14,767 vs 9,355 bytes)** | NO_MATCH | `AGENTS.md` PRESENT but **NOT identical** (bundle stale/older) |
| execution-doctrine/23_PAL_EXECUTION_RULES.md | 06e67cfd | (none) | NO_MATCH | absent at root |
| execution-doctrine/24_PAL_CHAINING_DOCTRINE.md | 4406632b | (none) | NO_MATCH | absent at root |
| execution-doctrine/25_PAL_PACKET_TEMPLATE.md | 9d3c6b8f | (none) | NO_MATCH | absent at root |
| execution-doctrine/26_dopetask-cannonical-spec.json | 81dd4402 | (none) — semantic variant `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` differs (6 lines); note bundle name misspells "cannonical" | NO_MATCH | absent at root |
| contracts/33_adapter-schema.md | ce9e878c | `docs/02-how-to/integrations/dopetask/adapter-schema.md` (+docs/integrations +archive +upload) | REF_DOC | tracked docs canonical |
| contracts/34_adapter-contract.md | 67a1763d | `docs/02-how-to/integrations/dopetask/adapter-contract.md` (+3 more) | REF_DOC | tracked docs canonical |
| contracts/35_proof-bundle-schema.md | f86e544d | `docs/governance/proof-bundle-schema.md` (+archive +upload) | REF_DOC | tracked docs canonical |
| contracts/36_proof-contract.md | ca2dc000 | `docs/governance/proof-contract.md` (+archive +upload) | REF_DOC | tracked docs canonical |
| contracts/37_handoff-contract.md | 20fe4682 | `docs/03-reference/governance/handoff-contract.md` (+docs/governance +archive +upload) | REF_DOC | tracked docs canonical |
| execution-doctrine/38_TEMPLATE_TASK_PACKET.md | 0f953ed2 | `out/…upload-set/…/31_TASK_PACKET_TEMPLATE.md` only | UPLOAD_ONLY | no tracked canonical variant identified |

## Root-path existence checks (git cat-file -e b176747:<path>)

PRESENT at root: `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, `AGENTS.md`.
ABSENT at root: `RULES.md`, `SYSTEM_BOUNDARIES.md`, `system-boundaries.md`, `TRUTH_SCOPE.md`,
`TRUTH_SYSTEMS.md`, `SYSTEM_Dopemux.md`, `SYSTEM_TaskOrchestrator.md`, `PAL_EXECUTION_RULES.md`,
`PAL_CHAINING_DOCTRINE.md`, `dopetask-cannonical-spec.json`.
Tracked variants PRESENT: `docs/03-reference/governance/rules.md` (blob 8c6fb115),
`docs/03-reference/systems/system-boundaries.md` (blob 3754ceb2),
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (blob a4620a82).

## Authority-tier resolution (prompt AUTHORITY ORDER)

- **Tier 3 (tracked authority docs at HEAD):** `PROJECT.md`, `ARCHITECTURE.md`, `SERVICE_CATALOG.md`
  are tracked at root **and byte-identical** to the bundle copies → usable as tier-3 authority.
  `PM_PLANE.md` and `AGENTS.md` are tracked at root but the **current tracked versions differ** from the
  bundle copies (bundle is stale); the *current tracked* versions are authoritative, not the bundle copies.
  `RULES.md` and root `system-boundaries.md` are **absent at root**; the tracked authority is
  `docs/03-reference/governance/rules.md` and `docs/03-reference/systems/system-boundaries.md`
  (near-equivalent, not byte-identical to bundle).
- **Tier 2 (`TRUTH_*` artifacts at HEAD):** **No canonical tracked `TRUTH_*` files exist at HEAD.**
  The only tracked `TRUTH_*` blobs are under `docs/research/mcp-customization/dopemux-constraints/`
  (research tier). The prompt's authority tier 2 is therefore effectively empty at HEAD; `TRUTH_*` content
  must be treated as research-tier context, not decisive authority.
- **Tier 4 (`SYSTEM_*` docs):** Canonical tracked forms exist for Dopetask, ConPort, DopeContext,
  DopeconBridge, ADHDEngine under `docs/03-reference/systems/…` (byte-identical to bundle). Dopemux,
  RepoTruthExtractor exist only as research copies; TaskOrchestrator has no byte-identical tracked copy.
- **Governance contracts (proof / proof-bundle / handoff / adapter):** all byte-identical to tracked
  `docs/governance/…`, `docs/03-reference/governance/…`, `docs/02-how-to/integrations/dopetask/…`
  reference docs → **referenceable without copying** (satisfies UR-TP-001 stop-condition on canonical
  contract reference; see finding UR-AUDIT-R3-001).

## Effect on UR-ARCH-001 material claims (traced independently — mandatory correction 5)

The architecture's authority-boundary claims (Freeflow=quota/admission owner, LiteLLM=proxy,
RTE=extraction, Task Orchestrator=workflow/capability-family, dopetask=execution, DCP=pure classifier,
`services/task-router` dormant, `agent_orchestrator`/`services/agents` isolated) are grounded in
**runtime code/config** that I verified present at census (see `05_AUTHORITY_AND_COEXISTENCE_AUDIT.md`),
not in the weak-provenance `TRUTH_*`/`SYSTEM_*` documents. **The provenance weakness therefore does not
invalidate the runtime-grounded authority findings.** No material UR-ARCH-001 decision was found to
depend decisively on an absent-root or research-tier bundle file; where such documents are cited, the
architecture explicitly preserved the conflict (C-001, UR-OQ-001).

## Provenance disposition

`SUFFICIENT_FOR_MATERIAL_AUTHORITY_CLAIMS_WITH_DOCUMENTATION_REPAIR`.

This audit **supplies the Git evidence UR-OQ-001 requested** (`git ls-tree` at census, content/blob
hashes for RULES/PROJECT/ARCHITECTURE/SYSTEM_BOUNDARIES/TRUTH/contracts). UR-OQ-001's authority-tracking
axis is therefore **resolvable now**. Residual repair (finding UR-AUDIT-R3-001, P2): UR-TP-001 must cite
the **tracked canonical paths** identified above (not the bundle archive names), treat `TRUTH_*` as
research-tier, and use the *current tracked* `PM_PLANE.md`/`AGENTS.md`, not the stale bundle copies.
