import json
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PAL = ROOT / "docker/mcp-servers-source/pal/pal-mcp-server"
RUNTIME_PAL = ROOT / "docker/mcp-servers/pal/pal-mcp-server"


def _models(pal_root: Path, provider: str) -> list[dict]:
    path = pal_root / "conf" / f"{provider}_models.json"
    return json.loads(path.read_text())["models"]


def test_current_xai_catalog_replaces_retired_models():
    models = _models(SOURCE_PAL, "xai")

    assert [model["model_name"] for model in models] == ["grok-4.5"]
    assert set(models[0]["aliases"]) == {
        "grok",
        "grok4.5",
        "grok-4.5-latest",
        "grok-build-latest",
    }
    assert models[0]["context_window"] == 500_000
    assert models[0]["use_openai_response_api"] is True


def test_current_openai_catalog_includes_gpt_5_6_family():
    models = {model["model_name"]: model for model in _models(SOURCE_PAL, "openai")}

    assert {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"} <= models.keys()
    for model_name in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        model = models[model_name]
        assert model["context_window"] == 1_050_000
        assert model["max_output_tokens"] == 128_000
        assert model["use_openai_response_api"] is True

    assert {"gpt-5.6", "sol"} <= set(models["gpt-5.6-sol"]["aliases"])


def test_pal_openai_dependency_supports_responses_api():
    assert "openai>=1.66.0" in (SOURCE_PAL / "requirements.txt").read_text()
    with (SOURCE_PAL / "pyproject.toml").open("rb") as project_file:
        dependencies = tomllib.load(project_file)["project"]["dependencies"]
    assert "openai>=1.66.0" in dependencies


def test_pal_source_and_runtime_model_surfaces_match():
    relative_paths = (
        "conf/openai_models.json",
        "conf/xai_models.json",
        "providers/openai.py",
        "providers/openai_compatible.py",
        "providers/xai.py",
        "pyproject.toml",
        "requirements.txt",
        "tests/test_openai_provider.py",
        "tests/test_xai_provider.py",
    )

    for relative_path in relative_paths:
        assert (SOURCE_PAL / relative_path).read_bytes() == (
            RUNTIME_PAL / relative_path
        ).read_bytes(), relative_path


def test_pal_services_receive_xai_api_key():
    services = yaml.safe_load((ROOT / "compose.yml").read_text())["services"]

    for service_name in ("pal", "pal-stdio"):
        environment = services[service_name]["environment"]
        assert "XAI_API_KEY=${XAI_API_KEY}" in environment


def test_pal_builds_use_canonical_non_symlink_source_paths():
    services = yaml.safe_load((ROOT / "compose.yml").read_text())["services"]
    pal_build = services["pal"]["build"]

    assert pal_build == {
        "context": "docker/mcp-servers-source/pal",
        "dockerfile": "Dockerfile",
    }
    assert not (ROOT / pal_build["context"]).is_symlink()

    dockerignore = (
        (ROOT / pal_build["context"] / ".dockerignore").read_text().splitlines()
    )
    for sensitive_pattern in (
        ".env",
        ".env.local",
        ".venv/",
        "logs/*.log*",
        "*.key",
        "*.pem",
    ):
        assert sensitive_pattern in dockerignore

    assert services["pal-stdio"]["build"] == {
        "context": ".",
        "dockerfile": "docker/mcp-servers-source/pal-stdio/Dockerfile",
    }
    dockerfile = (ROOT / services["pal-stdio"]["build"]["dockerfile"]).read_text()
    assert "COPY docker/mcp-servers-source/pal/pal-mcp-server/ ." in dockerfile
    assert "COPY docker/mcp-servers/pal/" not in dockerfile
