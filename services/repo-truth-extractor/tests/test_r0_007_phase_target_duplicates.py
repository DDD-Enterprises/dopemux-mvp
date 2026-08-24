"""Guard against duplicate entries in phase target lists (TP-RTE-TRUTH-R0-007 / F-07).

`extractor/phases/a.py` listed "compose.yml" twice in its `targets` list. F-07
classified this as trivial dead code. It is not: `Collector.collect()` builds
`roots = [self.root / d for d in subdirs]` and, for a root that is a file,
appends `_make_item(root)` unconditionally with no de-duplication anywhere in
the method. A repeated target is therefore ingested twice into the phase corpus
— the same file's content shipped to a paid LLM twice on every phase-A run.

These tests pin both halves of that: the concrete list must stay duplicate-free,
and the collector behaviour that makes duplicates costly is asserted directly so
the reason for the first test cannot be forgotten.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def _literal_string_lists(source_path: Path) -> list[list[str]]:
    """Every all-string list literal in a module, without importing it."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    found: list[list[str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List) or not node.elts:
            continue
        if all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
            found.append([e.value for e in node.elts])
    return found


@pytest.mark.parametrize(
    "phase_module",
    sorted(p.name for p in (SERVICE_ROOT / "extractor" / "phases").glob("[a-z].py")),
)
def test_phase_target_lists_contain_no_duplicates(phase_module: str) -> None:
    """No phase may list the same scan target twice.

    Parametrized over every phase module rather than just `a.py`, so the same
    defect appearing in a sibling phase is caught rather than only the one
    instance F-07 happened to name.
    """
    path = SERVICE_ROOT / "extractor" / "phases" / phase_module
    for literal in _literal_string_lists(path):
        duplicates = sorted({item for item in literal if literal.count(item) > 1})
        assert not duplicates, (
            f"{phase_module} repeats scan target(s) {duplicates}. Collector.collect() "
            f"does not de-duplicate its subdirs, so each repeat re-ingests that path "
            f"into the phase corpus and pays for its tokens again."
        )


def test_collector_does_not_deduplicate_repeated_targets(tmp_path: Path) -> None:
    """Pin the collector behaviour that makes a duplicated target expensive.

    This is deliberately an assertion that the CURRENT behaviour is non-dedup.
    If someone later makes `collect()` de-duplicate, this test fails and points
    at the test above — at that point the guard is redundant and both should be
    reconsidered together, rather than the dedup silently masking a real list bug.
    """
    spec = importlib.util.spec_from_file_location(
        "_r0_007_v5", SERVICE_ROOT / "run_extraction_v5.py"
    )
    assert spec and spec.loader
    v5 = importlib.util.module_from_spec(spec)
    sys.modules["_r0_007_v5"] = v5
    spec.loader.exec_module(v5)

    (tmp_path / "compose.yml").write_text("services: {}\n", encoding="utf-8")
    collector = v5.Collector(tmp_path, [])

    once = collector.collect(subdirs=["compose.yml"])
    twice = collector.collect(subdirs=["compose.yml", "compose.yml"])

    assert len(once) == 1
    assert len(twice) == 2, (
        "Collector.collect() now de-duplicates repeated targets. If that is "
        "intentional, revisit test_phase_target_lists_contain_no_duplicates."
    )
