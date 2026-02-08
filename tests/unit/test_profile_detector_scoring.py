from datetime import datetime
from pathlib import Path

import pytest
import yaml

from dopemux.profile_detector import DetectionContext, ProfileDetector


def _write_profile(profile_dir: Path, profile: dict) -> None:
    output = profile_dir / f"{profile['name']}.yaml"
    output.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")


@pytest.fixture
def profile_dir(tmp_path: Path) -> Path:
    path = tmp_path / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_file_pattern_analyzer_scores_by_percentage(profile_dir: Path):
    _write_profile(
        profile_dir,
        {
            "name": "detector",
            "display_name": "Detector",
            "description": "Test detector profile",
            "mcps": ["conport"],
            "auto_detection": {"file_patterns": ["*.py"]},
        },
    )
    detector = ProfileDetector(profile_dir=profile_dir)

    score = detector._score_file_patterns(
        patterns=["*.py"],
        recent_files=["src/app.py", "docs/README.md", "tests/test_api.py", "web/index.ts"],
    )

    assert score == pytest.approx(5.0)


def test_file_pattern_analyzer_deduplicates_recent_files(profile_dir: Path):
    _write_profile(
        profile_dir,
        {
            "name": "detector",
            "display_name": "Detector",
            "description": "Test detector profile",
            "mcps": ["conport"],
            "auto_detection": {"file_patterns": ["*.py"]},
        },
    )
    detector = ProfileDetector(profile_dir=profile_dir)

    score = detector._score_file_patterns(
        patterns=["*.py"],
        recent_files=["src/app.py", "src/app.py", "src/app.py"],
    )

    assert score == pytest.approx(10.0)


def test_confidence_threshold_auto_exact_85(profile_dir: Path):
    _write_profile(
        profile_dir,
        {
            "name": "auto-threshold",
            "display_name": "Auto Threshold",
            "description": "Reaches the auto confidence threshold exactly",
            "mcps": ["conport"],
            "adhd_config": {
                "energy_preference": "any",
                "attention_mode": "any",
                "session_duration": 50,
            },
            "auto_detection": {
                "git_branches": ["feature/*"],
                "directories": ["workspace"],
                "file_patterns": ["*.py"],
                "time_windows": [],
            },
        },
    )
    detector = ProfileDetector(profile_dir=profile_dir)
    workspace = profile_dir.parent / "workspace"
    workspace.mkdir()

    match = detector.detect(
        DetectionContext(
            current_dir=workspace,
            git_branch="feature/file-pattern-scoring",
            recent_files=["src/app.py"],
            energy_level="low",
            attention_mode="focused",
            current_time=datetime(2026, 2, 6, 11, 0, 0),
        )
    )

    assert match.profile_name == "auto-threshold"
    assert match.total_score == pytest.approx(85.0)
    assert match.confidence == pytest.approx(0.85)
    assert match.suggestion_level == "auto"


def test_confidence_threshold_prompt_exact_65(profile_dir: Path):
    _write_profile(
        profile_dir,
        {
            "name": "prompt-threshold",
            "display_name": "Prompt Threshold",
            "description": "Reaches the prompt confidence threshold exactly",
            "mcps": ["conport"],
            "auto_detection": {
                "git_branches": ["feature/*"],
                "directories": ["workspace"],
                "file_patterns": ["*.py"],
                "time_windows": [],
            },
        },
    )
    detector = ProfileDetector(profile_dir=profile_dir)
    workspace = profile_dir.parent / "workspace"
    workspace.mkdir()

    match = detector.detect(
        DetectionContext(
            current_dir=workspace,
            git_branch="feature/prompt-threshold",
            recent_files=["src/app.py"],
            energy_level=None,
            attention_mode=None,
            current_time=datetime(2026, 2, 6, 11, 0, 0),
        )
    )

    assert match.profile_name == "prompt-threshold"
    assert match.total_score == pytest.approx(65.0)
    assert match.confidence == pytest.approx(0.65)
    assert match.suggestion_level == "prompt"


def test_confidence_threshold_none_below_65(profile_dir: Path):
    _write_profile(
        profile_dir,
        {
            "name": "none-threshold",
            "display_name": "None Threshold",
            "description": "Falls below prompt threshold",
            "mcps": ["conport"],
            "auto_detection": {
                "git_branches": ["feature/*"],
                "directories": ["workspace"],
                "file_patterns": ["*.py"],
                "time_windows": [],
            },
        },
    )
    detector = ProfileDetector(profile_dir=profile_dir)
    workspace = profile_dir.parent / "workspace"
    workspace.mkdir()

    match = detector.detect(
        DetectionContext(
            current_dir=workspace,
            git_branch="feature/none-threshold",
            recent_files=["src/app.py", "docs/README.md"],
            energy_level=None,
            attention_mode=None,
            current_time=datetime(2026, 2, 6, 11, 0, 0),
        )
    )

    assert match.profile_name == "none-threshold"
    assert match.total_score == pytest.approx(60.0)
    assert match.confidence == pytest.approx(0.6)
    assert match.suggestion_level == "none"
    assert match.signal_scores["git_branch"] == pytest.approx(30.0)
    assert match.signal_scores["directory"] == pytest.approx(25.0)
    assert match.signal_scores["file_patterns"] == pytest.approx(5.0)
