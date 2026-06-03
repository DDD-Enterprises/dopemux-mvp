"""Canonical status-string constants for the Repo Truth Extractor.

Audit finding S6-MED-1: the RUN_MANIFEST.run_status field is written by two separate
producers -- reporting.write_run_manifest (initial) and
run_extraction_v5.compute_run_status / update_run_manifest_status (final) -- with
independently hardcoded string literals, risking divergence. Centralize the vocabulary
here so both producers reference the same constants.

Values are intentionally identical to the historical literals ("OK"/"BLOCKED"/
"COST_ABORTED") so existing RUN_MANIFEST.json consumers and characterization tests are
unaffected. This module is a leaf (no imports) to keep it cycle-safe for any importer.
"""
from __future__ import annotations

# Terminal RUN_MANIFEST.run_status states. compute_run_status() in run_extraction_v5 is the
# authoritative producer; reporting.write_run_manifest seeds the initial value.
RUN_STATUS_OK = "OK"
RUN_STATUS_BLOCKED = "BLOCKED"
RUN_STATUS_COST_ABORTED = "COST_ABORTED"

RUN_STATUS_VALUES = frozenset(
    {RUN_STATUS_OK, RUN_STATUS_BLOCKED, RUN_STATUS_COST_ABORTED}
)
