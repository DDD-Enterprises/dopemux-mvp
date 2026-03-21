from unittest.mock import MagicMock
import sys

# Mock missing dependencies
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import importlib

# Note: dependency modules are mocked within individual tests using patch.dict
# to avoid mutating sys.modules at import time.


def test_quote_identifier():
    with patch.dict(
        sys.modules,
        {
            "markdown_patterns": MagicMock(),
            "yaml_extractor": MagicMock(),
            "extraction.markdown_patterns": MagicMock(),
            "extraction.yaml_extractor": MagicMock(),
        },
    ):
        import extraction.document_classifier as document_classifier

        importlib.reload(document_classifier)
        classifier = document_classifier.DocumentClassifier()

        # Simple name
        assert classifier._quote_identifier("users") == '"users"'

        # Name with spaces
        assert classifier._quote_identifier("user profiles") == '"user profiles"'

        # Name with double quotes (the injection vector)
        assert (
            classifier._quote_identifier('users"; DROP TABLE secrets; --')
            == '"users""; DROP TABLE secrets; --"'
        )

        # Name with already doubled quotes
        assert classifier._quote_identifier('my""table') == '"my""""table"'

        # Reserved words
        assert classifier._quote_identifier("select") == '"select"'


def test_quote_identifier_extreme():
    with patch.dict(
        sys.modules,
        {
            "markdown_patterns": MagicMock(),
            "yaml_extractor": MagicMock(),
            "extraction.markdown_patterns": MagicMock(),
            "extraction.yaml_extractor": MagicMock(),
        },
    ):
        import extraction.document_classifier as document_classifier

        importlib.reload(document_classifier)
        classifier = document_classifier.DocumentClassifier()

        # Empty string
        assert classifier._quote_identifier("") == '""'

        # Only quotes
        assert classifier._quote_identifier('"""') == '""""""""'

        # Unicode
        assert classifier._quote_identifier("τάμπλα") == '"τάμπλα"'
        print("Manual security tests passed!")
    except AssertionError as e:
        print(f"Manual security tests failed: {e}")
        sys.exit(1)
