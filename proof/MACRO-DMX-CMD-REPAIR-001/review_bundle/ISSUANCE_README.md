# Issuance package - MACRO-DMX-CMD-REPAIR-001 (flattened)

The issuance package was issued at `task-packets/MACRO-DMX-CMD-REPAIR-001/` in the main checkout (untracked). It is kept here, flattened, because:

1. the change-contract preflight validates `task-packets/` against the legacy packet schema and a docs-frontmatter rule, and rejects GEC v2 packets and these return documents there; and
2. the proof-only closure form of `validate_change_contract.py` accepts only a fixed set of proof artifacts plus flat `review_bundle/<name>.(txt|json|md|diff)` files (no subdirectories).

Content is byte-identical to issuance for the pinned members (`MACRO_PACKET.json`, `EXECUTION_BINDING.json`, `W01..W04_TASK_PACKET.json`); `W05`/`W06` are the AMENDMENT-01/02 packets. Path strings inside the pinned JSON (for example `authority_refs.task_packet_ref`, `task_packet_ref.path`) still name the original structure and were deliberately not edited. To re-run `ct validate-macro`, rebuild the original tree from this table (the hashes are the authority). The raw AGY streams carry a `.txt` suffix; content unchanged. Per-audit checksum files use the flat names.

| Original path (in the issuance package) | Flat name in review_bundle/ | sha256 |
|---|---|---|
| `AMENDMENT-01/WORKSTREAMS/W05/TASK_PACKET.json` | `W05_TASK_PACKET.json` | `e7886743058c07625cafec13d97b08f69b335a23789fd0cc8d71e4151f87caca` |
| `AMENDMENT-02/WORKSTREAMS/W06/TASK_PACKET.json` | `W06_TASK_PACKET.json` | `43a1ded60555e109b9fd55256d692d0d86c55ca92a888b6527228b7735783dfa` |
| `AUDIT-01/ADJUDICATION.md` | `AUDIT01_ADJUDICATION.md` | `640cf57fc9aa47a16df57417f04e15cb7c140770854d1b60ca5bbcdd937ce1b1` |
| `AUDIT-01/AUDIT_PROMPT.txt` | `AUDIT01_AUDIT_PROMPT.txt` | `c5366bb6df8fc2aba6a438e7fd912837acfa86906b3f8c1940536cd37ec3c54d` |
| `AUDIT-01/AUDIT_RESPONSE.txt` | `AUDIT01_AUDIT_RESPONSE.txt` | `5a3ecd616088e767224aab4311706e72d1f2124d8ca7c84ce47e5c3204be9bde` |
| `AUDIT-01/INVOCATION.txt` | `AUDIT01_INVOCATION.txt` | `facfe6ee0a48a133981d846eca04f51a1c88a0cdfd31177ca2a4e9cc9556db0b` |
| `AUDIT-01/agy_err.txt` | `AUDIT01_agy_err.txt` | `3a7f8550106d86abb322e8ed0fb30a0296c0e97c6be03d5a8033b99d16737459` |
| `AUDIT-01/agy_out.ndjson.txt` | `AUDIT01_agy_out.ndjson.txt` | `a336751713a409ac4a559e85d47dad32acb3320297651a89ce1e9552d2d0581f` |
| `AUDIT-01/launched_at.txt` | `AUDIT01_launched_at.txt` | `d3e6fdb6d14180d8af3f173d2d538d0037653c661ae68f6b73644ecea2ece4ba` |
| `AUDIT-02/ADJUDICATION.md` | `AUDIT02_ADJUDICATION.md` | `6093438159e939a1d9de3ae243ac259bbfc91eaa92e616966b5118ca67bbe8ca` |
| `AUDIT-02/AUDIT_PROMPT.txt` | `AUDIT02_AUDIT_PROMPT.txt` | `94992742f6887fde3771dd5820424f5ee13803fb793c504ce1e01c5af308af74` |
| `AUDIT-02/AUDIT_RESPONSE.txt` | `AUDIT02_AUDIT_RESPONSE.txt` | `7fbd145b8cfc1896ac953126029957d3dcf19e78f415e06a08313c19748c5660` |
| `AUDIT-02/INVOCATION.txt` | `AUDIT02_INVOCATION.txt` | `f41966d8d5e4f315f3913fba6afead3508dc3a05817e0fbdbe4dc7408fea95a3` |
| `AUDIT-02/agy_err.txt` | `AUDIT02_agy_err.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `AUDIT-02/agy_out.ndjson.txt` | `AUDIT02_agy_out.ndjson.txt` | `e6fd24c16462330bf65ddb0fc0e1fe3a6c093423c5b5aee9a02d4911080a7684` |
| `AUDIT-02/launched_at.txt` | `AUDIT02_launched_at.txt` | `ffb6cc8c9aa36a7652c3d9fa2d8fc587b3a79c5c5bdf467e566fc79fa0175ac2` |
| `EXECUTION_BINDING.json` | `EXECUTION_BINDING.json` | `10dca84695fe6dd8207bf9b1388ae10721cc3ed13f0887cfa838a48a4ae067d9` |
| `ISSUANCE.md` | `ISSUANCE.md` | `40e6cb6e2bcbfb8da2264680800b960e7864136b07461200529cef22c121d7e0` |
| `MACRO_PACKET.json` | `MACRO_PACKET.json` | `70f16ae0ed733068f17ecfdd417e2d94391f36c41f3aedd73ecfca86f60ef394` |
| `README.md` | `ISSUANCE_README.md` | `524cb812a0579d2c13f1053df81d6b3bb35bf72c360dac581c9db7a0587a92f5` |
| `RETURN-01.md` | `RETURN-01.md` | `3c7de9e84d4fffe2b0b510b1965a1251100bb2203e2852a900af66a895938630` |
| `RETURN-02.md` | `RETURN-02.md` | `8bff93fcf20a6ab4bce5e2c54a6f0668c3968ab89f8df9b366becbda90fe190c` |
| `RETURN-03.md` | `RETURN-03.md` | `12613b22c6468765f8914e817caa1fddeaef4b674c488adb634dd2698f15b991` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `W01_TASK_PACKET.json` | `9ca0fc3ce33fc4a8bcdf488f7031d282b2ab90fa2960549d4bc7db5e4110282b` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `W02_TASK_PACKET.json` | `7f12e520b153facf582ead911532b026f6b921a981e7cf5a4d7f35c69d13d42e` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `W03_TASK_PACKET.json` | `1d9581f17a5aa7486d135a5e7446c2fa898bbd73a2df8544d8aea64fc4db2a5e` |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `W04_TASK_PACKET.json` | `236af3f2e1b8b276e732d1bc51ec9e47f28301e616d57c7496c1896ac866d113` |
