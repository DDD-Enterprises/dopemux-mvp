from pathlib import Path
import json

def test_payload():
    p=Path("docs/ops/load-plans/task_orchestrator_epics-LTAIP-H0.json")
    d=json.loads(p.read_text())
    assert len(d["epics"])==12
    keys=[d["root_epic"]["request"]["idempotency_key"]]+[x["request"]["idempotency_key"] for x in d["epics"]]
    assert len(keys)==len(set(keys))
    assert d["epics"][0]["load_status"]=="READY"
