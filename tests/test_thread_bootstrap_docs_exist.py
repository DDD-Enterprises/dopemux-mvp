from pathlib import Path

REQUIRED_ALTERNATES = [
    [
        "docs/thread-primer-taskx.md",
        "docs/04-explanation/root-relocated/THREAD_PRIMER_TASKX.md",
        "docs/04-explanation/root-relocated/thread-primer-taskx.md",
    ],
    [
        "docs/stateless-operator-mode-prompt.md",
        "docs/03-reference/instructions/STATELESS_OPERATOR_MODE_PROMPT.md",
        "docs/03-reference/instructions/stateless-operator-mode-prompt.md",
    ],
    [
        "docs/codex-desktop-bootstrap-prompt.md",
        "docs/03-reference/instructions/CODEX_DESKTOP_BOOTSTRAP_PROMPT.md",
        "docs/03-reference/instructions/codex-desktop-bootstrap-prompt.md",
    ],
    [
        "docs/dopemux-continuation-primer.md",
        "docs/04-explanation/root-relocated/DOPEMUX_CONTINUATION_PRIMER.md",
        "docs/04-explanation/root-relocated/dopemux-continuation-primer.md",
    ],
]


def test_thread_bootstrap_docs_exist():
    for candidates in REQUIRED_ALTERNATES:
        assert any(Path(path).exists() for path in candidates), (
            "Missing required bootstrap doc. Checked: " + ", ".join(candidates)
        )
