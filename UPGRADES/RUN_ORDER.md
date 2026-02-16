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
3. `python UPGRADES/run_extraction_v3.py --phase D --resume`
4. `python UPGRADES/run_extraction_v3.py --phase C --resume`
5. Once norms exist for A/H/D/C, run `python UPGRADES/run_extraction_v3.py --phase R --dry-run` to verify the gate passes before moving downstream.

### Default Phase Order (when running `--phase ALL`)
1. `A` – Repo Control Plane
2. `H` – Home Control Plane
3. `D` – Docs Pipeline
4. `C` – Code Surfaces
5. `E` – Execution Plane
6. `W` – Workflow Plane
7. `B` – Boundary Plane
8. `G` – Governance Plane
9. `Q` – Pipeline Doctor
10. `R` – Arbitration
11. `X` – Feature Index
12. `T` – Task Packets
13. `Z` – Handoff Freeze

## 6. Guardrails

- Prompt files must match `UPGRADES/PROMPT_{phase}{step}_*.md` and no duplicate step IDs are allowed (duplicates fail closed).
- Phase R fails closed unless the following norm directories contain at least one JSON:
  - `extraction/runs/<run_id>/A_repo_control_plane/norm`
  - `extraction/runs/<run_id>/H_home_control_plane/norm`
  - `extraction/runs/<run_id>/D_docs_pipeline/norm`
  - `extraction/runs/<run_id>/C_code_surfaces/norm`
- Phase R only ingests norm artifacts—no raw rescans or unsanctioned directories.
- When troubleshooting empty `norm/` buckets, check:
  - Raw outputs in `extraction/runs/<run_id>/<phase>/raw` to see if normalization steps failed.
  - Presence of merge/normalize prompts (`A9`, `H9`, `D4`, `C9`) in `UPGRADES/` to ensure the final steps exist.
