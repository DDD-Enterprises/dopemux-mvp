import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from interruption_shield.conport_client import ShieldConPortClient

@pytest.fixture
def client():
    return ShieldConPortClient(workspace_id="test_workspace")

def test_circuit_breaker_initially_closed(client):
    """Test that the circuit breaker is initially closed."""
    assert not client.circuit_open
    assert not client._is_circuit_open()

@patch('interruption_shield.conport_client.datetime')
def test_circuit_breaker_open(mock_datetime, client):
    """Test that the circuit breaker returns True when open and cooldown has not expired."""
    current_time = datetime(2023, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = current_time

    client.circuit_open = True
    client.circuit_open_until = current_time + timedelta(seconds=10)

    assert client._is_circuit_open() is True
    assert client.circuit_open is True

@patch('interruption_shield.conport_client.datetime')
def test_circuit_breaker_half_open(mock_datetime, client):
    """Test that the circuit breaker returns False and resets state when cooldown has expired."""
    current_time = datetime(2023, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = current_time

    client.circuit_open = True
    # Cooldown expired 10 seconds ago
    client.circuit_open_until = current_time - timedelta(seconds=10)

    assert client._is_circuit_open() is False
    assert client.circuit_open is False
    assert client.circuit_open_until is None

def test_circuit_breaker_open_no_until(client):
    """Test behavior when circuit_open is True but circuit_open_until is None."""
    client.circuit_open = True
    client.circuit_open_until = None

    assert client._is_circuit_open() is True
