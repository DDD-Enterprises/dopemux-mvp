MODE: Mechanical extractions unless explicitly marked ARBITRATION (GPT-5.2).
NO INTERPRETATION: No "purpose", "likely", "should", "means".
EVIDENCE REQUIRED: Every extracted item must include path + line_range.
OUTPUT: JSON only for scan phases. Markdown only for arbitration phases.
STABLE ORDER: Sort lists by path, then line_range[0], then id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase E1: Exec Command Index + What Starts What (Part X)

Run per partition from E0.

Outputs:
- EXEC_COMMAND_INDEX.partX.json
- EXEC_SIDE_EFFECTS.partX.json
- CAP_NOTICES.E1.partX.json (optional)

Prompt:
Parse partition files to extract:
- executable commands and their arguments
- referenced services, compose project names, profiles
- referenced env vars (names only)
- referenced paths (read/write)
- network/ports references

Output EXEC_COMMAND_INDEX.partX.json items:
- id, path, line_range, command, args, env_var_names[], reads[], writes[], calls_services[]

Output EXEC_SIDE_EFFECTS.partX.json:
- write targets, DB paths, "out/" usage, logs dirs, cache dirs
