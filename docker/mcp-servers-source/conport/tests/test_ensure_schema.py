"""
Tests for EnhancedConPortServer._ensure_schema() fail-closed behavior.

Regression coverage for a bug where post-apply schema verification was
fail-open: if the verification query found no expected tables, the code
logged a warning and "proceeded anyway" instead of raising. This meant a
genuinely-unverifiable schema state (e.g. schema.sql silently failed to
create objects) would let the server boot as if healthy.

Run with: mise exec -- python -m pytest tests/test_ensure_schema.py -q
"""

import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

CONPORT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONPORT_DIR))

# Same MCP stdio stubs used by tests/test_mcp_custom_data.py, so importing
# enhanced_server does not require the real `mcp` package to be installed.
if "mcp.server.fastmcp" not in sys.modules:
    class _FastMCPStub:
        def __init__(self, *args, **kwargs):
            self.tools = []

        def tool(self):
            def decorator(func):
                self.tools.append(func.__name__)
                return func

            return decorator

    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = _FastMCPStub
    mcp_module = types.ModuleType("mcp")
    mcp_server_module = types.ModuleType("mcp.server")
    mcp_server_models_module = types.ModuleType("mcp.server.models")
    mcp_server_models_module.InitializationOptions = object
    mcp_server_stdio_module = types.ModuleType("mcp.server.stdio")
    mcp_server_stdio_module.stdio_server = object

    sys.modules.setdefault("mcp", mcp_module)
    sys.modules.setdefault("mcp.server", mcp_server_module)
    sys.modules.setdefault("mcp.server.fastmcp", fastmcp_module)
    sys.modules.setdefault("mcp.server.models", mcp_server_models_module)
    sys.modules.setdefault("mcp.server.stdio", mcp_server_stdio_module)

from enhanced_server import EnhancedConPortServer  # noqa: E402


class _FakeAcquireCtx:
    """Async context manager mimicking asyncpg pool.acquire()."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    """Fake asyncpg pool whose acquire() yields fake connections in order.

    `fetchval_results` is consumed one value per `_ensure_schema` query:
    [initial existence check, post-apply verification check].
    """

    def __init__(self, fetchval_results):
        self._results = list(fetchval_results)

    def acquire(self):
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value=self._results.pop(0))
        return _FakeAcquireCtx(conn)


def _make_server_with_pool(fetchval_results):
    server = EnhancedConPortServer()
    server.db_pool = _FakePool(fetchval_results)
    return server


class _FakeProc:
    """Fake asyncio subprocess for psql invocation."""

    def __init__(self, returncode=0, output=b""):
        self.returncode = returncode
        self._output = output

    async def communicate(self):
        return (self._output, None)


@pytest.mark.asyncio
async def test_ensure_schema_raises_when_post_apply_verification_fails():
    """If schema.sql applies cleanly but the expected table still can't be
    verified, _ensure_schema must raise (fail closed), not warn-and-continue.
    """
    # First fetchval (pre-apply existence check) -> None (schema missing)
    # Second fetchval (post-apply verification) -> None (still missing/unverifiable)
    server = _make_server_with_pool(fetchval_results=[None, None])

    fake_proc = _FakeProc(returncode=0, output=b"CREATE TABLE\n")
    with patch(
        "asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)
    ):
        with pytest.raises(RuntimeError, match="Schema verification failed"):
            await server._ensure_schema()


@pytest.mark.asyncio
async def test_ensure_schema_succeeds_when_post_apply_verification_passes():
    """When the post-apply verification confirms the table exists, the method
    must return normally (no exception) and log success on the real success
    path (not inside a warning branch).
    """
    server = _make_server_with_pool(fetchval_results=[None, 1])

    fake_proc = _FakeProc(returncode=0, output=b"CREATE TABLE\n")
    with patch(
        "asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)
    ):
        with patch("enhanced_server.logger") as mock_logger:
            await server._ensure_schema()  # must not raise

    success_logged = any(
        "Schema verification OK" in str(call.args[0])
        for call in mock_logger.info.call_args_list
    )
    assert success_logged, "Expected '✅ Schema verification OK' to be logged on success"


@pytest.mark.asyncio
async def test_ensure_schema_tolerates_already_exists_idempotent_apply():
    """Idempotency must be preserved: if psql fails only because objects
    already exist, that is not a fatal error and verification should still
    succeed and return normally.
    """
    server = _make_server_with_pool(fetchval_results=[None, 1])

    fake_proc = _FakeProc(
        returncode=3, output=b'ERROR:  relation "workspace_contexts" already exists\n'
    )
    with patch(
        "asyncio.create_subprocess_exec", new=AsyncMock(return_value=fake_proc)
    ):
        await server._ensure_schema()  # must not raise
