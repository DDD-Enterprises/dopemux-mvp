# RTE-PKT-08 Downloaded JSONL Inventory

## Commands

```bash
rg --files -uu | rg '(^|/)[^/]+_(output|error)\.jsonl$'
rg --files -uu out extraction reports proof services/repo-truth-extractor 2>/dev/null | rg '(^|/)[^/]+_(output|error)\.jsonl$'
```

## Observed Result

Both commands returned exit code `1` with no matching paths.

## Disposition

Downloaded xAI/OpenAI-compatible batch output/error JSONL artifacts are `MISSING` in the local searched artifact classes.

Markers:

- `DOWNLOADED_JSONL_MISSING_IF_NOT_FOUND`
- `LIVE_VALIDATION_REQUIRED`
- `NO_PROVIDER_CALLS_PERFORMED`

No provider retrieval was attempted.
