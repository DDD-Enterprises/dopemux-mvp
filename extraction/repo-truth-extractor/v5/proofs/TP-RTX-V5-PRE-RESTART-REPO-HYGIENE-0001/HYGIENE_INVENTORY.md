---
title: "Hygiene Inventory — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "Inventory of extraction-relevant repo paths with classification and recommended handling."
tags: [extraction, hygiene, inventory]
---

# Hygiene Inventory

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001  
**Generated**: 2026-03-14  
**Scanner**: `services/repo-truth-extractor/extraction_hygiene.py`

## Summary from Live Scan

| Metric | Count |
|--------|-------|
| Noise paths flagged | 57 |
| Resume-state issues (stale FAILED files) | 7,373 |
| Version/path issues | 1 |
| Warnings total | 7,431 |
| Errors | 0 |

## Extraction-Relevant Surface Inventory

| Path | Type | Extraction Desirability | Authority | Recommended Handling |
|------|------|------------------------|-----------|---------------------|
| `src/dopemux/` | source root | HIGH | canonical | Always include |
| `services/` | service implementations | HIGH | canonical/reference | Include (service READMEs = reference) |
| `docker/` | compose/container config | HIGH | canonical | Include |
| `config/` | configuration files | HIGH | canonical | Include |
| `scripts/` | operational scripts | MEDIUM | reference | Include |
| `docs/01-tutorials/` | learning guides | MEDIUM | reference | Include |
| `docs/02-how-to/` | problem-solving guides | MEDIUM | reference | Include |
| `docs/03-reference/` | technical specs | HIGH | reference | Include |
| `docs/04-explanation/` | architecture docs | HIGH | reference | Include |
| `docs/90-adr/` | architectural decisions | HIGH | canonical | Include |
| `docs/91-rfc/` | requests for comment | MEDIUM | roadmap_speculative | Include (flagged speculative) |
| `docs/05-audit-reports/` | audit reports | LOW | status_audit | Include (flagged status_audit) |
| `docs/archive/` | historical docs | LOW | roadmap_speculative | Include (flagged archived/speculative) |
| `reports/` | generated reports/analysis | LOW | status_audit | Include (flagged status_audit) |
| `AUDIT_*.md`, `AUDIT_*.json` (root) | audit artifacts | LOW | status_audit | Include (flagged) |
| `extraction/repo-truth-extractor/v3/runs/` | extraction run outputs | NONE | generated | EXCLUDE — run artifacts |
| `extraction/repo-truth-extractor/v4/runs/` | extraction run outputs | NONE | generated | EXCLUDE — run artifacts |
| `extraction/repo-truth-extractor/v5/proofs/` | proof bundles | NONE | generated | EXCLUDE — generated |
| `extraction/repo-truth-extractor/quarantine/` | quarantined artifacts | NONE | generated | EXCLUDE — quarantine |
| `vendor/` | vendored dependencies | NONE | generated | EXCLUDE — vendor |
| `node_modules/` | npm packages | NONE | generated | EXCLUDE — vendored |
| `.venv/` | Python virtualenv | NONE | generated | EXCLUDE — virtualenv |
| `__pycache__/` | Python bytecache | NONE | generated | EXCLUDE — build cache |
| `dist/`, `build/` | build artifacts | NONE | generated | EXCLUDE — build artifacts |
| `htmlcov/` | coverage HTML | NONE | generated | EXCLUDE — generated |
| `tmp/` | temp files | NONE | generated | EXCLUDE — transient |
| `.DS_Store` | macOS metadata | NONE | os_artifact | EXCLUDE — OS noise |
| `*.pyc` | Python bytecode | NONE | generated | EXCLUDE — compiled |

## Live Noise Paths Detected (57)

### OS Artifacts (`.DS_Store`)
Found in: `.`, `proof/`, `docs/`, `repo-truth-pack/`, `extraction/`, `services/`, `reports/`, `reports/_audit_out/`, and more.  
**Status**: Harmless to extraction (excluded by glob). No action required unless they proliferate.

### Vendored Dependencies
- `vendor/` — top-level vendor directory (contains `dopetask/`)
- **Status**: Excluded by policy. No action required.

## Run-State Size
- **v3 runs**: ~204 run directories (~946 MB)
- **v4 runs**: ~14 run directories (~151 MB)
- **v5 proofs**: 1 existing proof bundle (TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001)

All run output directories are excluded from extraction by hardcoded globs and hygiene policy.
