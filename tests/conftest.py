"""
Pytest configuration and shared fixtures.
"""

import shutil
import sys
import tempfile
import types
import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Ensure `utils.*` resolves to repo-local package rather than third-party modules.
if "utils" in sys.modules and not hasattr(sys.modules["utils"], "__path__"):
    del sys.modules["utils"]
if "utils" not in sys.modules:
    try:
        sys.modules["utils"] = importlib.import_module("src.utils")
    except Exception:
        pass

# Provide a lightweight pydantic stub when the library is unavailable.
try:
    import pydantic
except ImportError:
    import types
    pydantic_stub = types.ModuleType("pydantic")

    class MockBaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        @classmethod
        def model_validate(cls, obj):
            return cls(**obj)

        def model_dump(self):
            return self.__dict__

    def mock_field(*args, **kwargs):
        return None

    def mock_validator(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

    pydantic_stub.BaseModel = MockBaseModel
    pydantic_stub.Field = mock_field
    pydantic_stub.field_validator = mock_validator
    pydantic_stub.model_validator = mock_validator
    pydantic_stub.ValidationError = Exception
    pydantic_stub.ConfigDict = dict

    sys.modules["pydantic"] = pydantic_stub

# Provide a lightweight yaml stub when the library is unavailable.
try:
    import yaml
except ImportError:
    import types
    yaml_stub = types.ModuleType("yaml")

    def safe_load(stream):
        return {}

    yaml_stub.safe_load = safe_load
    yaml_stub.YAMLError = Exception

    sys.modules["yaml"] = yaml_stub

# Provide a lightweight rich stub when the library is unavailable.
try:
    import rich
except ImportError:
    import types
    rich_stub = types.ModuleType("rich")
    rich_console_stub = types.ModuleType("rich.console")

    class MockConsole:
        def __init__(self, *args, **kwargs): pass
        def print(self, *args, **kwargs): pass
        def status(self, *args, **kwargs):
             class Status:
                 def __enter__(self): return self
                 def __exit__(self, *args): pass
             return Status()

    rich_console_stub.Console = MockConsole
    sys.modules["rich"] = rich_stub
    sys.modules["rich.console"] = rich_console_stub

# Provide a lightweight toml stub when the library is unavailable.
try:
    import toml
except ImportError:
    import types
    toml_stub = types.ModuleType("toml")

    def load(f):
        return {}

    toml_stub.load = load
    sys.modules["toml"] = toml_stub

# Provide a lightweight aiohttp stub when the library is unavailable.
from dopemux.adhd.attention_monitor import AttentionMonitor
from dopemux.adhd.context_manager import ContextManager
from dopemux.adhd.task_decomposer import TaskDecomposer
from dopemux.config.manager import ConfigManager
try:  # pragma: no cover - exercised indirectly during import
    import aiohttp  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover - fallback
    aiohttp_stub = types.ModuleType("aiohttp")
    aiohttp_stub.__dopemux_stub__ = True

    class ClientError(Exception):
        """Base client error placeholder."""

    class ClientResponseError(ClientError):
        """Response error placeholder for compatibility."""

        def __init__(self, request_info=None, history=None, *, status=None, message=None, headers=None):
            super().__init__(message or "Client response error")
            self.status = status
            self.headers = headers or {}

    class ClientTimeout:
        """Minimal timeout configuration stub."""

        def __init__(self, total=None, connect=None, sock_connect=None, sock_read=None):
            self.total = total
            self.connect = connect
            self.sock_connect = sock_connect
            self.sock_read = sock_read

    class TCPConnector:
        """Stub TCP connector."""

        def __init__(self, limit=None, limit_per_host=None):
            self.limit = limit
            self.limit_per_host = limit_per_host

        async def close(self):
            return None

    class _StubResponse:
        """Async context manager mimicking aiohttp responses."""

        def __init__(self, status=503, data=None, text_data=""):
            self.status = status
            self._data = data or {}
            self._text = text_data
            self.headers = {}

        async def __aenter__(self):
            raise ClientError("aiohttp stub cannot perform real HTTP requests")

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def json(self):
            return self._data

        async def text(self):
            return self._text

        def raise_for_status(self):
            raise ClientError("aiohttp stub response")

    class ClientSession:
        """Minimal async session stub that signals missing dependency."""

        def __init__(self, *args, **kwargs):
            self._closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            await self.close()
            return False

        async def close(self):
            self._closed = True

        def _request(self, *args, **kwargs):
            return _StubResponse()

        def get(self, *args, **kwargs):
            return self._request(*args, **kwargs)

        def post(self, *args, **kwargs):
            return self._request(*args, **kwargs)

        def patch(self, *args, **kwargs):
            return self._request(*args, **kwargs)

        def delete(self, *args, **kwargs):
            return self._request(*args, **kwargs)

    aiohttp_stub.ClientError = ClientError
    aiohttp_stub.ClientResponseError = ClientResponseError
    aiohttp_stub.ClientSession = ClientSession
    aiohttp_stub.ClientTimeout = ClientTimeout
    aiohttp_stub.TCPConnector = TCPConnector

    sys.modules["aiohttp"] = aiohttp_stub

# Skip asyncio-marked tests when pytest-asyncio is unavailable.
try:  # pragma: no cover - best effort compatibility
    import pytest_asyncio  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover - fallback

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(item):
        if item.get_closest_marker("asyncio"):
            pytest.skip(
                "pytest-asyncio is not installed in this environment",
                allow_module_level=False,
            )

# Legacy imports - commenting out as these modules have been refactored
# from dopemux.event_bus import RedisStreamsAdapter, InMemoryAdapter
# from dopemux.attention_mediator import AttentionMediator
# from dopemux.instance_registry import InstanceRegistry


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
