# Auth Before / After

## Before narrowing target

- Event publication was identified as insufficiently protected.
- Bridge-local task and DDG mutations could be reached through mixed-authority surfaces.
- Adapter layers were capable of looking authoritative to upstream callers.

## After current runtime state

- `POST /events` requires authentication.
- `POST /events/tasks-imported` requires authentication.
- `POST /events/session-started` requires authentication.
- `POST /events/progress-updated` requires authentication.
- `POST /route/pm` requires authentication.
- blocked task routes fail closed instead of mutating bridge-local authority.

## Residual note

- ConPort proxy routes under `/kg/*` are not independently authenticated in the bridge runtime and continue to rely on upstream boundary placement. This is acceptable for the narrowed adapter shape but remains an operational hardening consideration.
