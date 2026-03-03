import sys
import importlib
import pytest
import warnings
from unittest.mock import patch, MagicMock

# Helper to unload modules
def unload_modules():
    if "dopemux.utils.dotenv_loader" in sys.modules:
        del sys.modules["dopemux.utils.dotenv_loader"]
    if "dotenv" in sys.modules:
        del sys.modules["dotenv"]

class TestDotenvLoader:

    def teardown_method(self):
        unload_modules()

    def test_dotenv_available(self):
        """Test behavior when python-dotenv is available."""
        unload_modules()

        # Mock dotenv module being present
        mock_dotenv = MagicMock()
        mock_dotenv.load_dotenv.return_value = True

        with patch.dict(sys.modules, {"dotenv": mock_dotenv}):
            # Ensure we import/reload while the mock is in place
            import dopemux.utils.dotenv_loader
            importlib.reload(dopemux.utils.dotenv_loader)
            from dopemux.utils import dotenv_loader

            assert dotenv_loader.is_dotenv_available() is True
            assert dotenv_loader.load_dotenv() is True
            mock_dotenv.load_dotenv.assert_called_once()

            # check_dotenv_support should not warn
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                dotenv_loader.check_dotenv_support()
                # Filter out irrelevant warnings if any
                relevant = [w for w in record if "python-dotenv not installed" in str(w.message)]
                assert len(relevant) == 0

    def test_dotenv_unavailable(self):
        """Test behavior when python-dotenv is missing."""
        unload_modules()

        # Simulate ImportError when importing dotenv
        # We need to ensure 'dotenv' is NOT in sys.modules and import raises ImportError

        with patch.dict(sys.modules):
            if "dotenv" in sys.modules:
                del sys.modules["dotenv"]

            # We use a custom finder that raises ImportError for 'dotenv'
            class ImportBlocker:
                def find_spec(self, fullname, path, target=None):
                    if fullname == "dotenv":
                        raise ImportError("No module named 'dotenv'")
                    return None

            sys.meta_path.insert(0, ImportBlocker())
            try:
                # Ensure we import/reload while the blocker is in place
                import dopemux.utils.dotenv_loader
                importlib.reload(dopemux.utils.dotenv_loader)
                from dopemux.utils import dotenv_loader

                assert dotenv_loader.is_dotenv_available() is False
                assert dotenv_loader.load_dotenv() is False

                # check_dotenv_support should warn
                with pytest.warns(RuntimeWarning, match="python-dotenv not installed"):
                    dotenv_loader.check_dotenv_support()
            finally:
                sys.meta_path.pop(0)
