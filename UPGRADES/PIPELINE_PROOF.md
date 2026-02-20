# Pipeline Proof Pack Runbook

## 1. Canonical run order
1. Identify the active run with `run_id="$(cat extraction/latest_run_id.txt)"` and inspect tree depth 2 to confirm each phase directory exists.
1. Resume the data pipeline in deterministic order: Phase A → H → D → C (each with `py UPGRADES/run_extraction_v3.py --phase <PHASE> --resume`).
1. Once norms are available for A/H/D/C, run Phase R with `--dry-run` to prove the gate runs without missing-input errors.
1. (Optional) Continue through R/X/T/Z after Phase R succeeds to complete the full master extraction sweep.

## 2. Artifact presence checks
- Verify the run-level magic index exists and is populated before Phase R:
  ```
  run_id="$(cat extraction/latest_run_id.txt)"
  jq '.file_count, .files[0:5][]?.relative_path' "extraction/runs/$run_id/00_inputs/MAGIC_SURFACE_INDEX.json"
  ```
- Confirm partition ordering keeps Tier 0 first:
  ```
  run_id="$(cat extraction/latest_run_id.txt)"
  jq '.partitions[].files[].priority_tier' "extraction/runs/$run_id/A_repo_control_plane/inputs/PARTITION_MANIFEST.json" | head -40
  ```
- Prove deterministic dry-run ordering by running the same phase twice and diffing partition manifests:
  ```
  py UPGRADES/run_extraction_v3.py --phase A --dry-run --resume
  cp "extraction/runs/$run_id/A_repo_control_plane/inputs/PARTITION_MANIFEST.json" /tmp/A_PARTITION_MANIFEST_1.json
  py UPGRADES/run_extraction_v3.py --phase A --dry-run --resume
  diff -u /tmp/A_PARTITION_MANIFEST_1.json "extraction/runs/$run_id/A_repo_control_plane/inputs/PARTITION_MANIFEST.json"
  ```
- Ensure each norm directory contains at least one JSON artifact with:
  ```
  run_id="$(cat extraction/latest_run_id.txt)"
  for p in A_repo_control_plane H_home_control_plane D_docs_pipeline C_code_surfaces; do
    echo "== $p norm =="
    ls -1 "extraction/runs/$run_id/$p/norm"/*.json 2>/dev/null | wc -l
  done
  ```
- Capture the actual filenames with `ls -la` if counts are zero to confirm the normalization step produced files.
- Phase R now validates `R_REQUIRED_ARTIFACT_GROUPS` in `UPGRADES/run_extraction_v3.py`, so you can rely on these required globs to exist before R starts. The current enforcement list includes:
  - A: `REPO_INSTRUCTION_SURFACE.json`, `REPO_ROUTER_SURFACE.json`, `REPO_LITELLM_SURFACE.json`, and related repo-level surfaces.
  - H: `HOME_MCP_SURFACE.json`, `HOME_LITELLM_SURFACE.json`, `HOME_PROFILES_SURFACE.json`, etc.
  - D: `DOC_INDEX.json`, `DOC_TOPIC_CLUSTERS.json`, `DOC_SUPERSESSION.json`, plus duplicate/recency reports.
  - C: service/event surface descriptors like `SERVICE_ENTRYPOINTS.json`, `EVENTBUS_SURFACE.json`, and various risk surface files.
- If Phase R raises `missing norm artifacts`, the error now lists the missing glob(es) plus the norm directory that was checked, so copy that output into the proof pack alongside the dry-run log.

## 3. Troubleshooting matrix for empty `norm/`
| Symptom | Inspection | Why this happens | Mitigation |
| --- | --- | --- | --- |
| `norm/` directory exists but `*.json` count is 0 | `find extraction/runs/$run_id/<phase>/raw -maxdepth 1 -type f` and peek at the tail of `UPGRADES/PROMPT_<phase>*` to confirm the merge/normalize step prompt is present (A9, H9, D4, C9). | The phase never produced normalized JSON because its last prompt failed, was skipped, or the merge prompt is missing/renamed. | Re-add or fix the merge prompt (A9/H9/D4/C9) so that normalization runs after the last partition completes. Rerun `--phase <phase> --resume` to recreate `norm/`.
| `norm/` contains only `.md` files | Run `ls extraction/runs/$run_id/<phase>/norm` and ensure that the merge prompt writes JSON artifacts; double-check that the prompt output parser includes the JSON filename in its `normalize_step` call. | The normalization step might be using a text-only prompt or the parser stripped JSON. | Confirm the prompt and `normalize_step` scripts still produce `.json`. Add guard logs if necessary.
| `norm/` is missing entirely | Check `extraction/runs/$run_id/RUN_MANIFEST.json` for errors and rerun the phase with `--resume`; also confirm the previous run did not delete the directory. | Phase stopped before normalization (e.g., LLM failure) or cleanup removed the dir. | Recreate the directory or delete the run and rerun from scratch; ensure `--resume` is used after transient LLM errors.

## 4. Proof pack checklist (paste into PR description)
- [ ] A/H/D/C produced non-empty `norm/` JSONs for run_id `__________`
- [ ] Phase R dry-run proceeds past gating without `missing norm artifacts`
- [ ] `UPGRADES/PIPELINE_PROOF.md` is added or updated
- [ ] No duplicate prompt IDs per phase (verify via `rg PROMPT_<phase> UPGRADES/`)
- [ ] Home scan remained in safe mode (`--home-scan-mode=safe` is the default argument)
- [ ] `MAGIC_SURFACE_INDEX.json` exists and lists Tier 0 files for the run

Collect `stdout`/`stderr` from each command and attach a QA summary that lists the commands run, the counts from the artifact check, and the Phase R outcome. Include the folder name and the missing glob list if the gate still fails.
