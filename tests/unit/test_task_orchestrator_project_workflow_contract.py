"""Legacy v1 surfaces hold before looking up unowned data."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI, HTTPException

SERVICE_ROOT=Path(__file__).resolve().parents[2]/"services/task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:sys.path.insert(0,str(SERVICE_ROOT))
from app.api import project_workflow

@pytest.mark.asyncio
@pytest.mark.parametrize("project",["prj_a","foreign","unknown","123"])
async def test_v1_reads_and_transitions_hold_before_disclosure(monkeypatch,project):
    bomb=AsyncMock(side_effect=AssertionError("unowned data lookup"))
    monkeypatch.setattr(project_workflow,"_load_project_records",bomb)
    request=SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    for fn in [project_workflow.get_project_workflow_queue,project_workflow.get_project_workflow_blockers,project_workflow.get_project_workflow_state]:
        with pytest.raises(HTTPException) as err:await fn(project,request)
        assert err.value.status_code==503
    payload=project_workflow.TransitionWorkflowRequest(workflow_id="task",transition="start",actor="claims-are-not-auth")
    with pytest.raises(HTTPException) as err:await project_workflow.execute_transition_project_workflow(project,payload,request)
    assert err.value.status_code==503
    bomb.assert_not_called()

@pytest.mark.asyncio
async def test_service_lifespan_uses_explicit_runtime_without_coordinator(monkeypatch,tmp_path):
    from app import main
    from dopemux.pm.runtime import CanonicalTaskRuntime
    from dopemux.pm.sqlite_store import SQLiteTaskStore
    from tests.unit.pm.test_ownership_store import admission_fixture,seal
    root=tmp_path/"owned";bundle=admission_fixture(root)
    SQLiteTaskStore.bootstrap(root/"tasks.db",root/"checkpoint.jsonl",root/"bundle.json",seal(root/"bundle.json",bundle))
    runtime=CanonicalTaskRuntime(SQLiteTaskStore(root/"tasks.db",root/"checkpoint.jsonl"))
    app=FastAPI(lifespan=main.lifespan)
    app.state.canonical_runtime_factory=lambda:runtime
    bomb=AsyncMock(side_effect=AssertionError("live coordinator startup"))
    monkeypatch.setattr(main,"init_coordinator",bomb)
    async with app.router.lifespan_context(app):assert app.state.task_runtime is runtime
    assert runtime.closed
    bomb.assert_not_called()
