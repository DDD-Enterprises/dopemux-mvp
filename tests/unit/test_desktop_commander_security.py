import asyncio
import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


server_dir = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../docker/mcp-servers/desktop-commander",
    )
)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)


def _import_server_module():
    sys.modules.pop("server", None)
    fastmcp_module = MagicMock()
    fastmcp_module.FastMCP.return_value.tool.side_effect = lambda: (lambda func: func)
    with patch.dict(
        sys.modules,
        {
            "uvicorn": MagicMock(),
            "fastapi": MagicMock(),
            "pydantic": MagicMock(),
            "fastmcp": fastmcp_module,
        },
    ):
        return importlib.import_module("server")


class TestDesktopCommanderSecurity(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def test_type_text_macos_security(self):
        server = _import_server_module()
        with patch.object(server, "IS_MACOS", True), patch.object(
            server.subprocess, "run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            malicious_input = '"; do shell script "rm -rf /"; --'
            self.run_async(server.type_text(malicious_input))

            args, kwargs = mock_run.call_args
            cmd_list = args[0]

            self.assertEqual(cmd_list[:2], ["osascript", "-e"])
            applescript = cmd_list[2]
            self.assertNotIn(malicious_input, applescript)
            self.assertIn('\\"', applescript)
            self.assertEqual(kwargs["timeout"], 10)

    def test_focus_window_macos_security(self):
        server = _import_server_module()
        with patch.object(server, "IS_MACOS", True), patch.object(
            server.subprocess, "run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            malicious_input = 'Finder"; do shell script "rm -rf /"; --'
            self.run_async(server.focus_window(malicious_input))

            args, kwargs = mock_run.call_args
            cmd_list = args[0]

            self.assertEqual(cmd_list[:2], ["osascript", "-e"])
            applescript = cmd_list[2]
            self.assertNotIn(malicious_input, applescript)
            self.assertIn("tell application (item 1 of argv) to activate", applescript)
            self.assertEqual(cmd_list[3], malicious_input)
            self.assertEqual(kwargs["timeout"], 5)

    def test_type_text_linux_argument_injection(self):
        server = _import_server_module()
        with patch.object(server, "IS_MACOS", False), patch.object(
            server.subprocess, "run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            input_with_dash = "--help"
            self.run_async(server.type_text(input_with_dash))

            args, kwargs = mock_run.call_args
            cmd_list = args[0]

            self.assertEqual(cmd_list, ["xdotool", "type", input_with_dash])
            self.assertEqual(kwargs["timeout"], 10)

    def test_screenshot_linux_argument_passthrough(self):
        server = _import_server_module()
        with patch.object(server, "IS_MACOS", False), patch.object(
            server.subprocess, "run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")

            input_with_dash = "-h"
            self.run_async(server.screenshot(input_with_dash))

            args, kwargs = mock_run.call_args
            cmd_list = args[0]

            self.assertEqual(cmd_list, ["scrot", input_with_dash])
            self.assertEqual(kwargs["timeout"], 10)


if __name__ == "__main__":
    unittest.main()
