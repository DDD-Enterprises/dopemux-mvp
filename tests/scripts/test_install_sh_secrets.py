import shlex
import subprocess
from pathlib import Path


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
