---
title: "doc_audit_prescan.py — Reference"
category: reference
tags:
- documentation
- audit
- scripts
- grok
- xai
- litellm
- classification
created: 2026-03-14
updated: 2026-03-14
date: 2026-03-14
author: Dopemux Team
id: doc-audit-prescan-reference
type: reference
owner: '@hu3mann'
last_review: '2026-03-14'
next_review: '2026-06-14'
prelude: >
  Complete reference for scripts/doc_audit_prescan.py — a single-file corpus
  walker, authority classifier, and Grok 4.20 Beta caller for documentation
  auditing. Covers CLI options, authority classes, output artifacts, classifier
  rules, and configuration schema.
---
# `doc_audit_prescan.py` — Reference

**Location:** `scripts/doc_audit_prescan.py`
**Config:** `scripts/doc_audit_prescan.toml`
**Output:** `extraction/prescan/` (gitignored)
**Version:** 1.0.0

Single-file Python script (~900 lines). No install required — uses only stdlib plus optional `openai` for direct mode.

## CLI

```
python scripts/doc_audit_prescan.py MODE [OPTIONS]

Positional:
  MODE                    dry-run | direct | handoff

Options:
  --repo-root PATH        (default: git rev-parse --show-toplevel)
  --output-dir PATH       (default: extraction/prescan/)
  --config PATH           (default: scripts/doc_audit_prescan.toml)
  --max-file-size SIZE    (default: 100KB)
  --max-corpus-size SIZE  (default: 50MB)
  --include GLOB          (repeatable, additive)
  --exclude GLOB          (repeatable, additive)
  --model MODEL           (default: grok-4.20-beta-0309-non-reasoning)
  --provider PROVIDER     (default: xai)
  --verbose / -v
  --force                 (override corpus size limit)
```

## Execution Modes

| Mode | Description | Network? |
|------|-------------|---------|
| `dry-run` | Walk + classify + write manifests | ❌ None |
| `direct` | dry-run + package payload + call Grok | ✅ xAI API |
| `handoff` | dry-run + package payload + write bundle | ❌ None |

## Authority Classes

| Class | Description | Examples |
|-------|-------------|---------|
| `canonical` | Active architecture, current configs, live specs | `docs/planes/`, ADRs, RFCs, `model_map_v2_tp008.yaml` |
| `historical` | Archived plans, past decisions (valuable, not noise) | `docs/archive/`, `SYSTEM_ARCHIVE/` |
| `operational` | Runbooks, how-tos, setup guides | `docs/02-how-to/`, `README.md`, `INSTALL.md` |
| `audit` | Reports, analysis outputs, proof bundles | `reports/`, `proof/` |
| `template` | Prompt/skill templates, schema files | `templates/`, `.claude/prompts/` |
| `generated` | Auto-generated extraction results | `extraction/runs/`, doctor output |
| `noise` | Binaries, caches, vendored deps | `*.pyc`, images, `.venv/` |

## Classifier Rules (Priority Order)

Rules are applied top-to-bottom; first match wins.

1. **noise** — binary extensions (`.pyc`, `.so`, images, archives, etc.)
2. **generated** — `extraction/*/runs/` paths, `latest_run_id*` files, `out/` dir
3. **template** — `templates/`, `.claude/prompts/`, `.claude/modules/`, `UPGRADES/promptgen/`, `promptsets/`
4. **historical** — `archive/`, `deprecated`, `SYSTEM_ARCHIVE/`, `completed-projects/`, `implementation-history/`
5. **audit** — `reports/` (top-level), `proof/` (top-level), `audit` in filename
6. **operational** — `92-runbooks/`, `02-how-to/`, `01-tutorials/`, `README.md`, `INSTALL.md`, `QUICK_START.md`
7. **canonical** — `planes/`, `03-reference/`, `04-explanation/`, `90-adr/`, `91-rfc/`, `CLAUDE.md`, root configs
8. **canonical** (fallback) — any remaining file in `docs/`, `.claude/`, `UPGRADES/`
9. **generated** (default) — everything else

## Output Artifacts

All output goes to `extraction/prescan/` (configurable via `--output-dir`).

### Always written (`dry-run`, `direct`, `handoff`)

| File | Description |
|------|-------------|
| `corpus_manifest.json` | Every scanned file: path, size, class, include/exclude, reason, SHA256 |
| `included_files.txt` | Bare paths of included files, one per line |
| `excluded_files.txt` | `path\treason` for each excluded file |
| `corpus_stats.json` | Counts/sizes by authority class, extension, and top-level directory |
| `run_metadata.json` | Timestamp, mode, git SHA, git branch, config hash, script version |

### Written for `direct` and `handoff`

| File | Description |
|------|-------------|
| `audit_payload.md` | All included files truncated to 200 lines / 8KB, grouped by class |

### Written for `direct` only

| File | Description |
|------|-------------|
| `grok_response.json` | Parsed JSON classifications from Grok |
| `grok_call_metadata.json` | Token usage, model, finish reason |
| `grok_error.json` | Error details if call fails |

### Written for `handoff` only (`handoff_bundle/`)

| File | Description |
|------|-------------|
| `prompt.md` | System + user prompt |
| `corpus/<class>.md` | Per-class content files |
| `manifest.json` | Copy of corpus_manifest.json |
| `routing.json` | Model/provider/base_url for LiteLLM |
| `instructions.md` | How to execute via Python, LiteLLM proxy, or CLI agent |
| `checksums.json` | SHA256 for all bundle files |

## Configuration Schema (`doc_audit_prescan.toml`)

```toml
[corpus]
max_file_size = "100KB"       # files larger than this are excluded
max_corpus_size = "50MB"      # abort if corpus exceeds this (override with --force)
exclude_globs = [...]         # additional glob patterns to exclude
include_globs = []            # additional glob patterns to include

[corpus.large_json_threshold]
max_bytes = 512000            # JSON files above 500KB are auto-excluded

[model]
default = "grok-4.20-beta-0309-non-reasoning"
provider = "xai"
base_url = "https://api.x.ai/v1"
api_key_env = "XAI_API_KEY"
temperature = 0.1
max_response_tokens = 200000

[model.litellm_fallback]
model_name = "xai/grok-4.20-beta-0309-non-reasoning"
proxy_url = "http://localhost:4000"

[output]
default_dir = "extraction/prescan"
```

## Hardcoded Excludes

These directories are always excluded regardless of config:

```
node_modules  .venv  venv  __pycache__  .git  dist  build
.mypy_cache  .pytest_cache  .ruff_cache  htmlcov  .tox  .eggs
```

## File Type Handling

- **Included extensions:** `.md .mdx .txt .yaml .yml .toml .json .py .sh .cfg .ini .rst .csv .env .html .css .js .ts .tsx .jsx`
- **Excluded (binary):** images, fonts, archives, compiled objects, media, databases
- **Unknown extensions:** excluded with reason `unknown_extension:<ext>`
- **Large JSON (>500KB):** excluded with reason `large_json_blob`

## Safety Guards

- Corpus size gate: >50MB aborts unless `--force`
- File size gate: >100KB auto-excluded (configurable)
- API key checked before any network call
- Manifests written before model call — partial results preserved on failure
- Never deletes or modifies source files
- Deterministic output: sorted paths, `sort_keys=True`, reproducible hashes

## Grok Response Format

```json
{
  "classifications": [
    {
      "path": "relative/file/path",
      "proposed_class": "canonical",
      "confirmed_class": "canonical",
      "confidence": 0.95,
      "reasoning": "Active ADR with current system references",
      "signals": ["has ADR frontmatter", "references active service"]
    }
  ]
}
```

## Dependencies

All already available in the repo environment:

| Package | Use | Source |
|---------|-----|--------|
| `tomllib` | TOML config loading | Python 3.11+ stdlib |
| `openai>=1.0.0` | xAI API calls (`direct` mode only) | `pyproject.toml` |
| `pathlib`, `hashlib`, `subprocess`, `fnmatch`, `argparse`, `json`, `logging` | Core logic | stdlib |
