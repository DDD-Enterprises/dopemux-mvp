# LTAIP Task Orchestrator Load Plan

## Truth posture

- **OBSERVED:** The in-repo runtime exposes `POST /api/workflow/epics` using `CreateEpicRequest`.
- **OBSERVED:** That request contains no dependency or delete field.
- **OBSERVED:** Historical external v3 tools such as `create_work_tree` and `manage_items` are not source-verifiable in this repo.
- **PROPOSED:** Load one series root and twelve packet epics through REST; preserve dependencies in packet JSON, tags, and the DAG artifact.
- **UNKNOWN:** Whether the live service is healthy and backed by the expected bridge store at load time.

## Files

- REST payload: `docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json`
- Content-addressed task tree: `docs/ops/load-plans/task_orchestrator_task_tree-LTAIP-H0.json`
- Canonical plan: `docs/ops/load-plans/load_plan-LTAIP-H0.json`
- External v3 advisory: `docs/ops/load-plans/task_orchestrator_v3_advisory-LTAIP-H0.json`
- Loader: `scripts/leantime-ai-parity/load_task_orchestrator.py`

## Preflight

```bash
set -euo pipefail

test -f .dopetaskroot
test -f docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json
python -m json.tool docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json >/dev/null
python -m pytest -q tests/prototypes/leantime-ai-parity/test_task_orchestrator_load_payload.py
curl -fsS "${TASK_ORCHESTRATOR_URL:-http://localhost:8000}/health" | python -m json.tool
```

## Mandatory dry run

```bash
python scripts/leantime-ai-parity/load_task_orchestrator.py \
  --payload docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json \
  --dry-run
```

Expected: 13 entries, one root and twelve packet epics. No network write occurs.

## Apply gate

Applying is an explicit runtime write. Execute only after operator approval:

```bash
python scripts/leantime-ai-parity/load_task_orchestrator.py \
  --payload docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json \
  --apply \
  --approve LTAIP_TASK_ORCHESTRATOR_LOAD \
  --receipts reports/leantime-ai-parity/task-orchestrator-load-receipts.json
```

## Verification

```bash
curl -fsS "${TASK_ORCHESTRATOR_URL:-http://localhost:8000}/api/workflow/epics?tag=program:LTAIP&limit=100" \
  | python -m json.tool
python -m json.tool reports/leantime-ai-parity/task-orchestrator-load-receipts.json >/dev/null
```

## Dependency semantics

The REST epic model does not carry dependencies. Do not infer live dependency enforcement. The authoritative dependency sources are:

1. packet `depends_on` arrays;
2. `load_plan-LTAIP-H0.json` BLOCKS DAG;
3. `task_orchestrator_task_tree-LTAIP-H0.json`;
4. dependency tags on each epic.

## Partial failure

No delete endpoint is assumed. On partial failure the loader stops, writes receipts, and refuses automatic rollback. Reconcile idempotency keys and existing epic IDs before retrying.

## External v3

Do not call `create_work_tree`, `manage_items`, or `manage_dependencies` until their live schemas and source are inspected. Their plan is advisory and classified `TX`.
