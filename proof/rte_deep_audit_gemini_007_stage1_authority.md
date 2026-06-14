# RTE Deep Audit Stage 1: Authority Mapping

## Authority Hierarchy
1.  **Execution Authority (Canonical):** `services/repo-truth-extractor/run_extraction_v5.py`
    - Terminal runtime for all v5 phases.
    - Implements integrated Stage 0 prescan.
    - Enforces `DPMX_LIVE_OK_ENV` safety.
2.  **Contract Authority (Compatibility):** `services/repo-truth-extractor/run_extraction_v4.py`
    - Enforces v4 prompt/artifact schemas.
    - **Crucial Discovery:** It is a wrapper that delegates actual phase execution to `v5`.
3.  **Gate Authority (Safety):** `services/repo-truth-extractor/validate_pre_live_gate_v25.py`
    - Mandatory gate for v5 presets.
    - Validates prompt integrity, provider readiness, and critical tests.
4.  **Operator Authority (CLI):** `dopemux rte` command group in `src/dopemux/cli.py`.
    - Canonical operator entrypoint.
    - Forwards parameters to the v5 runner via subprocess.
    - Legacy aliases: `dopemux upgrades` (direct alias), `dopemux truth` (deprecated redirect).

## Legacy & Drift Boundaries
- **Shadow Authority:** `run_extraction_v3.py` remains in the service directory. It is a standalone legacy engine that bypasses v5 safety gates.
- **Surface Drift:** `dopemux extractor run` is explicitly disabled with a safety notice, yet remains in the command tree.
- **Version Coupling:** The 'v5' suffix is hard-coded in CLI wiring, output roots (`extraction/repo-truth-extractor/v5/`), and configuration. This creates friction for future versioning.

## Execution Path
`dopemux rte run` → `extractor_run()` → `_run_extractor_runner()` → `subprocess.run(run_extraction_v5.py)`.

## Verdict
Authority is **Execution-Canonical in v5** but **Contract-Fragmented** between v4 and v5. Hygiene risk is HIGH due to legacy script pollution in the primary service folder.
