# Input Pack — TP-DMX-MEMORY-TRINITY-001 Supervisor Review

**Pack ID**: `TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack`
**HEAD**: `19c6879d` (authoritative; run `./scripts/build_supervisor_input_pack.sh` to refresh)
**PR**: https://github.com/DDD-Enterprises/dopemux-mvp/pull/939

---

## Verify upload before review (mandatory)

ChatGPT/upload truncation has produced **stale partial packs** (~108,880 bytes / 32–33 entries).

**Canonical pack fingerprints** (from `PACK_INVENTORY.json`):

| Field | Expected |
|-------|----------|
| `zip_bytes` | **≥ 142000** (current build: **144741**) |
| `entry_count` | **≥ 44** (current build: **45**) |
| `zip_sha256` | `a8102235a5321835b52bec10e9ca8c1d34966620b70c2b77f93725eddd40c62c` |
| `zip_sha256_scope` | `all_entries_except_PACK_INVENTORY.json` (avoids self-referential drift) |
| `repo_head_sha` | `19c6879db594fea6e16585fdd5e8119b986fc89` (must match PROOF + supervisor final) |

**First step for supervisor**: unzip and confirm `PACK_INVENTORY.json` exists and lists:

```
proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.md
proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.json
proof/TP-DMX-MEMORY-TRINITY-001/PR_939_LIVE_REFRESH.md
proof/TP-DMX-MEMORY-TRINITY-001/PROOF.json
templates/plugin/l0_membership.json
audit_inputs/.../D2_D3_D4_EVIDENCE.md
docs/docs_index.yaml
```

If any are missing → **STOP** — pack is superseded/stale; do not grade D3/D5/final review.

---

## Build (reproducible)

```bash
cd /Users/hue/code/dopemux-mvp
./scripts/build_supervisor_input_pack.sh
./scripts/verify_supervisor_input_pack.sh   # must PASS before upload
```

Output: `audit_inputs/TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack.zip`

---

## Superseded packs (do not use)

| Pack | Bytes | Entries | Problem |
|------|-------|---------|---------|
| v1 ChatGPT upload | 100458 | 30 | No D2_D3_D4, no docs_index |
| v2 partial upload | ~108880 | 32–33 | Missing SUPERVISOR_FINAL_REVIEW, PR_939_LIVE_REFRESH, PROOF.json, l0_membership |
| **v3 canonical** | **144741** | **45** | Full required set + aligned PACK_INVENTORY.json |

---

## Tier 1 — Required (approval gate)

See `PACK_REQUIRED_FILES.txt` for machine-verified list.

| # | Path | Purpose |
|---|------|---------|
| 1 | `SUPERVISOR-5.5-PRO-PROMPT.md` | Full review prompt |
| 2 | `CHATGPT_DELTA_PROMPT.md` | Delta challenge only (preferred) |
| 3 | `proof/.../SUPERVISOR_FINAL_REVIEW.md` | Final verdict |
| 4 | `proof/.../SUPERVISOR_FINAL_REVIEW.json` | Machine verdict |
| 5 | `proof/.../PR_939_LIVE_REFRESH.md` | Live CI blockers |
| 6 | `proof/.../PROOF.json` | Refreshed proof + embedded_audit |
| 7 | `D2_D3_D4_EVIDENCE.md` | D2/D3/D4 corroboration |
| 8 | `docs/docs_index.yaml` | D3 catalog |
| 9 | `templates/plugin/l0_membership.json` | D5 fleet deps |
| 10 | `PACK_INVENTORY.json` | Upload integrity gate |

---

## ChatGPT instruction

Paste `CHATGPT_DELTA_PROMPT.md`. Verify `PACK_INVENTORY.json` before any grading.