Title: Image Enrichment + Image Psychology — Checkpoint
Status: Saved | Owner: TBD | Last Updated: 2025-09-03 PT

Objective
- Append a local-first image enrichment pipeline with an image-specific psychology module, mapped to labels.yml, without changing Message or the existing text enrichment pipeline.

Key Decisions
- Sidecar: Use per-attachment sidecar `image_enrichment.jsonl`; do not alter Message.
- Schema: Added `schemas/image_enrichment.schema.json` including a `psych` block and shared `provenance`.
- Models (initial stance):
  - Caption/Grounding: Florence-2 (local, literal captions/tags).
  - Image Psychology (proposed default): Qwen2.5-VL (7B instruct) for social/psych inference; LLaVA-NeXT as alternative; InternVL 2.5 for heavier setups.
  - Append-only: No changes to existing text 4-pass pipeline or its models.
- Privacy: No biometric identification; only faces.count allowed; EXIF GPS → `has_gps` boolean only.

Repo Changes (committed)
- docs/design/specifications/image-enrichment.md — Full spec and append-only plan.
- schemas/image_enrichment.schema.json — Sidecar schema with `psych` block.
- tests/image_enrich/test_schema_validation.py — Minimal schema validation tests.

Open Questions / Research (pending Exa)
- Confirm best image-psych VLM via benchmarks (Qwen2.5-VL vs LLaVA-NeXT vs InternVL 2.5): determinism, JSON validity, psych/relational inference quality, latency/footprint.
- Quantization and packaging guidance for local deploy.

Next Steps (when tools are up)
- Bring MCP servers online (at minimum: DuckDuckGo, Sequential Thinking; Exa once package/endpoint is confirmed).
- Run the research plan: docs/research/image-psychology-model-research-plan.md
- Produce recommendation memo + update spec/ADR if needed.
- Start TDD slices (OCR → detector → caption → similarity → context → psych), keeping tiny diffs.

MCP One-Liners (for later)
- Sequential Thinking:
  claude mcp add-json sequential-thinking '{"type":"stdio","command":"npx","args":["-y","mcp-sequential-thinking"]}'
- DuckDuckGo:
  claude mcp add-json duckduckgo '{"type":"stdio","command":"npx","args":["-y","mcp-duckduckgo"],"env":{"DDG_REGION":"us-en"}}'
- Filesystem:
  claude mcp add-json filesystem '{"type":"stdio","command":"npx","args":["-y","mcp-filesystem","--root","."]}'
- GitHub (optional):
  claude mcp add-json github '{"type":"stdio","command":"npx","args":["-y","mcp-github"],"env":{"GITHUB_TOKEN":"'$GITHUB_TOKEN'"}}'
- Notion (optional):
  claude mcp add-json notion '{"type":"stdio","command":"npx","args":["-y","mcp-notion"],"env":{"NOTION_API_KEY":"'$NOTION_API_KEY'","NOTION_BASE_ID":"'$NOTION_BASE_ID'"}}'
- Context7 (optional):
  claude mcp add-json context7 '{"type":"stdio","command":"npx","args":["-y","@upstash/context7-mcp","--api-key","'$CONTEXT7_API_KEY'"]}'
- Exa: awaiting correct MCP package or hosted URL; placeholder removed until confirmed.

Local Validation Commands
- python -m pip install -e .[dev]
- ruff check .
- mypy src
- pytest

Ollama Notes
- Existing text enrichment uses Ollama for LLM (gemma2 by default). For image work, VLMs (Florence-2/Qwen2.5-VL) will run locally via their own runtimes (not Ollama) unless we create wrappers.
- If embeddings are needed elsewhere, ensure Ollama is up and models exist as per user’s snippet (nomic-embed-text), though not directly required for image-psych.

Resume Checklist
- Ensure MCP servers are connected (Sequential Thinking + DuckDuckGo now; Exa later).
- Run research plan → choose default image-psych VLM → update spec/ADR if needed.
- Begin with TDD slice PR-1 (OCR) and proceed vertically, ending with PR-7 (image psychology).