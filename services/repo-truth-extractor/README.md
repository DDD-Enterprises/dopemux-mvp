# Repo Truth Extractor

Repo Truth Extractor is the canonical extraction service for dopemux.

## Engines

- `v4` (default): schema-first prompt/artifact contracts with canonical-writer enforcement.
- `v3` (fallback): legacy execution engine maintained for compatibility.

## Canonical CLI

```bash
dopemux extractor list --engine-version v4
dopemux extractor run --engine-version v4 --phase ALL --dry-run
dopemux extractor status --engine-version v4 --run-id <RUN_ID>
dopemux extractor doctor --engine-version v4 --run-id <RUN_ID>
dopemux extractor promptset audit --engine-version v4
```

## Runner Entrypoints

- `services/repo-truth-extractor/run_extraction_v3.py`
- `services/repo-truth-extractor/run_extraction_v4.py`

## v3 Introspection and Async Batch Utilities

```bash
# Deterministic CLI introspection
python services/repo-truth-extractor/run_extraction_v3.py --print-run-order
python services/repo-truth-extractor/run_extraction_v3.py --print-phase-routing --phase Q --dry-run
python services/repo-truth-extractor/run_extraction_v3.py --print-phase-prompts ALL

# Async batch split mode (explicit)
python services/repo-truth-extractor/run_extraction_v3.py --phase D --batch-mode --batch-submit-only --run-id <RUN_ID>
python services/repo-truth-extractor/run_extraction_v3.py --phase D --batch-watch --run-id <RUN_ID>
```

Webhook notify mode for `--batch-watch` is controlled by:

- `DPMX_WEBHOOK_URL`
- `DPMX_WEBHOOK_SECRET`
- `DPMX_WEBHOOK_TIMEOUT_SECONDS`
- `DPMX_WEBHOOK_REQUIRED`
- `DPMX_WEBHOOK_AUTO_CONTINUE`
- `DPMX_LIVE_OK`

## Prompt Assets

- v3 prompts: `services/repo-truth-extractor/prompts/v3/`
- v4 promptset: `services/repo-truth-extractor/promptsets/v4/`
- legacy prompt archive: `services/repo-truth-extractor/archive/legacy_prompts/`

## Output Roots

- v3 runs: `extraction/repo-truth-extractor/v3/runs/`
- v3 doctor: `extraction/repo-truth-extractor/v3/doctor/`
- v4 runs: `extraction/repo-truth-extractor/v4/runs/`
- v4 doctor: `extraction/repo-truth-extractor/v4/doctor/`

Historical extraction outputs under old roots are preserved and read-only.
