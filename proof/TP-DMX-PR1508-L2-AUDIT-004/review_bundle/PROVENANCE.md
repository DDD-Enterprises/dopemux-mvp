# Provenance

Auditor command: `opencode run --pure --format json --model cheaper-inference/kimi-k3 --dir /tmp/pr1508-kimi-seal-r4 --title pr1508-kimi-audit-r4c`.
OpenCode 1.18.30. Session `ses_e330e3207ffeH6Sbq5K2BFbQAG`.
Session `info.model` is `{id: kimi-k3, providerID: cheaper-inference, variant: default}`.
Assistant message modelID `kimi-k3`, providerID `cheaper-inference`.
Event types: step_start, text, step_finish. Message parts: step-start, reasoning, text, step-finish.
No tool parts. Exit 0.
Two earlier `opencode run` attempts (`ses_e331102fcffe6N57EtiWuwT0Ty`, `ses_e330fd0d9ffeRiH7Rpka74ZDQb`) failed before the model stream with `Unexpected server error` while `--dir` was a percent-encoded session path. They are spent attempts, not this verdict.
Content diff sha256 `13d4065908832b8842554bd670e13615d17b5fbbbf83a3ffba7d94b074e8f57f`.
Prompt sha256 `7486e2b02d30c9293c66294000739676ebdc4a9776ef90dba893367eaf86b3f5`.
Audit jsonl sha256 `f1314d619ff73ec7b0b97689f79f8bf2798864d29d2f4f2b79846e8b80fceaa6`.
Session export sha256 `22f866b1284daa276975fcca2d6d5f5b8491e487c205a024969516f506bffdbb`.
Audited commit `dd9ac0732e055e87721f7b6cf60661dcf95122f9`.
Skill files are unchanged from `c30f74fe385c768a7599aa7920cfa5abc92313db`.
Packet 003 remains the audit of `661fa97b344b7986d109f11790d449b79f5c9c6b`. This packet audits the child-stop commit.
