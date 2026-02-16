# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase Q1: Doc Recency + Duplicate Groups

Outputs:
- DOC_RECENCY_DUPLICATE_REPORT.json

Prompt:
Inputs: DOC_INVENTORY.json, DOC_DUPLICATES.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json

For each duplicate group:
- list docs with mtime, any explicit supersession markers, cluster membership
- emit needs_arbitration=true/false (mechanical criteria only)
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