# Input Pack — TP-DMX-MEMORY-TRINITY-001 Supervisor Review

**Pack ID**: `TP-DMX-MEMORY-TRINITY-001-supervisor-input-pack`
**HEAD**: `bab18a82f` (run `./scripts/build_supervisor_input_pack.sh` to refresh)
**PR**: https://github.com/DDD-Enterprises/dopemux-mvp/pull/939 (OPEN)

---

## Verify upload before review (mandatory)

ChatGPT upload truncation has produced **stale partial packs**. An external `PACK_INVENTORY.json` describing 144KB while the zip is 101KB means **wrong zip attached**.

**Canonical pack fingerprints** (from `PACK_INVENTORY.json` inside zip):

| Field | Expected |
|-------|----------|
| `zip_bytes` | **≥ 142000** (current build: **144602**) |
| `entry_count` | **≥ 44** (current build: **45**) |
| `zip_sha256` | `fa0c185691563d9b1111f11bbb77c45a9d4af378face7db30f0b07eebdc4a109` |
| `zip_sha256_scope` | `all_entries_except_PACK_INVENTORY.json` |
| `repo_head_sha` | `bab18a82f8ccd66fde2cd04ea0a33b5061768321` |

**First step for supervisor**: unzip attached zip and confirm these paths exist:

```
proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.md
proof/TP-DMX-MEMORY-TRINITY-001/SUPERVISOR_FINAL_REVIEW.json
proof/TP-DMX-MEMORY-TRINITY-001/PR_939_LIVE_REFRESH.md
proof/TP-DMX-MEMORY-TRINITY-001/PROOF.json
templates/plugin/l0_membership.json
audit_inputs/.../D2_D3_D4_EVIDENCE.md
audit_inputs/.../CHATGPT_DELTA_PROMPT.md
docs/docs_index.yaml
```

If any are missing → **STOP** — `PACK_STALE`; do not grade.

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
| v1 | 100458 | 30 | No D2_D3_D4, no docs_index |
| v2 | ~108880 | 32–33 | Missing final review, PROOF, l0 |
| v4 ChatGPT upload | **101458** | **30** | Missing 8 required files |
| **canonical** | **144602** | **45** | Full set + PACK_INVENTORY inside zip |

See `UPLOAD_GATE.md` for operator upload checklist.

---

## ChatGPT instruction

1. Attach zip only (~145 KB, 45 entries)
2. Paste `CHATGPT_DELTA_PROMPT.md`
3. Supervisor Step 0 must inspect zip bytes/entries before grading