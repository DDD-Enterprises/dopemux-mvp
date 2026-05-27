---
id: audit-bundles
title: Evidence Bundle Builder Runbook
type: how-to
owner: '@hu3mann'
date: '2026-05-26'
---

# Evidence Bundle Builder Runbook

## What It Does (TP-DMX-AUDIT-BUNDLE-001)

`scripts/audit/build_evidence_bundle.py` produces a deterministic, secret-safe bundle directory containing:

| File | Purpose |
|---|---|
| `manifest.json` | Sorted file inventory; validates against `schemas/audit/bundle_manifest.schema.json` |
| `request.json` | Raw file contents for included (and redacted placeholder) files |
| `checksums.sha256` | `sha256:<hex>  <path>` lines for included files, sorted |
| `redactions.json` | Log of redacted and excluded files with reasons |

## Security Defaults

**Fail-closed by default.** A file containing a secret pattern is **rejected** (not included, not redacted) unless `--allow-redact` is explicitly passed. This means the bundle build succeeds with the file in `rejected[]`, and callers must decide whether to retry with redaction or handle the rejection.

Secret patterns detected:

- AWS access keys (`AKIA…`)
- GitHub tokens (`ghp_`, `gho_`, `ghs_`, `github_pat_`)
- Anthropic keys (`sk-ant-…`)
- OpenAI keys (`sk-…`)
- PEM private key headers
- Generic `api_key`/`token`/`secret`/`password`/`bearer` with value ≥16 chars

## Path Safety

Symlinks are rejected unconditionally. Files outside `allowed_root` are rejected as `path_escape`. Both checks occur before any file content is read.

## Determinism

- `files[]` sorted by path
- `json.dumps(…, sort_keys=True, indent=2)` throughout
- No `mtime`, no host username, no absolute host paths in output
- `created_at` is caller-supplied; pass a fixed value in tests for reproducible output

## Usage

### Python library

```python
from pathlib import Path
from scripts.audit.build_evidence_bundle import build_bundle

result = build_bundle(
    sources=[Path("proof/TP-FOO/diff.patch"), Path("proof/TP-FOO/PROOF.json")],
    dest=Path("proof/TP-FOO/review_bundle"),
    allowed_root=Path("."),
    tp_id="TP-FOO",
)
print(result.bundle_path)
```

### CLI

```bash
python -m scripts.audit.build_evidence_bundle \
  --allowed-root . \
  --tp-id TP-DMX-AUDIT-BUNDLE-001 \
  --dest proof/TP-DMX-AUDIT-BUNDLE-001/review_bundle \
  scripts/audit/build_evidence_bundle.py \
  schemas/audit/bundle_manifest.schema.json \
  tests/audit/test_evidence_bundle.py

# Allow redaction of files containing secrets (opt-in)
python -m scripts.audit.build_evidence_bundle \
  --allow-redact \
  --allowed-root . \
  --tp-id TP-DMX-AUDIT-BUNDLE-001 \
  --dest proof/TP-DMX-AUDIT-BUNDLE-001/review_bundle_redacted \
  scripts/audit/build_evidence_bundle.py
```

Exit codes:
- `0` — success, no rejections
- `1` — fatal error (dest exists, ValueError)
- `2` — success but files were rejected (check stderr)

### Direct module invocation

```bash
python scripts/audit/build_evidence_bundle.py --help
```

## Schema Validation

```bash
python -c "
import json, jsonschema, pathlib
schema = json.loads(pathlib.Path('schemas/audit/bundle_manifest.schema.json').read_text())
data = json.loads(pathlib.Path('proof/TP-DMX-AUDIT-BUNDLE-001/review_bundle/manifest.json').read_text())
jsonschema.validate(data, schema)
print('manifest OK')
"
```

## Invariants

- `manifest.json::schema_version` is always `"1.0.0"`
- `manifest.json::redactions_path` is always `"redactions.json"`
- `manifest.json::checksums_path` is always `"checksums.sha256"`
- `manifest.json::request_path` is always `"request.json"`
- `sha256` field is 64-char hex for included files, empty string for redacted/excluded
- `size_bytes` is 0 for redacted/excluded files
- Binary files are included without secret scanning (labeled `<binary file: N bytes>` in request.json)

## Downstream Consumers

- **TP-DMX-AUDIT-ROUTER-002**: imports `build_bundle` to produce review bundles for routing
- **TP-DMX-PAL-CLINK-RUNNER-003**: imports `build_bundle` to assemble PAL codereview payloads
- **TP-DMX-AUDIT-PROOF-004**: uses bundle output as audit evidence in proof finalization
