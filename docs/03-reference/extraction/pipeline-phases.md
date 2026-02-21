---
id: EXTRACTION-PIPELINE-PHASES
title: Extraction Pipeline Phases
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Phase order and routing tier behavior for Repo Truth Extractor.
last_review: '2026-02-21'
next_review: '2026-05-21'
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/repo-truth-extractor/run_extraction_v3.py
    - services/repo-truth-extractor/run_extraction_v4.py
---
# Extraction Pipeline Phases

Canonical phase order:

- `A H D C E W B G Q R X T Z`

Routing tier classifier:

- `synthesis`: phases `R`, `X`, `T`, and steps `Z1`, `Z2`
- `qa`: phase `Q`, and any step ending in `9` or `99`
- `bulk`: any step ending in `0`
- `extract`: all other steps

Default routing policy:

- `cost` (hard-switched default)

Run-time controls:

- `--routing-policy {cost,balanced,quality}`
- `--disable-escalation`
- `--escalation-max-hops`
- `--batch-mode`
- `--batch-provider {auto,openai,gemini,xai}`

CLI examples (canonical `upgrades`):

```bash
dopemux upgrades run --pipeline-version v4 --phase A --routing-policy cost --dry-run --resume
```

```bash
dopemux upgrades run --pipeline-version v4 --phase C --batch-mode --batch-provider openai --ui rich --execute
```
