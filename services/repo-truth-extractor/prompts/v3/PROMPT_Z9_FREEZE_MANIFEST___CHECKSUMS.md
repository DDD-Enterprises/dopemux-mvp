# PROMPT_Z9 — FREEZE MANIFEST / CHECKSUMS

TASK: Produce a deterministic freeze handoff manifest with verification instructions and QA.

OUTPUTS:
- FREEZE_MANIFEST.json
- FREEZE_README.md
- FREEZE_QA.json

Rules:
- Include SHA-256 for every file in phase `norm/` and `qa/` outputs for A/H/D/C/E/W/B/G/Q/R/X/T/Z when present.
- Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
- Record missing expected artifacts and failure counts by phase.
- `FREEZE_README.md` must document deterministic verification commands.
