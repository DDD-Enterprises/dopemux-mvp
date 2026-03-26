# DOPEMUX MVP: Data Flow from Prescan to Extraction
## Comprehensive Intelligence Report Format Design

**Date Generated:** 2025-01-13  
**Source:** `/Users/hue/code/dopemux-mvp` repository analysis  
**Scope:** Prescan → Extraction pipeline data structures and field mappings

---

## SECTION 1: PRESCAN OUTPUT STRUCTURES

### 1.1 `build_manifests()` — Output JSON Files

**Location:** `scripts/doc_audit_prescan.py`, lines 439-503

The `build_manifests()` function writes THREE JSON files to `config.output_dir` (default: `extraction/prescan/`):

#### 1.1.1 **corpus_manifest.json**
- **Format:** Array of `FileEntry` objects, sorted by relative path
- **Each entry contains:**
  ```json
  {
    "rel_path": "string (relative path from repo root)",
    "size_bytes": "integer",
    "extension": "string (e.g., '.py', '.md', '.json')",
    "authority_class": "string (canonical|historical|operational|audit|template|generated|noise)",
    "include": "boolean (true if file passes all inclusion filters)",
    "exclude_reason": "string|null (e.g., 'binary_extension:.pyc', 'size_exceeds_max:123>100')",
    "content_hash": "string|null (SHA256 hex digest if include=true)",
    "directory_class": "string (top-level directory name for grouping)"
  }
  ```
- **Line of creation:** Line 450-451
- **Sorting:** `key=lambda x: x.rel_path`
- **Full record count:** All scanned files, including excluded ones

#### 1.1.2 **corpus_stats.json**
- **Format:** Single `CorpusStats` object (dataclass `asdict()`)
- **Structure:**
  ```json
  {
    "total_files_scanned": "integer (all files encountered)",
    "included_count": "integer (pass all filters)",
    "excluded_count": "integer (fail at least one filter)",
    "total_included_size": "integer (bytes, sum of included files)",
    "by_class": {
      "canonical": {"count": int, "total_size": int},
      "historical": {"count": int, "total_size": int},
      "operational": {"count": int, "total_size": int},
      "audit": {"count": int, "total_size": int},
      "template": {"count": int, "total_size": int},
      "generated": {"count": int, "total_size": int},
      "noise": {"count": int, "total_size": int}
    },
    "by_extension": {
      ".py": int,
      ".md": int,
      ".json": int,
      "... (one entry per unique extension)"
    },
    "by_directory": {
      "docs": int,
      "scripts": int,
      "src": int,
      "... (one entry per top-level directory in included files)"
    }
  }
  ```
- **Line of creation:** Line 484-485
- **Computed in:** `build_manifests()` loop lines 474-482

#### 1.1.3 **run_metadata.json**
- **Format:** Single `RunMetadata` object (dataclass `asdict()`)
- **Structure:**
  ```json
  {
    "timestamp": "ISO 8601 string (UTC)",
    "mode": "string (dry-run|direct|handoff)",
    "config_hash": "string (SHA256 first 16 chars of serialized config)",
    "git_sha": "string (current HEAD commit SHA or 'UNKNOWN')",
    "git_branch": "string (current branch name or 'UNKNOWN')",
    "repo_root": "string (absolute path)",
    "script_version": "string ('1.0.0')"
  }
  ```
- **Line of creation:** Line 499-500
- **Git info fetched:** Lines 413-427

---

### 1.2 `package_payload()` — audit_payload.md Structure

**Location:** `scripts/doc_audit_prescan.py`, lines 557-590

**Output file:** `audit_payload.md`

**Structure (Markdown format):**
```markdown
# Documentation Authority Audit Corpus
Generated: {metadata.timestamp}
Git SHA: {metadata.git_sha}
Files: {included_count} | Total Size: {human_size}

## canonical ({count} files)
### relative/path/file1 [123.5 KB]
\`\`\`
{file content preview — first 200 lines or 8192 bytes, whichever smaller}
\`\`\`

### relative/path/file2 [456.0 KB]
\`\`\`
{content preview}
\`\`\`

## historical ({count} files)
### ...

## operational ({count} files)
### ...

## audit ({count} files)
### ...

## template ({count} files)
### ...

## generated ({count} files)
### ...

## noise ({count} files)
### ...
```

**Key properties:**
- **Included files only** (filter: `e.include == True`)
- **Grouped by authority_class** in order: `AUTHORITY_CLASSES = ("canonical", "historical", "operational", "audit", "template", "generated", "noise")`
- **Preview truncation:** 
  - Max 200 lines per file
  - Max 8192 bytes per file (after line truncation)
  - Encoding errors replaced with `?`
- **Purpose:** LLM input payload for Grok classification
- **Used by:** `call_grok_direct()` (line 594) and `build_handoff_bundle()` (line 664)

---

### 1.3 `call_grok_direct()` — Return Value & Saved Files

**Location:** `scripts/doc_audit_prescan.py`, lines 594-660

**Return type:** `dict | None`

**Return structure (on success):**
```json
{
  "classifications": [
    {
      "path": "relative/file/path",
      "proposed_class": "class from prescan heuristic",
      "confirmed_class": "class from Grok assessment",
      "confidence": 0.0-1.0,
      "reasoning": "brief explanation (max 50 words)",
      "signals": ["authority signal 1", "authority signal 2", "..."]
    },
    "... (one per file in audit_payload.md)"
  ]
}
```

**Files saved:**
1. **grok_response.json** (line 632-635)
   - Full Grok response parsed as JSON
   - Contains `classifications` array as shown above

2. **grok_call_metadata.json** (line 638-649)
   ```json
   {
     "model": "string (response.model)",
     "usage": {
       "prompt_tokens": integer,
       "completion_tokens": integer,
       "total_tokens": integer
     },
     "finish_reason": "string (e.g., 'stop')"
   }
   ```

3. **grok_error.json** (line 657-659, on failure only)
   ```json
   {
     "error": "string (exception message)",
     "type": "string (exception class name)"
   }
   ```

**Return value on failure:** `None`

---

### 1.4 SYSTEM_PROMPT Sent to Grok

**Location:** `scripts/doc_audit_prescan.py`, lines 510-539

**Exact prompt text:**
```
You are a documentation authority auditor for a software repository.
Analyze each file's content and metadata to confirm or revise its authority classification.

Authority classes:
- canonical: Active architecture docs, current PRDs, live configs, system specs
- historical: Archived plans, old strategies, past decisions (valuable for rediscovery)
- operational: Runbooks, how-tos, setup guides, README files
- audit: Reports, analysis outputs, proof bundles
- template: Prompt templates, skill templates, schema files
- generated: Auto-generated outputs, extraction results
- noise: Truly irrelevant (vendored deps, caches, binaries, test artifacts)

IMPORTANT: "historical" is NOT noise. These contain forgotten plans and ideas
that should be preserved for future development reconsideration.

Return valid JSON:
{
  "classifications": [
    {
      "path": "relative/file/path",
      "proposed_class": "class from pre-scanner",
      "confirmed_class": "your assessment",
      "confidence": 0.0-1.0,
      "reasoning": "brief explanation (max 50 words)",
      "signals": ["authority signal 1", "authority signal 2"]
    }
  ]
}
```

**Configuration for API call:**
- **temperature:** 0.1 (deterministic, low creativity)
- **max_response_tokens:** 200000
- **response_format:** `{"type": "json_object"}` (strict JSON mode)
- **Model:** `grok-4.20-beta-0309-non-reasoning` (default)
- **Provider:** xAI (`https://api.x.ai/v1`)
- **Auth:** `XAI_API_KEY` environment variable

---

## SECTION 2: CORPUS.PY — WIZARD STAGE 2 USAGE

**Location:** `src/dopemux/ux/wizard/corpus.py`, lines 1-168

### 2.1 Prescan Input Loading

**Prescan output directory:** `extraction/prescan/` (line 44)

**Files read:**
1. **corpus_stats.json** (line 45, required)
   - Loaded into `state.corpus_stats`
   - Used to populate `state.corpus_included_count` (line 68)
   - Used to populate `state.corpus_total_size` (line 69)

2. **corpus_manifest.json** (line 60, optional, non-fatal if missing)
   - Loaded into `state.corpus_manifest`
   - Size: Explicitly noted as "large" (line 59 comment)
   - Used later for "phase mapping" (line 59)

3. **grok_response.json** (line 125, optional, only if Grok call succeeds)
   - Loaded when user opts into Grok upgrade
   - Stored in `state.grok_response`
   - Counted: `len(grok_data.get('classifications', []))` (line 133)

### 2.2 Display Logic

**Table render:** `render_corpus_table(state.corpus_stats)` (line 73)

**Stats displayed:**
- Breakdown by authority class: `by_class` dict with `{"count": int, "total_size": int}` per class
- Total files scanned: `total_files_scanned` (line 77)
- Excluded count: `excluded_count` (line 76)

### 2.3 Data Stored in WizardState

After prescan, the following fields are set:
```python
state.corpus_stats: Dict[str, Any]              # Full corpus_stats.json
state.corpus_manifest: List[Dict] | None        # Full corpus_manifest.json
state.corpus_included_count: int                # convenience
state.corpus_total_size: int                    # bytes
state.grok_response: Dict[str, Any] | None      # Only if Grok call succeeded
```

---

## SECTION 3: COST_PROFILES.PY — WIZARD STAGE 4 USAGE

**Location:** `src/dopemux/ux/wizard/cost_profiles.py`, lines 1-280

### 3.1 Cost Estimation Formula

**Function:** `estimate_cost(policy: str, corpus_size_bytes: int) -> Tuple[float, float]`

**Input:** Corpus total size in bytes (from `state.corpus_total_size`)

**Formula:**
```python
corpus_chars = corpus_size_bytes                        # bytes ≈ chars for text
input_tokens = corpus_chars / 4.0                       # rough token ratio
output_tokens = input_tokens * 0.3                      # typical output ratio

# Per tier (bulk, extract, synthesis, qa):
TIER_WEIGHTS = {
    "bulk": 0.50,           # high-volume file scanning
    "extract": 0.30,        # targeted content extraction
    "synthesis": 0.15,      # cross-referencing
    "qa": 0.05              # validation
}

# For each tier:
tier_tokens_in = input_tokens * weight
tier_tokens_out = output_tokens * weight

# Get cheapest and most expensive model prices in tier:
tier_low_input = min(model_prices[i][0] for i in tier_models)
tier_low_output = min(model_prices[i][1] for i in tier_models)
tier_high_input = max(model_prices[i][0] for i in tier_models)
tier_high_output = max(model_prices[i][1] for i in tier_models)

# Accumulate costs:
total_low += (tier_tokens_in * tier_low_input + tier_tokens_out * tier_low_output) / 1_000_000
total_high += (tier_tokens_in * tier_high_input + tier_tokens_out * tier_high_output) / 1_000_000

# Scale by phase factor:
phase_factor = 14 * 0.3              # ~30% of corpus per phase on average
total_low *= phase_factor
total_high *= phase_factor

# Returns: (low_estimate_usd, high_estimate_usd)
```

### 3.2 Routing Ladders Structure

**Definition:** `ROUTING_LADDERS: Dict[str, Dict[str, List[Tuple[str, str, str]]]]`

**Format per policy:**
```python
"policy_name": {
    "bulk": [
        ("provider", "model_id", "ENV_VAR"),
        ("provider", "model_id", "ENV_VAR"),
        # ... in priority order
    ],
    "extract": [...],
    "synthesis": [...],
    "qa": [...]
}
```

**Example (`balanced_grok_openrouter`):**
```python
"bulk": [
    ("xai", "grok-code-fast-1", "XAI_API_KEY"),
    ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY")
],
"extract": [
    ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ("openrouter", "openai/gpt-5.1", "OPENROUTER_API_KEY")
],
# ... etc
```

### 3.3 Model Pricing Table

**Defined:** Lines 78-94

**Format:** `MODEL_PRICING: Dict[str, Tuple[float, float]]`
- Key: Model ID (provider prefix stripped for lookup)
- Value: `(input_per_1M_tokens, output_per_1M_tokens)` in USD

**Sample entries:**
```python
"grok-4.20-beta-0309-non-reasoning": (2.00, 8.00),
"grok-4-1-fast-non-reasoning": (0.50, 2.00),
"gpt-5.2": (2.00, 8.00),
"gemini-2.5-pro": (1.25, 10.00),
"claude-sonnet-4-5": (3.00, 15.00),
```

---

## SECTION 4: REPO-TRUTH-EXTRACTOR FILE SELECTION & PARTITIONING

**Location:** `services/repo-truth-extractor/`

### 4.1 The "truth_map" Concept

**File:** `reports/repo_truth_map.json`

**Purpose:** JSON-managed list of extraction steps with their expected artifacts and file scopes

**Structure:**
```json
{
  "steps": [
    {
      "phase": "A",
      "step_id": "A0",
      "step": "A0",
      "prompt_declared": {
        "expected_artifacts": [
          "REPOCTRL_INVENTORY.json",
          "REPOCTRL_PARTITIONS.json"
        ],
        "required_item_keys": ["id", "path", "line_range"]
      }
    },
    "... (one per step)"
  ]
}
```

**Key fields per step:**
- `phase`: Phase letter (A, B, C, D, E, etc.)
- `step_id`: Step identifier within phase (A0, A1, A11, A12, etc.)
- `prompt_declared.expected_artifacts`: Array of output filenames (JSON + Markdown)
- `prompt_declared.required_item_keys`: Required fields in each item

**Reference:** `phase_contract_map.py` lines 209-243 parses this into `_repo_truth_scope_by_key()`

### 4.2 No "file_map" — Instead: Partitions Strategy

**Search result:** No `file_map` found in extractor.

**Instead, file selection is done via PARTITIONS:**

**Partition creation:** `run_extraction_v5.py`, `run_extraction_v3.py`

**Each partition contains:**
```python
partition = {
    "partition_id": "string (A0_P001, A0_P002, etc.)",
    "step_id": "string (A0)",
    "phase": "string (A)",
    "paths": ["list/of/file/paths"],  # relative to repo root
    "chars": integer,                  # total character count
    "file_count": integer              # len(paths)
}
```

**Files per partition determined by:**
1. **max_files:** Maximum files per partition (config parameter)
2. **max_chars:** Maximum characters per partition (config parameter)
3. **Inventory assignment:** Each file is mapped to the appropriate phase based on its properties

**Critical function:** `_stable_sort_partition_paths()` (line 7840 in v5, line 776 in v3)
- Normalizes paths for consistent ordering across runs
- Ensures deterministic partition assignment

**Partition usage in extraction:**
1. Each phase receives an **inventory** (list of all files for that phase)
2. `build_partitions(phase, inventory, max_files, max_chars)` creates partition list
3. Each partition is processed in a worker thread/process
4. Results are merged across partitions by artifact type

### 4.3 How the Extractor Decides Which Files to Process

**Source:** `lib/phase_contract_map.py`

**Decision flow:**
1. **Load repo_truth_map.json** → Get scope for each (phase, step)
2. **Load corpus_manifest.json** → Get all scanned files with metadata
3. **Per phase:** Filter corpus by authority class and other criteria
4. **Create inventory:** List of files eligible for current phase
5. **Create partitions:** Split inventory by max_files/max_chars
6. **Process each partition:** Send to LLM with step prompt

**Key function:** `compile_phase_contract_map()` (line 265)

**Returns:**
```python
{
    "version": "PHASE_CONTRACT_MAP_V2",
    "scope": "json_managed_only",
    "source_files": {
        "repo_truth_map": "path to repo_truth_map.json",
        "promptset": "path to promptset.yaml",
        "artifacts": "path to artifacts.yaml",
        "model_map": "path to model_map.yaml"
    },
    "policy": {...},
    "steps": {
        "A:A0": {...},
        "A:A1": {...},
        "...": {...}
    }
}
```

**Each step contract contains:**
```python
{
    "phase": "A",
    "step_id": "A0",
    "scope_source": "repo_truth_map",
    "scope": {
        "json_managed": True,
        "mixed_step": bool,
        "markdown_bypassed": bool
    },
    "expected_artifacts": ["ARTIFACT1.json", "ARTIFACT2.json"],
    "expected_markdown_artifacts": [],
    "artifact_order": ["ARTIFACT1.json", "ARTIFACT2.json"],
    "plural_expected_json_artifacts": bool,
    "lane": {
        "lane_class": "BULK|EXTRACT|SYNTHESIS|QA",
        "strict_schema_required_primary": bool,
        "sidefill_enabled": bool,
        "repair_mode": "string",
        "primary_routes": [{"provider": "...", "model_id": "...", "api_key_env": "..."}],
        "repair_routes": [...],
        "sidefill_routes": [...]
    },
    "artifacts": {
        "ARTIFACT1.json": {
            "artifact_name": "ARTIFACT1.json",
            "canonical_schema_name": "ARTIFACT1",
            "canonical_schema_id": "ARTIFACT1@v1",
            "required_fields": ["id", "path", "line_range"],
            "merge_strategy": "itemlist_by_id",
            "kind": "json_item_list",
            "norm_artifact": True
        },
        "...": {...}
    }
}
```

---

## SECTION 5: EXTRACTION PHASE INVENTORY CALCULATION

**Location:** `run_extraction_v5.py`

### 5.1 Inventory Building

**Process per phase:**
1. Read corpus_manifest.json (all scanned files)
2. Filter by prescan authority classification
3. Filter by file extension (phase-specific)
4. Filter by size/hygiene rules
5. Create "inventory" list with one entry per file

**Inventory entry structure:**
```python
{
    "path": "relative/path/to/file",
    "size": integer,
    "authority_class": "canonical|historical|...",
    "content_preview": "string (first N lines)"
}
```

### 5.2 Partition Creation from Inventory

**Function signature:**
```python
def build_partitions(
    phase: str,
    inventory: List[Dict],
    max_files: int,
    max_chars: int
) -> List[Dict]:
```

**Partitions created by:**
1. Sorting files deterministically
2. Accumulating files until `max_files` or `max_chars` reached
3. Creating new partition when threshold exceeded
4. Assigning stable partition ID (e.g., `A0_P001`, `A0_P002`)

---

## SECTION 6: INTELLIGENCE REPORT DESIGN RECOMMENDATIONS

Based on the data flow analysis, here are the recommended field names and structures for the intelligence report format:

### 6.1 Core Report Metadata
```json
{
  "report_version": "1.0.0",
  "generated_at": "ISO 8601 timestamp",
  "prescan_run_id": "config_hash from run_metadata.json",
  "git_sha": "from run_metadata.json",
  "repo_root": "from run_metadata.json",
  "corpus_stats_snapshot": {
    "total_files_scanned": "int",
    "included_count": "int",
    "total_included_size_bytes": "int",
    "by_authority_class": {
      "canonical": {"count": int, "total_size": int},
      "historical": {"count": int, "total_size": int},
      "operational": {"count": int, "total_size": int},
      "audit": {"count": int, "total_size": int},
      "template": {"count": int, "total_size": int},
      "generated": {"count": int, "total_size": int},
      "noise": {"count": int, "total_size": int}
    }
  }
}
```

### 6.2 File Classification Section
```json
{
  "file_classifications": {
    "by_prescan_heuristic": [
      {
        "rel_path": "string",
        "size_bytes": "int",
        "extension": "string",
        "authority_class": "string",
        "directory_class": "string",
        "content_hash": "string (SHA256)",
        "include": "boolean"
      }
    ],
    "by_grok_assessment": [
      {
        "rel_path": "string",
        "proposed_class": "string (from heuristic)",
        "confirmed_class": "string (from Grok)",
        "confidence": "float (0.0-1.0)",
        "reasoning": "string (max 50 words)",
        "signals": "array of strings"
      }
    ]
  }
}
```

### 6.3 Phase Contract Section
```json
{
  "phase_contracts": {
    "A:A0": {
      "phase": "A",
      "step_id": "A0",
      "expected_artifacts": ["ARTIFACT1.json", "ARTIFACT2.json"],
      "lane_class": "BULK|EXTRACT|SYNTHESIS|QA",
      "routing_policy": "policy_name",
      "routes": [
        {"provider": "xai", "model": "grok-4.20-beta-0309-non-reasoning", "tier": "1"},
        {"provider": "openrouter", "model": "openai/gpt-5.2", "tier": "2"}
      ]
    }
  }
}
```

### 6.4 Cost & Resource Section
```json
{
  "resource_estimation": {
    "selected_routing_policy": "policy_name",
    "corpus_size_bytes": "int",
    "estimated_tokens_in": "int",
    "estimated_tokens_out": "int",
    "cost_estimate": {
      "low_usd": "float",
      "high_usd": "float"
    },
    "tier_breakdown": {
      "bulk": {
        "weight": 0.50,
        "low_usd": "float",
        "high_usd": "float"
      },
      "extract": {
        "weight": 0.30,
        "low_usd": "float",
        "high_usd": "float"
      },
      "synthesis": {
        "weight": 0.15,
        "low_usd": "float",
        "high_usd": "float"
      },
      "qa": {
        "weight": 0.05,
        "low_usd": "float",
        "high_usd": "float"
      }
    }
  }
}
```

---

## APPENDIX A: FILE LOCATIONS SUMMARY

| Purpose | Path | Format |
|---------|------|--------|
| Prescan heuristic output | `extraction/prescan/corpus_manifest.json` | JSON array |
| Corpus statistics | `extraction/prescan/corpus_stats.json` | JSON object |
| Prescan metadata | `extraction/prescan/run_metadata.json` | JSON object |
| Payload for Grok | `extraction/prescan/audit_payload.md` | Markdown |
| Grok classifications | `extraction/prescan/grok_response.json` | JSON array |
| Grok call metadata | `extraction/prescan/grok_call_metadata.json` | JSON object |
| Phase contracts | `services/repo-truth-extractor/PHASE_CONTRACT_MAP.json` | JSON (per run) |
| Repository truth map | `reports/repo_truth_map.json` | JSON (reference) |
| Routing policies | `src/dopemux/ux/wizard/cost_profiles.py` | Python dict |
| Model pricing | `src/dopemux/ux/wizard/cost_profiles.py` (lines 78-94) | Python dict |

---

## APPENDIX B: Classification Heuristics

**From:** `scripts/doc_audit_prescan.py`, lines 297-403

Classification uses path matching as first match wins:

1. **noise:** Binary extensions, excluded, unreadable
2. **generated:** Auto-outputs, extraction results, /out/ dirs
3. **template:** Templates, promptsets, .claude/prompts
4. **historical:** Archive, deprecated, old sessions
5. **audit:** /reports, /proof, audit in name
6. **operational:** Runbooks, how-tos, setup, README
7. **canonical:** /planes, /docs, architecture references, .yaml/.toml at root
8. **default:** "generated"

