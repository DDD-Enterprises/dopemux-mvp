# Prompt Template Refactoring Spec (F-19)

**Date**: 2026-02-22
**Finding**: F-19 — Boilerplate Dominance in Prompt Templates
**ROI**: ~168K tokens saved per full run (~$2-4 cost reduction), improved prompt quality

---

## 1. Problem Statement

All 105 prompt files share an identical template with ~80% boilerplate:
- Evidence Rules (~150 tokens) — identical across all prompts
- Determinism Rules (~120 tokens) — identical across all prompts
- Anti-Fabrication Rules (~100 tokens) — identical across all prompts
- Failure Modes (~100 tokens) — identical across all prompts
- Schema container descriptions (~80 tokens) — identical
- **Total repeated boilerplate**: ~550 tokens × 105 prompts = **~57,750 tokens per run** (conservative)

Including the full template structure overhead (section headers, runner context lines, etc.), the actual waste is closer to **~1,600 tokens × 105 = ~168K tokens**.

---

## 2. Architecture: Shared Preamble Injection

### 2.1 New File: `SYSTEM_PREAMBLE.md`

**Location**: `services/repo-truth-extractor/promptsets/v4/SYSTEM_PREAMBLE.md`

**Contents** (extract from current prompt template):

```markdown
# Repo Truth Extractor — System Rules

You are a mechanical fact extractor. Your job is to produce deterministic, evidence-backed
artifacts from repository source files. Follow these rules for ALL extraction steps.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
  ```json
  {
    "path": "<repo-relative-path>",
    "line_range": [<start>, <end>],
    "excerpt": "<exact substring <=200 chars>"
  }
  ```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Schema Containers
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Token limit exceeded: prioritize highest-evidence items, emit `coverage_notes: "truncated"`.
- Timeout: emit partial results with `status: "partial"` and `coverage_notes`.
- Conflicting upstream artifacts: keep all candidates with evidence, mark `status: needs_review`.
```

### 2.2 New Slim Prompt Template

Each per-step prompt file becomes focused on step-specific content only:

```markdown
# PROMPT_<STEP_ID>

## Goal
<1-2 sentences: what this step produces>

## Inputs
- Source scope: <file globs>
- Upstream artifacts: <list>
- Runner context: <list>

## Outputs
<artifact list with contracts>

## Schema Contracts
<per-artifact: kind, merge_strategy, canonical_writer, id_rule, required_fields>

## Extraction Procedure
<step-specific numbered instructions — this is the KEY differentiator>
1. <specific instruction>
2. <specific instruction>
...

## Legacy Context
<preserved as-is from current prompts>
```

**Removed from per-step prompts** (now in preamble):
- Evidence Rules section
- Determinism Rules section
- Anti-Fabrication Rules section
- Failure Modes section
- Generic Schema container description

**Result**: Each prompt shrinks from ~1,600 tokens to ~500-700 tokens.

---

## 3. Runner Injection Points

### 3.1 Loading the Preamble

**File**: `services/repo-truth-extractor/run_extraction_v3.py`
**New constant** (near line 490):

```python
SYSTEM_PREAMBLE_PATH = Path(__file__).resolve().parent / "promptsets" / "v4" / "SYSTEM_PREAMBLE.md"
```

**New function** (utility section):

```python
_SYSTEM_PREAMBLE_CACHE: Optional[str] = None

def load_system_preamble() -> str:
    """Load shared system preamble for prompt injection."""
    global _SYSTEM_PREAMBLE_CACHE
    if _SYSTEM_PREAMBLE_CACHE is not None:
        return _SYSTEM_PREAMBLE_CACHE
    prompt_root = os.environ.get("REPO_TRUTH_EXTRACTOR_PROMPT_ROOT")
    if prompt_root:
        preamble_path = Path(prompt_root) / "SYSTEM_PREAMBLE.md"
    else:
        preamble_path = SYSTEM_PREAMBLE_PATH
    if preamble_path.exists():
        _SYSTEM_PREAMBLE_CACHE = preamble_path.read_text(encoding="utf-8").strip()
    else:
        _SYSTEM_PREAMBLE_CACHE = ""
    return _SYSTEM_PREAMBLE_CACHE
```

### 3.2 Injection Point

The v3 runner constructs prompts in its `build_step_prompt` or equivalent function (the function that reads the prompt file and prepends context). The preamble should be injected as follows:

**Injection strategy**: Prepend preamble as a system message prefix.

Find the function in v3 that constructs the messages array for the API call. The preamble goes as the first system message content:

```python
# In the API call construction:
system_content = load_system_preamble()
if system_content:
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": step_prompt_content},
    ]
else:
    # Fallback: prompt contains everything (legacy mode)
    messages = [
        {"role": "user", "content": step_prompt_content},
    ]
```

**Alternative** (simpler, no message structure change): Prepend preamble text to the user prompt:

```python
preamble = load_system_preamble()
if preamble:
    full_prompt = f"{preamble}\n\n---\n\n{step_prompt_content}"
else:
    full_prompt = step_prompt_content
```

### 3.3 Backward Compatibility

The preamble injection is **additive**. If `SYSTEM_PREAMBLE.md` doesn't exist, the runner falls back to the full prompt (current behavior). This means:
- Old prompts with inline rules still work (rules appear twice — harmless)
- New slim prompts require the preamble file to exist
- Migration can be incremental (one phase at a time)

---

## 4. Token Savings Calculation

| Component | Current | After Refactor | Savings |
|-----------|---------|----------------|---------|
| Preamble (shared rules) | 0 tokens (inline) | ~550 tokens (once) | — |
| Per-prompt boilerplate | ~1,600 tokens × 105 | ~600 tokens × 105 | ~105,000 tokens |
| Total input per run | ~168K boilerplate | ~63K + 550 preamble | **~104,450 tokens** |
| Cost savings (@ $0.40/1M) | — | — | **~$0.04/run input** |
| Cost savings (@ $2.00/1M synthesis) | — | — | **~$0.21/run** |

**Total estimated savings**: **$0.50-$2.00 per full run** depending on model tier distribution.

The savings are more significant for synthesis-tier models ($2-8/1M tokens) where the boilerplate reduction on R/S/T/Z phases saves the most.

**Note**: The bigger win is **prompt quality** — step-specific extraction guidance is no longer buried under boilerplate, making extraction more accurate.

---

## 5. Migration Script Spec

### Script: `scripts/split_prompt_preamble.py`

**Purpose**: Automated migration of 105 prompts from full-template to slim format.

**Algorithm**:

```python
#!/usr/bin/env python3
"""Split shared boilerplate from per-step prompts into SYSTEM_PREAMBLE.md."""

import re
from pathlib import Path

PROMPT_DIR = Path("services/repo-truth-extractor/promptsets/v4/prompts")
PREAMBLE_PATH = Path("services/repo-truth-extractor/promptsets/v4/SYSTEM_PREAMBLE.md")

# Sections to extract into preamble (exact header matches)
PREAMBLE_SECTIONS = [
    "## Evidence Rules",
    "## Determinism Rules",
    "## Anti-Fabrication Rules",
    "## Failure Modes",
]

# These lines in Schema section are boilerplate:
SCHEMA_BOILERPLATE = [
    "- Use deterministic containers only:",
    '  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`',
    '  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`',
]

def extract_section(content: str, header: str) -> tuple[str, str]:
    """Extract a markdown section and return (section_content, remaining_content)."""
    pattern = rf"({re.escape(header)}\n)(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return "", content
    section = match.group(0)
    remaining = content[:match.start()] + content[match.end():]
    return section.strip(), remaining.strip()


def migrate_prompt(prompt_path: Path) -> str:
    """Remove preamble sections from a prompt, return slimmed content."""
    content = prompt_path.read_text(encoding="utf-8")

    for header in PREAMBLE_SECTIONS:
        _section, content = extract_section(content, header)

    # Remove schema boilerplate lines (keep per-artifact contracts)
    for line in SCHEMA_BOILERPLATE:
        content = content.replace(line + "\n", "")

    # Rename "## Schema" to "## Schema Contracts" for clarity
    content = content.replace("## Schema\n", "## Schema Contracts\n")

    # Clean up double blank lines
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")

    return content.strip() + "\n"


def main():
    # Step 1: Generate preamble from first prompt (they're all identical)
    reference = sorted(PROMPT_DIR.glob("PROMPT_*.md"))[0]
    ref_content = reference.read_text(encoding="utf-8")

    preamble_parts = ["# Repo Truth Extractor — System Rules\n"]
    preamble_parts.append(
        "You are a mechanical fact extractor. Produce deterministic, "
        "evidence-backed artifacts from repository source files.\n"
    )

    for header in PREAMBLE_SECTIONS:
        section, _ = extract_section(ref_content, header)
        if section:
            preamble_parts.append(section)

    # Add schema container description
    preamble_parts.append("\n## Schema Containers")
    preamble_parts.append("\n".join(SCHEMA_BOILERPLATE))

    PREAMBLE_PATH.write_text("\n\n".join(preamble_parts) + "\n", encoding="utf-8")
    print(f"Wrote {PREAMBLE_PATH}")

    # Step 2: Slim each prompt
    count = 0
    for prompt_path in sorted(PROMPT_DIR.glob("PROMPT_*.md")):
        slimmed = migrate_prompt(prompt_path)
        prompt_path.write_text(slimmed, encoding="utf-8")
        count += 1

    print(f"Migrated {count} prompts")

    # Step 3: Regenerate coverage map (hashes changed)
    print("NOTE: Run scripts/rewrite_repo_truth_extractor_v4_prompts.py to update coverage map")


if __name__ == "__main__":
    main()
```

### Execution Order

1. **Backup**: `cp -r services/repo-truth-extractor/promptsets/v4/prompts/ /tmp/prompts_backup/`
2. **Run**: `python scripts/split_prompt_preamble.py`
3. **Verify preamble**: `wc -l services/repo-truth-extractor/promptsets/v4/SYSTEM_PREAMBLE.md` (should be ~40-60 lines)
4. **Verify prompts slimmed**: `wc -l services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A0_*.md` (should be ~40-60 lines, down from ~110)
5. **Regenerate map**: `python scripts/rewrite_repo_truth_extractor_v4_prompts.py`
6. **Run audit**: `python scripts/repo_truth_extractor_promptset_audit_v4.py --repo-root .`

---

## 6. Legacy Context Promotion

For each prompt, the Legacy Context section contains step-specific extraction guidance that is currently marked "for intent only; never as evidence." The most actionable instructions should be promoted into the Extraction Procedure section.

### Promotion Guidelines

For the implementer migrating each prompt:

1. **Read the Legacy Context section** at the bottom of each prompt
2. **Identify concrete extraction instructions** (file paths to scan, specific patterns to look for, output field mappings)
3. **Add them as numbered steps** in the Extraction Procedure section
4. **Keep abstract/intent guidance** in Legacy Context (it's still useful for LLM intent)
5. **Remove redundant instructions** that are already covered by the Extraction Procedure

### Example: PROMPT_A0 Legacy Context Promotion

**Current Legacy Context** (lines 94-109 of PROMPT_A0):
```markdown
MODE: Mechanical extractor, zero interpretation.
INPUT: repo working tree (top-level), include hidden dirs shown in ls -la (not .git contents).
OUTPUT:
- REPOCTRL_INVENTORY.json: list files (path, ext, size, mtime, sha256 if available), plus first 30 non-empty lines for text.
- REPOCTRL_PARTITIONS.json: partitions by type:
  - instructions/prompts (CLAUDE.md, AGENTS.md, .claude/**, docs/** instruction files)
  - mcp/proxy configs (mcp-proxy-config*, start-mcp-servers.sh, compose/**)
  - hooks (.githooks/**, scripts called by hooks)
  - routers/provider ladders (litellm.config*, any router yaml/toml/json)
  - compose/service graphs (compose.yml, docker-compose*.yml, compose/**)
  - CI/gates (.github/**, pre-commit, ruff/mypy/pytest configs)
  - taskx surfaces (.taskx/**, .taskx-pin, task packets in repo)
RULES: JSON only. Every item must include path + line_range (or null if binary).
```

**Promote to Extraction Procedure** (add as steps 7-9):
```markdown
7. For REPOCTRL_INVENTORY: enumerate all files in source scope. For each text file, capture path, extension, size, mtime, sha256 (if available), and first 30 non-empty lines as `head_lines`.
8. For REPOCTRL_PARTITIONS: classify files into partition types:
   - `instructions_prompts`: CLAUDE.md, AGENTS.md, .claude/**, docs/** instruction files
   - `mcp_proxy_configs`: mcp-proxy-config*, start-mcp-servers.sh, compose/**
   - `hooks`: .githooks/**, scripts called by hooks
   - `routers_provider_ladders`: litellm.config*, any router yaml/toml/json
   - `compose_service_graphs`: compose.yml, docker-compose*.yml, compose/**
   - `ci_gates`: .github/**, pre-commit, ruff/mypy/pytest configs
   - `taskx_surfaces`: .taskx/**, .taskx-pin, task packets in repo
9. For binary files, set `line_range` to null and omit `head_lines`.
```

### Prompts Requiring Manual Review for Promotion

These prompts have substantive Legacy Context that should be manually reviewed:

| Prompt | Phase | Legacy Context Quality | Promotion Priority |
|--------|-------|----------------------|-------------------|
| A0 | A | Detailed file scan instructions | HIGH — promote partition types |
| R0 | R | Explicit MUST INCLUDE sections | HIGH — promote required sections |
| C1 | C | Minimal ("Find how services start") | LOW — already covered |
| T1 | T | Brief, unclear "Top 10" criteria | MEDIUM — clarify ranking criteria |
| Z2 | Z | Very brief for critical handoff | MEDIUM — add manifest requirements |
| Q0 | Q | Minimal for meta-verification | LOW — generic verification |

---

## 7. Verification Checklist

After full migration:

- [ ] `SYSTEM_PREAMBLE.md` exists and contains all 4 shared rule sections + schema containers
- [ ] All 105 prompt files no longer contain Evidence Rules, Determinism Rules, Anti-Fabrication Rules, or Failure Modes sections
- [ ] All 105 prompt files retain: Goal, Inputs, Outputs, Schema Contracts, Extraction Procedure, Legacy Context
- [ ] `prompt_artifact_coverage_map.json` regenerated with `prompt_count: 105`
- [ ] `repo_truth_extractor_promptset_audit_v4.py` passes
- [ ] Spot-check 3 prompts (A0, C9, R0) to verify no content loss
- [ ] Runner loads preamble correctly: `python -c "from run_extraction_v3 import load_system_preamble; print(len(load_system_preamble()))"`
