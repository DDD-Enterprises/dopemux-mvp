# R2 replacement final-audit subject binding

- Packet proof root: `TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002`
- Recovery amendment: `TP-DMX-GOV-G0-LITE-PR1282-AUDIT-EVIDENCE-RECOVERY-001-A1`
- Repository: `DDD-Enterprises/dopemux-mvp`
- Branch: `docs/g0-lite-implementation-authority-001`
- Base: `c7bc2fb479d7386825df73e028acdce723ee3388`
- Audited content head: `79404f3929c47fe09434ac07a36b936190282b56`
- Audited content tree: `324348b70013207d908e3f5af66302336dfd99e9`
- Base-to-content changed paths: `17`
- Candidate diff SHA-256: `e96480de3e258a3a41458e5dc928aa7ed9f75c7ce54c1b82349def667f0131fb`
- R2 packet SHA-256/blob: `4063e49b11c6acf68df762c90e73a3679541eb2c3e3f5c9cea9f8b0357d97a3d` / `dbc83426febe60eb8749ccac308826daf615d4d4`
- Current G0 packet SHA-256/blob: `6d6e9d5e2f93084a0738cd7cac57306299939df206bbeac5c3b4881329992856` / `aafe6fbcc3ce6321893722fefcf4121b35dd0d89`
- Current authority record SHA-256/blob: `03d3f76a7249e7e05b9c431c74ff33d9d72219c81338d51a844efb22d8743879` / `ae03821eac7c6295ea795a66220d03065e64e4f6`
- Late R1 proof SHA-256/blob: `c1128fe48d798b3e5891427ca9c28e568421c8a6c8c41db9cc4f28ab5ad33e0a` / `4bdd036dcd91ce07478a35c197dee3b5770f7b6c`
- Audit runner/model: `copilot-cli 1.0.82-0` / `claude-sonnet-4.6`
- Observed provider: `github`
- Fallback observed: `false`
- Tools executed: `0`
- Audit verdict: `PASS_WITH_RISKS`

Canonical R1 historical proof remains bound to historical audited bytes. Late
R1 closure proof binds historical R1 audit identity plus current closure bytes.
Replacement R2 audit binds exact frozen content above. No history rewrite.

Proof-only successors may touch only this packet proof root and
`proof/pr_merge/embedded-audit/pr-1282/`. They may not alter audited
substantive paths. READY, dispatch, merge, and activation authority: `NONE`.
