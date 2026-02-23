import sys
import os
from unittest.mock import MagicMock, patch
import unittest
import asyncio

# Add the server directory to sys.path
server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docker/mcp-servers/desktop-commander"))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

class TestDesktopCommanderSecurity(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def test_type_text_macos_security(self):
        with patch.dict(sys.modules, {
            "uvicorn": MagicMock(),
            "fastapi": MagicMock(),
            "pydantic": MagicMock()
        }):
            import server
            with patch.object(server, "IS_MACOS", True), \
                 patch("server.subprocess.run") as mock_run:

                mock_run.return_value = MagicMock(returncode=0, stdout="")

                malicious_input = '"; do shell script "rm -rf /"; --'
                self.run_async(server.type_text(malicious_input))

                args, _ = mock_run.call_args
                cmd_list = args[0]

                applescript = cmd_list[2]
                self.assertNotIn(malicious_input, applescript)
                self.assertEqual(cmd_list[3], malicious_input)

    def test_focus_window_macos_security(self):
        with patch.dict(sys.modules, {
            "uvicorn": MagicMock(),
            "fastapi": MagicMock(),
            "pydantic": MagicMock()
        }):
            import server
            with patch.object(server, "IS_MACOS", True), \
                 patch("server.subprocess.run") as mock_run:

                mock_run.return_value = MagicMock(returncode=0, stdout="")

                malicious_input = 'Finder"; do shell script "rm -rf /"; --'
                self.run_async(server.focus_window(malicious_input))

                # The first call is Attempt 1
                args, _ = mock_run.call_args_list[0]
                cmd_list = args[0]

                applescript = cmd_list[2]
                self.assertNotIn(malicious_input, applescript)
                self.assertEqual(cmd_list[3], malicious_input)

    def test_type_text_linux_argument_injection(self):
        with patch.dict(sys.modules, {
            "uvicorn": MagicMock(),
            "fastapi": MagicMock(),
            "pydantic": MagicMock()
        }):
            import server
            with patch.object(server, "IS_MACOS", False), \
                 patch("server.subprocess.run") as mock_run:

                mock_run.return_value = MagicMock(returncode=0, stdout="")

                input_with_dash = "--help"
                self.run_async(server.type_text(input_with_dash))

                args, _ = mock_run.call_args
                cmd_list = args[0]

                self.assertEqual(cmd_list, ["xdotool", "type", "--", "--help"])

    def test_take_screenshot_linux_argument_injection(self):
        with patch.dict(sys.modules, {
            "uvicorn": MagicMock(),
            "fastapi": MagicMock(),
            "pydantic": MagicMock()
        }):
            import server
            with patch.object(server, "IS_MACOS", False), \
                 patch("server.subprocess.run") as mock_run:

                mock_run.return_value = MagicMock(returncode=0, stdout="")

                input_with_dash = "-h"
                self.run_async(server.take_screenshot(input_with_dash))

                args, _ = mock_run.call_args
                cmd_list = args[0]

                self.assertEqual(cmd_list, ["scrot", "--", "-h"])

if __name__ == "__main__":
    unittest.main()
