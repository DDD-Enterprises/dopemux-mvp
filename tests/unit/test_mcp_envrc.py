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


def test_secret_like_redaction():
    assert is_secret_like_key("OPENAI_API_KEY") is True
    assert is_secret_like_key("CONPORT_MCP_PORT") is False
    assert is_secret_like_key("DOPEMUX_WORKSPACE_ID") is False
    assert redact_value("OPENAI_API_KEY", "sk-secret") == "[REDACTED]"
    assert redact_value("CONPORT_MCP_PORT", "3041") == "3041"
    assert redact_value("DB_URL", "postgres://user:pass@host/db") == "[REDACTED_URL_WITH_CREDENTIALS]"


def test_redact_value_localhost_urls_kept():
    assert (
        redact_value("URL", "http://localhost:3041/sse") == "http://localhost:3041/sse"
    )
    assert (
        redact_value("URL", "http://127.0.0.1:3020/mcp") == "http://127.0.0.1:3020/mcp"
    )


def test_redact_value_non_localhost_host_redacted():
    redacted = redact_value("URL", "https://mcp.example.com:8443/sse?x=1")
    assert redacted.startswith("https://[REDACTED_HOST]:8443")
    assert "example.com" not in redacted
    assert redacted.endswith("/sse?x=1")


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


def test_load_envrc_partial_on_malformed_with_keys(tmp_path: Path):
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text("not a valid line\nexport CONPORT_MCP_PORT=3041\nexport OK=1\n")
    result = load_envrc(path)
    assert result.present is True
    assert result.parse_status == "PARTIAL"
    assert result.values["CONPORT_MCP_PORT"] == "3041"
    assert result.values["OK"] == "1"
    assert any("malformed" in e for e in result.errors)
    merged = merge_envrc_into_environ({}, result)
    assert merged["CONPORT_MCP_PORT"] == "3041"


def test_load_envrc_error_when_no_usable_keys(tmp_path: Path):
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text("this is garbage\nalso bad\n")
    result = load_envrc(path)
    assert result.present is True
    assert result.parse_status == "ERROR"
    assert result.values == {}


def test_merge_envrc_into_environ_override(tmp_path: Path):
    path = tmp_path / ".envrc.dopemux-mcp"
    path.write_text("export CONPORT_MCP_PORT=3041\n")
    parsed = load_envrc(path)
    merged = merge_envrc_into_environ({"CONPORT_MCP_PORT": "3005", "OTHER": "x"}, parsed)
    assert merged["CONPORT_MCP_PORT"] == "3041"
    assert merged["OTHER"] == "x"
