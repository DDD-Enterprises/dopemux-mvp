"""RTE-TRUTH P0 characterization harness: golden snapshot equality.

Regenerates each introspection-only capture (CLI help texts, ``rte list``,
``rte status``, ``--print-config`` for all 11 cost profiles, and the
value-default ``--print-cost-preview``) and asserts the normalized output is
byte-identical to the stored golden under ``tests/goldens/``. Later refactor
PRs prove "no behavior change" by these hashes staying green.

Safety: every capture is dry-run/introspection only (no ``--execute``, no
``DPMX_LIVE_OK``); the capture subprocess env additionally strips provider
API keys and ``DPMX_*`` consent vars. Network-touching surfaces (doctor /
preflight / validate-live live runs) are captured at ``--help`` level only -
see ``_normalize.SKIPPED_CAPTURES`` for the audit trail.

Slow captures (``--print-cost-preview``: ~259s wall, full dry-run phase
execution precedes the preview) are skipped unless ``RTE_TRUTH_SLOW_GOLDENS=1``.

Regenerating goldens intentionally (after an approved behavior change):
    mise exec -- python services/repo-truth-extractor/tests/goldens/_normalize.py
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

GOLDENS_DIR = Path(__file__).resolve().parent / "goldens"
sys.path.insert(0, str(GOLDENS_DIR))

import _normalize as harness  # noqa: E402

RUN_SLOW = os.environ.get("RTE_TRUTH_SLOW_GOLDENS") == "1"

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="RTE requires Python >=3.11 (use the repo's mise python 3.12).",
)


def _spec_param(spec):
    marks = []
    if spec.name in harness.SLOW_CAPTURE_NAMES and not RUN_SLOW:
        marks.append(
            pytest.mark.skip(
                reason=(
                    "slow capture (~259s: --print-cost-preview runs a full "
                    "dry-run phase execution incl. repo file walk + hashing "
                    "before emitting the preview). Set RTE_TRUTH_SLOW_GOLDENS=1 "
                    "to include it."
                )
            )
        )
    return pytest.param(spec, id=spec.name, marks=marks)


@pytest.mark.parametrize("spec", [_spec_param(s) for s in harness.CAPTURES])
def test_capture_matches_golden(spec) -> None:
    golden_path = GOLDENS_DIR / spec.golden_filename
    assert golden_path.exists(), (
        f"missing golden {golden_path.name}; regenerate via "
        "`python tests/goldens/_normalize.py`"
    )
    actual = harness.run_capture(spec)
    expected = golden_path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"normalized output of {spec.name} diverged from golden "
        f"{golden_path.name}. If this behavior change is intentional, "
        "regenerate goldens via `python tests/goldens/_normalize.py` and "
        "review the diff."
    )


def test_manifest_matches_golden_files() -> None:
    """MANIFEST.sha256 must exactly cover the golden set (tamper guard)."""
    manifest_path = GOLDENS_DIR / harness.MANIFEST_NAME
    assert manifest_path.exists()
    entries = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        entries[name.strip()] = digest
    on_disk = sorted(p.name for p in GOLDENS_DIR.glob("*.golden.txt"))
    assert sorted(entries) == on_disk, "MANIFEST.sha256 out of sync with goldens/"
    for name, digest in entries.items():
        actual = hashlib.sha256((GOLDENS_DIR / name).read_bytes()).hexdigest()
        assert actual == digest, f"golden {name} does not match MANIFEST.sha256"


def test_every_capture_has_a_golden_and_vice_versa() -> None:
    spec_files = {spec.golden_filename for spec in harness.CAPTURES}
    disk_files = {p.name for p in GOLDENS_DIR.glob("*.golden.txt")}
    assert spec_files == disk_files


def test_normalizer_masks_key_presence_and_env() -> None:
    """Goldens must never encode local env/key state (unit-level guard)."""
    sample = (
        '{"api_key_present": true, "secret_set": false, "live_ok": true,'
        ' "api_key_env_resolved": "OPENAI_API_KEY",'
        ' "dpmx_webhook_url": "http://x", "dpmx_live_ok": "1",'
        ' "python_version": "3.12.13",'
        ' "generated_at": "2026-07-10T21:38:37.783343+00:00",'
        ' "git_sha": "542c17bb4753d3440f73ac09c5e7042fd00cfecb"}'
    )
    out = harness.normalize_text(sample)
    for leak in ("true", "3.12.13", "OPENAI_API_KEY", "http://x", "542c17bb"):
        assert leak not in out
    assert '"api_key_present": "<MASKED>"' in out
    assert "<GITSHA>" in out
    assert "<TIMESTAMP>" in out
