"""
Tests for the main server functionality
"""

import json

import pytest

import server



class TestServerTools:
    """Test server tool handling"""

    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown(self):
        """Test calling an unknown tool"""
        result = await server.handle_call_tool("unknown_tool", {})
        assert len(result) == 1
        assert "Unknown tool: unknown_tool" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_chat(self):
        """Test chat functionality using real integration testing"""
        import importlib
        import os

        # Set test environment
        os.environ["PYTEST_CURRENT_TEST"] = "test"

        # Save original environment
        original_env = {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "DEFAULT_MODEL": os.environ.get("DEFAULT_MODEL"),
        }

        try:
            # Set up environment for real provider resolution
            os.environ["OPENAI_API_KEY"] = "sk-test-key-server-chat-test-not-real"
            os.environ["DEFAULT_MODEL"] = "o3-mini"

            # Clear other provider keys to isolate to OpenAI
            for key in ["GEMINI_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY"]:
                os.environ.pop(key, None)

            # Reload config and clear registry
            import config

            importlib.reload(config)
            from providers.registry import ModelProviderRegistry

            ModelProviderRegistry._instance = None

            # Test with real provider resolution
            try:
                result = await handle_call_tool("chat", {"prompt": "Hello Gemini", "model": "o3-mini"})

                # If we get here, check the response format
                assert len(result) == 1
                # Parse JSON response
                import json

                response_data = json.loads(result[0].text)
                assert "status" in response_data

            except Exception as e:
                # Expected: API call will fail with fake key
                error_msg = str(e)
                # Should NOT be a mock-related error
                assert "MagicMock" not in error_msg
                assert "'<' not supported between instances" not in error_msg

                # Should be a real provider error
                assert any(
                    phrase in error_msg
                    for phrase in ["API", "key", "authentication", "provider", "network", "connection"]
                )

        finally:
            # Restore environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

            # Reload config and clear registry
            importlib.reload(config)
            ModelProviderRegistry._instance = None

    @pytest.mark.asyncio
    async def test_handle_version(self):
        """Test getting version info"""
        result = await server.handle_call_tool("version", {})
        assert len(result) == 1

        response = result[0].text
        # Parse the JSON response
        import json

        data = json.loads(response)
        assert data["status"] == "success"
        content = data["content"]

        # Check for expected content in the markdown output
        assert "# Zen MCP Server Version" in content
        assert "## Server Information" in content
        assert "## Configuration" in content
        assert "Current Version" in content

    @pytest.mark.asyncio
    async def test_handle_call_tool_writes_structured_activity_events(self, monkeypatch, tmp_path):
        class FakeTool:
            name = "fake"

            def requires_model(self):
                return False

            async def execute(self, arguments):
                payload = {
                    "status": "success",
                    "content": "ok",
                    "metadata": {
                        "request_id": "req_123",
                        "input_tokens": 11,
                        "output_tokens": 7,
                    },
                }
                return [server.TextContent(type="text", text=json.dumps(payload))]

        activity_path = tmp_path / "mcp_activity.jsonl"
        monkeypatch.setattr(server, "_activity_jsonl_path", lambda: activity_path)
        monkeypatch.setitem(server.TOOLS, "fake", FakeTool())

        result = await server.handle_call_tool(
            "fake",
            {"trace_id": "trace_abc", "prompt": "hello"},
        )

        assert len(result) == 1
        rows = [
            json.loads(line)
            for line in activity_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        event_types = {row["event_type"] for row in rows}
        assert "tool_call_started" in event_types
        assert "tool_context_resolved" in event_types
        assert "tool_completed" in event_types
        for row in rows:
            assert row["trace_id"] == "trace_abc"

    def test_extract_trace_id_uses_continuation_id_when_not_provided(self):
        trace_a = server._extract_trace_id({"continuation_id": "thread-42"})
        trace_b = server._extract_trace_id({"continuation_id": "thread-42"})
        trace_c = server._extract_trace_id({"continuation_id": "thread-43"})

        assert trace_a == trace_b
        assert trace_a != trace_c
