from click.testing import CliRunner

from src.dopemux.cli import cli


class _DummyAnalysis:
    total_commits = 12
    avg_commits_per_day = 0.4
    common_branch_prefixes = [("feature", 6)]
    common_directories = [("src", 20)]
    common_work_hours = [9, 10]
    peak_work_time = "morning"
    suggested_energy_level = "medium"
    suggested_session_duration = 25
    suggested_mcps = ["serena-v2", "conport", "dope-context"]


class _DummyAnalyzer:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.displayed = False

    def analyze(self, days_back=90, max_commits=500):
        assert days_back == 30
        assert max_commits == 120
        return _DummyAnalysis()

    def display_analysis(self, analysis):
        self.displayed = True
        assert analysis.total_commits == 12


def test_profile_analyze_usage_command(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("src.dopemux.profile_analyzer.GitHistoryAnalyzer", _DummyAnalyzer)

    result = runner.invoke(cli, ["profile", "analyze-usage", "--days", "30", "--max-commits", "120"])

    assert result.exit_code == 0, result.output
