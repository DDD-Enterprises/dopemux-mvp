---
title: 'How to: Use the Universal Repo-Truth-Extractor'
type: how-to
status: active
prelude: Guide for running the repo-truth-extractor against any codebase using the
  sync pipeline.
tags:
- extractor
- how-to
- universal
id: universal-extractor-usage
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-06'
last_review: '2026-03-06'
next_review: '2026-06-04'
---
# How to: Use the Universal Repo-Truth-Extractor

## Prerequisites

- Python 3.11+ with dopemux installed (`pip install -e .`)
- Target repository accessible on local disk
- Optional: Jinja2 (`pip install jinja2`) for template rendering
- Optional: Questionary (`pip install questionary`) for interactive discovery

## Quick Start

### 1. Initialize — Generate a promptset for your repo

```bash
# Interactive mode (recommended)
dopemux extractor init --repo /path/to/your/repo

# Non-interactive mode (CI/automation)
dopemux extractor init --repo /path/to/your/repo --no-interactive

# Custom output directory
dopemux extractor init --repo /path/to/your/repo --output /path/to/output
```

### 2. Validate — Check generated promptset integrity

```bash
dopemux extractor validate --output-dir /path/to/output
```

### 3. Review — Inspect what was generated

```bash
dopemux extractor status --output-dir /path/to/output
```

## What the init pipeline does

The `init` command runs this pipeline:

1. **Feature Detection** — Scans your repo for 30+ feature patterns (HTTP APIs, databases, Docker, CI, testing, etc.)
2. **Phase Planning** — Determines which of 15 extraction phases apply to your repo
3. **Interactive Discovery** — Asks you to confirm detected features and add missing ones
4. **Scope Resolution** — Maps each extraction step to specific directories in your repo
5. **Template Rendering** — Generates customized prompts from base templates
6. **Contract Generation** — Creates `promptset.yaml`, `artifacts.yaml`, `model_map.yaml`
7. **Integrity Validation** — Verifies all cross-references are consistent

## Generated artifacts

After `init`, your output directory contains:

| File | Purpose |
|------|---------|
| `AUTO_FEATURES.json` | Detected features with confidence scores |
| `PHASE_PLAN.json` | Which phases are included/skipped |
| `FEATURE_MAP.json` | Confirmed features (after interactive discovery) |
| `SCOPE_RESOLUTION.json` | Per-step scan directories |
| `promptset.yaml` | Phase→step→prompt registry |
| `artifacts.yaml` | Output artifact contracts |
| `model_map.yaml` | LLM model routing per step |
| `INTEGRITY_REPORT.json` | Validation results |
| `SYNC_MANIFEST.json` | Pipeline run summary |
| `prompts/` | Rendered prompt files |

## Advanced usage

### Force-include or skip phases

```bash
# Include H (Home Control) and T (Task Packets) even for non-dopemux repos
dopemux extractor init --repo . --force-include H --force-include T

# Skip Boundaries and Workflows phases
dopemux extractor init --repo . --force-skip B --force-skip W
```

### Use a pre-authored feature map

If you've hand-edited a `FEATURE_MAP.json` with custom features:

```bash
dopemux extractor init --repo . --feature-map my_features.json
```

### Programmatic usage

```python
from lib.promptgen.sync_engine import run_sync
from pathlib import Path

result = run_sync(
    repo_root=Path("/path/to/repo"),
    output_root=Path("/path/to/output"),
    interactive=False,
)

if result.success:
    print(f"Generated {result.summary['steps']} steps across {result.summary['phases']} phases")
else:
    for err in result.errors:
        print(f"Error: {err['message']}")
```

### Adding custom feature rules

```python
from lib.promptgen.feature_detector import FeatureRule, detect_features

custom_rule = FeatureRule(
    feature_id="my_custom_feature",
    label="Custom Feature",
    description="Detects my specific pattern",
    file_globs=("**/my_pattern.yaml",),
    maps_to_steps=("C99",),
    maps_to_phases=("C",),
)

features = detect_features(
    root=Path("/path/to/repo"),
    run_id="my-run",
    extra_rules=[custom_rule],
)
```

## Troubleshooting

### "No features detected"
Your repo may not match any built-in rules. Use `--interactive` mode to manually add features, or pass a `--feature-map` with your custom feature definitions.

### Integrity validation fails
Run `dopemux extractor validate --output-dir <path>` to see specific errors. Common causes:
- Orphaned step references in model_map
- Missing artifact contracts for step outputs
- Undefined lane references

### Templates not rendering
Ensure Jinja2 is installed: `pip install jinja2`. Without it, a simple fallback renderer is used that only handles `{{ variable }}` substitution (no conditionals or loops).
