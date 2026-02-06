from datetime import datetime, timedelta

import asyncio

import dopemux.profile_analytics as profile_analytics
from dopemux.profile_analytics import (
    ProfileAnalytics,
    ProfileStats,
    ProfileSwitch,
    display_stats,
    generate_optimization_suggestions,
)


class _DummyConsole:
    def __init__(self):
        self.lines = []

    def print(self, message):
        self.lines.append(str(message))


def test_analyze_switches_computes_duration_and_mcp_averages():
    analytics = ProfileAnalytics(workspace_id="workspace-a")
    now = datetime.now()

    switches = [
        ProfileSwitch(
            timestamp=now - timedelta(hours=2),
            from_profile="full",
            to_profile="developer",
            trigger="manual",
            switch_duration_seconds=3.2,
            mcp_count=3,
        ),
        ProfileSwitch(
            timestamp=now - timedelta(hours=1),
            from_profile="developer",
            to_profile="full",
            trigger="auto",
            switch_duration_seconds=4.8,
            mcp_count=4,
        ),
    ]

    stats = analytics._analyze_switches(switches, days_back=30)

    assert stats.total_switches == 2
    assert stats.manual_switches == 1
    assert stats.auto_switches == 1
    assert stats.avg_switch_duration_seconds == 4.0
    assert stats.avg_mcp_count == 3.5
    assert stats.switch_accuracy >= 0.0


def test_log_switch_includes_duration_and_mcp_metrics(monkeypatch):
    analytics = ProfileAnalytics(workspace_id="workspace-a", conport_port=3010)
    captured = {}

    class _DummyResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            return _DummyResponse()

    monkeypatch.setattr(profile_analytics.aiohttp, "ClientSession", lambda: _DummySession())

    ok = asyncio.run(
        analytics.log_switch(
            to_profile="developer",
            trigger="manual",
            from_profile="full",
            confidence=0.88,
            switch_duration_seconds=5.25,
            mcp_count=3,
        )
    )

    assert ok is True
    payload = captured["json"]["value"]
    assert payload["switch_duration_seconds"] == 5.25
    assert payload["mcp_count"] == 3
    assert payload["trigger"] == "manual"


def test_display_stats_includes_ascii_heatmap_and_usage_insights(monkeypatch):
    fake_console = _DummyConsole()
    monkeypatch.setattr(profile_analytics, "console", fake_console)

    stats = ProfileStats(
        total_switches=4,
        manual_switches=2,
        auto_switches=1,
        suggestion_accepted=1,
        suggestion_declined=0,
        most_used_profile="developer",
        avg_switches_per_day=0.4,
        switch_accuracy=75.0,
        avg_switch_duration_seconds=4.25,
        avg_mcp_count=3.5,
        usage_by_hour={9: 2, 14: 1, 16: 1},
        usage_by_profile={"developer": 3, "full": 1},
    )

    display_stats(stats, days_back=10)

    rendered = "\n".join(fake_console.lines)
    assert "Time-of-Day Heatmap" in rendered
    assert "Profile Usage" in rendered
    assert "Avg switch time" in rendered


def test_generate_optimization_suggestions_returns_pattern_based_actions():
    stats = ProfileStats(
        total_switches=20,
        manual_switches=20,
        auto_switches=0,
        suggestion_accepted=1,
        suggestion_declined=5,
        most_used_profile="developer",
        avg_switches_per_day=1.0,
        switch_accuracy=55.0,
        avg_switch_duration_seconds=12.2,
        avg_mcp_count=7.0,
        usage_by_hour={9: 5, 14: 4},
        usage_by_profile={"developer": 16, "full": 4},
    )

    suggestions = generate_optimization_suggestions(stats)
    ids = {item["id"] for item in suggestions}

    assert "low_switch_accuracy" in ids
    assert "slow_profile_switch" in ids
    assert "manual_only_switching" in ids
    assert "high_suggestion_decline_rate" in ids
    assert "dominant_profile_detected" in ids
    assert "high_mcp_density" in ids


def test_archive_optimization_suggestions_posts_payload(monkeypatch):
    analytics = ProfileAnalytics(workspace_id="workspace-a", conport_port=3010)
    captured = {}

    class _DummyResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            return _DummyResponse()

    monkeypatch.setattr(profile_analytics.aiohttp, "ClientSession", lambda: _DummySession())

    stats = ProfileStats(
        total_switches=12,
        manual_switches=8,
        auto_switches=4,
        suggestion_accepted=2,
        suggestion_declined=1,
        most_used_profile="developer",
        avg_switches_per_day=0.4,
        switch_accuracy=80.0,
        avg_switch_duration_seconds=6.0,
        avg_mcp_count=3.2,
        usage_by_hour={10: 3},
        usage_by_profile={"developer": 9, "full": 3},
    )
    suggestions = [{"id": "test", "severity": "low", "title": "t", "detail": "d", "recommended_action": "a"}]

    ok = asyncio.run(
        analytics.archive_optimization_suggestions(
            suggestions=suggestions,
            stats=stats,
            days_back=14,
        )
    )

    assert ok is True
    payload = captured["json"]
    assert payload["category"] == "profile_optimization_recommendations"
    assert payload["value"]["days_back"] == 14
    assert payload["value"]["suggestions"][0]["id"] == "test"
