
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add services/dope-context/src/utils to python path to import workspace directly
sys.path.insert(0, str(Path.cwd() / "services/dope-context/src/utils"))

def test_get_workspace_root_dynamic_fallback():
    # Force ModuleNotFoundError for src.dopemux.workspace_detection
    with patch.dict(sys.modules, {'src.dopemux.workspace_detection': None}):
        # We need to import workspace module.
        # Since we added utils to path, we can import it as 'workspace'
        import workspace

        # Now mock the environment and path existence
        with patch("os.getenv") as mock_getenv, \
             patch("pathlib.Path.exists") as mock_exists:

            def getenv_side_effect(key, default=None):
                if key == "HOST_PROJECT_RELATIVE_PATH":
                    return "dopemux-mvp"
                if key == "DOPEMUX_WORKSPACE_ROOT":
                    return None
                return default

            mock_getenv.side_effect = getenv_side_effect
            mock_exists.return_value = True

            result = workspace._get_workspace_root()

            assert str(result) == "/workspaces/dopemux-mvp"

if __name__ == "__main__":
    pytest.main([__file__])
