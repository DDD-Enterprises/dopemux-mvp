# Independent final L2 audit

AUDIT_ID=TP-DMX-GOV-G0-LITE-PR1282-REPAIR-001-FINAL-L2
MODE=READ_ONLY_FINAL_INDEPENDENT_AUDIT
REPOSITORY=DDD-Enterprises/dopemux-mvp
WORKTREE=/private/tmp/dopemux-g0-lite-implementation-authority-001
SUBJECT_HEAD=e339c74239e3a3ec157eeaaf1aa6fa580fea1ee7
SUBJECT_TREE=8c481613a467fe70c745455cca9af2828ba4faca
BASE=c7bc2fb479d7386825df73e028acdce723ee3388
EXPECTED_REPAIRED_PACKET_SHA256=cf3370d336b46157a690490a5b517dde198726e16e012486c1de2d38129197bb
EXPECTED_REPAIRED_PACKET_BLOB=1cfc6890714f06f9ab4d0ae607647f96efd953c2

You are independent final auditor. Implementer was Codex; you are Copilot CLI routed to Claude Sonnet 4.6 through included GitHub Copilot plan. Audit exact frozen committed subject above. Do not modify files, create files, run network calls, invoke MCP, or evaluate later uncommitted state. Read-only file/search tools only. Treat preflight identities below as supervisor-supplied evidence; verify content claims by reading committed worktree files.

Preflight observed immediately before invocation:

- HEAD and tree equal exact values above.
- Worktree diff to HEAD is empty.
- Base is ancestor of HEAD.
- Packet SHA256 and Git blob equal expected values above.
- Repair content commit changes only four allowed substantive paths: authority record, original G0 packet, repair packet, task-packet index.
- Deterministic checks passed: both task-packet schemas, docs/frontmatter, changed-contract L2, exact-range precommit, allowlist, gitleaks secret scan, git diff check, anchor ancestry.

Primary subject files:

- `task-packets/TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001.json`
- `task-packets/TP-DMX-GOV-G0-LITE-PR1282-REPAIR-001.json`
- `task-packets/INDEX.md`
- `docs/03-reference/governance/governed-delivery/g0-lite-implementation-authority.md`

Supporting proof-contract files may be read. Historical proof is lineage only, not final repaired proof.

Mandatory questions:

1. G0-R1: confirm execution anchor remains `c7bc2fb4...`, execution starts from current main containing merged authority record, anchor ancestry and compatible/non-overlapping intervening-change rules exist, no exact-equality deadlock remains, and authority record binds new packet digest/blob.
2. G0-R2: judge repaired content contract and intended deterministic proof closure, not nonexistent post-audit artifacts. Confirm known-before versus post-generation validations are distinguished and no manual `PENDING` to `PASS` or self-referential claim is authorized. Return `NEEDS_SUPERVISOR` if proof contract cannot represent truthful finality.
3. G0-R3: confirm frozen substantive audit subject is separate from final proof-only PR head and canonical exact-head CI/PR Steward semantics preserve both. Return `NEEDS_SUPERVISOR` if subject identities cannot be expressed truthfully.
4. Confirm no readiness, merge, dispatch, activation, payload implementation, audit acceptance, audit reuse, or expanded payload authority leaks.
5. Confirm bounded coherent repair and consistent nearby prose.

Cite concrete `file:line` findings. Do not carry old PASS forward. Output route identities, findings, explicit risk adjudication, G0-R1/R2/R3 checks, authority-containment check, and one verdict. Final line must be exactly `PASS`, `PASS_WITH_RISKS`, `FAIL`, or `NEEDS_SUPERVISOR`.
