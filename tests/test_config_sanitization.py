import json
from pathlib import Path
from dopemux.claude_config import ClaudeConfig

def test_sanitization():
    corrupted = {
        "hooks": {
            "Start": [{"hooks": [{"type": "command", "command": "echo start"}]}],
            "Stop": {"command": "echo stop"},
            "PreToolUse": [{"hooks": [{"type": "command", "command": "echo pre"}]}],
            "command": [
                {"events": ["SessionStart"], "command": "python3 native_hooks.py"}
            ]
        }
    }
    
    settings_path = Path("corrupted_settings.json")
    settings_path.write_text(json.dumps(corrupted))
    
    config_manager = ClaudeConfig(config_path=settings_path)
    config = config_manager.read_config()
    sanitized = config_manager._sanitize_config(config)
    
    print(json.dumps(sanitized, indent=2))
    
    assert "Start" not in sanitized["hooks"]
    assert "Stop" not in sanitized["hooks"]
    assert "PreToolUse" not in sanitized["hooks"]
    assert len(sanitized["hooks"]["command"]) >= 3
    
    # Check migration
    commands = [h["command"] for h in sanitized["hooks"]["command"]]
    assert "echo start" in commands
    assert "echo stop" in commands
    assert "echo pre" in commands
    
    settings_path.unlink()
    print("Sanitization test passed!")

if __name__ == "__main__":
    test_sanitization()
