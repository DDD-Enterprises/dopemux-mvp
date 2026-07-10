"""Unit tests for dopemux.mcp.envrc (read-only parser + redaction)."""

from __future__ import annotations

from pathlib import Path

from dopemux.mcp.envrc import (
    is_secret_like_key,
    load_envrc,
    merge_envrc_into_environ,
    parse_envrc_text,
    redact_value,
    redacted_snapshot,
    safe_port_int,
)


def test_parse_simple_key_value():
    values, errors = parse_envrc_text("FOO=bar\n")
    assert errors == []
    assert values["FOO"] == "bar"


def test_parse_export_key_value():
    values, errors = parse_envrc_text("export CONPORT_MCP_PORT=3041\n")
    assert errors == []
    assert values["CONPORT_MCP_PORT"] == "3041"


def test_parse_comments_and_blank_lines():
    text = """
# comment
export A=1

# another
B=2
"""
    values, errors = parse_envrc_text(text)
    assert errors == []
    assert values == {"A": "1", "B": "2"}


def test_parse_quoted_values():
    values, errors = parse_envrc_text(
        "export PATH_VAL='/Users/hue/code/x'\nexport Q=\"hello world\"\n"
    )
    assert errors == []
    assert values["PATH_VAL"] == "/Users/hue/code/x"
    assert values["Q"] == "hello world"


def test_parse_numeric_ports():
    values, errors = parse_envrc_text("export CONPORT_MCP_PORT=3041\n")
    assert errors == []
    assert safe_port_int(values, "CONPORT_MCP_PORT") == 3041


def test_parse_malformed_line():
    values, errors = parse_envrc_text("not a valid line\nexport OK=1\n")
    assert values["OK"] == "1"
    assert any("malformed" in e for e in errors)


def test_load_envrc_partial_keeps_values(tmp_path: Path):
    """Malformed lines must not hard-fail when keys loaded (parse_status OK)."""
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text(
        "not a valid line\n"
        "export CONPORT_MCP_PORT=3041\n"
        "export DOPEMUX_INSTANCE_ID=abcd\n"
        "also bad\n"
    )
    result = load_envrc(path)
    assert result.present is True
    assert result.parse_status == "OK"
    assert result.values["CONPORT_MCP_PORT"] == "3041"
    assert result.values["DOPEMUX_INSTANCE_ID"] == "abcd"
    assert len(result.errors) >= 2
    merged = merge_envrc_into_environ({}, result)
    assert merged["CONPORT_MCP_PORT"] == "3041"


def test_secret_like_redaction():
    assert is_secret_like_key("OPENAI_API_KEY") is True
    assert is_secret_like_key("CONPORT_MCP_PORT") is False
    assert is_secret_like_key("DOPEMUX_WORKSPACE_ID") is False
    assert redact_value("OPENAI_API_KEY", "sk-secret") == "[REDACTED]"
    assert redact_value("CONPORT_MCP_PORT", "3041") == "3041"
    assert redact_value("DB_URL", "postgres://user:pass@host/db") == "[REDACTED_URL_WITH_CREDENTIALS]"
    assert redact_value("URL", "http://localhost:3041/sse") == "http://localhost:3041/sse"
    assert redact_value("URL", "http://127.0.0.1:3041/sse") == "http://127.0.0.1:3041/sse"
    assert redact_value("URL", "https://internal.example.com/mcp") == "[REDACTED_URL]"


def test_load_envrc_missing(tmp_path: Path):
    result = load_envrc(tmp_path / ".envrc.dopemux-mcp")
    assert result.present is False
    assert result.parse_status == "MISSING"
    assert result.to_report_dict()["redacted"] is True


def test_load_envrc_ok(tmp_path: Path):
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text(
        "# header\nexport DOPEMUX_INSTANCE_ID=8d6d\nexport CONPORT_MCP_PORT=3041\n"
        "export OPENAI_API_KEY=sk-test\n"
    )
    result = load_envrc(path)
    assert result.present is True
    assert result.parse_status == "OK"
    assert "CONPORT_MCP_PORT" in result.keys_present
    assert result.values["OPENAI_API_KEY"] == "sk-test"  # internal values kept
    snap = redacted_snapshot(result.values)
    assert snap["OPENAI_API_KEY"] == "[REDACTED]"
    assert snap["CONPORT_MCP_PORT"] == "3041"


def test_load_envrc_partial_parse_is_ok(tmp_path: Path):
    """Useful keys + one malformed line must not hard-fail doctor (parse_status OK)."""
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text(
        "export CONPORT_MCP_PORT=3041\n"
        "not a valid line\n"
        "export DOPEMUX_INSTANCE_ID=abcd\n"
    )
    result = load_envrc(path)
    assert result.present is True
    assert result.parse_status == "OK"
    assert result.values["CONPORT_MCP_PORT"] == "3041"
    assert result.values["DOPEMUX_INSTANCE_ID"] == "abcd"
    assert any("malformed" in e for e in result.errors)


def test_load_envrc_only_malformed_is_error(tmp_path: Path):
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text("garbage line\nanother bad\n")
    result = load_envrc(path)
    assert result.present is True
    assert result.parse_status == "ERROR"
    assert result.values == {}
    assert result.errors


def test_merge_envrc_into_environ_override(tmp_path: Path):
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text("export CONPORT_MCP_PORT=3041\n")
    parsed = load_envrc(path)
    merged = merge_envrc_into_environ({"CONPORT_MCP_PORT": "3005", "OTHER": "x"}, parsed)
    assert merged["CONPORT_MCP_PORT"] == "3041"
    assert merged["OTHER"] == "x"


def test_repair_envrc_regeneration_keys(tmp_path: Path):
    """Envrc repair path produces catalog-owned port keys without secrets."""
    from dopemux.mcp.config_repair import _build_envrc_text

    text = _build_envrc_text(
        "/tmp/wt",
        "/tmp/proj",
        {
            "DOPEMUX_WORKSPACE_ID": "/tmp/wt",
            "DOPEMUX_PROJECT_ROOT": "/tmp/proj",
            "DOPEMUX_INSTANCE_ID": "abcd",
            "CONPORT_MCP_PORT": "3015",
            "DOPE_MEMORY_PORT": "3030",
            "CUSTOM_SAFE": "keep-me",
        },
        preserve_values={"CUSTOM_SAFE": "keep-me", "OPENAI_API_KEY": "sk-x"},
    )
    assert "export CONPORT_MCP_PORT=3015" in text
    assert "export CUSTOM_SAFE=keep-me" in text
    assert "OPENAI_API_KEY" not in text
    assert "sk-x" not in text
