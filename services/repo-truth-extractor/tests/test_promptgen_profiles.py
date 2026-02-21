from __future__ import annotations

import json
from pathlib import Path
import sys


SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from lib.promptgen.profile_select import select_profile
from lib.promptgen.profile_validate import validate_profiles


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "promptgen" / "profile_selection"
PROFILES_DIR = SERVICE_DIR / "lib" / "promptgen" / "profiles"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_profile_schema_validation_passes_for_profile_set() -> None:
    report = validate_profiles(PROFILES_DIR)
    assert report["status"] == "PASS"
    assert report["profiles_total"] >= 9
    assert report["profiles_valid"] == report["profiles_total"]


def test_profile_selection_is_deterministic_for_monorepo_fixture(tmp_path: Path) -> None:
    fingerprint = _load_json(FIXTURES / "fingerprint_monorepo.json")
    archetypes = _load_json(FIXTURES / "archetypes_monorepo.json")

    one = select_profile(
        run_id="fixture_monorepo",
        root=tmp_path,
        repo_fingerprint=fingerprint,
        archetypes_payload=archetypes,
        profiles_dir=PROFILES_DIR,
    )
    two = select_profile(
        run_id="fixture_monorepo",
        root=tmp_path,
        repo_fingerprint=fingerprint,
        archetypes_payload=archetypes,
        profiles_dir=PROFILES_DIR,
    )

    assert one == two
    assert one["selected_profile_id"] == "P01_MONOREPO_MICROSERVICES"
    assert one["selection_mode"] == "deterministic_weighted_rules"
    assert isinstance(one["per_profile_scores"], list) and one["per_profile_scores"]

