# Extractor Recovery Supervisor Plan

## Objective
Finish the `v5 repo-truth-extractor` recovery branch using ONLY the designated recovery worktree (`/Users/hue/.codex/worktrees/extractor-prod/dopemux-mvp`). Preserve the already-implemented production-readiness surface, validate it cleanly, include recovery provenance artifacts, and package the branch into the final PR.

## Hard Rules
1. Use ONLY `/Users/hue/.codex/worktrees/extractor-prod/dopemux-mvp`
2. DO NOT touch `/Users/hue/code/dopemux-mvp`
3. DO NOT restart or reimplement the workstream from scratch
4. DO NOT rebase again
5. DO NOT pop or mutate `stash@{0}` unless explicitly told later
6. DO NOT make live provider calls or PAL live calls unless strictly necessary; OpenRouter models are permitted if needed.
7. Treat current runtime code and passing tests as authority.
8. Fail closed if validation fails.
9. Execute packets in exact order, pausing for confirmation. If a step freezes, restart the step.
10. Emit `proof/<TP_ID>/proof.json` upon completion of each packet.

## Execution Model
The execution will be processed sequentially via four Task Packets (TPs). After each TP completes successfully, execution will pause and await operator confirmation before proceeding to the next TP.

### TP-EXTRACTOR-RECOVERY-001
- **Objective:** Normalize the current recovery worktree into one coherent and intentional diff.
- **Actions:** Run `git status/diff` checks, inspect scope, intentionally stage rebase-fix follow-ups and required provenance artifacts. Emit proof JSON.

### TP-EXTRACTOR-RECOVERY-002
- **Objective:** Verify and preserve the current contract/runtime truth exactly.
- **Actions:** Inspect staged files (`cli.py`, `batch_clients.py`, `batch_retriever.py`, `run_extraction_v5.py`, `model_map.yaml`, etc.) to ensure proper live-guard behavior and configuration are maintained. Emit proof JSON.

### TP-EXTRACTOR-RECOVERY-003
- **Objective:** Run the required proof set exactly and fail closed on any failure.
- **Actions:** Execute multiple `pytest` test commands and specific CLI validation commands without live provider calls. Make surgical fixes to tests/code if required. Emit proof JSON.

### TP-EXTRACTOR-RECOVERY-004
- **Objective:** Curate the validated recovery branch into exactly two final commits and open the draft PR.
- **Actions:** Stage files logically to produce two exact commits (`feat:` and `docs:`). Push branch and create a draft PR via `gh pr create` with the required structured PR body. Emit proof JSON.