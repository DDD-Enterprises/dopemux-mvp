# RTE Pre-Run Hygiene Stage 1 Challenge

Date: 2026-04-23

## Inputs Challenged

- Preserve canonical runtime/config/tests/truth docs and existing evidence trees.
- Treat `AGENTS.md` local memory refresh as unrelated worktree drift to isolate rather than discard.
- Allow only transient-noise cleanup classes for physical mutation.
- Treat heavy hidden local trees as exclusion-only candidates unless proven irrelevant.

## PAL Pressure Test Record

- `analyze:gpt-4.1`
  - completed with a provider quota error on the second continuation call, but returned a full analysis payload before failure.
  - main pressure:
    - broad cleanup under `proof/`, `reports/`, `extraction/`, or hidden control-plane directories risks deleting analyzable drift or launch evidence.
- `thinkdeep:gemini-3-pro-preview`
  - requested model unavailable.
- `thinkdeep:gemini-2.5-pro`
  - fallback used after provider rejection.
  - main pressure:
    - preservation-first is the only safe posture.
    - ambiguous hidden trees may be excluded from first-pass input, but should not be deleted or moved in hygiene.
- `challenge`
  - produced a critical reassessment prompt, reinforcing explicit gap reporting instead of silent substitution.

## Challenge Outcome

The boundary model held.

Qualified adjustments:

- Model/tool availability gaps must be stated explicitly in downstream artifacts.
- Exclusion decisions for `.claude/`, `.dopemux/`, and `.conport/` are run-boundary controls only, not repository cleanup approvals.
- Any later cleanup command must explicitly prune virtualenvs and `.git` to avoid avoidable churn.
