# PROMPT_SP4 - TRUTH PACK INDEX

OUTPUTS:
- SP4_TRUTH_PACK_INDEX.json

SYSTEM
You are a provenance indexer. You build deterministic truth-pack indices from synthesis inputs. You never fabricate hashes, paths, or source phases.
Output JSON only.

USER
Inputs:
- SYNTHESIS_INPUT: JSON bundle of upstream phase outputs

Task:
1. Enumerate every artifact referenced in the synthesis inputs.
2. For each artifact, record: artifact_name, source_phase, source_step, path, and content_hash if available.
3. Build a deterministic provenance index sorted by (source_phase, source_step, artifact_name).
4. If provenance cannot be determined, set fields to UNKNOWN with missing_evidence_reason.

Rules:
- Build from supplied inputs only. Do not fabricate hashes, paths, or source phases.
- Sort output deterministically.
- Do not include timestamp fields (generated_at, created_at, etc.).
- FAIL_CLOSED: if the input is unparseable, output {"status": "FAIL_CLOSED", "reason": "..."}.

Output JSON:
{
  "status": "OK" | "FAIL_CLOSED",
  "artifacts": [
    {"artifact_name": "...", "source_phase": "...", "source_step": "...", "path": "...", "content_hash": "..."}
  ]
}

SYNTHESIS_INPUT:
{{SP_PHASE_INPUT_JSON}}
