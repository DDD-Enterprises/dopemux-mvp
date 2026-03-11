from pathlib import Path

REQUIRED_ALTERNATES = [
    [
        "docs/THREAD_PRIMER_TASKX.md",
        "docs/04-explanation/root-relocated/THREAD_PRIMER_TASKX.md",
    ],
    [
        "docs/STATELESS_OPERATOR_MODE_PROMPT.md",
        "docs/03-reference/instructions/STATELESS_OPERATOR_MODE_PROMPT.md",
    ],
    [
        "docs/CODEX_DESKTOP_BOOTSTRAP_PROMPT.md",
        "docs/03-reference/instructions/CODEX_DESKTOP_BOOTSTRAP_PROMPT.md",
    ],
    [
        "docs/DOPEMUX_CONTINUATION_PRIMER.md",
        "docs/04-explanation/root-relocated/DOPEMUX_CONTINUATION_PRIMER.md",
    ],
]


def test_thread_bootstrap_docs_exist():
    for candidates in REQUIRED_ALTERNATES:
        assert any(Path(path).exists() for path in candidates), (
            "Missing required bootstrap doc. Checked: " + ", ".join(candidates)
        )
