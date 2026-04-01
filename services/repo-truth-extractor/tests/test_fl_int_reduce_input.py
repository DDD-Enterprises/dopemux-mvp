from __future__ import annotations

import json
from pathlib import Path

from _fl_int_helpers import (
    PHASE_DIR_NAMES,
    build_fl_int_run_root,
    build_large_fl_int_run_root,
    fake_fl_int_payload,
    load_collect_module,
    load_reduce_module,
    load_run_module,
    write_json,
)


def test_reduce_input_is_deterministic_and_preserves_pm_terms(tmp_path: Path) -> None:
    collect_module = load_collect_module()
    reduce_module = load_reduce_module()
    run_root = build_large_fl_int_run_root(tmp_path)
    input_payload = collect_module.collect_input_payload(run_root)

    first_f0 = reduce_module.reduce_f0_input(input_payload)
    second_f0 = reduce_module.reduce_f0_input(input_payload)
    assert json.dumps(first_f0, sort_keys=True) == json.dumps(second_f0, sort_keys=True)
    assert any(row["guardrail_preserved"] for row in first_f0["selected_chunks"])
    assert any("pm" in row["content"].lower() or "policy" in row["content"].lower() for row in first_f0["selected_chunks"])

    prior_outputs = {"F1": fake_fl_int_payload("F1"), "_f0_reduction": first_f0}
    first_l0 = reduce_module.reduce_l0_input(input_payload, prior_outputs)
    second_l0 = reduce_module.reduce_l0_input(input_payload, prior_outputs)
    assert json.dumps(first_l0, sort_keys=True) == json.dumps(second_l0, sort_keys=True)
    assert any(row["guardrail_preserved"] for row in first_l0["selected_units"])


def test_reduction_materially_shrinks_large_prompts(tmp_path: Path) -> None:
    collect_module = load_collect_module()
    reduce_module = load_reduce_module()
    run_module = load_run_module()
    run_root = build_large_fl_int_run_root(tmp_path)
    input_payload = collect_module.collect_input_payload(run_root)

    f0_step = next(step for step in run_module.FL_INT_STEPS if step.step_id == "F0")
    l0_step = next(step for step in run_module.FL_INT_STEPS if step.step_id == "L0")

    original_f0_input = run_module._step_input_payload(f0_step, input_payload, {})
    original_f0_prompt = run_module._render_prompt(f0_step, original_f0_input, {})
    f0_reduction = reduce_module.reduce_f0_input(input_payload)
    reduced_f0_prompt_lengths = []
    for batch in f0_reduction["batches"]:
        batch_rows = run_module._batch_rows_for_ids(f0_reduction["selected_chunks"], batch["selected_ids"])
        reduced_f0_input = run_module._f0_batch_step_input(f0_step, input_payload, batch_rows, batch["batch_id"])
        reduced_f0_prompt_lengths.append(len(run_module._render_prompt(f0_step, reduced_f0_input, {})))
    assert reduced_f0_prompt_lengths
    assert max(reduced_f0_prompt_lengths) < len(original_f0_prompt)

    full_prior = {
        "F0": fake_fl_int_payload("F0"),
        "F1": fake_fl_int_payload("F1"),
        "F2": fake_fl_int_payload("F2"),
        "F4": fake_fl_int_payload("F4"),
    }
    original_l0_input = run_module._step_input_payload(l0_step, input_payload, full_prior)
    original_l0_prompt = run_module._render_prompt(l0_step, original_l0_input, full_prior)
    l0_reduction = reduce_module.reduce_l0_input(input_payload, {"F1": full_prior["F1"], "_f0_reduction": f0_reduction})
    reduced_l0_prompt_lengths = []
    for batch in l0_reduction["batches"]:
        family = batch["batch_id"].split("_")[2]
        family_rows = l0_reduction["selected_by_family"][family]
        batch_rows = run_module._batch_rows_for_ids(family_rows, batch["selected_ids"])
        reduced_l0_input = run_module._l0_batch_step_input(l0_step, input_payload, family, batch_rows, full_prior)
        reduced_l0_prior = run_module._l0_f1_prior_outputs(full_prior, batch_rows) if family == "F1" else {}
        reduced_l0_prompt_lengths.append(len(run_module._render_prompt(l0_step, reduced_l0_input, reduced_l0_prior)))
    assert reduced_l0_prompt_lengths
    assert max(reduced_l0_prompt_lengths) < len(original_l0_prompt)


def test_reduce_f0_accepts_real_shape_phase_d_list_artifacts(tmp_path: Path) -> None:
    collect_module = load_collect_module()
    reduce_module = load_reduce_module()
    run_root = build_fl_int_run_root(tmp_path)
    docs_norm = run_root / PHASE_DIR_NAMES["D"] / "norm"
    for child in docs_norm.iterdir():
        child.unlink()
    write_json(
        docs_norm / "DOC_CONTRACT_CLAIMS.part0001.json",
        [
            {
                "id": "claim_pm_policy",
                "path": "docs/governance.md",
                "line_range": [11, 14],
                "claim_text": "PM governance policy controls orchestration and authority routing.",
                "evidence": [
                    {
                        "path": "docs/governance.md",
                        "line_range": [11, 14],
                        "excerpt": "PM governance policy controls orchestration and authority routing.",
                    }
                ],
            },
            {
                "id": "status_noise",
                "path": "docs/status.md",
                "line_range": [3, 4],
                "claim_text": "Daily status report without design-bearing detail.",
                "evidence": [
                    {
                        "path": "docs/status.md",
                        "line_range": [3, 4],
                        "excerpt": "Daily status report without design-bearing detail.",
                    }
                ],
            },
        ],
    )
    input_payload = collect_module.collect_input_payload(run_root)

    reduction = reduce_module.reduce_f0_input(input_payload)

    assert reduction["candidate_chunk_count"] > 0
    assert reduction["selected_chunk_count"] > 0
    assert any(row["guardrail_preserved"] for row in reduction["selected_chunks"])
    assert any(
        "pm" in row["content"].lower() or "governance" in row["content"].lower()
        for row in reduction["selected_chunks"]
    )


def test_batch_merges_are_stable_and_rewrite_ids() -> None:
    reduce_module = load_reduce_module()
    f0_first = {
        "status": "OK",
        "design_claims_raw": {
            "schema": "DESIGN_CLAIMS_RAW@v1",
            "items": [
                {
                    "id": "z",
                    "path": "docs/b.md",
                    "line_range": [5, 7],
                    "claim_text": "B claim",
                    "source_artifact": "B.json",
                    "plane": "pm",
                    "evidence": [{"path": "docs/b.md", "line_range": [5, 7], "excerpt": "B"}],
                }
            ],
        },
        "missing_evidence": [],
    }
    f0_second = {
        "status": "OK",
        "design_claims_raw": {
            "schema": "DESIGN_CLAIMS_RAW@v1",
            "items": [
                {
                    "id": "a",
                    "path": "docs/a.md",
                    "line_range": [1, 2],
                    "claim_text": "A claim",
                    "source_artifact": "A.json",
                    "plane": "control",
                    "evidence": [{"path": "docs/a.md", "line_range": [1, 2], "excerpt": "A"}],
                }
            ],
        },
        "missing_evidence": [],
    }
    merged_f0 = reduce_module.merge_f0_batch_payloads([f0_first, f0_second])
    assert [row["id"] for row in merged_f0["design_claims_raw"]["items"]] == ["f0-000001", "f0-000002"]
    assert [row["path"] for row in merged_f0["design_claims_raw"]["items"]] == ["docs/a.md", "docs/b.md"]

    l0_first = {
        "status": "OK",
        "feature_candidates_raw": {
            "schema": "FEATURE_CANDIDATES_RAW@v1",
            "items": [
                {
                    "id": "2",
                    "path": "docs/feature.md",
                    "line_range": [3, 4],
                    "title": "Sync",
                    "trigger": "task",
                    "outcome": "sync",
                    "domain": "planning",
                    "plane": "pm",
                    "evidence_class": "REPO_PROVEN_CURRENT",
                    "temporal_status": "current",
                    "evidence": [{"path": "docs/feature.md", "line_range": [3, 4], "excerpt": "Sync"}],
                }
            ],
        },
        "missing_evidence": [],
    }
    l0_second = {
        "status": "OK",
        "feature_candidates_raw": {
            "schema": "FEATURE_CANDIDATES_RAW@v1",
            "items": [
                {
                    "id": "1",
                    "path": "docs/feature.md",
                    "line_range": [3, 4],
                    "title": "Sync",
                    "trigger": "task",
                    "outcome": "sync",
                    "domain": "planning",
                    "plane": "pm",
                    "evidence_class": "REPO_PROVEN_CURRENT",
                    "temporal_status": "current",
                    "evidence": [{"path": "docs/feature.md", "line_range": [3, 4], "excerpt": "Sync"}],
                }
            ],
        },
        "missing_evidence": [],
    }
    merged_l0 = reduce_module.merge_l0_batch_payloads([l0_first, l0_second])
    assert [row["id"] for row in merged_l0["feature_candidates_raw"]["items"]] == ["l0-000001"]
    assert merged_l0["feature_candidates_raw"]["items"][0]["title"] == "Sync"


def test_large_run_reduced_fake_executor_stays_non_empty(tmp_path: Path) -> None:
    run_module = load_run_module()
    run_root = build_large_fl_int_run_root(tmp_path)
    out_root = tmp_path / "postprocess"

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        assert "{{FL_INT_INPUT_JSON}}" not in rendered_prompt
        assert "{{PRIOR_OUTPUTS_JSON}}" not in rendered_prompt
        return {"payload": fake_fl_int_payload(step.step_id)}

    summary = run_module.run_fl_int(run_root, dry_run=False, out_root=out_root, prompt_executor=fake_executor)
    assert summary["status"] == "OK"
    f0_payload = json.loads((out_root / "DESIGN_CLAIMS_RAW.json").read_text(encoding="utf-8"))
    l0_payload = json.loads((out_root / "FEATURE_CANDIDATES_RAW.json").read_text(encoding="utf-8"))
    assert len(f0_payload["items"]) > 0
    assert len(l0_payload["items"]) > 0
