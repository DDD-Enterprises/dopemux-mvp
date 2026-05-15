# RTE-PKT-11 Research

## Evidence Summary

- OBSERVED: Primary checkout `/Users/hue/code/dopemux-mvp` is on `codex/rte-dr00-normalized-baseline` at `a4214ca5bf431e1b59791661e2b664a6cd24c1da` and has unrelated untracked files. It was not modified.
- OBSERVED: Dedicated worktree `/Users/hue/code/dopemux-mvp/.worktrees/rte-pkt-11-risk-dashboard` is on branch `codex/rte-pkt-11-risk-dashboard` and was initially clean.
- OBSERVED: Required markers exist in the dedicated worktree: `pyproject.toml`, `src/dopemux/cli.py`, `services/repo-truth-extractor/run_extraction_v5.py`, and `services/repo-truth-extractor/tests/`.
- OBSERVED: `AGENTS.md` requires worktree isolation, proof, targeted validation, diff review, and precommit.
- OBSERVED: `PROJECT.md`, `ARCHITECTURE.md`, `SERVICE_CATALOG.md`, and `SYSTEM_RepoTruthExtractor` identify `services/repo-truth-extractor/run_extraction_v5.py` as the strongest RTE runtime authority and generated artifacts as evidence, not source truth.
- OBSERVED: Existing run dashboard writer is `emit_run_dashboard_snapshot()` in `run_extraction_v5.py`, writing `telemetry/RUN_DASHBOARD.json`.
- OBSERVED: Current base lacks `services/repo-truth-extractor/lib/proof_contract.py`; accepted RTE-PKT-10 local worktree contains the proof-contract helper used here without semantic changes.
- OBSERVED: Current branch does not contain prior `out/rte-pkt-01` through `out/rte-pkt-10` proof roots. Local sibling worktrees contain readable prior packet proof roots and were used only as evidence references.

## Risks

- Prior packet proof roots are not all present in this branch, so the runtime dashboard must preserve missing/unknown evidence states.
- A new telemetry artifact must not call provider, batch, live-validation, or external network paths.
- Generated dashboard files must not expose secret-shaped values.
- Generated artifacts must remain lower authority than runtime source.

## Verification Commands

- `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/risk_dashboard.py services/repo-truth-extractor/lib/proof_contract.py`
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest services/repo-truth-extractor/tests -k 'risk and dashboard' -q`
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest services/repo-truth-extractor/tests -k 'proof_contract or artifact_authority' -q`
- `python -m json.tool out/rte-pkt-11-risk-dashboard/RTE-PKT-11_MANIFEST.json >/dev/null`
- `git diff --check`
- `git status --short --branch`
