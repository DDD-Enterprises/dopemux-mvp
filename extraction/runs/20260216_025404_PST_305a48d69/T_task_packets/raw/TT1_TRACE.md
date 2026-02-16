# SYSTEM PROMPT\nMODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase T1: Emit Task Packets (Top 10)

Outputs:
- docs/task-packets/TP-*.md (or staged outputs)

Prompt:
ROLE: GPT-5.2 (arbitration).
Inputs: TP_BACKLOG_TOPN.json

Action:
Generate complete Task Packet markdowns for the top 10 items in the backlog.
Each packet must standalone for a Sonnet/Opus coder.
\n\n# USER CONTEXT\n... [truncated for trace]