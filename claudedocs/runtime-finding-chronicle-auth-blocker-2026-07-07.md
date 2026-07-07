# Runtime Finding — Chronicle Fill Has an Upstream Auth Blocker

**Date**: 2026-07-07 · **Severity**: HIGH (changes the P0 chronicle fix) · discovered via full-path runtime proof on the live stack
**Supersedes the "mirror alone fills the chronicle" assumption** from `service-audit-2026-07-04.md` §4.

## What runtime proof revealed (that static audit + unit tests did not)

I rebuilt `dopecon-bridge` from the branch (mirror code confirmed deployed: `/app/dopecon_bridge/promotable_mirror.py` present, 2 refs in `routes.py`), then logged a **real** ConPort decision via `POST /api/decisions` (HTTP 200, `status: logged`). The chronicle did **not** fill. Tracing the failure:

```
ConPort _log_decision → integration_bridge_client → POST bridge /events
  → HTTP 401 Unauthorized
     (ConPort sends NO auth token; bridge /events requires get_current_user JWT)
  → event never reaches _publish_event_internal → my mirror never runs
```

And the deeper cause: **`dopecon_bridge/auth.py: users_db = {}`** — the bridge's user store is empty, so **no caller can ever obtain a JWT**. The authenticated `/events` publish path is 100% dead for every service, not just ConPort.

### The real publisher topology (measured)

| Publisher | Target | Mechanism | Reaches mirror? |
|---|---|---|---|
| ConPort `decision.logged` | bridge `/events` | HTTP (no auth) | ❌ 401 — reaches neither stream |
| native_hooks `native_hook_activity` | `dopemux:events` | **direct Redis XADD** | ❌ bypasses bridge HTTP entirely (and non-promotable) |
| capture_client (PM, hook errors) | `activity.events.v1` | direct Redis XADD | ✅ already correct — this is the one working promotable path |

`dopemux:events` (3489+ events) is **all** `native_hook_activity` heartbeat from direct-Redis writes; `activity.events.v1` = 0; `work_log_entries` = 0.

## Why my current fix (bridge HTTP mirror) cannot work here

`mirror_promotable_event` lives inside `_publish_event_internal`, which only runs for **successful authenticated** HTTP publishes to `/events`. With `users_db` empty, nothing authenticates, so the mirror is unreachable dead code in this deployment. The 7 unit tests pass because they call the mirror function directly, bypassing the auth gate that blocks it in production.

## What IS proven

- **Consumer side (runtime PASS)**: injecting my exact `build_mirror_envelope()` output into `activity.events.v1` → real dope-memory promotes it → `work_log_entries` 0→1. The promotion path works; the envelope shape is correct.
- **Mirror deploys correctly**: the branch image contains and wires the mirror.
- **The gap is purely getting promotable events onto `activity.events.v1`** through a live (non-dead-auth) mechanism.

## Corrected fix options (needs a decision)

The mirror must move off the dead authenticated-HTTP path. Ranked:

1. **[Recommended] ConPort emits `decision.logged` direct to `activity.events.v1`** — mirror the pattern that already works (capture_client → activity.events.v1). ConPort's `integration_bridge_client` does a Redis `XADD` to `activity.events.v1` (capture-envelope shape) instead of / in addition to the 401'ing HTTP POST. Publisher-owned, no auth, reuses `build_mirror_envelope` logic. Effort **S–M**. Fixes decisions (the highest-value promotable type).
2. **Stream relay `dopemux:events` → `activity.events.v1`** — a bridge background consumer that mirrors promotable types, publisher-mechanism-agnostic. But note: ConPort decisions never reach `dopemux:events` either (they 401), so a relay alone does **not** fix decisions — only helps if publishers are first redirected to write `dopemux:events`. Effort **M**.
3. **Fix bridge auth** — seed a service user + give ConPort credentials + send Bearer, so the existing HTTP mirror fires. Keeps my code as-is but adds credential management to a private-network internal call that arguably shouldn't need user-JWT auth. Effort **M**, brittle.

**Recommendation**: Option 1. It's the minimal change on the canonical writer (ConPort), uses the proven-working stream, and keeps `promotable_mirror.build_mirror_envelope` as the shared envelope builder. The bridge HTTP mirror stays as a correct-but-secondary path for any future authenticated publisher.

## Live-stack state after this session

- `dopecon-bridge` now runs the **branch build** (`2b146bfb31d2`, healthy, backward-compatible superset) — the original `:latest` image was replaced by the rebuild and pruned, so it wasn't restorable. This is the code about to merge via PR #1009; rebuild from `main` or merge to normalize.
- Test decision deleted from ConPort KG; `activity.events.v1` stream/group restored; `work_log_entries` back to 0. No other changes.
