from __future__ import annotations

import json
from pathlib import Path

from tools.pr_steward.classifier import (
    load_trusted_security_approvers,
    load_trusted_security_release_apps,
)


def test_missing_key_returns_empty_list(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(json.dumps({"known_reviewers": [], "trusted_author_associations": []}))
    assert load_trusted_security_approvers(path) == []
    assert load_trusted_security_release_apps(path) == []


def test_populated_key_returns_list(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(
        json.dumps(
            {
                "known_reviewers": [],
                "trusted_author_associations": [],
                "trusted_security_release_approvers": ["alice", "bob"],
                "trusted_security_release_apps": [
                    {
                        "login": "ddd-release-gate[bot]",
                        "owner": "DDD-Enterprises",
                        "installation_scope": "DDD-Enterprises/dopemux-mvp",
                    }
                ],
            }
        )
    )
    assert load_trusted_security_approvers(path) == ["alice", "bob"]
    apps = load_trusted_security_release_apps(path)
    assert len(apps) == 1
    assert apps[0]["login"] == "ddd-release-gate[bot]"


def test_forbidden_generic_bots_dropped_from_apps_roster(tmp_path: Path):
    path = tmp_path / "known_reviewers.json"
    path.write_text(
        json.dumps(
            {
                "trusted_security_release_apps": [
                    {
                        "login": "github-actions[bot]",
                        "owner": "DDD-Enterprises",
                        "installation_scope": "DDD-Enterprises/dopemux-mvp",
                    },
                    {
                        "login": "ddd-release-gate[bot]",
                        "owner": "DDD-Enterprises",
                        "installation_scope": "DDD-Enterprises/dopemux-mvp",
                    },
                ]
            }
        )
    )
    apps = load_trusted_security_release_apps(path)
    assert [a["login"] for a in apps] == ["ddd-release-gate[bot]"]


def test_repo_known_reviewers_preserves_human_and_registers_release_app():
    """Shipped roster: hu3mann human + ddd-release-gate org app."""
    repo_path = (
        Path(__file__).resolve().parents[2]
        / "tools"
        / "pr_steward"
        / "known_reviewers.json"
    )
    humans = load_trusted_security_approvers(repo_path)
    assert "hu3mann" in humans
    apps = load_trusted_security_release_apps(repo_path)
    assert any(a["login"] == "ddd-release-gate[bot]" for a in apps)
    assert all(a["owner"] == "DDD-Enterprises" for a in apps)
