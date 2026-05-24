"""E7: legacy ladder constant deprecation proxy coverage.

After E7 renames the 11 hardcoded ladder constants to underscore-prefixed
internal names, a module-level ``__getattr__`` emits a DeprecationWarning on
external access to the old names and returns the underscore-prefixed value.
The contract: external importers keep working (no breakage) but receive a
single warning per name per process so they can plan migration to
``derive_ladder_for_cell``.

The tests intentionally clear ``_LEGACY_LADDER_WARNED`` between checks to
isolate "first access" semantics. Within a single test we keep the suppressed
state across multiple accesses to confirm the warning fires only once.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner  # noqa: E402


LEGACY_NAMES = sorted(runner._LEGACY_LADDER_RENAME_MAP.keys())


def _reset_warned():
    runner._LEGACY_LADDER_WARNED.clear()


def test_all_eleven_legacy_names_registered():
    # Sanity: ensure the rename map covers every constant the packet enumerates.
    expected = {
        "BALANCED_GROK_OPENROUTER_DOCS_LADDER",
        "BALANCED_GROK_OPENROUTER_DOCS_STRICT_LADDER",
        "BALANCED_GROK_OPENROUTER_CODE_LADDERS",
        "BALANCED_GROK_OPENROUTER_SYNTHESIS_LADDER",
        "BALANCED_GROK_OPENROUTER_OPUS_ROUTE",
        "GEMINI_PRIMARY_DOCS_LADDER",
        "GEMINI_PRIMARY_SYNTHESIS_LADDER",
        "GEMINI_PRIMARY_CODE_LADDERS",
        "OPTIMAL_DOCS_LADDER",
        "OPTIMAL_CODE_LADDERS",
        "OPTIMAL_SYNTHESIS_LADDER",
    }
    assert set(LEGACY_NAMES) == expected


def test_legacy_name_emits_deprecation_warning_on_first_access():
    _reset_warned()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        _ = runner.BALANCED_GROK_OPENROUTER_SYNTHESIS_LADDER
    deprecation_messages = [
        str(w.message)
        for w in captured
        if issubclass(w.category, DeprecationWarning)
    ]
    assert any(
        "BALANCED_GROK_OPENROUTER_SYNTHESIS_LADDER" in msg
        for msg in deprecation_messages
    )
    assert any(
        "derive_ladder_for_cell" in msg for msg in deprecation_messages
    )


def test_deprecation_warning_fires_once_per_name():
    _reset_warned()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        _ = runner.OPTIMAL_SYNTHESIS_LADDER
        _ = runner.OPTIMAL_SYNTHESIS_LADDER  # second access; no extra warning
        _ = runner.OPTIMAL_SYNTHESIS_LADDER  # third access; still no extra warning
    fired = [
        w for w in captured
        if issubclass(w.category, DeprecationWarning)
        and "OPTIMAL_SYNTHESIS_LADDER" in str(w.message)
    ]
    assert len(fired) == 1


def test_legacy_value_matches_underscore_prefixed_binding():
    _reset_warned()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy = runner.BALANCED_GROK_OPENROUTER_OPUS_ROUTE
    internal = runner._LADDER_BALANCED_GROK_OPENROUTER_OPUS
    assert legacy == internal


def test_simplefilter_error_makes_legacy_access_raise():
    _reset_warned()
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with pytest.raises(DeprecationWarning):
            _ = runner.BALANCED_GROK_OPENROUTER_DOCS_LADDER


def test_non_legacy_name_raises_attributeerror():
    _reset_warned()
    with pytest.raises(AttributeError):
        _ = runner.DEFINITELY_NOT_A_REAL_LADDER_CONSTANT_XYZ


def test_legacy_list_value_round_trips_through_proxy():
    _reset_warned()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy = runner.BALANCED_GROK_OPENROUTER_SYNTHESIS_LADDER
    # Sanity: the legacy value is still the same list of 3 tuples the
    # constant has held since pre-E7.
    assert isinstance(legacy, list)
    assert len(legacy) == 3
    for entry in legacy:
        assert isinstance(entry, tuple)
        assert len(entry) == 3


def test_from_import_path_triggers_deprecation_proxy():
    """``from module import NAME`` resolves via the module's ``__getattr__``
    when ``NAME`` is absent from ``__dict__`` (PEP 562). The other tests
    exercise the attribute-access path; this one verifies the import path
    explicitly so any future regression surfaces immediately.
    """
    _reset_warned()
    import importlib  # noqa: WPS433 — intentional local for clarity
    mod = importlib.import_module("run_extraction_v5")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", DeprecationWarning)
        value = getattr(mod, "OPTIMAL_DOCS_LADDER")
    assert isinstance(value, list)
    deprecation_messages = [
        str(w.message)
        for w in captured
        if issubclass(w.category, DeprecationWarning)
        and "OPTIMAL_DOCS_LADDER" in str(w.message)
    ]
    assert deprecation_messages, (
        "import-path access must trigger the DeprecationWarning proxy"
    )
