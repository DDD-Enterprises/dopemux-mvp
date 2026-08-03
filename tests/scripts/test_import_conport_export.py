"""Regression test for scripts/migration/import_conport_export.py.

Reproduces the PR #1188 review finding: link 33 in the real export bundle
targets custom_data key "python-tmux-research", and the export *does* include
that row (id=2). The importer used to quarantine it as unresolved anyway,
because (a) import_context_links() ran before import_custom_data() populated
the ledger, and (b) even after that ordering fix, custom_data was only ledgered
under its numeric id while context_links reference custom_data endpoints by
key.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "migration"
    / "import_conport_export.py"
)
_spec = importlib.util.spec_from_file_location("import_conport_export", MODULE_PATH)
import_conport_export = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("import_conport_export", import_conport_export)
_spec.loader.exec_module(import_conport_export)

Importer = import_conport_export.Importer


class _FakeConn:
    """Only load_ledger() touches the connection in dry-run mode."""

    async def fetch(self, *_args, **_kwargs):
        return []


def _bundle() -> dict:
    return {
        "export_timestamp": "2025-10-25T00:00:00+00:00",
        "decisions": [
            {"id": 15, "summary": "libtmux + Textual architecture", "timestamp": "2025-10-05T00:00:00+00:00"},
        ],
        "progress_entries": [],
        "custom_data": [
            {
                "id": 2,
                "category": "research",
                "key": "python-tmux-research",
                "value": {"title": "Comprehensive Python tmux Design Patterns Research"},
                "timestamp": "2025-10-05T16:05:30+00:00",
            },
        ],
        "context_links": [
            {
                "id": 33,
                "source_item_type": "decision",
                "source_item_id": "15",
                "target_item_type": "custom_data",
                "target_item_id": "python-tmux-research",
                "relationship_type": "validated_by",
                "description": "Decision #15 validated by comprehensive Python tmux research",
                "timestamp": "2025-10-05T16:05:30+00:00",
            },
        ],
        "system_patterns": [],
        "active_context": None,
        "product_context": None,
    }


@pytest.mark.asyncio
async def test_key_addressed_custom_data_link_resolves():
    importer = Importer(_FakeConn(), "/workspace", _bundle(), dry_run=True)
    await importer.run()

    stats = importer.stats["context_links"]
    assert stats["unresolved"] == 0, "link 33 should resolve, not quarantine"
    assert stats["new"] == 1


@pytest.mark.asyncio
async def test_custom_data_row_addressable_by_both_id_and_key():
    importer = Importer(_FakeConn(), "/workspace", _bundle(), dry_run=True)
    await importer.run()

    by_id = importer.seen("custom_data", 2)
    by_key = importer.seen("custom_data", "python-tmux-research")
    assert by_id is not None
    assert by_id == by_key
