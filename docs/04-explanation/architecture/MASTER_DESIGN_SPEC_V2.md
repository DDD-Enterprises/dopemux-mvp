---
id: MASTER_DESIGN_SPEC_V2
title: Master Design Spec V2
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Master Design Spec V2 (explanation) for dopemux documentation and developer
  workflows.
---
# ChatRipperXXX Master Design Spec V2

_Generated: 2026-02-03T05:44:13.734921+00:00 (UTC)_

**Canon rule:** This spec is distilled from the *best ideas across the repo’s Markdown files*, even when they conflict. Conflicts are resolved explicitly in the **Decisions & Conflict Resolutions** section, with operator overrides taking priority.

## 0) Executive intent

- **Local-first, privacy-first** ingestion + analysis of chat/media sources.
- **Deterministic artifacts**: every run produces validated JSON artifacts with provenance hashes.
- **Evidence-first outputs**: answers are grounded in retrieved chunks with explicit citations.
- **Psych-on**: a psychology lens runs on every synthesis (as *signals*, not diagnoses), with strict privacy tiers.
- **Cloud synthesis from day 1**: allowed only on `cloud_safe` content unless explicitly overridden.

## 1) System boundaries

### In scope
- CLI-first pipeline: extract → transform → redact → enrich → index → query/synthesize.
- Pluggable backends: vector store, graph store, transcription, cloud provider.
- Run artifact suite: manifest, stage reports, synthesis outputs, envelopes, quarantine.

### Out of scope (for now)
- Always-on server mode (HTTP API may exist later, but CLI remains canonical).
- Non-consensual inference: medical/clinical claims, diagnosis, or therapeutic advice.

## 2) Canonical pipeline

### Stages
1. **Extract**: acquire raw sources (e.g., iMessage DB, Instagram exports) into a staging directory.
2. **Transform**: normalize into canonical message/chunk records.
3. **Redact (Policy Shield)**: classify + redact to produce privacy-tiered text.
4. **Enrich**: local-first enrichment; media metadata extraction; optional cloud enrichment only on `cloud_safe`.
5. **Index**: embed and index redacted/enriched chunks.
6. **Query + Synthesize**: retrieve → (optional rerank) → synthesize answer with citations (cloud-first allowed per policy).

### Artifacts per stage (high level)
- `manifest.json`: run provenance + inputs/hashes.
- `stage_report.json`: per-stage summaries + metrics + warnings.
- `quarantine/`: invalid outputs, schema failures, provider failures.
- `answer.json` + `llm_envelope.json`: synthesis output and audit envelope.

## 3) Core data contracts

### Canonical identities
- **conversation_id**: stable ID per thread/source.
- **chunk_id**: stable ID per chunk; must be used for citations.
- **run_id**: unique per run; threads all artifacts.

### Schema validation
- Every artifact is validated with strict JSON Schema (`additionalProperties: false` where applicable).
- Any invalid artifact is quarantined; synthesis must hard-fail on invalid outputs.

## 4) Privacy tiers & Policy Shield

### Privacy tiers
- `local_only`: never leaves the machine.
- `cloud_safe`: redacted/sanitized text suitable for cloud synthesis.
- `public`: already public; may be treated as `cloud_safe`.

### Cloud policy
- Cloud synthesis is permitted only when **all** sources are `cloud_safe`, unless an explicit operator override is used.
- Default `store_remote=false` for providers.

## 5) Cloud synthesis with citations

### Requirements
- Structured Outputs (json_schema) must be used when supported by the provider.
- Every claim includes `source_chunk_ids[]` referencing retrieved chunks.
- Citation integrity: any citation referencing an unknown chunk_id is a hard failure.

### Required artifacts
- `answer.json`: final answer + claims + citations + limits + next actions.
- `llm_envelope.json`: provider/model + request/response hashes + raw output + validation flags.

## 6) Psychology lane (psych-on)

### Semantics
- Outputs are **signals** inferred from available text. No diagnosis; no medical claims.
- Use coarse labels for cloud-safe summaries; fine labels remain local-only unless operator override.

### Outputs
- A `psychology.summary` in `answer.json` grounded in citations.
- Optional `psychology.profile` only if produced by an enabled backend.

## 7) Storage backends

### Vector store
- Vector index is the primary retrieval mechanism.
- Indexing must operate on redacted/enriched content.

### Graph store
- Graph is an auxiliary structure for relationship queries and temporal evolution.
- **Default backend: embedded (Kùzu)** for portability.
- Optional Neo4j backend remains available behind extras.

## 8) Decisions & conflict resolutions (operator overrides)

- **Canon source**: best ideas across repo `.md` files; conflicts resolved here.
- **Cloud synthesis**: supported from day 1 for query synthesis, gated by privacy tiers.
- **Graph default**: embedded backend preferred; Neo4j optional.
- **Psych-on**: enabled for every synthesis; outputs are signals with citations.

### Conflict ledger (excerpt)

# Design Conflict Ledger (vNext)

_Generated: 2026-02-03T05:35:38.699294Z_

This ledger enumerates conflicting directives across Markdown sources and records the current resolution decisions (operator overrides win).

## CLOUD_DEFAULT: Cloud disabled by default vs cloud synthesis from start

**Sources:**

- `docs/interfaces.md:L7`

- `MASTER_DESIGN_SPEC.md:L34`

- `docs/architecture.md:L31`


**Decision:**

- Enable cloud synthesis from the start for the *synthesis/assist* stage only, but keep cloud disabled by default for enrichment and other stages unless explicitly enabled. Cloud calls require Policy Shield + cloud_safe tier; store_remote default false.


## GRAPH_BACKEND: Neo4j planned vs local-first embedded graph and 'not operationally required'

**Sources:**

- `docs/design/adrs/ADR-008-psychology-graph-integration.md:L14`

- `docs/architecture.md:L45`

- `lab/16_GRAPH_AND_PSYCHOLOGY_MODEL.md:L2`


**Decision:**

- Graph is optional and must not be a hard dependency. Default backend becomes embedded Kuzu for portability; Neo4j remains an optional extra for advanced users.


## CLOUD_BLOCKED: Architecture doc says cloud providers planned/blocked vs current implementation includes cloud client

**Sources:**

- `docs/architecture.md:L31`


**Decision:**

- Modernize: cloud is supported for synthesis when enabled; treat architecture statement as outdated. Update docs to reflect reality once A3 is merged.

## 9) vNext delta

# MASTER_DESIGN_SPEC vNext (Delta + Additions)

_Generated: 2026-02-03T05:35:38.699294Z_

This document lists high-impact design requirements present in repo Markdown that should be treated as canonical going forward.

## 1) Policy Shield hard requirements

- Coverage thresholds: standard ≥99.5%, strict ≥99.9% (`lab/03_PRIVACY_AND_POLICY_SHIELD.md:L8-L10`, `docs/interfaces.md:L6-L7`).

- Deterministic pseudonymization; stable within a run; non-reversible without salt (`lab/03_PRIVACY_AND_POLICY_SHIELD.md:L14-L16`).

- Field visibility boundary: raw text/attachments/fine labels local-only; redacted+coarse labels cloud-eligible (`lab/03_PRIVACY_AND_POLICY_SHIELD.md:L28-L31`).

## 2) Psychology analysis architecture

- Label taxonomy: 53 coarse (cloud-safe) + 100+ fine (local-only) (`docs/psychology-analysis.md:L18-L24`).

- Temporal graph relationship types (12) + pattern types (6) (`docs/psychology-analysis.md:L44-L56`).

- Cloud reconstruction strategy: token-preserving redaction flow (see `docs/psychology-analysis.md` section "Cloud Reconstruction Strategy").

## 3) CLI interface contracts

- Explicit CLI flags and defaults for pipeline steps (local model baseline, allow-cloud gate, windows/limits) are specified in `docs/interfaces.md`.

- `ingest` is deprecated in favor of source-specific pull → transform → redact → index (`docs/interfaces.md:L71`).

## 4) Cloud synthesis from start (operator override)

- Synthesis/assist may use cloud from day one if and only if inputs are Policy-Shielded and cloud-safe (override conflicts with "cloud disabled by default" docs).

## 5) Graph optionality

- Graph is exploratory and must not be an operational requirement (`lab/16_GRAPH_AND_PSYCHOLOGY_MODEL.md:L2-L35`).

## 10) Implementation gap map

# Implementation Gap Map (from Markdown canon)
_Generated: 2026-02-03T05:35:38.699294Z_
| Area | Status | Evidence / Notes |
|---|---|---|
| Policy Shield coverage thresholds (0.995/0.999) | implemented | src/chatx/redaction/policy_shield.py |
| Deterministic pseudonymization + salt file | implemented | src/chatx/redaction |
| Cloud-safe vs local-only field visibility | implemented | src/chatx |
| Psychology coarse/fine labels present in schemas | implemented | src/chatx/schemas |
| Psychology label taxonomy (53 coarse + 100+ fine) represented as data file | implemented | repo |
| Graph relationship types + pattern detection (as per psychology-analysis.md) | implemented | src/chatx/storage |
| Embedded graph backend (Kuzu) available | missing/partial | A1 |
| Cloud synthesis with strict schema + citations | implemented | src/chatx/synthesis |
| HEIC support as core dep + plugin registration | implemented | src/chatx/media |

## 11) Source index (design-relevant markdown)

The following repo markdown files were scanned as primary design inputs:

- `CHANGELOG.md`
- `MASTER_DESIGN_SPEC.md`
- `README.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/README.md`
- `docs/agent-workflows.md`
- `docs/architecture.md`
- `docs/design/adrs/0001-record-architecture-decisions.md`
- `docs/design/adrs/0002-default-chunking-strategy.md`
- `docs/design/adrs/0003-local-transcription-engine.md`
- `docs/design/adrs/0004-acquisition-ux-imessage-icloud-usb.md`
- `docs/design/adrs/0017-transcription-engine-faster-whisper.md`
- `docs/design/adrs/0018-cli-error-model-rfc7807.md`
- `docs/design/adrs/ADR-008-psychology-graph-integration.md`
- `docs/design/adrs/index.md`
- `docs/design/specifications/cloud-enrichment.md`
- `docs/design/specifications/image-enrichment.md`
- `docs/design/specifications/imessage-extractor.md`
- `docs/design/specifications/index.md`
- `docs/interfaces.md`
- `docs/policy/code-of-conduct.md`
- `docs/policy/pr.md`
- `docs/policy/security.md`
- `docs/psychology-analysis.md`
- `docs/reference/changelog.md`
- `docs/reference/workflow/taskmaster-integration.md`
- `lab/03_PRIVACY_AND_POLICY_SHIELD.md`
- `lab/06_DATA_MODELS_AND_CONCEPTUAL_SCHEMAS.md`

## 12) ADR inventory (for reference only)

- `docs/design/adrs/0001-record-architecture-decisions.md`
- `docs/design/adrs/0002-default-chunking-strategy.md`
- `docs/design/adrs/0003-local-transcription-engine.md`
- `docs/design/adrs/0004-acquisition-ux-imessage-icloud-usb.md`
- `docs/design/adrs/0017-transcription-engine-faster-whisper.md`
- `docs/design/adrs/0018-cli-error-model-rfc7807.md`
- `docs/design/adrs/ADR-008-psychology-graph-integration.md`
