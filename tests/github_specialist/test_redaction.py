import pytest
from dopemux_github_specialist.redaction import RedactionPolicy
from dopemux_github_specialist.errors import RedactionError


def test_blocks_aws_key():
    p = RedactionPolicy()
    with pytest.raises(RedactionError):
        p.assert_safe_text("AKIA1234567890ABCDEF")


def test_blocks_private_key():
    p = RedactionPolicy()
    with pytest.raises(RedactionError):
        p.assert_safe_text("-----BEGIN RSA PRIVATE KEY-----")


def test_blocks_password():
    p = RedactionPolicy()
    with pytest.raises(RedactionError):
        p.assert_safe_text("password: mysecretpassword")


def test_allows_safe_text():
    p = RedactionPolicy()
    p.assert_safe_text("This is a safe report about CI failures.")
