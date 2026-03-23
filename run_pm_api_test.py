import sys
from unittest.mock import MagicMock
sys.modules['pydantic'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['redis.asyncio'] = MagicMock()
sys.modules['aiohttp'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['toml'] = MagicMock()

import pytest
pytest.main(['-q', 'tests/test_pm_api.py'])
