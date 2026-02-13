from pathlib import Path

REQUIRED = [
    "docs/THREAD_PRIMER_TASKX.md",
    "docs/STATELESS_OPERATOR_MODE_PROMPT.md",
    "docs/CODEX_DESKTOP_BOOTSTRAP_PROMPT.md",
    "docs/DOPEMUX_CONTINUATION_PRIMER.md",
]


def test_thread_bootstrap_docs_exist():
    for path in REQUIRED:
        assert Path(path).exists(), f"Missing required bootstrap doc: {path}"
