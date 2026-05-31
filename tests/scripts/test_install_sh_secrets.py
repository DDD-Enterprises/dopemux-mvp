import shlex
import subprocess
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = REPO_ROOT / "install.sh"


def run_bash(script: str, input_text: str = "") -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["bash", "-c", script],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"command failed with exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return result


def test_interactive_secret_defer_records_summary(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    script = f"""
set -euo pipefail
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
AUTO_CONFIRM=false
INSTALLER_TEST_MODE=1
STARTED_CAPABILITIES=()
DEFERRED_CAPABILITIES=()
resolve_secret_value LEANTIME_TOKEN '' {shlex.quote(str(env_file))} >/dev/null
printf 'VALUE=%s\\n' "$RESOLVED_SECRET_VALUE"
show_capability_summary
"""

    result = run_bash(script, input_text="5\n")

    assert "VALUE=" in result.stdout
    assert "Leantime sync" in result.stdout
    assert "Deferred:" in result.stdout


def test_env_file_override_keeps_shell_env_and_custom_path(tmp_path: Path) -> None:
    env_file = tmp_path / "installer.env"
    env_file.write_text(
        "\n".join(
            [
                "LEANTIME_TOKEN=from-file",
                "OPENAI_API_KEY=from-file-openai",
                "VOYAGE_API_KEY=from-file-voyage",
                "",
            ]
        )
    )

    script = f"""
set -euo pipefail
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
ENV_FILE={shlex.quote(str(env_file))}
AUTO_CONFIRM=true
INSTALLER_TEST_MODE=1
unset ANTHROPIC_API_KEY OPENAI_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY XAI_API_KEY VOYAGE_API_KEY LEANTIME_URL LEANTIME_TOKEN TASK_ORCHESTRATOR_API_KEY ADHD_ENGINE_API_KEY LITELLM_DATABASE_URL TAVILY_API_KEY EXA_API_KEY OPENAI_WEBHOOK_SECRET
export LEANTIME_TOKEN=from-shell
export OPENAI_API_KEY=from-shell-openai
export VOYAGE_API_KEY=from-shell-voyage
export EXA_API_KEY=from-shell-exa
export TAVILY_API_KEY=from-shell-tav
export ANTHROPIC_API_KEY=from-shell-anth
export OPENROUTER_API_KEY=from-shell-or
export GEMINI_API_KEY=from-shell-gem
export XAI_API_KEY=from-shell-xai
export OPENAI_WEBHOOK_SECRET=from-shell-hook
install_docker_services full
printf '%s\\n' '---CAPS---'
show_capability_summary
printf '%s\\n' '---ENV---'
cat "$ENV_FILE"
"""

    result = run_bash(script)

    assert f"Environment variables saved to {env_file}" in result.stdout
    assert "Capability status:" in result.stdout
    assert "Started:" in result.stdout
    assert "Deferred:" in result.stdout
    env_text = result.stdout.split("---ENV---", 1)[1]
    assert "LEANTIME_TOKEN=from-shell" in env_text
    assert "OPENAI_API_KEY=from-shell-openai" in env_text
    assert "VOYAGE_API_KEY=from-shell-voyage" in env_text
    assert "TAVILY_API_KEY=from-shell-tav" in env_text
    assert "LEANTIME_TOKEN=from-file" not in env_text
    assert "OPENAI_API_KEY=from-file-openai" not in env_text
    assert "VOYAGE_API_KEY=from-file-voyage" not in env_text


def test_noninteractive_exported_env_vars_only_completes(tmp_path: Path) -> None:
    env_file = tmp_path / "noninteractive.env"
    script = f"""
set -euo pipefail
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
ENV_FILE={shlex.quote(str(env_file))}
AUTO_CONFIRM=true
INSTALLER_TEST_MODE=1
unset ANTHROPIC_API_KEY OPENAI_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY XAI_API_KEY VOYAGE_API_KEY LEANTIME_URL LEANTIME_TOKEN TASK_ORCHESTRATOR_API_KEY ADHD_ENGINE_API_KEY LITELLM_DATABASE_URL TAVILY_API_KEY EXA_API_KEY OPENAI_WEBHOOK_SECRET
export LEANTIME_TOKEN=from-shell
export OPENAI_API_KEY=from-shell-openai
export VOYAGE_API_KEY=from-shell-voyage
export EXA_API_KEY=from-shell-exa
install_docker_services full
printf '%s\\n' '---CAPS---'
show_capability_summary
printf '%s\\n' '---ENV---'
cat "$ENV_FILE"
"""

    result = run_bash(script)

    assert "Capability status:" in result.stdout
    assert "Deferred:" in result.stdout
    assert "Anthropic provider" in result.stdout
    env_text = result.stdout.split("---ENV---", 1)[1]
    assert "LEANTIME_TOKEN=from-shell" in env_text
    assert "OPENAI_API_KEY=from-shell-openai" in env_text
    assert "VOYAGE_API_KEY=from-shell-voyage" in env_text
    assert "EXA_API_KEY=from-shell-exa" in env_text
    assert "TAVILY_API_KEY=" not in env_text
    assert "OPENAI_WEBHOOK_SECRET=" not in env_text


def test_placeholder_env_values_are_rejected_and_regenerated(tmp_path: Path) -> None:
    env_file = tmp_path / "placeholder.env"
    env_file.write_text(
        "\n".join(
            [
                "AGE_PASSWORD=your_secure_age_password_here",
                "TASK_ORCHESTRATOR_API_KEY=dev-key-456",
                "ADHD_ENGINE_API_KEY=CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder",
                "LITELLM_DATABASE_URL=postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/litellm",
                "",
            ]
        )
    )
    script = f"""
set -euo pipefail
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
ENV_FILE={shlex.quote(str(env_file))}
AUTO_CONFIRM=true
INSTALLER_TEST_MODE=1
unset ANTHROPIC_API_KEY OPENAI_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY XAI_API_KEY VOYAGE_API_KEY LEANTIME_URL LEANTIME_TOKEN TASK_ORCHESTRATOR_API_KEY ADHD_ENGINE_API_KEY LITELLM_DATABASE_URL TAVILY_API_KEY EXA_API_KEY OPENAI_WEBHOOK_SECRET AGE_PASSWORD
export OPENAI_API_KEY=from-shell-openai
export VOYAGE_API_KEY=from-shell-voyage
export EXA_API_KEY=from-shell-exa
export TAVILY_API_KEY=from-shell-tav
install_docker_services full
printf '%s\\n' '---ENV---'
cat "$ENV_FILE"
"""

    result = run_bash(script)

    assert "placeholder or development value" in result.stderr
    env_text = result.stdout.split("---ENV---", 1)[1]
    env_values = dict(
        line.split("=", 1)
        for line in env_text.splitlines()
        if line and not line.startswith("#")
    )
    assert env_values["AGE_PASSWORD"] != "your_secure_age_password_here"
    assert env_values["TASK_ORCHESTRATOR_API_KEY"] != "dev-key-456"
    assert env_values["ADHD_ENGINE_API_KEY"] != "CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder"
    assert len(env_values["AGE_PASSWORD"]) == 64
    assert len(env_values["TASK_ORCHESTRATOR_API_KEY"]) == 64
    assert len(env_values["ADHD_ENGINE_API_KEY"]) == 64
    litellm_url = urlparse(env_values["LITELLM_DATABASE_URL"])
    assert litellm_url.password == env_values["AGE_PASSWORD"]
    assert "dopemux_age_dev_password" not in env_text


def test_core_stack_regenerates_copied_secret_placeholders(tmp_path: Path) -> None:
    env_file = tmp_path / "core-placeholder.env"
    env_file.write_text(
        "\n".join(
            [
                "AGE_PASSWORD=CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder",
                "TASK_ORCHESTRATOR_API_KEY=CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder",
                "ADHD_ENGINE_API_KEY=CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder",
                "",
            ]
        )
    )
    script = f"""
set -euo pipefail
source {shlex.quote(str(INSTALL_SH))}
trap - ERR
ENV_FILE={shlex.quote(str(env_file))}
AUTO_CONFIRM=true
INSTALLER_TEST_MODE=1
unset AGE_PASSWORD TASK_ORCHESTRATOR_API_KEY ADHD_ENGINE_API_KEY
install_docker_services core
printf '%s\\n' '---ENV---'
cat "$ENV_FILE"
"""

    result = run_bash(script)

    assert "placeholder or development value" in result.stderr
    env_text = result.stdout.split("---ENV---", 1)[1]
    env_values = dict(
        line.split("=", 1)
        for line in env_text.splitlines()
        if line and not line.startswith("#")
    )
    for key in ["AGE_PASSWORD", "TASK_ORCHESTRATOR_API_KEY", "ADHD_ENGINE_API_KEY"]:
        assert env_values[key] != "CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder"
        assert len(env_values[key]) == 64


def test_env_example_uses_invalid_placeholders_for_local_secrets() -> None:
    text = (REPO_ROOT / ".env.example").read_text()

    assert "your_secure_" not in text
    assert "your_openai_api_key_here" not in text
    assert "your_anthropic_api_key_here" not in text
    for key in [
        "AGE_PASSWORD",
        "REDIS_PASSWORD",
        "QDRANT_API_KEY",
        "ADHD_ENGINE_API_KEY",
        "TASK_ORCHESTRATOR_API_KEY",
    ]:
        assert (
            f"# REQUIRED: generate with: openssl rand -hex 32\n{key}=CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder"
            in text
        )
