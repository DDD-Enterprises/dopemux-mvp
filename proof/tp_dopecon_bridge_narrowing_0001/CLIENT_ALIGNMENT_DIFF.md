# Client Alignment Diff

## Shared client surfaces aligned to active runtime

- `recent_decisions()` -> `/ddg/decisions`
- `search_decisions()` -> `/ddg/search`
- `set_custom_data()` / `get_custom_data()` -> `/kg/custom_data`
- `log_decision()` / `get_decisions()` -> `/kg/decisions`
- `log_progress()` / `get_progress_entries()` -> `/kg/progress`

## Explicitly blocked or deprecated client surfaces

- `route_cognitive()`
- `related_decisions()`
- `related_text()`
- `create_link()`

These now raise `DopeconBridgeError` instead of targeting dead, legacy, or non-canonical bridge surfaces.

## Compatibility note

- `get_progress_entries()` expects `entries`; the server normalization returns both `entries` and `progress` to preserve compatibility.
