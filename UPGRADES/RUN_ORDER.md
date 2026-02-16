# Upgrade Pipeline Run Order

This document defines the strict execution order for the Dopemux upgrade extraction pipeline.

## 1. Environment Setup

Ensure you are in the repository root.
The extraction runner is located at `UPGRADES/run_extraction.py`.

## 2. Priority Control Plane (Phase A + Phase H)

Run this first to capture the "truth" of the repository and home configuration.

```bash
python UPGRADES/run_extraction.py priority --dry-run
```

- **Phase A (Repo Control Plane)**: Scans repository configuration files (`config/`, `.github/`, `.claude/`, etc.) to understand the intended architecture.
- **Phase H (Home Control Plane)**: Scans local user configuration (`~/.dopemux`, `~/.config/dopemux`, `~/.config/taskx`, etc.) to understand local overrides and enablement.
  - **Safety Note**: All home configuration files are subject to strict redaction rules. Secrets (API keys, tokens, passwords) are replaced with `REDACTED_SECRET` before processing.
  - **Exclusions**: Caches, logs, and temporary files are automatically excluded.

## 3. Docs Pipeline (Phase D)

Run this after the Priority Control Plane to extract knowledge from documentation.

The docs pipeline follows a strict sequence: **D0 → D1/D2 (Partitioned) → D3 → M1 → QA → CL**.

### Step 3.1: Inventory & Partitioning (D0)

First, generate the document inventory and partition plan.

```bash
python UPGRADES/run_extraction.py docs --dry-run
```

This produces `DOC_INVENTORY.json` and `PARTITION_PLAN.json`.

### Step 3.2: Deep Extraction (D1/D2)

Run deep extraction on specific partitions defined in `PARTITION_PLAN.json`.

```bash
# Example: Run partition P1
python UPGRADES/run_extraction.py docs --doc-partition P1 --dry-run
```

- **D1**: Claims & Boundaries extraction.
- **D2**: Deep interface & workflow extraction.

### Step 3.3: Synthesis (M1, QA, CL)

Once partitions are processed, run the synthesis phases.

```bash
python UPGRADES/run_extraction.py docs --dry-run
```

(The runner will automatically detect if D1/D2 outputs exist and proceed to M1).

- **M1**: Merge partition outputs.
- **QA**: Quality Assurance check.
- **CL**: Cluster analysis.

## 4. Arbitration (Phase R) & Synthesis (Phase S)

These phases are run after extraction is complete.

- **Phase R**: GPT-5.2 arbitration to resolve conflicts between Repo, Home, and Docs.
- **Phase S**: Opus synthesis to generate the final upgrade plan.

## 5. Canonical v3 Execution Order

When running the v3 extraction runner (`UPGRADES/run_extraction_v3.py`), follow this exact sequence for deterministic outputs:

1. `python UPGRADES/run_extraction_v3.py --phase A --resume`
2. `python UPGRADES/run_extraction_v3.py --phase H --resume`
3. `python UPGRADES/run_extraction_v3.py --phase M --resume`
4. `python UPGRADES/run_extraction_v3.py --phase D --resume`
5. `python UPGRADES/run_extraction_v3.py --phase E --resume`
6. `python UPGRADES/run_extraction_v3.py --phase C --resume`
7. For the arbitration gate:
   - Base gate: `python UPGRADES/run_extraction_v3.py --phase R --dry-run --r-profile base`
   - Full gate: `python UPGRADES/run_extraction_v3.py --phase R --dry-run --r-profile full`

### Default Phase Order (when running `--phase ALL`)
1. `A` – Repo Control Plane
2. `H` – Home Control Plane
3. `M` – Runtime Exports Plane
4. `D` – Docs Pipeline
5. `E` – Execution Plane
6. `C` – Code Surfaces
7. `W` – Workflow Plane
8. `B` – Boundary Plane
9. `G` – Governance Plane
10. `Q` – Pipeline Doctor
11. `R` – Arbitration
12. `X` – Feature Index
13. `T` – Task Packets
14. `Z` – Handoff Freeze

## 6. Guardrails

- Prompt files must match `UPGRADES/PROMPT_{phase}{step}_*.md` and no duplicate step IDs are allowed (duplicates fail closed).
- Phase R supports two deterministic profiles:
  - `--r-profile base` requires A/H/D/C norm artifacts.
  - `--r-profile full` requires A/H/D/C norm artifacts plus M runtime-export norm artifacts.
- Phase R fails closed unless required norm directories contain at least one JSON:
  - `extraction/runs/<run_id>/A_repo_control_plane/norm`
  - `extraction/runs/<run_id>/H_home_control_plane/norm`
  - `extraction/runs/<run_id>/M_runtime_exports/norm` (full profile only)
  - `extraction/runs/<run_id>/D_docs_pipeline/norm`
  - `extraction/runs/<run_id>/C_code_surfaces/norm`
- Phase R only ingests norm artifacts—no raw rescans or unsanctioned directories.
- Every phase writes `qa/PHASE_<phase>_MANIFEST.json` with prompts executed, inputs, outputs, caps, redaction policy, and resume metadata.
- When troubleshooting empty `norm/` buckets, check:
  - Raw outputs in `extraction/runs/<run_id>/<phase>/raw` to see if normalization steps failed.
  - Presence of merge/normalize prompts (`A9`, `H9`, `D4`, `C9`) and runtime prompts (`M0..M6`) in `UPGRADES/`.
