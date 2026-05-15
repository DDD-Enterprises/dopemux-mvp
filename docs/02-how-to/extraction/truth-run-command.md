---
id: HOWTO-EXTRACTION-TRUTH-RUN
title: Legacy dopemux extract truth-run compatibility note
type: how-to
owner: '@hu3mann'
date: '2026-03-14'
author: '@copilot'
prelude: Legacy compatibility note for the hidden and disabled dopemux extract truth-run surface. Current v5 operator workflows use dopemux rte.
last_review: '2026-03-14'
next_review: '2026-06-14'
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - src/dopemux/commands/extract_commands.py
    - services/repo-truth-extractor/run_extraction_v5.py
    - services/repo-truth-extractor/extraction_hygiene.py
---
# Legacy `dopemux extract truth-run` compatibility note

`dopemux extract truth-run` is not the canonical entrypoint. Runtime code keeps it hidden and disabled as a legacy compatibility alias that raises a refusal directing operators to `dopemux rte run`.

Current operator truth:

- Canonical operator family: `dopemux rte`.
- Strongest v5 runtime authority: `services/repo-truth-extractor/run_extraction_v5.py`.
- Direct runner calls are advanced/debug/manual only.
- Legacy v3 migration remains a compatibility concern, not the normal v5 path.
- Proof packs and generated outputs are evidence artifacts, not source truth.

Older versions of this document described a disabled wrapper that combined up to four phases:

0. **(Optional) v3 → v5 migration** — copies a legacy v3 run into the v5 runs
   directory so it can be resumed in v5 (`--import-v3`)
1. **Pre-flight hygiene scan** — read-only check for stale artifacts, noisy
   paths, version/path mismatches, and authority-tier summary
2. **Optional quarantine cleanup** — archives stale FAILED sidecars and junk
   files before the run starts
3. **Live extraction** — streams `run_extraction_v5.py` output directly to
   your terminal

## Quick start

```bash
# Minimal run (scan + extract, auto run ID)
dopemux rte run --pipeline-version v5 --phase ALL --dry-run

# Full control
dopemux rte run \
  --pipeline-version v5 \
  --run-id MY_RUN_001 \
  --phase ALL \
  --partition-workers 10 \
  --routing-policy balanced_openrouter \
  --dry-run

# Resume a previous v5 run (skip completed partitions)
dopemux rte run --pipeline-version v5 --run-id MY_RUN_001 --resume --dry-run

# Legacy v3 output migration is not a canonical operator path in the current CLI.
# Use v3 only through explicitly gated compatibility flows.

# Runner-level hygiene helpers are advanced/manual:
python services/repo-truth-extractor/extraction_hygiene.py scan

# Live execution requires explicit consent:
DPMX_LIVE_OK=1 dopemux rte run --pipeline-version v5 --phase A --execute
```

## Options reference

The legacy wrapper exposed these options before it was disabled. They are preserved here only to aid migration:

| Option | Default | Description |
|--------|---------|-------------|
| `--run-id TEXT` | auto timestamp | Extraction run ID (`RUN-YYYYMMDDTHHmmss`) |
| `--phase TEXT` | `ALL` | Phase(s) to run: `A`, `A,B`, `ALL` |
| `-w / --workers INT` | `10` | Parallel partition worker count |
| `--routing-policy TEXT` | `balanced_openrouter` | LLM routing policy |
| `--doctor` | off | Run provider preflight doctor checks first |
| `--resume` | off | Skip partitions that already have valid success outputs |
| `--import-v3 RUN_ID` | — | Migrate a v3 run into v5 before resuming (see below) |
| `--skip-hygiene` | off | Skip Phase 1 hygiene scan entirely |
| `--apply-cleanup` | off | Apply quarantine cleanup if scan finds hazards |
| `--force` | off | Run extraction even if hygiene scan has errors |

## Phase 0: Migrate a v3 run into v5 (--import-v3)

Use `--import-v3 <RUN_ID>` to continue a run that was started under the legacy
v3 output path (`extraction/repo-truth-extractor/v3/runs/`) in v5.

```bash
# The hidden legacy wrapper used to support one-step v3 migration.
# It now refuses and directs operators to dopemux rte run.

# Current v5 resume path:
dopemux rte run --pipeline-version v5 --run-id FULL_RUN --resume --dry-run
```

**What happens:**

1. Source: `extraction/repo-truth-extractor/v3/runs/<RUN_ID>/`
2. Target: `extraction/repo-truth-extractor/v5/runs/<RUN_ID>/` (created by
   `shutil.copytree` — the v3 directory is **never modified**)
3. `extraction/repo-truth-extractor/v5/latest_run_id.txt` is updated to
   `<RUN_ID>`
4. A per-phase summary table is printed showing raw outputs, FAILED markers,
   norm and QA counts for each migrated phase directory
5. `--resume` is automatically activated; `--run-id` is pinned to `<RUN_ID>`

If the v5 target already exists, the copy step is skipped and the existing v5
artifacts are used as-is.

**Resume semantics**: v5 checks each partition's
`<phase>/raw/<step>__<partition_id>.json` for a valid success payload. If found
and newer than any `.FAILED.*` sidecar, the partition is skipped. Only
incomplete or failed partitions are re-run.

## Using --resume without --import-v3

`--resume` can be used on any run — not just migrated ones. Use it to pick up
after a partial run or a crash:

```bash
# Resume a v5 run that was interrupted
dopemux rte run --pipeline-version v5 --run-id MY_RUN_001 --resume --dry-run

# Resume the latest run (uses v5/latest_run_id.txt)
dopemux rte run --pipeline-version v5 --resume --dry-run
```

The `+resume` indicator appears in the banner when resume mode is active.

## Phase 1: Pre-flight hygiene scan

The scan runs `extraction_hygiene.run_scan()` and shows a Rich panel with:

- **Version/path wiring**: confirms v5 code writes to `v5/` output (✅ or ❌)
- **Noise paths**: vendored deps, `.venv`, `node_modules`, build artifacts in
  extraction paths
- **Resume-state hazards**: stale FAILED sidecars, orphaned metadata files
- **Authority classification summary**: breakdown of doc tiers found

If the scan reports **errors**, the command aborts unless `--force` is passed.
Warnings are shown but do not block.

To run the scan standalone:

```bash
python services/repo-truth-extractor/extraction_hygiene.py scan
python services/repo-truth-extractor/extraction_hygiene.py scan --scan-mode full
```

## Phase 2: Quarantine cleanup

Pass `--apply-cleanup` to archive stale artifacts before the run. This calls
`extraction_hygiene.run_apply(dry_run=False)` which:

- Moves stale `*.FAILED.*` sidecars that have a corresponding success file to
  `extraction/repo-truth-extractor/quarantine/<timestamp>/`
- Removes `.DS_Store` files from the extraction tree
- Writes an archive manifest JSON file

The cleanup is **non-destructive**: originals are moved, not deleted. A manifest
records every moved path so you can reverse the operation manually.

To preview what would be moved without touching anything:

```bash
python services/repo-truth-extractor/extraction_hygiene.py apply --dry-run
```

## Phase 3: Live extraction

Use `dopemux rte run` for live extraction. Live provider execution is guarded by `--execute` plus `DPMX_LIVE_OK=1`; batch/provider operation remains proof- and policy-gated. The v5 UI provides:

- **Per-partition LLM display**: each partition shows which provider/model
  it is using (color-coded: openai=green, anthropic=magenta, gemini=blue,
  xai=yellow, openrouter=cyan)
- **Retry visibility**: `⟳ RETRY attempt=2/3 status=429 reason=rate_limit
  wait=2.0s` printed live before each retry sleep
- **Escalation alerts**: `🔀 ESCALATE openai/gpt-4.1 → anthropic/claude-3-haiku`
  with colored route arrows
- **Failure trace dump**: when a partition fails after multiple retries, the
  full retry trace (each attempt: status code + delay) is printed

All output is also persisted to:
- `extraction/repo-truth-extractor/v5/runs/<run_id>/telemetry/terminal_timeline.jsonl`
- `extraction/repo-truth-extractor/v5/runs/<run_id>/events.jsonl` (if enabled)

## Output location

All v5 run artifacts are written under:

```
extraction/repo-truth-extractor/v5/
  runs/
    <run_id>/
      A/   B/   C/   D/   E/   H/   Q/   R/
      telemetry/
      RUN_MANIFEST.json
      RUNNER_IDENTITY.json
  latest_run_id.txt
  doctor/
```

> **Note**: v3 run directories under `extraction/repo-truth-extractor/v3/`
> are legacy. Use `--import-v3` to migrate them into v5; they will not be
> modified or overwritten by v5 runs.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `extraction_hygiene.py not found` | Path mismatch | Run from repo root |
| Hygiene scan errors block run | Stale FAILED sidecars or noise | Run `--apply-cleanup` or `--force` |
| `run_extraction_v5.py not found` | Wrong cwd | Run from repo root |
| Partition retries visible but slow | Rate limits | Reduce `--workers` or switch routing policy |
| Missing LLM API key | `auth_missing` failure type | Set the required env var (e.g. `OPENAI_API_KEY`) |
| `v3 run not found` with `--import-v3` | Wrong run ID | Check `extraction/repo-truth-extractor/v3/runs/` for available run IDs |
| Partitions not being skipped on resume | Success JSON missing/invalid | Check `v5/runs/<id>/<phase>/raw/*.json` for valid content |

## Related

- `docs/02-how-to/extraction/repo-truth-extractor-user-guide.md` — full operator guide
- `docs/02-how-to/extraction/batch-quickstart.md` — batch mode
- `services/repo-truth-extractor/extraction_hygiene.py` — hygiene scanner
- `config/extraction_hygiene/hygiene_policy.yaml` — policy config
