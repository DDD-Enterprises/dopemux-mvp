from src.dopemux.cli import cli


def test_profile_group_exposes_extended_command_set():
    profile_group = cli.commands.get("profile")
    assert profile_group is not None

    expected = {
        "list",
        "init",
        "analyze-usage",
        "auto-enable",
        "auto-disable",
        "auto-status",
        "stats",
        "show",
        "validate",
        "create",
        "copy",
        "edit",
        "delete",
        "apply",
        "use",
        "current",
    }

    missing = expected.difference(profile_group.commands.keys())
    assert not missing, f"Missing profile commands: {sorted(missing)}"


def test_profile_apply_and_use_alias_same_callback():
    profile_group = cli.commands["profile"]
    assert profile_group.commands["apply"].callback is profile_group.commands["use"].callback


def test_top_level_switch_alias_present():
    assert "switch" in cli.commands

    profile_group = cli.commands["profile"]
    assert cli.commands["switch"].callback is profile_group.commands["use"].callback
