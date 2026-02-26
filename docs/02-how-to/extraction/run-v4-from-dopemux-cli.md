---
id: HOWTO-EXTRACTION-RUN-V4-FROM-CLI
title: Run V4 Extraction from Dopemux CLI
type: how-to
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Execute, resume, and troubleshoot Repo Truth Extractor v4 from canonical dopemux upgrades commands.
last_review: '2026-02-21'
next_review: '2026-05-21'
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - src/dopemux/cli.py
    - services/repo-truth-extractor/run_extraction_v4.py
---
# Run v4 extraction from Dopemux CLI

This guide uses `dopemux upgrades` as the canonical entrypoint for extraction v4.
`dopemux extractor` is still supported as a legacy alias.

For broader operator workflows, see:

- `docs/02-how-to/extraction/repo-truth-extractor-user-guide.md`
- `docs/02-how-to/extraction/batch-quickstart.md`

## 1) Promptset audit

```bash
dopemux upgrades promptset audit --pipeline-version v4
```

## 2) Provider preflight

```bash
dopemux upgrades preflight --pipeline-version v4 --auth-doctor
```

## 3) Run a phase

```bash
dopemux upgrades run --pipeline-version v4 --phase A --run-id rte_v4_local_001 --dry-run --resume
```

## 4) Run full pipeline

```bash
dopemux upgrades run --pipeline-version v4 --phase ALL --run-id rte_v4_full_001 --execute --resume
```

Cost-first routing with escalation controls:

```bash
dopemux upgrades run \
  --pipeline-version v4 \
  --phase C \
  --routing-policy cost \
  --escalation-max-hops 2 \
  --execute
```

Batch mode with rich terminal UI:

```bash
dopemux upgrades run \
  --pipeline-version v4 \
  --phase A \
  --routing-policy cost \
  --ui rich \
  --pretty \
  --batch-mode \
  --batch-provider openai \
  --batch-poll-seconds 30 \
  --batch-wait-timeout-seconds 86400 \
  --batch-max-requests-per-job 2000 \
  --execute
```

## 5) Check status

```bash
dopemux upgrades status --pipeline-version v4 --run-id rte_v4_full_001
```

JSON status:

```bash
dopemux upgrades status --pipeline-version v4 --run-id rte_v4_full_001 --json
```

## 6) Doctor and reprocess plan

```bash
dopemux upgrades doctor --pipeline-version v4 --run-id rte_v4_full_001
```

With auto-reprocess:

```bash
dopemux upgrades doctor \
  --pipeline-version v4 \
  --run-id rte_v4_full_001 \
  --auto-reprocess \
  --reprocess-dry-run
```

## 7) Output locations

- v4 runs: `extraction/repo-truth-extractor/v4/runs/<RUN_ID>/`
- v4 doctor artifacts: `extraction/repo-truth-extractor/v4/doctor/`
- latest v4 run pointer: `extraction/repo-truth-extractor/v4/latest_run_id.txt`

## 8) Legacy fallback

Use v3 fallback when needed:

```bash
dopemux upgrades run --pipeline-version v3 --phase ALL --run-id rte_v3_legacy_001 --execute
```

## 9) Dope-context startup autoindex (current workspace)

Startup commands trigger dope-context bootstrap indexing plus async ongoing updates:

```bash
dopemux start
dopemux launch --preset standard
dopemux dope --theme muted
```

Behavior:

- Bootstrap once per workspace snapshot: code + docs indexing batch pass
- Ongoing updates: autonomous code + docs watchers

Controls:

```bash
DOPEMUX_AUTO_INDEX_ON_STARTUP=0 dopemux start
DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS=3 DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS=300 dopemux start
```
