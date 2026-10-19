"""W2-F08: workspace_path containment and file-pattern hardening.

No Qdrant, Voyage, OpenAI or network: every collaborator is mocked.
"""

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TEST_HOME = Path(tempfile.gettempdir()) / "dope-context-test-home"
TEST_HOME.mkdir(parents=True, exist_ok=True)
os.environ["HOME"] = str(TEST_HOME)
os.environ.setdefault("VOYAGE_API_KEY", "test")
os.environ.setdefault("VOYAGEAI_API_KEY", "test")

import sys
import types

sys.modules.setdefault(
    "rank_bm25", types.SimpleNamespace(BM25Okapi=type("BM25Okapi", (), {}))
)


@pytest.fixture
def roots(tmp_path, monkeypatch):
    """An allowed root with a workspace inside it, and a sibling outside it."""
    root = tmp_path / "code"
    inside = root / "proj"
    inside.mkdir(parents=True)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    monkeypatch.setenv("DOPE_CONTEXT_ALLOWED_ROOTS", str(root))
    monkeypatch.delenv("HOST_CODE_PARENT_DIR", raising=False)
    return SimpleNamespace(root=root, inside=inside, outside=outside)


def _guard():
    from src.utils import workspace_guard

    return workspace_guard


def test_normal_path_accepted(roots):
    assert _guard().validate_workspace_path(str(roots.inside)) == roots.inside.resolve()


def test_outside_path_rejected(roots):
    g = _guard()
    with pytest.raises(g.WorkspaceRejected):
        g.validate_workspace_path(str(roots.outside))


def test_dotdot_escape_and_missing_and_file_rejected(roots):
    g = _guard()
    escape = f"{roots.inside}/../../elsewhere"
    with pytest.raises(g.WorkspaceRejected):
        g.validate_workspace_path(escape)
    with pytest.raises(g.WorkspaceRejected):
        g.validate_workspace_path(str(roots.inside / "nope"))
    f = roots.inside / "a.py"
    f.write_text("x=1\n")
    with pytest.raises(g.WorkspaceRejected):
        g.validate_workspace_path(str(f))


def test_symlinked_workspace_pointing_outside_rejected(roots):
    g = _guard()
    link = roots.root / "link"
    link.symlink_to(roots.outside)
    with pytest.raises(g.WorkspaceRejected):
        g.validate_workspace_path(str(link))


def test_no_root_fails_closed(tmp_path, monkeypatch):
    g = _guard()
    monkeypatch.delenv("DOPE_CONTEXT_ALLOWED_ROOTS", raising=False)
    monkeypatch.setenv("HOST_CODE_PARENT_DIR", str(tmp_path / "does-not-exist"))
    with patch.object(g, "CONTAINER_MOUNT_TARGET", str(tmp_path / "no-mount")):
        with pytest.raises(g.WorkspaceRejected):
            g.validate_workspace_path(str(tmp_path))


@pytest.mark.parametrize(
    "pattern", ["../x", "a/../../x", "/etc/passwd", "/abs/*.py", "~/x", "..\\x"]
)
def test_bad_patterns_rejected(pattern):
    g = _guard()
    with pytest.raises(g.WorkspaceRejected):
        g.validate_patterns([pattern])


def test_good_patterns_accepted():
    _guard().validate_patterns(["*.py", "src/**/*.ts", "*test*", "a..b.py"])


# ---- handler guards: rejection happens before any collection/network work ----


@pytest.mark.asyncio
async def test_index_workspace_outside_root_creates_no_collection(roots):
    from src.mcp import server

    g = _guard()
    with patch.object(server, "MultiVectorSearch") as mvs, patch.object(
        server, "VoyageEmbedder"
    ) as emb, patch.object(server, "IndexingPipeline") as pipe:
        with pytest.raises(g.WorkspaceRejected):
            await server._index_workspace_impl(workspace_path=str(roots.outside))
    mvs.assert_not_called()
    emb.assert_not_called()
    pipe.assert_not_called()


@pytest.mark.asyncio
async def test_index_docs_outside_root_creates_no_collection(roots):
    from src.mcp import server

    g = _guard()
    with patch.object(server, "DocumentSearch") as ds, patch.object(
        server, "DocIndexingPipeline"
    ) as pipe:
        with pytest.raises(g.WorkspaceRejected):
            await server._index_docs_impl(workspace_path=str(roots.outside))
    ds.assert_not_called()
    pipe.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["../x", "/etc/passwd"])
async def test_index_workspace_bad_pattern_rejected_before_work(roots, bad):
    from src.mcp import server

    g = _guard()
    with patch.object(server, "MultiVectorSearch") as mvs:
        with pytest.raises(g.WorkspaceRejected):
            await server._index_workspace_impl(
                workspace_path=str(roots.inside), include_patterns=[bad]
            )
        with pytest.raises(g.WorkspaceRejected):
            await server._index_workspace_impl(
                workspace_path=str(roots.inside), exclude_patterns=[bad]
            )
    mvs.assert_not_called()


@pytest.mark.asyncio
async def test_search_and_sync_and_clear_outside_root_rejected(roots):
    from src.mcp import server

    g = _guard()
    out = str(roots.outside)
    with patch.object(server, "get_collection_names") as names:
        for call in (
            server._search_code_impl(query="q", workspace_path=out),
            server._docs_search_impl(query="q", workspace_path=out),
            server._sync_workspace_impl(workspace_path=out),
            server._sync_docs_impl(workspace_path=out),
            server._clear_index_impl(workspace_path=out),
        ):
            with pytest.raises(g.WorkspaceRejected):
                await call
    names.assert_not_called()


def test_multi_workspace_resolvers_reject_outside(roots):
    from src.mcp import server

    g = _guard()
    out = str(roots.outside)
    with pytest.raises(g.WorkspaceRejected):
        server._resolve_explicit_workspaces(out)
    with pytest.raises(g.WorkspaceRejected):
        server._resolve_target_workspaces(None, [str(roots.inside), out])
    assert server._resolve_explicit_workspaces(str(roots.inside)) == [
        roots.inside.resolve()
    ]


@pytest.mark.asyncio
async def test_autoindex_start_rest_handler_rejects_outside(roots):
    from src.mcp import server

    request = MagicMock()
    request.json = AsyncMock(return_value={"workspace_path": str(roots.outside)})
    handler = [
        getattr(server, n)
        for n in ("autoindex_start", "autoindex_bootstrap")
        if hasattr(server, n)
    ]
    assert handler, "REST autoindex start handler not found"
    with patch.object(server.asyncio, "create_task") as ct:
        resp = await getattr(handler[0], "fn", handler[0])(request)
    ct.assert_not_called()
    assert resp.status_code == 400


# ---- file discovery: symlinks that leave the workspace are not read ----


def _tree(roots):
    secret = roots.outside / "secret.py"
    secret.write_text("TOKEN = 1\n")
    (roots.inside / "ok.py").write_text("x = 1\n")
    (roots.inside / "leak.py").symlink_to(secret)
    (roots.inside / "leakdir").symlink_to(roots.outside)
    return secret


def test_code_pipeline_discovery_skips_escaping_symlinks(roots):
    from src.pipeline.indexing_pipeline import IndexingConfig, IndexingPipeline

    _tree(roots)
    pipe = object.__new__(IndexingPipeline)
    pipe.config = IndexingConfig(
        workspace_path=roots.inside.resolve(),
        include_patterns=["*.py"],
        exclude_patterns=["__pycache__"],
    )
    names = {p.name for p in pipe._discover_files()}
    assert names == {"ok.py"}


def test_docs_pipeline_discovery_skips_escaping_symlinks(roots):
    from src.pipeline.docs_pipeline import DocIndexingPipeline

    secret = roots.outside / "secret.md"
    secret.write_text("# secret\n")
    (roots.inside / "ok.md").write_text("# ok\n")
    (roots.inside / "leak.md").symlink_to(secret)
    pipe = object.__new__(DocIndexingPipeline)
    pipe.workspace_path = roots.inside.resolve()
    found = {p.name for p in pipe._discover_documents(include_patterns=["*.md"])}
    assert found == {"ok.md"}


def test_synchronizer_scan_skips_escaping_symlinks(roots, tmp_path):
    from src.sync.file_synchronizer import FileSynchronizer

    _tree(roots)
    with patch(
        "src.sync.file_synchronizer.get_snapshot_dir", return_value=tmp_path / "snap"
    ):
        sync = FileSynchronizer(
            workspace_path=roots.inside.resolve(), include_patterns=["*.py"]
        )
        snap = sync._scan_workspace()
    assert set(snap.files) == {"ok.py"}
