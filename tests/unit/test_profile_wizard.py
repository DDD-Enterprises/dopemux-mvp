from types import SimpleNamespace

from dopemux.profile_wizard import ProfileWizard


def test_profile_wizard_build_profile_from_git_analysis(tmp_path):
    wizard = ProfileWizard(repo_path=tmp_path)
    analysis = SimpleNamespace(
        common_branch_prefixes=[("feature", 10), ("fix", 5)],
    )

    profile = wizard._build_profile(
        name="custom-flow",
        mcps=["serena-v2", "conport", "dope-context"],
        session_duration=25,
        energy_level="medium",
        git_analysis=analysis,
    )

    assert profile.name == "custom-flow"
    assert profile.adhd_config is not None
    assert profile.adhd_config.session_duration == 25
    assert profile.auto_detection is not None
    assert "feature/*" in profile.auto_detection.git_branches


def test_profile_wizard_save_profile_writes_yaml(tmp_path, monkeypatch):
    wizard = ProfileWizard(repo_path=tmp_path)
    monkeypatch.setattr(
        "dopemux.profile_wizard.console",
        SimpleNamespace(
            print=lambda *args, **kwargs: None,
            logger=SimpleNamespace(info=lambda *args, **kwargs: None),
        ),
    )
    analysis = SimpleNamespace(common_branch_prefixes=[])
    profile = wizard._build_profile(
        name="saved-flow",
        mcps=["serena-v2", "conport"],
        session_duration=20,
        energy_level="low",
        git_analysis=analysis,
    )

    out_file = tmp_path / "saved-flow.yaml"
    wizard._save_profile(profile, out_file)

    content = out_file.read_text(encoding="utf-8")
    assert "name: saved-flow" in content
    assert "mcps:" in content
