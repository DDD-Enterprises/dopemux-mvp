import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
WMA_DIR = REPO_ROOT / "services" / "working-memory-assistant"


def _load_wma_module(module_name: str):
    if str(WMA_DIR) not in sys.path:
        sys.path.insert(0, str(WMA_DIR))
    spec = importlib.util.spec_from_file_location(
        module_name,
        WMA_DIR / f"{module_name}.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wma_rejects_missing_secret_in_production(monkeypatch):
    security_config = _load_wma_module("security_config")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("WMA_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="WMA_SECRET_KEY"):
        security_config.resolve_secret("WMA_SECRET_KEY")


def test_wma_rejects_weak_secret_in_production(monkeypatch):
    security_config = _load_wma_module("security_config")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("WMA_SECRET_KEY", "dev-only-change-me")

    with pytest.raises(RuntimeError, match="WMA_SECRET_KEY"):
        security_config.resolve_secret("WMA_SECRET_KEY")


def test_wma_generates_ephemeral_secret_only_in_development(monkeypatch):
    security_config = _load_wma_module("security_config")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("WMA_SECRET_KEY", "dev-only-change-me")

    resolved = security_config.resolve_secret(
        "WMA_SECRET_KEY",
        allow_ephemeral_dev=True,
        generator=lambda: "generated-local-secret",
    )

    assert resolved == "generated-local-secret"


def test_wma_adhd_client_does_not_default_to_weak_api_key(monkeypatch):
    monkeypatch.delenv("ADHD_ENGINE_API_KEY", raising=False)
    adhd_engine_client = _load_wma_module("adhd_engine_client")

    client = adhd_engine_client.ADHDEngineClient(base_url="http://adhd-engine:8095")
    try:
        assert client.api_key == ""
        assert "X-API-Key" not in client.client.headers
        assert "Authorization" not in client.client.headers
    finally:
        asyncio.run(client.client.aclose())


def test_wma_adhd_client_sends_explicit_api_key_header(monkeypatch):
    monkeypatch.setenv("ADHD_ENGINE_API_KEY", "expected-key")
    adhd_engine_client = _load_wma_module("adhd_engine_client")

    client = adhd_engine_client.ADHDEngineClient(base_url="http://adhd-engine:8095")
    try:
        assert client.api_key == "expected-key"
        assert client.client.headers["X-API-Key"] == "expected-key"
    finally:
        asyncio.run(client.client.aclose())


def test_compose_does_not_inject_weak_secret_defaults():
    compose_text = (REPO_ROOT / "compose.yml").read_text(encoding="utf-8")

    forbidden_defaults = [
        "ADHD_ENGINE_API_KEY=${ADHD_ENGINE_API_KEY:-dev-key-123}",
        "WMA_SECRET_KEY=${WMA_SECRET_KEY:-dev-only-change-me}",
        "WMA_ENCRYPTION_KEY=${WMA_ENCRYPTION_KEY:-dev-only-change-me}",
    ]

    for forbidden_default in forbidden_defaults:
        assert forbidden_default not in compose_text
