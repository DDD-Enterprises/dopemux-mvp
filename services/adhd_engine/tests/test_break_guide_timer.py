import pytest
from unittest.mock import patch
from services.adhd_engine.cli.break_guide import _timer

@patch("subprocess.run")
@patch("services.adhd_engine.cli.break_guide.time.sleep")
@patch("services.adhd_engine.cli.break_guide.console.print")
def test_timer_plays_sound(mock_print, mock_sleep, mock_subprocess_run):
    _timer(0, "Test Break")
    # subprocess.run is called twice: once for _notify, once for playing sound
    # Let's just check that it's called with afplay
    mock_subprocess_run.assert_any_call(['afplay', '/System/Library/Sounds/Glass.aiff'], check=False)
