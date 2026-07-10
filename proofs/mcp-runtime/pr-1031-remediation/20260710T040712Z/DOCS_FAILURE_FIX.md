# Docs Workflow Failure Fix

**Head (fix commit):** `2f947530b9fe796c8c419212e1a303f3303f27a2`  
**Prior failing head:** `e2c684eaa0686c99f558a60b73119c6cfe27b4f9`

## Failure

Workflow `docs` run `29067426635` failed pre-commit on PR range.

Hooks:

1. `markdown-location-guard` — rejected `proofs/.../SUMMARY.md`
2. `root-hygiene` — rejected all files under top-level `proofs/`

## Root cause

Packet 006 introduced intentional evidence path `proofs/mcp-runtime/...`.
Repo hygiene allowlisted `proof/` and `proof_bundle/` but not `proofs/`.
Markdown location guard excluded `proof/` but not `proofs/`.

## Files changed

- `config/repo_hygiene/root_hygiene_policy.json` — add `proofs` to `allowed_root_dirs`
- `.pre-commit-config.yaml` — include `proofs/` in markdown-location-guard exclusions

## Local reproduction

```bash
pre-commit run markdown-location-guard root-hygiene \
  --from-ref origin/codex/tp-dmx-mcp-runtime-006-dnh-e2e-proof --to-ref HEAD
```

## Local pass evidence

Policy load confirms `proofs` allowlisted; markdown guard regex includes `proofs/`.
GitHub docs workflow re-run on fixed head required for VERIFIED.
