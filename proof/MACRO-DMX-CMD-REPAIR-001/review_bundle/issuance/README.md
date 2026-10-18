# Issuance package - MACRO-DMX-CMD-REPAIR-001

This is the in-branch copy of the issuance package. It was issued at `task-packets/MACRO-DMX-CMD-REPAIR-001/` in the main checkout (untracked) and is kept here, under `proof/`, because the repo's change-contract preflight validates everything under `task-packets/` against the legacy packet schema and a docs-frontmatter rule, and rejects GEC v2 packets and these return documents.

- The six pinned members (`MACRO_PACKET.json`, `EXECUTION_BINDING.json`, `WORKSTREAMS/W01..W04/TASK_PACKET.json`) are byte-identical to issuance. Their internal path strings (for example `authority_refs.task_packet_ref`) still name the original `task-packets/...` location and were deliberately not edited.
- `ct validate-macro --file MACRO_PACKET.json` resolves its references relative to this folder and reports STATIC_VALID here.
- Documents in this folder that name paths were updated to the in-branch location.
- `AUDIT-0x/agy_out.ndjson.txt` is the raw AGY stream, renamed with `.txt` so it classifies as an L0 path; its content is unchanged.
- The proof-only closure form of `validate_change_contract.py` allows only `PROOF.json`, `PROOF.json.sig`, `AUDITOR_REPORT.md` and `review_bundle/`; this folder therefore lives under `proof/MACRO-DMX-CMD-REPAIR-001/review_bundle/issuance/`, and `SUMMARY.md` under `review_bundle/`.
