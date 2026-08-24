"""RTE-TRUTH R3-005c regression tests.

Covers HIGH finding F-24 ("T-phase load-bearing contract marooned in the
non-normative Legacy block; generic boilerplate is normative", A3c C2) and HIGH
finding F-26 ("TP_BACKLOG_TOPN.json multi-writer collision — T0/T1/T5 all write,
all declare canonical=T9", A3c H1), plus the T-phase slice of HIGH finding F-27
("Determinism-rule violation baked into T0/T1 legacy schemas: required
run_id/generated_at vs Determinism ban", A3c H2), all from
claudedocs/rte-truth-program-2026-07/A3c-prompts-QRST.md (audit branch
claude/rte-audit-improvement-f4beb7, commit 478265eff9).

F-26 mechanism (confirmed in source, not assumed from the finding title):
T0, T1, and T5 each declared `TP_BACKLOG_TOPN.json` as their own step Output,
all with `canonical_writer_step_id: T9`. `run_extraction_v5.py`'s per-step
artifact-write path (`out_path = norm_dir / artifact_name`, ~line 8819) writes
directly into the shared phase norm_dir per step being processed, and phase
steps run concurrently via a `ThreadPoolExecutor` (confirmed present:
`from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor,
as_completed`, executor selection ~line 16738, `as_completed(future_map)`
~line 16747) — so three physically distinct threads could race to write the
same `norm/TP_BACKLOG_TOPN.json` path with three different, un-merged
payloads, and whichever finishes last silently wins (last-writer-wins, not a
real merge: `run_extraction_v5.py` only merges partitions *within* a single
step's own output, never across different steps writing the same
artifact_name). Separately, T1's own Legacy Context (its real, hand-authored
contract) never listed `TP_BACKLOG_TOPN.json` as an output at all -- the
normative Outputs section had drifted to add it as a third, spurious writer.

Fix: renamed T0's contribution to `TP_BACKLOG_TOPN_DRAFT.json` and T5's to
`TP_BACKLOG_TOPN_ORDERED.json` (each is now the sole writer of its own
filename), removed the spurious `TP_BACKLOG_TOPN.json` output from T1
entirely, and made T9 (the only remaining writer of the literal
`TP_BACKLOG_TOPN.json` filename) explicitly merge the two renamed
intermediate artifacts via `itemlist_by_id`. `artifacts.yaml` and
`promptset.yaml` were updated to match, and `prompt_artifact_coverage_map.json`
(the checked-in prompt-hash/output ledger under promptsets/v4/) was updated
with matching outputs and recomputed `prompt_sha256` values for every prompt
file this packet edited.

KNOWN GAP (OUT-OF-BOUNDARY for this packet, not silently absorbed): this
packet's allowlist is `services/repo-truth-extractor/promptsets/v4/` and
`services/repo-truth-extractor/tests/` only. `reports/repo_truth_map.json`
(repo-root level, outside promptsets/v4/) is a SEPARATE checked-in snapshot
that `lib.phase_contract_map.get_step_contract()` actually reads for
`expected_artifacts` -- confirmed by reading `lib/phase_contract_map.py`
(`_repo_truth_declared_by_key` loads `REPO_TRUTH_MAP_PATH`, and
`expected_artifacts` in the compiled step contract comes *only* from that
file's `steps[].prompt_declared.expected_artifacts`, never from
promptset.yaml's own `outputs:` list). It still lists the old
`TP_BACKLOG_TOPN.json` name for T0/T1/T5 as of this commit, so the *live*
`get_step_contract("T", "T0")` compiled contract does NOT yet reflect this
fix -- only the prompt text / promptset.yaml / artifacts.yaml static contracts
do. Likewise `run_extraction_v5.py`'s `DEFAULT_OUTPUT_BY_STEP = {"T1":
("TP_BACKLOG_TOPN.json",)}` fallback (a latent regression trap that would
silently reintroduce the T1 collision if T1's Outputs section ever became
unparseable) is untouched. Both are real runtime files outside this packet's
allowlist; patching them is a required follow-up, not something this test
file can honestly claim is done. No test below asserts on either file.

F-24 mechanism: T0/T1/T3's normative `## Goal`/`## Inputs` were generic
boilerplate ("Focus on concrete, machine-verifiable implementation facts",
a repo-scan-shaped Inputs list) while the real contract -- required packet
header keys, required packet sections, authority hierarchy, no-rescan rule,
stop conditions -- lived only in the non-normative `## Legacy Context`
block. Fix: promoted the real contract into a new normative
"Required packet contract (promoted from Legacy Context)" subsection under
`## Schema` for T0, T1, and T3, and replaced the repo-scan-shaped Inputs on
T0/T1 with the correct arbitration-only (R/X norm artifact) input list.

F-27 (T-phase slice): T0's and T1's Legacy Context required-schema-key lists
for `TP_BACKLOG_TOPN_DRAFT.json` / `TP_PACKET_IMPLEMENTATION_INDEX.json`
included `run_id` and `generated_at`, which PROMPTSET_RULES.md's Determinism
Rules explicitly ban from norm outputs. Removed both bullet lines from each.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
RTE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"
PROMPTS_DIR = RTE_ROOT / "promptsets" / "v4" / "prompts"
PROMPTSET_YAML = RTE_ROOT / "promptsets" / "v4" / "promptset.yaml"
ARTIFACTS_YAML = RTE_ROOT / "promptsets" / "v4" / "artifacts.yaml"

T_PROMPT_FILES = {
    "T0": PROMPTS_DIR / "PROMPT_T0_TASK_PACKET_FACTORY.md",
    "T1": PROMPTS_DIR / "PROMPT_T1_EMIT_TASK_PACKETS___TOP10.md",
    "T2": PROMPTS_DIR / "PROMPT_T2_PACKET_SCHEMA___AUTHORITY_RULES.md",
    "T3": PROMPTS_DIR / "PROMPT_T3_PACKET_GENERATION___BATCHED.md",
    "T4": PROMPTS_DIR / "PROMPT_T4_PACKET_DEDUP___COLLISION_RESOLUTION.md",
    "T5": PROMPTS_DIR / "PROMPT_T5_PACKET_ORDERING___RUN_PLAN.md",
    "T9": PROMPTS_DIR / "PROMPT_T9_MERGE___QA.md",
}


def _text(step_id: str) -> str:
    return T_PROMPT_FILES[step_id].read_text(encoding="utf-8")


def _promptset() -> dict:
    return yaml.safe_load(PROMPTSET_YAML.read_text(encoding="utf-8"))


def _artifacts() -> dict:
    return yaml.safe_load(ARTIFACTS_YAML.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# F-26 (HIGH) part 1: promptset.yaml declares TP_BACKLOG_TOPN.json as an
# Output for exactly one step (T9) -- the multi-writer collision is gone.
# ---------------------------------------------------------------------------


def test_tp_backlog_topn_json_has_exactly_one_declared_writer_in_promptset() -> None:
    promptset = _promptset()
    writers = [
        step["step_id"]
        for step in promptset["phases"]["T"]["steps"]
        if "TP_BACKLOG_TOPN.json" in step.get("outputs", [])
    ]
    assert writers == ["T9"], writers


def test_t0_writes_a_distinctly_named_draft_not_the_canonical_filename() -> None:
    promptset = _promptset()
    t0 = next(s for s in promptset["phases"]["T"]["steps"] if s["step_id"] == "T0")
    assert "TP_BACKLOG_TOPN_DRAFT.json" in t0["outputs"]
    assert "TP_BACKLOG_TOPN.json" not in t0["outputs"]


def test_t5_writes_a_distinctly_named_ordered_revision_not_the_canonical_filename() -> None:
    promptset = _promptset()
    t5 = next(s for s in promptset["phases"]["T"]["steps"] if s["step_id"] == "T5")
    assert "TP_BACKLOG_TOPN_ORDERED.json" in t5["outputs"]
    assert "TP_BACKLOG_TOPN.json" not in t5["outputs"]


def test_t1_no_longer_declares_the_spurious_backlog_output() -> None:
    """T1's own Legacy Context never listed TP_BACKLOG_TOPN.json as an output --
    it was a spurious third writer introduced by contract drift."""
    promptset = _promptset()
    t1 = next(s for s in promptset["phases"]["T"]["steps"] if s["step_id"] == "T1")
    assert "TP_BACKLOG_TOPN.json" not in t1["outputs"]
    assert set(t1["outputs"]) == {
        "TP_PACKETS_TOP10.partX.md",
        "TP_PACKET_IMPLEMENTATION_INDEX.json",
    }


# ---------------------------------------------------------------------------
# F-26 (HIGH) part 2: artifacts.yaml registers the two renamed intermediate
# artifacts with the correct sole canonical writer each, and the canonical
# filename itself still resolves to exactly one row with T9 as writer.
# ---------------------------------------------------------------------------


def test_artifacts_yaml_registers_the_renamed_intermediate_backlog_artifacts() -> None:
    rows = {
        (row["phase"], row["artifact_name"]): row for row in _artifacts()["artifacts"]
    }
    draft = rows.get(("T", "TP_BACKLOG_TOPN_DRAFT.json"))
    ordered = rows.get(("T", "TP_BACKLOG_TOPN_ORDERED.json"))
    canonical = rows.get(("T", "TP_BACKLOG_TOPN.json"))

    assert draft is not None, "TP_BACKLOG_TOPN_DRAFT.json missing from artifacts.yaml"
    assert ordered is not None, "TP_BACKLOG_TOPN_ORDERED.json missing from artifacts.yaml"
    assert canonical is not None, "TP_BACKLOG_TOPN.json missing from artifacts.yaml"

    assert draft["canonical_writer_step_id"] == "T0"
    assert ordered["canonical_writer_step_id"] == "T5"
    assert canonical["canonical_writer_step_id"] == "T9"

    # Both renamed intermediates use a known-implemented kind/merge_strategy pair
    # (never invent new runtime enum values -- see RTE-TRUTH R3-005e revert).
    for row in (draft, ordered):
        assert row["kind"] == "json_item_list"
        assert row["merge_strategy"] == "itemlist_by_id"


def test_artifacts_yaml_has_no_duplicate_or_conflicting_canonical_writer_rows() -> None:
    """Mirrors scripts/repo_truth_extractor_promptset_audit_v4.py's own
    _canonical_uniqueness_issues check: each (phase, artifact_name) key must
    appear once, with one canonical_writer_step_id."""
    seen: dict[tuple[str, str], str] = {}
    for row in _artifacts()["artifacts"]:
        key = (row["phase"], row["artifact_name"])
        writer = row["canonical_writer_step_id"]
        assert key not in seen, f"duplicate artifact registry entry: {key}"
        seen[key] = writer
    assert seen[("T", "TP_BACKLOG_TOPN.json")] == "T9"
    assert seen[("T", "TP_BACKLOG_TOPN_DRAFT.json")] == "T0"
    assert seen[("T", "TP_BACKLOG_TOPN_ORDERED.json")] == "T5"


# ---------------------------------------------------------------------------
# F-26 (HIGH) part 3: T9's own Schema/Extraction Procedure explicitly names
# the itemlist_by_id merge of the two renamed intermediates into the
# canonical filename, and no other step's prompt text still names the
# canonical filename as something it personally writes.
# ---------------------------------------------------------------------------


def test_t9_prompt_text_documents_the_two_source_merge_into_canonical_backlog() -> None:
    text = _text("T9")
    assert "TP_BACKLOG_TOPN_DRAFT.json" in text
    assert "TP_BACKLOG_TOPN_ORDERED.json" in text
    assert "itemlist_by_id" in text


@pytest.mark.parametrize("step_id", ["T0", "T1", "T5"])
def test_non_canonical_steps_no_longer_declare_the_canonical_backlog_output(step_id: str) -> None:
    """T0/T1/T5's own '## Outputs' section must not list the literal
    TP_BACKLOG_TOPN.json filename any more (that is T9's sole output)."""
    text = _text(step_id)
    outputs_start = text.index("## Outputs")
    schema_start = text.index("## Schema")
    outputs_body = text[outputs_start:schema_start]
    assert "TP_BACKLOG_TOPN.json" not in outputs_body


# ---------------------------------------------------------------------------
# F-24 (HIGH): T0/T1/T3 real contract promoted into the normative Schema
# section, no longer marooned solely in the non-normative Legacy block.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step_id", ["T0", "T1", "T3"])
def test_promoted_contract_marker_present_outside_legacy_block(step_id: str) -> None:
    text = _text(step_id)
    legacy_start = text.index("## Legacy Context")
    normative_body = text[:legacy_start]
    assert "promoted from Legacy Context" in normative_body, (
        f"{step_id} has no normative promoted-contract marker before its "
        "Legacy Context block"
    )
    assert "RTE-TRUTH F-24" in normative_body


# T0 authors the JSON backlog draft (packets[].<field> keys); T1 authors the
# packet markdown itself (human-readable section titles); T3 batches the same
# markdown packets (lowercase prose list, matching its own Legacy source).
# Each step's promoted contract must carry the markers that are actually
# load-bearing for *that* step's own output shape.
_PACKET_CONTRACT_MARKERS = {
    "T0": ("scope_in", "scope_out", "invariants", "acceptance_criteria", "stop_conditions"),
    "T1": ("Objective", "Invariants", "Acceptance criteria", "Stop conditions"),
    "T3": ("objective", "invariants", "acceptance criteria", "stop conditions"),
}


@pytest.mark.parametrize("step_id", ["T0", "T1", "T3"])
def test_required_packet_sections_are_normative_not_legacy_only(step_id: str) -> None:
    text = _text(step_id)
    legacy_start = text.index("## Legacy Context")
    normative_body = text[:legacy_start]
    for marker in _PACKET_CONTRACT_MARKERS[step_id]:
        assert marker in normative_body, (
            f"{step_id}: required packet marker {marker!r} is not present in the "
            "normative body (only Legacy Context would not satisfy F-24)"
        )


@pytest.mark.parametrize("step_id", ["T0", "T1"])
def test_repo_scan_framing_removed_from_arbitration_only_steps(step_id: str) -> None:
    text = _text(step_id)
    assert "Source scope (scan these roots first)" not in text, (
        f"{step_id} still frames its Inputs as a repo scan, contradicting the "
        "arbitration-only / no-rescan design (RTE-TRUTH L2)"
    )


# ---------------------------------------------------------------------------
# F-27 (HIGH, T-phase slice): run_id/generated_at stripped from T0/T1 Legacy
# required-schema-key lists.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step_id", ["T0", "T1"])
def test_t0_t1_legacy_schema_no_longer_requires_run_id_or_generated_at(step_id: str) -> None:
    text = _text(step_id)
    for key in ("run_id", "generated_at"):
        assert not re.search(rf"(?m)^-\s*{key}\s*$", text), (
            f"{step_id} Legacy Context still lists {key!r} as a required schema key "
            "bullet, violating PROMPTSET_RULES.md Determinism Rules"
        )


# ---------------------------------------------------------------------------
# Consistency: prompt_artifact_coverage_map.json (the checked-in prompt-hash
# ledger under promptsets/v4/) was updated to match -- both the renamed
# outputs and the recomputed prompt_sha256 for every prompt file this packet
# edited, so the ledger does not silently drift from the prompts on disk.
# ---------------------------------------------------------------------------


def test_prompt_artifact_coverage_map_matches_edited_prompt_files_on_disk() -> None:
    import hashlib
    import json

    coverage_path = RTE_ROOT / "promptsets" / "v4" / "prompt_artifact_coverage_map.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    rows = {row["step_id"]: row for row in coverage["phases"]["T"]}

    edited_steps = ("T0", "T1", "T2", "T3", "T4", "T5", "T9")
    for step_id in edited_steps:
        row = rows[step_id]
        prompt_path = REPO_ROOT / row["prompt_file"]
        expected_digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        assert row["prompt_sha256"] == expected_digest, (
            f"prompt_artifact_coverage_map.json prompt_sha256 for {step_id} is stale "
            f"relative to {prompt_path}"
        )

    assert rows["T0"]["outputs"] == ["PROJECT_INSTRUCTIONS.md", "TP_BACKLOG_TOPN_DRAFT.json", "TP_INDEX.json"]
    assert rows["T1"]["outputs"] == ["TP_PACKETS_TOP10.partX.md", "TP_PACKET_IMPLEMENTATION_INDEX.json"]
    assert rows["T5"]["outputs"] == ["TP_RUN_PLAN.json", "TP_BACKLOG_TOPN_ORDERED.json"]
    assert "TP_BACKLOG_TOPN.json" in rows["T9"]["outputs"]
