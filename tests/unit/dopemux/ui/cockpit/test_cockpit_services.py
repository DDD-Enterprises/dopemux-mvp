from dopemux.ui.cockpit.render import render_cockpit
from dopemux.ui.cockpit.seed import load_seed


def test_top_level_modes_are_packet_modes_only() -> None:
    assert load_seed()["top_level_modes"] == ["PM", "Implementer", "Overview", "Services", "Events"]


def test_services_mode_contains_authority_src_and_expected_services() -> None:
    output = render_cockpit(120, 40)
    for service in (
        "dopemux",
        "task-orchestrator",
        "conport",
        "dope-memory",
        "dope-context",
        "dopecon-bridge",
        "adhd-engine",
        "repo-truth-extractor",
    ):
        assert service in output
    assert "Services authority:" in output
    assert "Inspector authority:" in output
    assert "SRC=" in output
    assert "[UNKNOWN]" not in output


def test_placeholder_modes_use_edge_chip_plain_unknown_and_next() -> None:
    output = render_cockpit(120, 40, mode="PM")
    assert "[EDGE] placeholder mode." in output
    assert "UNKNOWN: PM renderer not wired" in output
    assert "NEXT: implement PM mode" in output
    assert "[UNKNOWN]" not in output
