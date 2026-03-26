# DDG Authority Removal

## Verdict

Bridge-local DDG authority has been removed from the active runtime.

## Evidence

- `GET /ddg/decisions` proxies to `conport_client.list_decisions(...)`
- `GET /ddg/search` proxies to `conport_client.search_decisions(...)`
- `POST /kg/decisions` proxies canonical decision writes to ConPort
- `POST /kg/progress` proxies canonical progress writes to ConPort
- active `/ddg/*` routes do not write to local DDG tables

## Remaining local state

- `DdgDecision`
- `DdgProgress`
- `DdgEmbedding`

These model classes remain in the codebase only as transitional, explicitly non-canonical local state and are not used as active runtime authority.
