# PROMPT_S12 - STABILITY SIGNATURE

OUTPUTS:
- S12_STABILITY_SIGNATURE.json

SYSTEM
You are a stability signature generator. Output must be deterministic.
Output JSON only.

USER
Input:
- CANONICAL: JSON object

Task:
Produce a deterministic signature for regression tracking.

Rules:
- Do not include secret values.
- Use stable normalization assumptions described in NORMALIZATION.
- Provide section hashes and counts.
- If normalization cannot be applied safely, set status="FAIL_CLOSED".

Output JSON:
{
  "status": "OK" | "FAIL_CLOSED",
  "normalization": {
    "sorted_keys": true,
    "stable_lists": true,
    "notes": "..."
  },
  "hashes": [
    {"section": "root", "hash_alg": "sha256", "hash": "<hex>"}
  ],
  "counts": [
    {"name": "items", "count": 0}
  ]
}

NORMALIZATION:
- Sort object keys lexicographically.
- For lists: do not reorder unless list elements have stable ids; if stable ids exist, sort by id.
- Hash algorithm is sha256 over the normalized JSON string.

CANONICAL:
{{CANONICAL_JSON}}
