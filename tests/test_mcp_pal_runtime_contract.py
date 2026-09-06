from pathlib import Path

import tomllib
import yaml


ROOT = Path(__file__).resolve().parents[1]
PAL_ROOT = ROOT / "docker/mcp-servers-source/pal"
PAL_SOURCE = PAL_ROOT / "pal-mcp-server"


def test_compose_litellm_build_uses_tracked_source_dockerfile() -> None:
    compose = yaml.safe_load((ROOT / "compose.yml").read_text(encoding="utf-8"))

    build = compose["services"]["litellm"]["build"]

    assert build["context"] == "."
    assert build["dockerfile"] == "docker/mcp-servers-source/litellm/Dockerfile"
    assert (ROOT / build["dockerfile"]).is_file()


def test_pal_http_and_stdio_images_share_canonical_source_tree() -> None:
    http_dockerfile = (PAL_ROOT / "Dockerfile").read_text(encoding="utf-8")
    stdio_dockerfile = (
        ROOT / "docker/mcp-servers-source/pal-stdio/Dockerfile"
    ).read_text(encoding="utf-8")

    assert "COPY pal-mcp-server/ ." in http_dockerfile
    assert (
        "COPY docker/mcp-servers-source/pal/pal-mcp-server/ ."
        in stdio_dockerfile
    )
    assert "COPY docker/mcp-servers-source/pal-stdio/pal-mcp-server/" not in stdio_dockerfile


def test_pal_source_is_pinned_to_verified_upstream_version() -> None:
    project = tomllib.loads((PAL_SOURCE / "pyproject.toml").read_text(encoding="utf-8"))
    config_text = (PAL_SOURCE / "config.py").read_text(encoding="utf-8")

    assert project["project"]["version"] == "9.8.2"
    assert '__version__ = "9.8.2"' in config_text


def test_canonical_pal_image_preserves_codex_opt_venv_compatibility() -> None:
    dockerfile = (PAL_ROOT / "Dockerfile").read_text(encoding="utf-8")
    ensure_script = (ROOT / "scripts/mcp-wrappers/ensure-pal.sh").read_text(
        encoding="utf-8"
    )

    assert "/opt/venv" in dockerfile
    assert "/app/.venv" in dockerfile
    assert "docker/mcp-servers-source/pal" in ensure_script
    assert "docker build" in ensure_script


def test_pal_http_wrapper_keeps_local_health_endpoint() -> None:
    wrapper = (PAL_ROOT / "pal_http_wrapper.py").read_text(encoding="utf-8")

    assert "'/health'" in wrapper or '"/health"' in wrapper
    assert "mcp_process.poll()" in wrapper


def test_pal_services_select_generated_direct_ci_manifest() -> None:
    compose = yaml.safe_load((ROOT / "compose.yml").read_text(encoding="utf-8"))

    for service_name in ("pal", "pal-stdio"):
        environment = compose["services"][service_name]["environment"]
        assert (
            "CUSTOM_MODELS_CONFIG_PATH=/app/conf/custom_models.direct-ci.json"
            in environment
        )
