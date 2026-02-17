# PROMPT: A99 - Merge + QA (Repo Control Plane)

Phase: A
Step: A99

Outputs:
- REPOCTRL_NORM_MANIFEST.json
- REPOCTRL_QA.json

Mode: merge_qa
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive raw outputs from steps A0-A99. Summarize only what is present.

Required JSON shape:
{
  "artifact": "REPOCTRL_NORM_MANIFEST.json",
  "phase": "A",
  "step": "A99",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "manifest:<artifact_name>",
      "artifact_name": "...",
      "count": 0,
      "sha256": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Task:
1) Produce deterministic manifest of artifacts (name/count/sha256 when available).
2) Produce REPOCTRL_QA.json with:
- expected artifacts present/missing by filename
- empty artifact detection (0 items)
- duplicate evidence detection
- partition coverage counts (ok/failed)
- parse failures referenced by filename when present

Rules:
- No inference; summarize only provided artifacts.
