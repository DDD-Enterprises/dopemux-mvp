---
id: HOWTO-EXTRACTION-TRUTH-RUN
title: Run v5 Extraction via dopemux extract truth-run
type: how-to
owner: '@hu3mann'
date: '2026-03-14'
author: '@copilot'
prelude: Orchestrate the full v5 extraction workflow — hygiene scan, optional cleanup, resume, and live-streaming extraction — from a single dopemux CLI command. Supports migrating v3 runs into v5 for resumption.
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
# Run v5 extraction via `dopemux extract truth-run`

`dopemux extract truth-run` is the canonical entrypoint for launching a v5
repo-truth extraction run. It combines up to four phases into one command:

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
dopemux extract truth-run

# Full control
dopemux extract truth-run \
  --run-id MY_RUN_001 \
  --phase ALL \
  --workers 10 \
  --routing-policy balanced_openrouter

# Resume a previous v5 run (skip completed partitions)
dopemux extract truth-run --run-id MY_RUN_001 --resume

# Continue a v3 FULL_RUN in v5 (migrate + resume in one step)
dopemux extract truth-run --import-v3 FULL_RUN --resume

# Scan + apply cleanup + extract
dopemux extract truth-run --apply-cleanup

# Skip hygiene check (e.g. CI, already cleaned)
dopemux extract truth-run --skip-hygiene --run-id CI_RUN_$(date +%Y%m%d)

# Run even if hygiene errors are found
dopemux extract truth-run --force
```

## Options reference

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
# One-step: migrate FULL_RUN from v3 → v5 then resume
dopemux extract truth-run --import-v3 FULL_RUN --resume

# If v5 copy already exists (e.g. second restart), skip --import-v3
dopemux extract truth-run --run-id FULL_RUN --resume --skip-hygiene
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
dopemux extract truth-run --run-id MY_RUN_001 --resume

# Resume the latest run (uses v5/latest_run_id.txt)
dopemux extract truth-run --resume --skip-hygiene
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

The extractor is launched as a subprocess and its output streams directly to
your terminal. The v5 UI provides:

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
