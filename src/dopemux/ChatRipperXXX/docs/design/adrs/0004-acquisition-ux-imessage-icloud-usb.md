ADR-0004: iMessage Acquisition UX (USB Backup & iCloud)

Status: Proposed | Owner: You | Last Updated: 2025-09-02 PT

## Context

We support macOS local DB extraction today. Users also request iPhone USB backup and Messages in iCloud paths. iCloud may evict attachments, leading to missing binaries even for local DBs.

## Decision (Proposed)

1) Standardize on USB backup acquisition for iPhone path: detect backups (encrypted ok with password), locate messages DB and attachments, and run the same normalizer as macOS local.
2) For iCloud, initially provide a completeness scan and operator guidance; do not automate downloads until an OS‑supported, reliable method is identified.

## Consequences

- CLI to accept a `--from-backup <path>` option (future slice) while keeping the current macOS local DB path.
- Maintain and emit `missing_attachments.json` to guide manual remediation for iCloud‑evicted files.
- Defer automation of iCloud downloads; document manual steps and risks.

## Alternatives Considered

- Full iCloud automation via UI scripting: brittle and policy‑sensitive; deferred.
- Third‑party tools: raises trust and licensing concerns; not adopted as default.

## References

- iMessage Extractor Spec – completeness & evicted attachments
- NEXT.md – Open question on iCloud/USB acquisition UX
