from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILES = (
    ROOT / "docker/mcp-servers/gptr-mcp/Dockerfile",
    ROOT / "docker/mcp-servers-source/gptr-mcp/Dockerfile",
)


def _dockerfile_texts() -> list[tuple[Path, str]]:
    return [(path, path.read_text(encoding="utf-8")) for path in DOCKERFILES]


def test_gptr_mcp_dockerfiles_pin_current_gpt_researcher_version() -> None:
    for path, text in _dockerfile_texts():
        assert "ARG GPT_RESEARCHER_VERSION=0.15.1" in text, path


def test_gptr_mcp_dockerfiles_copy_declared_package_trees() -> None:
    for path, text in _dockerfile_texts():
        assert "COPY src/ src/" in text, path
        assert "COPY tools/ tools/" in text, path
        assert "COPY src/dopemux/__init__.py src/dopemux/" not in text, path


def test_gptr_mcp_dockerfiles_provide_legacy_server_entrypoint() -> None:
    for path, text in _dockerfile_texts():
        assert 'cat > /app/server.py <<\'PY\'' in text, path
        assert "import importlib.util" in text, path
        assert 'server_dir = Path("/app/gptr-mcp")' in text, path
        assert 'spec_from_file_location("gptr_mcp_server", server_dir / "server.py")' in text, path
        assert 'os.getenv("DOPEMUX_GPTR_TRANSPORT", "stdio").lower()' in text, path
        assert 'module.mcp.run(transport="stdio")' in text, path
        assert 'DOPEMUX_GPTR_TRANSPORT=sse exec python /app/server.py' in text, path
