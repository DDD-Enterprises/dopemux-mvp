from pathlib import Path


def test_ai_startup_preflights_external_network_before_full_fleet() -> None:
    """Cloud bootstrap must create the external Compose network before ensure."""
    script = Path("scripts/ai_startup.sh").read_text(encoding="utf-8")

    helper_import = "from dopemux.coldstart.network import ensure_docker_networks"
    helper_call = 'ensure_docker_networks(["dopemux-network"])'
    full_fleet = "dopemux mcp ensure --full"

    assert helper_import in script
    assert helper_call in script
    assert full_fleet in script
    assert script.index(helper_call) < script.index(full_fleet)
