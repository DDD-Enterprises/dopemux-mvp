import subprocess
from pathlib import Path

import pytest

from dopemux.coldstart.secrets_resolver import (
    SecretResolution,
    SecretResolutionError,
    SecretSource,
    is_placeholder_value,
    read_secret_from_1password,
    read_secret_from_keychain,
    resolve_secret_value,
)


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["cmd"], returncode, stdout=stdout, stderr="")


def test_noninteractive_reads_exported_env_value() -> None:
    result = resolve_secret_value(
        "OPENAI_API_KEY",
        current=None,
        env_file=None,
        non_interactive=True,
        env={"OPENAI_API_KEY": "sk-test"},
    )

    assert result == SecretResolution(
        value="sk-test",
        source=SecretSource.ENV,
        is_sensitive=True,
    )


def test_unknown_boot_critical_secret_fails_closed_in_noninteractive_mode() -> None:
    with pytest.raises(SecretResolutionError, match="not configured"):
        resolve_secret_value(
            "UNKNOWN_BOOT_SECRET",
            current=None,
            env_file=None,
            non_interactive=True,
            env={},
        )


def test_provider_optional_secret_defers_in_noninteractive_mode() -> None:
    result = resolve_secret_value(
        "GEMINI_API_KEY",
        current=None,
        env_file=None,
        non_interactive=True,
        env={},
    )

    assert result == SecretResolution(
        value=None,
        source=SecretSource.DEFER,
        is_sensitive=True,
    )


def test_existing_placeholder_value_is_ignored(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder\n", encoding="utf-8")

    result = resolve_secret_value(
        "OPENAI_API_KEY",
        current=None,
        env_file=env_file,
        non_interactive=True,
        env={},
    )

    assert result.source is SecretSource.DEFER
    assert result.value is None


def test_keychain_reader_uses_explicit_argument_list() -> None:
    seen: list[list[str]] = []

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(args)
        return completed("secret-from-keychain\n")

    assert read_secret_from_keychain("OPENAI_API_KEY", runner=runner) == "secret-from-keychain"
    assert seen == [["security", "find-generic-password", "-w", "-s", "OPENAI_API_KEY"]]


def test_1password_reader_requires_reference() -> None:
    assert read_secret_from_1password("", runner=lambda args, **kwargs: completed("unused")) is None


def test_missing_secret_provider_cli_is_lookup_miss() -> None:
    def missing_cli(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError(args[0])

    assert read_secret_from_keychain("OPENAI_API_KEY", runner=missing_cli) is None
    assert read_secret_from_1password("op://vault/item/field", runner=missing_cli) is None


def test_litellm_database_url_reuses_generated_age_password() -> None:
    env: dict[str, str] = {}
    age_password = resolve_secret_value(
        "AGE_PASSWORD",
        current=None,
        env_file=None,
        non_interactive=True,
        env=env,
    )
    dsn = resolve_secret_value(
        "LITELLM_DATABASE_URL",
        current=None,
        env_file=None,
        non_interactive=True,
        env=env,
    )

    assert age_password.value
    assert env["AGE_PASSWORD"] == age_password.value
    assert dsn.value == f"postgresql://dopemux_age:{age_password.value}@dopemux-postgres-age:5432/litellm"


def test_manual_value_wins_over_local_defaultable_secret() -> None:
    result = resolve_secret_value(
        "AGE_PASSWORD",
        current=None,
        env_file=None,
        non_interactive=False,
        env={},
        source=SecretSource.MANUAL,
        manual_value="operator-entered-password",
    )

    assert result == SecretResolution(
        value="operator-entered-password",
        source=SecretSource.MANUAL,
        is_sensitive=True,
    )


def test_placeholder_detection_matches_installer_policy() -> None:
    assert is_placeholder_value("dev-key-456")
    assert is_placeholder_value("postgresql://dopemux_age:dopemux_age_dev_password@host/db")
    assert not is_placeholder_value("actual-value")
