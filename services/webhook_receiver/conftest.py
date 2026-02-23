"""Pytest configuration for webhook_receiver service tests."""

def pytest_configure(config):
    """Configure coverage to exclude src/dopemux for service tests.

    Coverage options should be configured via pytest.ini or pyproject.toml
    rather than by mutating config.option at runtime. This hook is retained
    for backwards compatibility but intentionally left as a no-op to avoid
    fragile interactions with pytest-cov.
    """
    # Coverage configuration is handled by pytest configuration files.
    return
