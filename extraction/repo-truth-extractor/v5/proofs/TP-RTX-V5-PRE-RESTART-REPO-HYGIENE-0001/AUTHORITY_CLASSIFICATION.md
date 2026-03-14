---
title: "Authority Classification — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "Five-tier authority classification scheme for extraction-facing document surfaces."
tags: [extraction, authority, classification]
---

# Authority Classification

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001  
**Implementation**: `config/extraction_hygiene/authority_tiers.yaml`, `services/repo-truth-extractor/extraction_hygiene.py`

## Overview

Five authority tiers distinguish canonical implementation truth from summaries, roadmaps, audits, and machine-generated artifacts. Tier 1 is highest authority; Tier 5 is lowest.

## Tier Definitions

| Tier | Name | Description | Extraction Weight |
|------|------|-------------|-------------------|
| 1 | **canonical** | Design specs, ADRs, RFCs, service contracts, pyproject.toml, compose files | Highest — authoritative source of truth |
| 2 | **reference** | Implementation guides, API docs, service READMEs, tutorials, how-to | High — implementation reference |
| 3 | **status_audit** | Audit reports, status summaries, progress docs, AUDIT_* files | Medium — current state, not design truth |
| 4 | **roadmap_speculative** | Roadmaps, planned features, UPGRADES/, archive/ | Low — aspirational, may not be implemented |
| 5 | **generated** | Extraction run outputs, proof bundles, CI artifacts, vendored code, node_modules | None — machine-generated noise |

## Live Classification Summary (from scan)

| Tier | File Count |
|------|-----------|
| canonical | 15,328 |
| reference | 1,967 |
| status_audit | 616 |
| roadmap_speculative | 622 |
| generated | 157,577 |
| **Total** | **176,110** |

The 157,577 `generated` files are dominated by extraction run outputs (v3/v4 runs) and are already excluded from extraction by policy.

## Classification Rules

### Canonical paths
- `docs/90-adr/` — Architecture Decision Records
- `config/` — configuration files
- Root-level `README.md`, `pyproject.toml`, `compose.yml`
- `src/dopemux/` source files

### Reference paths
- `docs/01-tutorials/`, `docs/02-how-to/`, `docs/03-reference/`, `docs/04-explanation/`
- `docs/` (catch-all for other docs/ paths)
- `services/*/README.md`, `CHANGELOG.md`

### Status Audit paths
- `reports/` — generated reports/analysis
- `docs/05-audit-reports/`
- `review_artifacts/`, `repo-truth-pack/`
- Files matching `AUDIT_*.md` and `AUDIT_*.json`

### Roadmap/Speculative paths
- `UPGRADES/`, `docs/archive/`, `task-packets/`, `contracts/`, `docs/91-rfc/`

### Generated (excluded) paths
- `extraction/repo-truth-extractor/v3/runs/`, `v4/runs/`, `v5/proofs/`
- `vendor/`, `node_modules/`, `.venv/`, `__pycache__/`, `dist/`, `build/`
- `tmp/`, `out/`, `proof/`, `htmlcov/`, `SYSTEM_ARCHIVE/`
- Anything containing `node_modules`, `vendor/`, `.venv`, `__pycache__`

## Usage

```bash
# Classify a single path
python3 -c "
from pathlib import Path
import sys; sys.path.insert(0, 'services/repo-truth-extractor')
from extraction_hygiene import classify_authority
print(classify_authority('docs/90-adr/adr-207.md'))
"

# Get full authority summary from scan
python services/repo-truth-extractor/extraction_hygiene.py scan --json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['authority_summary'])"
```
