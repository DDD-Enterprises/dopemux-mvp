"""Tests for bounded socket probes."""

from dopemux.mcp.socket_probe import port_is_free, port_is_listening, probe_port


def test_probe_port_structure():
    # Port 1 is typically free or filtered; just validate structure
    result = probe_port(1)
    assert result["port"] == 1
    assert "free" in result
    assert result["listening"] is (not result["free"])


def test_port_is_free_invalid():
    assert port_is_free(0) is False
    assert port_is_free(99999) is False


def test_port_is_listening_inverse_of_free():
    free = port_is_free(1)
    assert port_is_listening(1) is (not free)
