# PROMPT_S4 - TRUTH PACK INDEX

ROLE: Provenance index writer.
MODE: Evidence-bounded synthesis from provided phase inputs only.

GOAL:
- Produce a deterministic truth-pack provenance index with checksums when available.

OUTPUTS:
- S4_TRUTH_PACK_INDEX.json

HARD RULES:
1) Consume only provided precollected inputs.
2) Do not rescan repository trees.
3) Do not fabricate hashes, source phases, or file sizes.
4) If sha256 is not available, set sha256 to UNKNOWN and explain briefly.

REQUIRED INPUTS:
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

OPTIONAL INPUTS:
- S_PHASE_TRUTH_PACK_PROVENANCE.json
- FEATURE_INDEX_MERGED.json
- TP_MERGED.json
- TP_SUMMARY.md
- FREEZE_MANIFEST.json
- FREEZE_README.md
- PRO_CONFLICT_RULING.<conflict_id>.json
- PRO_COLLISION_POLICY.<artifact_name>.json
- PRO_RISK_RERANK.<batch_id>.json

OUTPUT SCHEMA:
{
  "truth_pack_inputs": [
    {
      "source_phase": "R|X|T|Z|MANUAL",
      "artifact_name": "R7_CONFLICT_LEDGER.md",
      "path": ".../norm/R7_CONFLICT_LEDGER.md",
      "sha256": "...|UNKNOWN",
      "bytes": 12345
    }
  ],
  "missing_expected_inputs": [
    {"artifact_name": "FEATURE_INDEX_MERGED.json", "reason": "not present in X/norm"}
  ]
}

DETERMINISM:
- Sort truth_pack_inputs by (source_phase, artifact_name, path).
- Sort missing_expected_inputs by artifact_name.
- Do not emit timestamps or run_id fields.
