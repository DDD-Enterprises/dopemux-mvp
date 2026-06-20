# ChatGPT Upload Gate — read before attaching zip

## STOP if your attached zip matches any stale fingerprint

| Variant | Bytes | Entries | Verdict |
|---------|-------|---------|---------|
| v1 | 100458 | 30 | **STALE** |
| v2 | ~108880 | 32–33 | **STALE** |
| v4 (latest bad upload) | **101458** | **30** | **STALE** — missing 8 required files |
| **canonical** | **≥ 142000** | **≥ 44** | OK |

## v4 missing files (observed 2026-06-20)

If any are absent inside the zip → output `PACK_STALE: STOP`:

- `audit_inputs/.../CHATGPT_DELTA_PROMPT.md`
- `audit_inputs/.../D2_D3_D4_EVIDENCE.md`
- `proof/.../SUPERVISOR_FINAL_REVIEW.md`
- `proof/.../SUPERVISOR_FINAL_REVIEW.json`
- `proof/.../PR_939_LIVE_REFRESH.md`
- `proof/.../AUDITOR_REPORT.md`
- `docs/docs_index.yaml`
- `templates/plugin/l0_membership.json`

## Do not upload PACK_INVENTORY.json separately

Integrity gate lives **inside** the zip at:
`audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack/PACK_INVENTORY.json`

An external inventory describing a 144KB pack while the zip is 101KB means **wrong zip attached**.

## Operator upload steps

```bash
cd /Users/hue/code/dopemux-mvp
./scripts/build_supervisor_input_pack.sh
./scripts/verify_supervisor_input_pack.sh   # must print PASS
open audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack.zip
```

Confirm Finder shows **~145 KB** and **45 items** before upload.

## ChatGPT paste (after zip attached)

Paste contents of `CHATGPT_DELTA_PROMPT.md` only. Do not paste the full A–F prompt unless doing first review.