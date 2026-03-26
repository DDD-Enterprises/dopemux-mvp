---
title: "Changeset Map — TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001"
type: reference
status: active
prelude: "All files changed by this packet with purpose and risk level."
tags: [extraction, hygiene, changeset]
---

# Changeset Map

**Packet**: TP-RTX-V5-PRE-RESTART-REPO-HYGIENE-0001  
**Commits**:
- `f4e65251a` — `test(v5): add failing tests for repo hygiene scan, authority classification, and version-path checks`
- `06b31eb60` — `feat(v5): add pre-restart hygiene scan, safe quarantine mode, and extraction noise policy`

## Files Added

| File | Purpose | Risk |
|------|---------|------|
| `services/repo-truth-extractor/extraction_hygiene.py` | Main hygiene CLI script: scan + apply modes, all classification logic | None — new file, no existing behavior changed |
| `config/extraction_hygiene/hygiene_policy.yaml` | Machine-readable extraction policy (include/exclude/quarantine/version wiring) | None — new config, not read by extractor |
| `config/extraction_hygiene/authority_tiers.yaml` | 5-tier authority classification with path patterns | None — new config, not read by extractor |
| `services/repo-truth-extractor/tests/test_hygiene_noise_detection.py` | T1: Noise-path detection tests | None — test file |
| `services/repo-truth-extractor/tests/test_hygiene_dry_run_safety.py` | T2: Dry-run no-mutation tests | None — test file |
| `services/repo-truth-extractor/tests/test_hygiene_quarantine.py` | T3: Apply-mode quarantine tests | None — test file |
| `services/repo-truth-extractor/tests/test_hygiene_authority.py` | T4: Authority classification tests | None — test file |
| `services/repo-truth-extractor/tests/test_hygiene_version_path.py` | T5: Version/path mismatch tests | None — test file |
| `services/repo-truth-extractor/tests/test_hygiene_resume_state.py` | T6: Resume-state hazard tests | None — test file |
| `services/repo-truth-extractor/tests/test_hygiene_nondestructive.py` | T7: Non-destructive behavior tests | None — test file |

## Files Modified

| File | Change | Risk |
|------|--------|------|
| `.gitignore` | Added `extraction/repo-truth-extractor/quarantine/` | None — additive only |

## Files NOT Modified

The following files were inspected but deliberately left unchanged:

| File | Reason Not Changed |
|------|--------------------|
| `services/repo-truth-extractor/run_extraction_v5.py` | TP requires no changes to extractor semantics; V3_EXTRACTION_ROOT mismatch handled by documentation only |
| `pytest.ini` | Service-level tests run via explicit path, no change needed |
| Any canonical source doc | Non-destructive requirement — no source content mutated |

## Key Design Choices in `extraction_hygiene.py`

| Choice | Rationale |
|--------|-----------|
| Single file, no new packages | Keeps tool self-contained and easy to run without install |
| YAML config in `config/extraction_hygiene/` | Consistent with existing `config/repo_hygiene/` pattern |
| Apply mode moves (not deletes) to quarantine/ | Non-destructive; reversible; manifest-tracked |
| Grep-friendly log tags | All log lines prefixed with `HYGIENE_*` or `VERSION_*` for easy grepping |
| `--json` flag on scan | Machine-parsable output for CI integration |
| argparse subcommands (`scan`/`apply`) | Discoverable, extensible CLI |
