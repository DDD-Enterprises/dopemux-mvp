"""Every host port published by compose.yml must bind loopback only."""
from pathlib import Path

import pytest
import yaml

COMPOSE = Path(__file__).resolve().parents[2] / "compose.yml"
LOOPBACK = "127.0.0.1"


def _entries():
    data = yaml.safe_load(COMPOSE.read_text())
    for name, svc in (data.get("services") or {}).items():
        for entry in svc.get("ports") or []:
            yield name, entry


def test_compose_has_published_ports():
    assert list(_entries()), "no ports found in compose.yml; test would be vacuous"


@pytest.mark.parametrize(
    "service,entry", list(_entries()), ids=lambda v: v if isinstance(v, str) else repr(v)
)
def test_published_port_binds_loopback(service, entry):
    if isinstance(entry, dict):
        assert entry.get("host_ip") == LOOPBACK, (
            f"service '{service}' long-syntax port {entry!r} must set host_ip: {LOOPBACK}"
        )
    else:
        assert str(entry).startswith(f"{LOOPBACK}:"), (
            f"service '{service}' port entry {entry!r} must start with '{LOOPBACK}:'"
        )
