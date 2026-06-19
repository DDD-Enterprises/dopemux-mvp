# ECC Audit Evidence Index

## Repo

- URL: https://github.com/affaan-m/ECC
- Commit SHA: 5b173d2e6c11b976a0f13b2f59125e08956c1d47
- Harvest mode: read-only static inspection
- Dopemux mutation: none

## Commands Run

See `COMMAND_LOG.md`. Clone plus git/file inventory, selected-file copy, and static `rg` scans only.

## Evidence Files

- `evidence/COMMANDS-QUICK-REF.md`
- `evidence/LICENSE`
- `evidence/README.md`
- `evidence/docs/SELECTIVE-INSTALL-ARCHITECTURE.md`
- `evidence/docs/SELECTIVE-INSTALL-DESIGN.md`
- `evidence/manifests/install-modules.json`
- `evidence/manifests/install-profiles.json`
- `evidence/package.json`
- `evidence/schemas/install-modules.schema.json`
- `evidence/schemas/install-profiles.schema.json`
- `evidence/schemas/install-state.schema.json`
- `evidence/the-security-guide.md`

## Candidate Areas

- Keyword hits: 25814 lines. Review `ECC_KEYWORD_HITS.txt`.
- Structure summary captured in `ECC_STRUCTURE_SUMMARY.md`.

## Security / Intake Concerns

- Suspicious text hits: 159 lines. Review `ECC_SUSPICIOUS_TEXT_HITS.txt`.
- Exec/secret risk hits: 6215 lines. Review `ECC_EXEC_SECRET_RISK_HITS.txt` before attaching excerpts.
- ECC is untrusted supply-chain input. No ECC code was executed.

## Skipped Commands

- npm install / npx / pnpm / bun: skipped by packet.
- hook/runtime execution: skipped by packet.
- ECC imports or scripts: skipped by packet.
- network after clone: not used.

## UNKNOWNs

- Runtime behavior is UNKNOWN because no ECC code was executed.
- Package lifecycle behavior is UNKNOWN because no package manager commands were run.
