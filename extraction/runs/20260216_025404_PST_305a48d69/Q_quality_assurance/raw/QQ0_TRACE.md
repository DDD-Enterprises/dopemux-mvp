# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase Q0: Pipeline Doctor + Coverage & Schema

Outputs:
- PIPELINE_DOCTOR_REPORT.json

Prompt:
Input: all phase outputs in extraction/latest/**

Checks:
- required artifacts exist per phase
- each JSON item has required keys (path, line_range, stable id)
- no duplicate prompt collisions (same prefix)
- no CAP_NOTICES unresolved
- no secrets leakage (match only; do not print secret values)
- stable sorting verified

Emit PASS/WARN/FAIL with reasons and file lists.
\n\n# USER CONTEXT\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA8_OUTPUT.json ---\n{
  "artifact_type": "AA8_MOCK",
  "generated_at": "2026-02-16T07:33:06.971098",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA1_OUTPUT.json ---\n{
  "artifact_type": "AA1_MOCK",
  "generated_at": "2026-02-16T07:32:21.643065",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA4_OUTPUT.json ---\n{
  "artifact_type": "AA4_MOCK",
  "generated_at": "2026-02-16T07:32:44.450494",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA7_OUTPUT.json ---\n{
  "artifact_type": "AA7_MOCK",
  "generated_at": "2026-02-16T07:33:01.817669",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA2_OUTPUT.json ---\n{
  "artifact_type": "AA2_MOCK",
  "generated_at": "2026-02-16T07:32:28.694937",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA5_OUTPUT.json ---\n{
  "artifact_type": "AA5_MOCK",
  "generated_at": "2026-02-16T07:32:50.264138",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA0_OUTPUT.json ---\n{
  "artifact_type": "AA0_MOCK",
  "generated_at": "2026-02-16T07:32:14.856402",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA9_OUTPUT.json ---\n{
  "artifact_type": "AA9_MOCK",
  "generated_at": "2026-02-16T07:33:11.824351",
  "items": []
}\n\n--- FILE: /Users/hue/code/dopemux-mvp/extraction/runs/20260216_025404_PST_305a48d69/A_repo_control_plane/raw/AA3_OUTPUT.json ---\n{
  "artifact_type": "AA3_MO... [truncated for trace]