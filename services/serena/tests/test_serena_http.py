import pytest
from fastapi.testclient import TestClient
from services.serena.v2.http_server import app

client = TestClient(app)

def test_read_file_rate_limit():
    response = client.post("/read_file", json={"path": "test.py"})
    assert response.status_code == 200
    # More tests for endpoints, limits