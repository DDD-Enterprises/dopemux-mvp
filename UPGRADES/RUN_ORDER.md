# Upgrade Pipeline Run Order (Canonical)

This run order is authoritative for the v3 extraction runner:
`UPGRADES/run_extraction_v3.py`

## 1. Initialize run scaffold

```bash
make x-run-init RUN_ID=<YYYYMMDD_HHMM_slug>
```

## 2. Execute full pipeline

```bash
python UPGRADES/run_extraction_v3.py --phase ALL
```

Default phase order:
1. `A` repo control plane
2. `H` home control plane
3. `D` docs pipeline
4. `C` code surfaces
5. `E` execution plane
6. `W` workflow plane
7. `B` boundary plane
8. `G` governance plane
9. `Q` pipeline doctor
10. `R` arbitration
11. `X` feature index
12. `T` task packets
13. `Z` handoff freeze

## 3. Run a single phase

```bash
python UPGRADES/run_extraction_v3.py --phase R
```

## 4. Dry-run mode

```bash
python UPGRADES/run_extraction_v3.py --phase A --dry-run
```

## Guardrails

- Prompt files must match: `UPGRADES/PROMPT_{phase}{step}_*.md`
- Duplicate step IDs fail closed.
- Phase R fails closed unless required normalized artifacts exist in:
  - `extraction/runs/<run_id>/A_repo_control_plane/norm`
  - `extraction/runs/<run_id>/H_home_control_plane/norm`
  - `extraction/runs/<run_id>/D_docs_pipeline/norm`
  - `extraction/runs/<run_id>/C_code_surfaces/norm`
- Phase R inputs are norm-only (no repo rescan).
