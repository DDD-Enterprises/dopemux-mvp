import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pm_metrics_exposed():
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics_text = response.text
    
    assert "pm_canonical_writes_total" in metrics_text
    assert "pm_canonical_write_failures_total" in metrics_text
    assert "pm_mirror_failures_total" in metrics_text
    assert "pm_reconciliation_pending_total" in metrics_text
    assert "pm_reconciliation_completed_total" in metrics_text
    assert "pm_reconciliation_failed_total" in metrics_text
    assert "pm_degraded_results_total" in metrics_text
