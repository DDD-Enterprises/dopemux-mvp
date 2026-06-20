# Zip Byte-Level Validation

validated_at_utc=2026-06-16T06:14:59Z
head_sha=5d9a3e074f3d026d9f823e1e3fc0d320dfb83e86
zip_path=audit_inputs/final_gpt55_bundle/20260612T005736Z-final-gpt55-manifest.zip

## Commands

```bash
unzip -l audit_inputs/final_gpt55_bundle/20260612T005736Z-final-gpt55-manifest.zip
unzip -t audit_inputs/final_gpt55_bundle/20260612T005736Z-final-gpt55-manifest.zip
shasum -a 256 audit_inputs/final_gpt55_bundle/20260612T005736Z-final-gpt55-manifest.zip
```

## Results

| Check | Result |
|-------|--------|
| `unzip -t` | PASS — No errors detected in compressed data |
| SHA256 matches `ZIP_SHA256.txt` | PASS |
| Entry count | 15 files (7 manifest reports + 4 source packet files + 4 duplicate-free paths) |

## Zip scope (explicit)

This zip is a **manifest-plus-source courier**, not the full evidence warehouse.

**Included in zip:**
- Pack 5 manifest metadata (`ATTACHMENT_MANIFEST.md`, `ATTACHMENT_EXISTENCE_REPORT.md`, `PROOF.json`, `RESULT.md`, etc.)
- Preserved prompt source packet (`gpt55_recon_source/CODEX_RECON_PACKS_SOURCE.md` + checksum sidecars)

**Not included in zip (attach separately from PR tree or raw GitHub paths):**
- `audit_inputs/dcp-runner-recon/**`
- `audit_inputs/multi_model_orchestration_evidence/20260612T003401Z.zip`
- `audit_inputs/ecc_dopemux_audit/ECC_DOPMUX_AUDIT_EVIDENCE.tgz`
- `docs/03-reference/dcp/chatgpt-mcp-readonly/**`
- `proof/TP-DCP-MCP-RO-0001/**` (published proof uses `COMMAND_LOG_SUMMARY.md`; full `COMMAND_LOG.md` is local-only)

## Stale validation note

Reviews against commit `4a5ecf86db` describe an older 7-entry manifest-only zip (`SHA256 8506a92c...`). Current head `5d9a3e074` supersedes that artifact.