"""Regression tests for InstanceResolver authority/provenance semantics.

Context (DMX-W1-04-F018): an environment URL override previously replaced a
repo-profile service's ``provenance`` with ``env_var``, silently downgrading
its authority classification (repo-profile services are the ones the
DiscoveryGate treats as mandatory). This suite locks in the corrected
invariant: an endpoint override may change *where* Dopemux connects, but it
may not silently change *who declared the service authoritative*.
"""

import os

import pytest

from dopemux.mcp.resolver import InstanceResolver


def _write_repo_profile(project_root, body):
    dopemux_dir = project_root / ".dopemux"
    dopemux_dir.mkdir(exist_ok=True)
    (dopemux_dir / "mcp.instances.toml").write_text(body)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    # Guard against DOPMUX_*_URL leaking in from the ambient environment.
    for key in list(os.environ):
        if key.startswith("DOPMUX_") and key.endswith("_URL"):
            monkeypatch.delenv(key, raising=False)
    yield


def test_r1_repo_profile_url_no_env_override(tmp_path):
    """Case R1: repo-profile URL, no env override -> authority=repo_profile."""
    _write_repo_profile(
        tmp_path,
        """
[project]
project_id = "test-repo"

[mcp.conport]
url = "http://repo-url:3000"
""",
    )
    resolver = InstanceResolver(tmp_path)
    res = resolver.resolve()
    assert res["servers"]["conport"]["url"] == "http://repo-url:3000"
    assert res["provenance"]["conport"] == "repo_profile"


def test_r2_repo_profile_url_plus_env_override_preserves_authority(tmp_path, monkeypatch):
    """Case R2: env URL override must not erase repo-profile authority (F018)."""
    _write_repo_profile(
        tmp_path,
        """
[project]
project_id = "test-repo"

[mcp.conport]
url = "http://repo-url:3000"
""",
    )
    monkeypatch.setenv("DOPMUX_CONPORT_URL", "http://env-url:4000")

    resolver = InstanceResolver(tmp_path)
    res = resolver.resolve()

    # The endpoint address does move to the env override...
    assert res["servers"]["conport"]["url"] == "http://env-url:4000"
    # ...but the authority/provenance classification must remain repo_profile.
    assert res["provenance"]["conport"] == "repo_profile"


def test_r3_env_only_service_remains_env_var_and_nonmandatory(tmp_path, monkeypatch):
    """Case R3: a service introduced solely via env var stays env_var provenance."""
    _write_repo_profile(
        tmp_path,
        """
[project]
project_id = "test-repo"
""",
    )
    monkeypatch.setenv("DOPMUX_STANDALONE_URL", "http://standalone-url:5000")

    resolver = InstanceResolver(tmp_path)
    res = resolver.resolve()

    assert res["servers"]["standalone"]["url"] == "http://standalone-url:5000"
    assert res["provenance"]["standalone"] == "env_var"


def test_reused_resolver_does_not_leak_stale_provenance(tmp_path, monkeypatch):
    """A reused InstanceResolver instance must not let repo_profile provenance
    from a prior resolve() call leak into a later call where the service is
    genuinely env-only (e.g. the repo profile was removed/changed between
    calls). resolve() must reset its state each call."""
    _write_repo_profile(
        tmp_path,
        """
[project]
project_id = "test-repo"

[mcp.conport]
url = "http://repo-url:3000"
""",
    )
    resolver = InstanceResolver(tmp_path)
    res1 = resolver.resolve()
    assert res1["provenance"]["conport"] == "repo_profile"

    # Repo profile no longer declares conport; only an env var does now.
    _write_repo_profile(
        tmp_path,
        """
[project]
project_id = "test-repo"
""",
    )
    monkeypatch.setenv("DOPMUX_CONPORT_URL", "http://env-only-url:6000")

    res2 = resolver.resolve()
    assert res2["servers"]["conport"]["url"] == "http://env-only-url:6000"
    assert res2["provenance"]["conport"] == "env_var"


def test_resolver_precedence_legacy(tmp_path, monkeypatch):
    """Legacy smoke test retained: repo-profile then env override, in sequence."""
    _write_repo_profile(
        tmp_path,
        """
[project]
project_id = "test-repo"

[mcp.conport]
url = "http://repo-url:3000"
""",
    )

    resolver = InstanceResolver(tmp_path)
    res = resolver.resolve()
    assert res["servers"]["conport"]["url"] == "http://repo-url:3000"
    assert res["provenance"]["conport"] == "repo_profile"

    monkeypatch.setenv("DOPMUX_CONPORT_URL", "http://env-url:4000")
    res = resolver.resolve()
    assert res["servers"]["conport"]["url"] == "http://env-url:4000"
    assert res["provenance"]["conport"] == "repo_profile"
