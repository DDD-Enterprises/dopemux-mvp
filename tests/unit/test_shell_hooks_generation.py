import pytest
from dopemux.hooks.claude_code_hooks import get_shell_hook_scripts

def test_shell_hooks_contain_gating_logic():
    """
    Verify that generated shell hooks include first-word gating
    and the DOPEMUX_SAW_RELEVANT_CMD marker.
    """
    hooks = get_shell_hook_scripts()
    
    # Test ZSH hooks
    zsh = hooks['zsh_hooks']
    assert 'DOPEMUX_SAW_RELEVANT_CMD=1' in zsh
    assert 'if [[ "$cmd" == "claude"* || "$cmd" == "claude-code"* ]]; then' in zsh
    assert 'unset DOPEMUX_SAW_RELEVANT_CMD' in zsh
    assert '&!' in zsh
    
    # Test Bash hooks
    bash_preexec = hooks['bash_preexec']
    assert 'DOPEMUX_SAW_RELEVANT_CMD=1' in bash_preexec
    assert 'case "$cmd" in' in bash_preexec
    assert 'claude*|"claude-code"*)' in bash_preexec
    assert 'disown' in bash_preexec
    
    bash_precmd = hooks['bash_precmd']
    assert 'DOPEMUX_SAW_RELEVANT_CMD' in bash_precmd
    assert 'unset DOPEMUX_SAW_RELEVANT_CMD' in bash_precmd
    assert 'disown' in bash_precmd
