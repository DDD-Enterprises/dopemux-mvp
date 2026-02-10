from dopemux.hooks.claude_code_hooks import get_shell_hook_scripts


def test_zsh_hooks_gate_command_done():
    scripts = get_shell_hook_scripts()
    zsh = scripts["zsh_hooks"]
    assert "DOPEMUX_SAW_RELEVANT_CMD" in zsh
    assert "if (( DOPEMUX_SAW_RELEVANT_CMD ))" in zsh
    assert 'cmd="${full%% *}"' in zsh
    assert '"claude"' in zsh and '"dopemux"' in zsh


def test_bash_hooks_gate_command_done():
    scripts = get_shell_hook_scripts()
    bash_pre = scripts["bash_preexec"]
    bash_post = scripts["bash_precmd"]
    assert "DOPEMUX_SAW_RELEVANT_CMD=0" in bash_pre
    assert 'cmd="${full%% *}"' in bash_pre
    assert "DOPEMUX_SAW_RELEVANT_CMD" in bash_post
    assert "if [[ \"${DOPEMUX_SAW_RELEVANT_CMD" in bash_post
