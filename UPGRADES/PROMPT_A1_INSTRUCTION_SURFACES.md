Goal: REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json

Prompt:
- Find instruction-bearing files:
  - CLAUDE.md, AGENTS.md, **/custom-instructions/**, .claude/**, docs/** instruction docs, any *_PROMPT*.md
- Extract:
  - instruction blocks, "DO / DO NOT", invariants, tool invocation cues, server names, file paths referenced.
  - references graph: instruction file -> referenced file(s)/server(s).
- Output JSON with citations: file + line_range + quoted excerpt <= 2 lines.