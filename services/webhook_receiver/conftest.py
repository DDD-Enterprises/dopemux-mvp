"""Pytest configuration for webhook_receiver service tests."""

def pytest_configure(config):
    """Configure coverage to exclude src/dopemux for service tests."""
    # Service tests should only measure coverage of services/webhook_receiver
    # not the entire src/dopemux package
    config.option.cov_source = ["services/webhook_receiver"]
    config.option.cov_report = ["term-missing", "html"]
