# Wave 2 Write Freeze Plan

## Scope

Four running ConPort-like containers are in scope:

- `conport-dnh-crm-tgmirror0117`
- `dopemux-dopemux-mvp-dcd6-conport`
- `mcp-conport-dnh-crm-8d6d`
- `mcp-conport`

Each exposes ConPort HTTP, MCP/SSE, and info ports. Source inspection found
direct API writes plus stdio-admin and MCP write dispatches. All therefore
remain writers until stopped. Sanitized host-process inventory found no
additional local writer marker process.

## Mechanism

Use permitted mechanism 3: set each scoped container restart policy to `no`,
then stop every scoped container. This covers every container-served transport
without issuing a live write request. Client configurations remain unchanged:
their `docker exec` routes cannot execute against stopped containers.

## Authorized Commands

```sh
docker update --restart=no <each-scoped-container>
docker stop <each-scoped-container>
```

Commands operate only on the four discovered writer containers. No container,
image, volume, database, schema, credential, or client route is deleted or
changed. Docker inspection after each action is piped immediately through the
approved in-memory redactor.

## Expected Disruption

ConPort reads and writes through the four scoped instances become unavailable.
No target is deployed and no client is cut over. The freeze remains active for
independent review.

## Verification

- Re-list ConPort-named containers after freeze.
- Inspect state and restart policy only through `redact_docker_inspect.js`.
- Confirm every discovered container is stopped and restart policy is `no`.
- Confirm no local process matches the configured ConPort writer markers.

## Rollback

Only after explicit authorization to restore legacy writes:

```sh
docker update --restart=unless-stopped <each-scoped-container>
docker start <each-scoped-container>
```

Do not run rollback during Wave 2 unless continued freeze creates immediate
operational safety risk.

## Stop Conditions

- Any newly discovered writer not included in this plan.
- Any scoped writer cannot be stopped or has a restart policy other than `no`.
- Evidence of a remote writer sharing the authority plane.
- Redaction failure or secret persistence risk.
