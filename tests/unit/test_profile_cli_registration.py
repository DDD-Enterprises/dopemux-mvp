from src.dopemux.cli import cli


def test_profile_group_exposes_extended_command_set():
    profile_group = cli.commands.get("profile")
    assert profile_group is not None

    expected = {
        "list",
        "init",
        "auto-enable",
        "auto-disable",
        "auto-status",
        "stats",
        "show",
        "validate",
        "create",
        "apply",
        "use",
        "current",
    }

    missing = expected.difference(profile_group.commands.keys())
    assert not missing, f"Missing profile commands: {sorted(missing)}"


def test_profile_apply_and_use_alias_same_callback():
    profile_group = cli.commands["profile"]
    assert profile_group.commands["apply"].callback is profile_group.commands["use"].callback
