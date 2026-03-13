from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import build_smoke_run, normalize_for_determinism


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v5_golden_fixture_smoke_is_deterministic_and_offline(tmp_path: Path, monkeypatch) -> None:
    payloads = []

    for run_id in ("golden_one", "golden_two"):
        built = build_smoke_run(tmp_path, run_id)
        runner = built["runner"]
        monkeypatch.setattr(runner, "call_llm", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("golden smoke must stay offline")))
        verify_code = runner.verify_phase_output(built["dirs"], ["D"])
        assert verify_code == 0

        dirs = built["dirs"]
        assert (dirs["root"] / "RUNNER_IDENTITY.json").exists()
        assert (dirs["root"] / "RUN_ROUTING_FINGERPRINT.json").exists()
        assert (dirs["root"] / "PHASE_CONTRACT_MAP.json").exists()
        assert (dirs["root"] / "COVERAGE_ROLLUP.json").exists()
        assert (dirs["root"] / "RESUME_PROOF.json").exists()
        assert (dirs["root"] / "PROOF_PACK.json").exists()

        payloads.append(
            {
                "runner_identity": normalize_for_determinism(_load_json(dirs["root"] / "RUNNER_IDENTITY.json")),
                "routing_fingerprint": normalize_for_determinism(_load_json(dirs["root"] / "RUN_ROUTING_FINGERPRINT.json")),
                "contract_map": normalize_for_determinism(_load_json(dirs["root"] / "PHASE_CONTRACT_MAP.json")),
                "coverage_rollup": normalize_for_determinism(_load_json(dirs["root"] / "COVERAGE_ROLLUP.json")),
                "resume_proof": normalize_for_determinism(_load_json(dirs["root"] / "RESUME_PROOF.json")),
            }
        )

    assert payloads[0] == payloads[1]
