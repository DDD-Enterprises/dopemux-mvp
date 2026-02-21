# PROMPT_Z0 — Handoff freeze digest + archive manifest

ROLE: Freeze/handoff bot.
GOAL: Produce a deterministic digest of this run, what artifacts exist, what is missing, and what Opus should ingest.

OUTPUTS:
  • HANDOFF_DIGEST.md
    - includes run_id, phase completion summary, key artifact paths, known blockers, and recommended next run command
  • ARCHIVE_MANIFEST.json
    - files[]: {path, bytes, sha256, phase, category(raw/norm/qa/prompt)}
  • OPUS_CONTEXT_BUNDLE_INDEX.json
    - bundle[]: {topic, recommended_files[], why}

RULES:
  • No interpretation of truth. Only index and summarize structure.
  • sha256 must be computed by the runner or marked UNKNOWN if unavailable.
