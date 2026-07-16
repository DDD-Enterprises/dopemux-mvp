"""Regression guards for services retired by DMX-HYG-DEADSVC-001."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_retired_service_paths_remain_absent() -> None:
    for relative_path in (
        "services/session_intelligence",
        "services/voice-commands",
    ):
        assert not (ROOT / relative_path).exists(), relative_path


def test_current_docs_do_not_advertise_retired_services() -> None:
    reference_expectations = {
        "services/shared/dopecon_bridge_client/README.md": "services.voice_commands",
        "docs/04-explanation/architecture/dopemux-architecture-overview.md": (
            "services/session_intelligence"
        ),
    }

    for relative_path, retired_reference in reference_expectations.items():
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        assert retired_reference not in content, relative_path
