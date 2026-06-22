---
id: to-canon-000-research
title: To Canon 000 Research
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: To Canon 000 Research (reference) for dopemux documentation and developer
  workflows.
---
# TP-TO-CANON-000 Research

## Evidence Summary

- `AGENTS.md` requires repo-changing work to be task-packet scoped, schema validated where possible, minimal, and proof-backed.
- `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md` states that the in-repo FastAPI Task Orchestrator and upstream 13-tool stdio MCP Task Orchestrator are distinct; the latter stores repo-scoped SQLite under the operator local data directory.
- `/tmp/to-all-dbs-20260622T192814Z/README_FOR_5_5PRO.md` states the export was read-only, redacts likely sensitive free-form fields, omits FTS row exports, and warns not to blindly merge multiple `dopemux-mvp-*` DBs.
- `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh --print-resolution` resolved `state_id=dopemux-mvp-2e346e2084bca021` for this worktree.
- `DATABASE_INDEX.csv` has 26 DB rows. `COMBINED_WORK_ITEMS.csv` has 539 rows. `COMBINED_COLDSTART_ITEMS.csv` has 22 rows. `EXPORT_ERRORS.csv` has zero data rows.

## Risks

- The pack is a safe redacted export, not a forensic clone. Raw note-body adjudication remains out of scope.
- Task Orchestrator DB rows are workflow-memory evidence, not governance acceptance by themselves.
- Multiple project and stale DBs are present; title-only or DB-flattening dedupe would corrupt authority boundaries.
- Later packets that implement importer/resolver behavior must preserve provenance and avoid live DB writes.

## Candidate Verification Commands

```bash
shasum -a 256 /private/tmp/to-all-dbs-20260622T192814Z.tar.gz
python - <<'PY'
from pathlib import Path
import pandas as pd
root = Path('/tmp/to-all-dbs-20260622T192814Z')
for name in ['DATABASE_INDEX.csv','COMBINED_WORK_ITEMS.csv','COMBINED_ROOT_OVERVIEW.csv','COMBINED_COLDSTART_ITEMS.csv','EXPORT_ERRORS.csv']:
    df = pd.read_csv(root / name)
    print(name, df.shape, list(df.columns))
PY
scripts/mcp-wrappers/task-orchestrator-current-stdio.sh --print-resolution
python -m json.tool audit_inputs/task-orchestrator-canon/to-all-dbs-20260622T192814Z/ADJUDICATION_MANIFEST.json
python -m jsonschema -i task-packets/TP-TO-CANON-000.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```
