from types import SimpleNamespace

from dopemux.profile_analyzer import GitHistoryAnalyzer


def test_git_history_analyzer_extracts_usage_patterns(monkeypatch, tmp_path):
    analyzer = GitHistoryAnalyzer(repo_path=tmp_path)

    fake_log = "\n".join(
        [
            "abc123|2026-02-05 09:10:00 -0700|feat: add workflow",
            "src/app.py",
            "docs/guide.md",
            "def456|2026-02-05 14:20:00 -0700|fix: adjust profile",
            "services/api.py",
            "tests/test_api.py",
        ]
    )

    monkeypatch.setattr(
        "dopemux.profile_analyzer.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=fake_log),
    )

    analysis = analyzer.analyze(days_back=30, max_commits=20)

    assert analysis.total_commits == 2
    assert analysis.total_files_changed == 4
    assert analysis.common_directories
    assert "serena-v2" in analysis.suggested_mcps
    assert "conport" in analysis.suggested_mcps
