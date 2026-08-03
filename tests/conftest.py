import os
import sys
from pathlib import Path
src_path = str(Path(__file__).resolve().parents[1] / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import os
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

"""
Pytest configuration and shared fixtures.
"""

import shutil
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Provide lightweight stubs for heavy/external dependencies ONLY.
# Core dependencies like click, pydantic, yaml, toml should be installed in the test env.

# Provide a lightweight asyncpg stub when the library is unavailable.
try:
    import asyncpg
except ImportError:
    asyncpg_stub = types.ModuleType("asyncpg")
    class Connection:
        pass
    asyncpg_stub.Connection = Connection
    sys.modules["asyncpg"] = asyncpg_stub

# Provide a lightweight litellm stub when the library is unavailable.
try:
    import litellm
except ImportError:
    litellm_stub = types.ModuleType("litellm")
    litellm_stub.completion = MagicMock()
    litellm_stub.embedding = MagicMock()
    sys.modules["litellm"] = litellm_stub

# Provide a lightweight psutil stub when the library is unavailable.
try:
    import psutil
except ImportError:
    psutil_stub = types.ModuleType("psutil")
    psutil_stub.cpu_percent = MagicMock(return_value=0.0)
    psutil_stub.virtual_memory = MagicMock(return_value=MagicMock(percent=0.0))
    psutil_stub.disk_usage = MagicMock(return_value=MagicMock(percent=0.0))
    psutil_stub.process_iter = MagicMock(return_value=[])
    sys.modules["psutil"] = psutil_stub

# Provide a lightweight httpx stub when the library is unavailable.
try:
    import httpx
except ImportError:
    httpx_stub = types.ModuleType("httpx")
    httpx_stub.get = MagicMock()
    httpx_stub.post = MagicMock()
    httpx_stub.AsyncClient = MagicMock
    sys.modules["httpx"] = httpx_stub

# Provide a lightweight requests stub when the library is unavailable.
try:
    import requests
except ImportError:
    requests_stub = types.ModuleType("requests")
    requests_stub.get = MagicMock()
    requests_stub.post = MagicMock()
    sys.modules["requests"] = requests_stub

# Now import dopemux modules after stubs are in place
from dopemux.adhd.attention_monitor import AttentionMonitor
from dopemux.adhd.context_manager import ContextManager
from dopemux.adhd.task_decomposer import TaskDecomposer
from dopemux.config.manager import ConfigManager

# Skip asyncio-marked tests when pytest-asyncio is unavailable.
try:  # pragma: no cover - best effort compatibility
    import pytest_asyncio  # type: ignore  # noqa: F401

    _HAVE_PYTEST_ASYNCIO = True
except ImportError:  # pragma: no cover - fallback
    _HAVE_PYTEST_ASYNCIO = False

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(item):
        if item.get_closest_marker("asyncio"):
            pytest.skip(
                "pytest-asyncio is not installed in this environment",
                allow_module_level=False,
            )


# Single pytest_addoption for the whole file. Defining a second one at module
# scope would silently shadow this via normal Python rebinding, so the
# asyncio_mode ini registration lives here rather than inside the ImportError
# branch above.
def pytest_addoption(parser):
    parser.addoption(
        "--run-database-tests",
        action="store_true",
        default=False,
        help="Run tests marked @pytest.mark.database against a real database. "
             "Use a throwaway instance, never the shared dev store.",
    )
    if not _HAVE_PYTEST_ASYNCIO:
        parser.addini(
            "asyncio_mode",
            "Compatibility setting consumed by pytest-asyncio when installed.",
            default="auto",
        )


# ---------------------------------------------------------------------------
# Fail-closed guard: tests must never write to a live ConPort.
# ---------------------------------------------------------------------------
# On 2026-08-02 the shared ConPort database was found holding 238 custom_data
# rows across 197 distinct workspace_ids, ~236 of which were pytest temp
# directories: `/private/var/folders/.../pytest-of-hue/pytest-N/test_*` and
# `.../tmpXXXX/test_project`. The test suite had been writing into the live
# development database for months.
#
# The path: `dopemux start` calls instance_state.save_instance_state_sync(),
# which builds an InstanceStateManager and POSTs to
# http://localhost:<port>/api/custom_data. resolve_conport_port() actively
# PROBES localhost for a listening ConPort, so it finds production by design.
# Any test that invokes `cli, ["start", ...]` without mocking that call writes
# real rows — e.g. tests/integration/test_project_workflow.py and
# tests/integration/test_start_crit_gaps.py, whose base_mocks stop short of it.
#
# Environment variables alone are NOT sufficient: cli.py passes
# `conport_port=3004` explicitly at four call sites, and an explicit argument
# is candidate #1 in resolve_conport_port's precedence order, ahead of every
# env override. Measured against a live ConPort: with no guard,
# resolve_conport_port(3004) returned 3019 (it probed and found production) and
# a real row was written. So the guard is applied at the actual network
# chokepoint — InstanceStateManager.save_instance_state, the method that
# performs the POST.
#
# resolve_conport_port itself is deliberately left unpatched so that
# tests/dopemux/test_instance_state_filtering.py and friends keep testing the
# real resolver.

@pytest.fixture(autouse=True)
def _block_live_conport_writes(monkeypatch):
    """Neutralise the ConPort state writer so no test can reach a live server.

    Deliberately does NOT set DOPEMUX_CONPORT_PORT / CONPORT_PORT / CONPORT_URL.
    Every one of those feeds port resolution as well as client base URLs, and
    forcing them to an unreachable value breaks tests that legitimately assert
    on resolved ports:
      - test_port_config.py::test_get_conport_port_multi_instance (wanted 3034)
      - test_startup_integration.py::test_startup_flow_calls_recovery_menu
        (wanted 3004; CONPORT_URL is candidate #3 in resolve_conport_port)
    They were only ever defense in depth. Measured against a live ConPort, the
    env vars did not reliably block the write while this method patch did —
    resolve_conport_port still returned 3019 (production) and the POST was
    refused anyway. So the guard sits exactly on the write.
    """
    try:
        from dopemux.instance_state import InstanceStateManager
    except Exception:  # pragma: no cover - import shape varies across envs
        return

    async def _refuse_to_write(self, state):
        # Same return contract as a ConPort that is simply down, which is the
        # condition cli.py's try/except already handles.
        return False

    monkeypatch.setattr(
        InstanceStateManager, "save_instance_state", _refuse_to_write, raising=False
    )


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.database tests unless explicitly opted in.

    pytest.ini has declared a `database` marker for a long time and no test has
    ever used it. It is the supported way to write a test that genuinely needs a
    real database: mark it, and run with --run-database-tests against a
    throwaway instance — never against the shared dev store.
    """
    if config.getoption("--run-database-tests", default=False):
        return
    skip = pytest.mark.skip(reason="needs a real database; pass --run-database-tests")
    for item in items:
        if item.get_closest_marker("database"):
            item.add_marker(skip)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "version": "1.0",
        "adhd_profile": {
            "focus_duration_avg": 25,
            "break_interval": 5,
            "distraction_sensitivity": 0.5,
            "hyperfocus_tendency": False,
            "notification_style": "gentle",
            "visual_complexity": "minimal",
        },
        "mcp_servers": {
            "test-server": {
                "enabled": True,
                "command": "python",
                "args": ["test.py"],
                "env": {},
                "timeout": 30,
                "auto_restart": True,
            }
        },
        "attention": {
            "enabled": True,
            "sample_interval": 5,
            "keystroke_threshold": 2.0,
            "context_switch_threshold": 3,
            "adaptation_enabled": True,
        },
        "context": {
            "enabled": True,
            "auto_save_interval": 30,
            "max_sessions": 50,
            "compression": True,
            "backup_enabled": True,
        },
    }


@pytest.fixture
def config_manager(temp_config_dir, sample_config_data):
    """Create a ConfigManager instance for testing."""
    config_file = temp_config_dir / "config.yaml"

    with patch("dopemux.config.manager.ConfigManager._init_paths") as mock_init_paths:
        from dopemux.config.manager import ConfigPaths

        mock_init_paths.return_value = ConfigPaths(
            global_config=temp_config_dir / "global.yaml",
            user_config=config_file,
            project_config=temp_config_dir / "project.yaml",
            cache_dir=temp_config_dir / "cache",
            data_dir=temp_config_dir / "data",
        )

        manager = ConfigManager()
        # Mock the default config
        with patch.object(
            manager, "_get_default_config", return_value=sample_config_data
        ):
            yield manager


@pytest.fixture
def context_manager(temp_project_dir):
    """Create a ContextManager instance for testing."""
    return ContextManager(temp_project_dir)


@pytest.fixture
def attention_monitor(temp_project_dir):
    """Create an AttentionMonitor instance for testing."""
    return AttentionMonitor(temp_project_dir)


@pytest.fixture
def task_decomposer(temp_project_dir):
    """Create a TaskDecomposer instance for testing."""
    return TaskDecomposer(temp_project_dir)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls."""
    with patch("subprocess.run") as mock_run:
        # Default successful git commands
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\n"
        yield mock_run


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    with patch("dopemux.adhd.context_manager.datetime") as mock_dt:
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        yield mock_dt


@pytest.fixture
def sample_context_data():
    """Sample context data for testing."""
    return {
        "session_id": "test-session-123",
        "timestamp": "2024-01-01T12:00:00",
        "working_directory": "/test/project",
        "open_files": [
            {
                "path": "src/main.py",
                "absolute_path": "/test/project/src/main.py",
                "last_modified": "2024-01-01T11:30:00",
                "cursor_position": {"line": 10, "column": 5},
                "scroll_position": 0,
                "unsaved_changes": False,
            }
        ],
        "current_goal": "Implement feature X",
        "mental_model": {
            "approach": "Using pattern Y",
            "next_steps": ["Step 1", "Step 2"],
            "blockers": [],
        },
        "git_state": {
            "branch": "feature-branch",
            "status": "",
            "has_changes": False,
            "last_commit": "abc123 Last commit message",
        },
        "recent_commands": ["git status", "python test.py"],
        "decisions": [
            {
                "timestamp": "2024-01-01T11:45:00",
                "decision": "Use approach A over B",
                "rationale": "Better performance",
            }
        ],
        "attention_state": "focused",
        "focus_duration": 25,
        "context_switches": 2,
        "unsaved_changes": False,
        "message": "Working on feature implementation",
    }


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "EXA_API_KEY": "test-exa-key",
    }

    with patch.dict("os.environ", env_vars):
        yield env_vars
