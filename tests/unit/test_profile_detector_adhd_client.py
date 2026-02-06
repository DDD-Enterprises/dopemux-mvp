from pathlib import Path
from urllib.error import URLError

import pytest

from dopemux.profile_detector import ProfileDetector


@pytest.fixture
def profile_dir(tmp_path: Path) -> Path:
    path = tmp_path / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    (path / "test.yaml").write_text(
        "\n".join(
            [
                "name: test",
                "display_name: Test",
                "description: Test profile",
                "mcps:",
                "  - conport",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_adhd_engine_base_urls_default_priority(profile_dir: Path, monkeypatch):
    monkeypatch.delenv("DOPEMUX_ADHD_ENGINE_BASE_URL", raising=False)
    monkeypatch.delenv("DOPEMUX_ADHD_ENGINE_PORT", raising=False)
    detector = ProfileDetector(profile_dir=profile_dir)

    urls = detector._adhd_engine_base_urls()
    assert urls[0] == "http://localhost:5448"
    assert "http://localhost:8095" in urls


def test_fetch_adhd_engine_state_falls_back_to_second_base_url(profile_dir: Path, monkeypatch):
    detector = ProfileDetector(profile_dir=profile_dir)
    monkeypatch.setattr(detector, "_adhd_engine_base_urls", lambda: ["http://localhost:5448", "http://localhost:8095"])

    def fake_read_json_url(url: str, headers=None):
        if url.startswith("http://localhost:5448"):
            raise URLError("connection refused")
        if "/energy-level/" in url:
            return {"energy_level": "LOW"}
        if "/attention-state/" in url:
            return {"attention_state": "Focused"}
        return {}

    monkeypatch.setattr(detector, "_read_json_url", fake_read_json_url)
    energy, attention = detector._fetch_adhd_engine_state()
    assert energy == "low"
    assert attention == "focused"


def test_fetch_adhd_engine_state_graceful_failure(profile_dir: Path, monkeypatch):
    detector = ProfileDetector(profile_dir=profile_dir)
    monkeypatch.setattr(detector, "_adhd_engine_base_urls", lambda: ["http://localhost:5448"])
    monkeypatch.setattr(detector, "_read_json_url", lambda *a, **k: (_ for _ in ()).throw(URLError("down")))

    energy, attention = detector._fetch_adhd_engine_state()
    assert energy is None
    assert attention is None
