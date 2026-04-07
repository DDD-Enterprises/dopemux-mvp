import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pm_update_work_item_emits_metric(monkeypatch):
    import src.dopemux.pm.writes
    from src.dopemux.pm.writes import CanonicalReceipt
    
    def mock_pm_transition_work_item(*args, **kwargs):
        return CanonicalReceipt(
            canonical_system="leantime",
            canonical_id="test_task_123",
            success=True,
            mirror_receipts=[],
            reconciliation_state="SYNCED"
        )
        
    monkeypatch.setattr("app.api.pm_tools.pm_transition_work_item", mock_pm_transition_work_item)
    
    
    class MockClient:
        def update_task(self, *args, **kwargs):
            pass
        def transition(self, *args, **kwargs):
            pass
            
    app.state.coordinator = type("MockCoordinator", (), {
        "metrics": {},
        "leantime_client": MockClient(),
        "workflow_service": MockClient()
    })()
    
    response = client.post("/api/pm/work-items/test_task_123/transition?idempotency_key=123&expected_version=1&reason=r&new_status=IN_PROGRESS")
    assert response.status_code == 200
    
    metrics = app.state.coordinator.metrics
    assert metrics.get("pm_canonical_writes_total", 0) == 1
    assert metrics.get("pm_canonical_write_failures_total", 0) == 0


def test_pm_update_work_item_mirror_failure_emits_metric(monkeypatch):
    from src.dopemux.pm.writes import CanonicalReceipt, MirrorReceipt
    
    def mock_pm_transition_work_item(*args, **kwargs):
        return CanonicalReceipt(
            canonical_system="leantime",
            canonical_id="test_task_123",
            success=True,
            mirror_receipts=[MirrorReceipt(system="some_mirror", success=False, error="timeout")],
            reconciliation_state="PARTIAL"
        )
        
    monkeypatch.setattr("app.api.pm_tools.pm_transition_work_item", mock_pm_transition_work_item)
    
    class MockClient:
        def update_task(self, *args, **kwargs):
            pass
        def transition(self, *args, **kwargs):
            pass
            
    app.state.coordinator = type("MockCoordinator", (), {
        "metrics": {},
        "leantime_client": MockClient(),
        "workflow_service": MockClient()
    })()
    
    response = client.post("/api/pm/work-items/test_task_123/transition?idempotency_key=123&expected_version=1&reason=r&new_status=IN_PROGRESS")
    assert response.status_code == 200
    
    metrics = app.state.coordinator.metrics
    assert metrics.get("pm_canonical_writes_total", 0) == 1
    assert metrics.get("pm_mirror_failures_total", 0) == 1
    assert metrics.get("pm_reconciliation_pending_total", 0) == 1
    assert metrics.get("pm_degraded_results_total", 0) == 1
