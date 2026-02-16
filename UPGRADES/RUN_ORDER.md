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

## Redaction & Safety

The runner implements hard redaction for all file content before it leaves the machine (or is saved to trace files).
- **Patterns**: API Keys, Bearer tokens, JWTs, PEM blocks, high-entropy strings.
- **Report**: A `*_REDACTION_REPORT.json` file is generated for each phase, listing redaction hits (without revealing the secret).

## Troubleshooting

- **Missing D1/D2 Outputs**: If M1 fails or is skipped, ensure you have run `docs --doc-partition <ID>` for all required partitions.
- **Exclusion Issues**: The runner uses relative path matching. Ensure your exclusions in the script match the relative structure.
