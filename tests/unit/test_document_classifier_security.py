try:
    import pytest
except ImportError:
    pytest = None
from pathlib import Path

from extraction.document_classifier import DocumentClassifier

def test_quote_identifier():
    classifier = DocumentClassifier()

    # Simple name
    assert classifier._quote_identifier("users") == '"users"'

    # Name with spaces
    assert classifier._quote_identifier("user profiles") == '"user profiles"'

    # Name with double quotes (the injection vector)
    assert classifier._quote_identifier('users"; DROP TABLE secrets; --') == '"users""; DROP TABLE secrets; --"'

    # Name with already doubled quotes
    assert classifier._quote_identifier('my""table') == '"my""""table"'

    # Reserved words
    assert classifier._quote_identifier("select") == '"select"'

def test_quote_identifier_extreme():
    classifier = DocumentClassifier()

    # Empty string
    assert classifier._quote_identifier("") == '""'

    # Only quotes
    assert classifier._quote_identifier('"""') == '""""""""'

    # Unicode
    assert classifier._quote_identifier('τάμπλα') == '"τάμπλα"'

if __name__ == "__main__":
    # Run tests manually if pytest is not available or having issues
    try:
        test_quote_identifier()
        test_quote_identifier_extreme()
        print("Manual security tests passed!")
    except AssertionError as e:
        print(f"Manual security tests failed: {e}")
        sys.exit(1)
