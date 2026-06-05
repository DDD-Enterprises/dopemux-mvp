"""Pytest bootstrap + fixtures for the DCP read-only facade.

Adds the facade ``src`` to ``sys.path`` (repo ``src`` is already on
pytest ``pythonpath`` for the dopemux import). Fixtures build real temporary
git workspaces with ``.dopemux/``, ``.repo_id``, and proof bundles so the
resolver/gitstate/proofs logic is exercised against genuine on-disk state.

All filesystem writes here are TEST-FIXTURE setup only; the facade
implementation modules perform no writes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

_FACADE_SRC = Path(__file__).resolve().parent / "src"
if str(_FACADE_SRC) not in sys.path:
    sys.path.insert(0, str(_FACADE_SRC))


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture
def make_workspace(tmp_path_factory):
    """Factory building a real git workspace.

    Returns a dict: {path, head_sha}. Options control eligibility/identity
    fixtures (missing .dopemux, missing/mismatched .repo_id), dirty state, and
    proof bundles. ``bundles`` maps bundle_id -> PROOF.json dict.
    """

    def _make(
        name: str = "ws",
        *,
        project: str = "testproj",
        owner: Optional[str] = "tester",
        with_dopemux: bool = True,
        with_repo_id: bool = True,
        dirty: bool = False,
        bundles: Optional[dict] = None,
        extra_proof_files: Optional[dict] = None,
    ) -> dict:
        ws = tmp_path_factory.mktemp(name)
        _git(ws, "init", "-q")
        _git(ws, "config", "user.email", "t@example.test")
        _git(ws, "config", "user.name", "tester")
        if with_dopemux:
            (ws / ".dopemux").mkdir()
        (ws / "README.md").write_text("hello\n", encoding="utf-8")
        if with_repo_id:
            lines = [f"project={project}"]
            if owner is not None:
                lines.append(f"owner={owner}")
            (ws / ".repo_id").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if bundles:
            for bname, proof_meta in bundles.items():
                bdir = ws / "proof" / bname
                bdir.mkdir(parents=True)
                (bdir / "PROOF.json").write_text(json.dumps(proof_meta), encoding="utf-8")
                (bdir / "AUDIT.md").write_text(f"# audit {bname}\n", encoding="utf-8")
        if extra_proof_files:
            for relpath, content in extra_proof_files.items():
                fp = ws / "proof" / relpath
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")
        _git(ws, "add", "-A")
        _git(ws, "commit", "-q", "-m", "init")
        head = _git(ws, "rev-parse", "HEAD")
        if dirty:
            (ws / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")
        return {"path": ws, "head_sha": head}

    return _make


@pytest.fixture
def build_registry():
    """Build an in-memory Registry from project dicts (no file IO)."""
    from dcp_facade.registry import parse_registry

    def _build(projects: list[dict], approved_roots: Optional[list[str]] = None):
        doc: dict = {"projects": projects}
        if approved_roots is not None:
            doc["approved_roots"] = approved_roots
        return parse_registry(doc)

    return _build


@pytest.fixture
def project_entry():
    """Helper to construct a registry project dict pointing at a workspace."""

    def _entry(
        ws_path: Path,
        *,
        project_id: str = "proj",
        identity_project: str = "testproj",
        identity_owner: Optional[str] = "tester",
        enabled: bool = True,
        service_profiles: Optional[dict] = None,
    ) -> dict:
        identity: dict = {"project": identity_project}
        if identity_owner is not None:
            identity["owner"] = identity_owner
        return {
            "project_id": project_id,
            "workspace_path": str(ws_path),
            "enabled": enabled,
            "identity": identity,
            "service_profiles": service_profiles or {},
        }

    return _entry


class _FakeTransport:
    """Records the last HTTP call and returns a configured response (no network)."""

    def __init__(self, status=200, json_body=None, raise_exc=None):
        self.status = status
        self.json_body = json_body if json_body is not None else {}
        self.raise_exc = raise_exc
        self.calls: list[dict] = []

    def __call__(self, *, method, url, params, json, timeout):
        self.calls.append(
            {"method": method, "url": url, "params": params, "json": json, "timeout": timeout}
        )
        if self.raise_exc is not None:
            raise self.raise_exc
        from dcp_facade.http_client import HttpResponse

        ok = 200 <= self.status < 300
        return HttpResponse(status=self.status, json=self.json_body, ok=ok)

    @property
    def last(self) -> dict:
        return self.calls[-1]


@pytest.fixture
def fake_transport():
    """Factory: fake_transport(status=, json_body=, raise_exc=) -> recording transport."""

    def _make(status=200, json_body=None, raise_exc=None):
        return _FakeTransport(status=status, json_body=json_body, raise_exc=raise_exc)

    return _make


@pytest.fixture
def make_client(fake_transport):
    """Build a ReadOnlyHttpClient backed by a fake transport; returns (client, transport)."""

    def _make(status=200, json_body=None, raise_exc=None):
        from dcp_facade.http_client import ReadOnlyHttpClient

        ft = _FakeTransport(status=status, json_body=json_body, raise_exc=raise_exc)
        return ReadOnlyHttpClient(transport=ft), ft

    return _make


@pytest.fixture
def conport_dm_profiles():
    """Loopback-bound conport + dope_memory service profiles for a test project."""
    return {
        "conport": {"base_url": "http://127.0.0.1:3004", "workspace_id": "ws-test"},
        "dope_memory": {"base_url": "http://127.0.0.1:3020", "workspace_id": "ws-test"},
    }
