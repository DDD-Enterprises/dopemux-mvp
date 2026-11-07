# PR 1500 freeze record

Frozen 2026-11-05 at about 06:21Z. Kept outside the repo. After this head only
proof/pr_merge/embedded-audit/pr-1500/ and the new audit packet dir may change.

- Head: 9fbd5fe27da6b21b58c59df34a34c14671ab5007
- Base (main): 583720375df69fbe50f7b8a6b199eaf026f46fb5
- Rulings: AUTHORIZATION.md.
- Unresolved review threads: 0. Mergeable: MERGEABLE. PR is ready for review, not a draft.
- Review bots finished at this head before the freeze: Codex no findings, Copilot no open issues.

## Required checks at the freeze

| Check | State |
|---|---|
| Analyze (javascript-typescript) | SUCCESS |
| Analyze (python) | SUCCESS |
| Analyze (ruby) | SUCCESS |
| PR Steward / final readiness | FAILURE |
| identity-check | SUCCESS |
| independent embedded audit | FAILURE |
| 📊 CI Pipeline Summary | SUCCESS |
| 📚 Documentation Check | SUCCESS |
| 🔒 Security Review | SUCCESS |
| 🧪 Unit Tests | SUCCESS |

The two FAILURE rows wait for this audit. `recheck` also fails for that reason and is not required.

## Audit input

13 changed, 13 included, 0 excluded. Each file's full text is in the diff (git diff -U100000).
Prompt 162933 bytes, the same bytes for both auditors, under AGY's 192 KB cap.
Scans: 0 instruction-like matches, 0 secret shapes, 0 email addresses, 0 unfilled placeholders.
A random delivery token is the last thing in the prompt.

## Probes (no repository content, not audit attempts)

Grok: exit 0, init.tools == [], 0 tool_use, receipt grok-4.5-build, self-reports grok-4.7, $0.012380896.
AGY: exit 0, SUCCESS, steps user_input and agent_response only, 60 tools offered, permission always-proceed.

## Hashes (sha256)

91d3a072e4a8f8a8a96aba8f2815bd035d4f19a48fd9d89f2d3f6aa3e5e14126  AUDIT_PROMPT.txt
013a62a21c15e32f6e78c59c69d9e4d9546a3fa5b4454cb2ad773b7b7148029f  TRUSTED_AUDIT_SECTION.txt
5b98c49918f878f3ea8eae0eb121c79a64a15626306fcdeb02ab47930258bd36  VALIDATION_SUMMARY.txt
01b05e442c45290f9f8642f5aa45c9c00e0174b95b867645eb4356234ca5b8f0  UNIFIED_DIFF.patch
b226e19a2081aeb37b1c6387c138e1a1b227a7cf21e50d24ecbab5952d7b1894  CHANGED_FILES.txt
e486d7841c47d1a9f09e5ee37ba4da8784063d01f9c8eb917db3a6bc9157e960  INSTRUCTION_LIKE.json
74092fbe37558ca74f2ad22fa184f12cf7125f0dfdff84925b6c8a100abb2c76  CHECKS_AT_FREEZE.json
b02139d368d707c03a6395cd3dd49d91b5f8a0aaa72d5c68ce978fcd4fc5ee5d  build_audit_input.py
b2a7fec5792c90bad5a0a19479a624779224f9e7bd51c0557fd7a711abd12d94  run_grok.sh
e4c00550d101ba9b08fa26f94cc55f18a16c124f91113ebe053efafb0fdcd448  run_agy.sh
92084492cf10e2dadb18417761b9d274e80a4ed910e215915dd8d92393b26e99  check_agy_delivery.py
4ba5a7746170ecbf57bbc8f01bc18b3ccaa1b6b76f3571e66885f771f957cc3b  DISALLOWED.txt
