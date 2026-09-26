# Live Evidence

Captured: 2026-08-28T13:42:31Z

Operation: verification-only reconciliation. No credential or repository-setting mutation occurred.

## Repository custody

- Root: `/Users/hue/code/dopemux-mvp`
- Remote: `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- Starting branch: `main`
- `CURRENT_MAIN`: `5900c27d3c38b515204bd5dc4baed8b5e14e2a8e`
- `CURRENT_TREE`: `5900c27d3c38b515204bd5dc4baed8b5e14e2a8e`
- Primary checkout had unrelated dirty cache paths; proof materialization used isolated worktree `/private/tmp/dopemux-mvp__ddd_key_rotation_002`.

## Prior receipt search

- `PRIOR_ROTATION_RECEIPT`: `NONE`
- Repository history and current tree had no match for predecessor ID, rotation marker, compromised fingerprint, or `INCIDENT_RECEIPT`.
- Bounded identifier-only search of `/Users/hue/Downloads` had no match.
- Historical receipt absence was not treated as evidence that rotation remained incomplete.

## Actions secret metadata

- Repository `DDD_RELEASE_GATE_PRIVATE_KEY`: present, updated `2026-08-28T11:28:04Z`.
- Repository `DDD_RELEASE_GATE_APP_ID`: not present.
- Organization secret metadata: `UNKNOWN`; GitHub API returned HTTP 403 because current token lacks organization Actions-secrets administration permission.
- No secret value was read.
- Update timestamp is supporting evidence only.

## Current GitHub App state

Source: authenticated GitHub App settings UI for organization-owned App `ddd-release-gate`.

- App ID: `4420140`
- Compromised fingerprint present: `NO`
- Registered fingerprint: `SHA256:K3J6LTIKlDnBxI7ogv/7OCIwujz/GMm4s1F7TfaDo8U=`; UI says added Jul 28 by `hu3mann`.
- Registered fingerprint: `SHA256:pvV1uU7OdLHLNOzjTeLtaZuGSWQ/5xPxBHGViNniJfM=`; UI says added about 2 hours before observation by `hu3mann`.
- App permissions: Actions read, Checks read, Contents read, Metadata read, Pull requests write.
- Events: none.
- Installation selection: only selected repositories.
- Selected repository count: 1.
- Selected repository: `DDD-Enterprises/dopemux-mvp`.
- No generate, delete, save, remove, suspend, or uninstall control was invoked.

## Current secret-backed smoke

Source: GitHub Actions run `33168063288`, URL `https://github.com/DDD-Enterprises/dopemux-mvp/actions/runs/33168063288`.

- Event: `workflow_dispatch`
- Ref: `main`
- Head: `5900c27d3c38b515204bd5dc4baed8b5e14e2a8e`
- Created: `2026-08-28T11:40:46Z`
- `Fail closed without app secrets`: PASS
- `Mint ddd-release-gate installation token`: PASS
- `Resolve PR head and preflight`: expected FAIL because PR `0` does not exist
- `Post exact-head APPROVE as ddd-release-gate[bot]`: SKIPPED
- Token cleanup: PASS; run log says token revoked

The repository secret update timestamp predates this smoke by about 12 minutes and remained unchanged when queried. Combined with current App-key inventory, this proves the effective secret corresponds to a currently registered valid App key while the known compromised fingerprint is absent.

## Outcome

`ALREADY_ROTATED_VERIFIED`

Anti-double-rotation invariant applied:

- New key generation: NO
- Secret rewrite: NO
- App-key deletion: NO
- Real PR approval: NO
- App permission change: NO
- Installation-scope change: NO
