# SOURCE_RESOLUTION_REPORT

For every slot: logical slot, selected source, rejected candidates, authority class, blob SHA, content SHA-256, byte count, rationale.

## Slot 01 -- 01_AGENTS.md

- Selected source path: `AGENTS.md`
- Authority class: runtime_governance
- Freshness class: VOLATILE_14_DAYS
- Source blob SHA: `c640eb5539d6de584126534ba2a81a01d24feb9d`
- Content SHA-256: `369e7af2b15af9305ab1256d1ed4b8b231c62d76b0a286ed73d18f488d207bed`
- Bytes: 17848
- Rationale: Root AGENTS.md is the single tracked candidate and is the canonical Codex/agent governing-doctrine file referenced directly by .claude/CLAUDE.md.
- Rejected candidates: none (single tracked candidate)

## Slot 02 -- 02_RULES.md

- Selected source path: `docs/03-reference/governance/rules.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `8c6fb115d9e39024d1423e98cc5dc4c334256f3f`
- Content SHA-256: `b9382cff07d86d2ee6f45949a5cdfabb987be87e294309332e53e1fe4b0529d8`
- Bytes: 9968
- Rationale: Root RULES.md is absent from EXECUTION_BASE_SHA (confirmed via git cat-file -e). Per packet fallback instruction, used the tracked governance rules file instead.
- Rejected candidates:
    - `RULES.md` -- BLOCKED_SOURCE_MISSING: git cat-file -e <sha>:RULES.md fails; not present in tree

## Slot 03 -- 03_PROJECT.md

- Selected source path: `PROJECT.md`
- Authority class: runtime_governance
- Freshness class: VOLATILE_14_DAYS
- Source blob SHA: `29670dd2286c7936f28da598a3c961a6eb8765f3`
- Content SHA-256: `a3bfabc28ad461c85be3b97c939e99c4288a641fa412ccaeebf12d935d839942`
- Bytes: 12763
- Rationale: Root PROJECT.md is the single tracked candidate named explicitly by the packet.
- Rejected candidates: none (single tracked candidate)

## Slot 04 -- 04_ARCHITECTURE.md

- Selected source path: `ARCHITECTURE.md`
- Authority class: runtime_governance
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `34438d5e0f7299455a44c33e25eac6bb14ec4616`
- Content SHA-256: `f6d1dfdaddb6afc719cf7bab299bb71552bbc1849fc2b2378a34d309d98e89e5`
- Bytes: 8742
- Rationale: Packet slot text explicitly names 'current tracked ARCHITECTURE.md'; the root file is tracked at EXECUTION_BASE_SHA (contradicting the now-stale doc-trust-map.md note that it was untracked). docs/04-explanation/architecture/dopemux-architecture.md is a distinct, differently-scoped explanation-type doc and is not the file the packet names.
- Rejected candidates:
    - `docs/04-explanation/architecture/dopemux-architecture.md` -- REDUNDANT_WITH_HIGHER_AUTHORITY: Packet slot 04 explicitly names root ARCHITECTURE.md; this is a separate 'explanation' typed doc (frontmatter type: explanation, dated 2026-05-19), not the named source.

## Slot 05 -- 05_SYSTEM_BOUNDARIES.md

- Selected source path: `docs/03-reference/systems/system-boundaries.md`
- Authority class: truth_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `3754ceb22b9293cda71a0bcd35d9fae19a6799bf`
- Content SHA-256: `eb155df96b2f6bd3a24196c004bc0fca54cd9974e720afad701149b33273bedb`
- Bytes: 8436
- Rationale: Root SYSTEM_BOUNDARIES.md absent at EXECUTION_BASE_SHA; docs/03-reference/systems/system-boundaries.md is the sole tracked candidate and is doc-trust-map HIGH-classified.
- Rejected candidates:
    - `SYSTEM_BOUNDARIES.md` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent

## Slot 06 -- 06_PM_PLANE.md

- Selected source path: `docs/03-reference/planes/pm/pm-plane.md`
- Authority class: truth_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `ce63000a39e9c86cb6fb02662d030af6acf2931a`
- Content SHA-256: `039e4c7feb51102204009dd6b5e95287c236e0c934e54d4c5e3c15456dccc776`
- Bytes: 9530
- Rationale: doc-trust-map.md rates docs/03-reference/planes/pm/pm-plane.md HIGH ('PM plane references') and notes it derives from tracked truth docs plus src/dopemux/pm/reads.py and writes.py. Root PM_PLANE.md is NOT itself named in doc-trust-map.md's source-path lists (this is an analogical extension, not a direct citation, corrected after embedded-audit review) -- the direct evidence is a content comparison of the two files themselves: docs/03-reference/planes/pm/pm-plane.md carries dated frontmatter and an explicit authority chain (truth-gaps.md, truth-data-events.md, truth-systems.md, truth-canonicals.md, src/dopemux/pm/writes.py, services/dopecon-bridge/README.md, routes.py, workflow_store.py, bridge_adapter.py), while root PM_PLANE.md has no such frontmatter or cited chain. The packet's own slot-6 wording is deliberately generic ('current tracked PM-plane source') unlike slots 3/4 which name the root filename explicitly, indicating the resolver should pick the higher-authority tracked reference rather than the root file.
- Rejected candidates:
    - `PM_PLANE.md` -- REDUNDANT_WITH_HIGHER_AUTHORITY: Not itself named in doc-trust-map.md's LOW-trust source-path list; rejected on independent content comparison instead -- it lacks the dated frontmatter and explicit truth/runtime-path authority chain that docs/03-reference/planes/pm/pm-plane.md carries.

## Slot 07 -- 07_SERVICE_CATALOG.md

- Selected source path: `SERVICE_CATALOG.md`
- Authority class: runtime_governance
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `3bd2102260ffab7946bcf289fd80f252ab42dbdd`
- Content SHA-256: `1a824133ef2c49144eeb55a258a2c218a9777ad57d006055f30eee6490202fea`
- Bytes: 13810
- Rationale: Root SERVICE_CATALOG.md is the sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 08 -- 08_DOC_TRUST_MAP.md

- Selected source path: `docs/03-reference/governance/doc-trust-map.md`
- Authority class: governance
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `8157276847ea462ef5caaa227e8ac8dc156f97b0`
- Content SHA-256: `fa7690867a5f2d8ebc97168798a52c79f17285672f67d45497283bdc9992b3c4`
- Bytes: 9770
- Rationale: Sole tracked candidate; dated 2026-04-30 with next_review 2026-07-29 (one day after packaging date 2026-07-28) -- near its own review horizon, noted as a residual risk.
- Rejected candidates: none (single tracked candidate)

## Slot 09 -- 09_RUNTIME_AUTHORITY_VERIFICATION.md

- Selected source path: `docs/03-reference/governance/runtime-authority-verification.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `5182816340817ba2c59990735628901ea01e9be1`
- Content SHA-256: `88eaba545c129fab9e6fb64f233bb906427a163be714b53fc07e04170eeff83a`
- Bytes: 4701
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 10 -- 10_RUNTIME_AUTHORITY_MANIFEST.json

- Selected source path: `config/runtime_authority_manifest.json`
- Authority class: runtime_config
- Freshness class: VOLATILE_14_DAYS
- Source blob SHA: `9bd725c8445372a037379156bc2a0b21473dcb74`
- Content SHA-256: `ac8b68fed0b9048644c122d2c4f27c273ee01d81acc5d6e97b61fe503c5d0831`
- Bytes: 29486
- Rationale: Sole tracked candidate; also the input to scripts/verify_runtime_authority.py.
- Rejected candidates: none (single tracked candidate)

## Slot 11 -- 11_MEMORY_TRINITY_ADR.md

- Selected source path: `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md`
- Authority class: adr
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `2fd463ca4609a1acc15be79d29dab1c2133d06c5`
- Content SHA-256: `4f233a41689d67736dba0a13a3a15e201d058c50f0c3e36f5ff07e0abbb6f52a`
- Bytes: 13475
- Rationale: Sole tracked candidate; frontmatter confirms status: accepted, matching the required 'accepted Memory Trinity authority ADR'.
- Rejected candidates: none (single tracked candidate)

## Slot 12 -- 12_TRUTH_CANONICALS.md

- Selected source path: `docs/03-reference/truth/truth-canonicals.md`
- Authority class: truth_reference
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `423aabdd661d879a6b64692047e259c88dc8267e`
- Content SHA-256: `2b1580abfb30bb4d4c643fa8c76c3de593762949c0aea8718d2ae2356db05741`
- Bytes: 12438
- Rationale: Root TRUTH_CANONICALS.md absent at EXECUTION_BASE_SHA; tracked docs/03-reference/truth path is doc-trust-map HIGH and the sole remaining candidate.
- Rejected candidates:
    - `TRUTH_CANONICALS.md` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent

## Slot 13 -- 13_TRUTH_INTERFACES.md

- Selected source path: `docs/03-reference/truth/truth-interfaces.md`
- Authority class: truth_reference
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `f22267907cf3443876fd8bec9e1dc28d43b459e1`
- Content SHA-256: `166710c38e2b930d1e6f6c8cd6ee8aee26578265631fa51bb4e42912a416da12`
- Bytes: 11666
- Rationale: Root TRUTH_INTERFACES.md absent at EXECUTION_BASE_SHA; tracked docs/03-reference/truth path is the sole remaining candidate.
- Rejected candidates:
    - `TRUTH_INTERFACES.md` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent

## Slot 14 -- 14_TRUTH_GAPS.md

- Selected source path: `docs/03-reference/truth/truth-gaps.md`
- Authority class: truth_reference
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `82d6034d3ae7a3e1b80f0b4edf8b4f2383f1e82e`
- Content SHA-256: `450f52a5cb1c609db67e64af013590e8a22e8b69b7c8720c231aa33599af5967`
- Bytes: 6875
- Rationale: Root TRUTH_GAPS.md absent at EXECUTION_BASE_SHA; tracked docs/03-reference/truth path is the sole remaining candidate.
- Rejected candidates:
    - `TRUTH_GAPS.md` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent

## Slot 15 -- 15_SYSTEM_DOPEMUX.md

- Selected source path: `docs/03-reference/systems/dopemux/system-dopemux.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `c3b990a54eec0086bf052f6c00a0bfbb19586f0c`
- Content SHA-256: `28c3791264ccadcfca400bde67547dd1000f104763cbe7ac93269861f56d0d38`
- Bytes: 15177
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 16 -- 16_SYSTEM_DOPETASK.md

- Selected source path: `docs/03-reference/systems/dopetask/system-dopetask.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `4c52e38c54f827ecc6ab26027ee619eb3ef2ec4b`
- Content SHA-256: `6ebe437b8f9bed32183a7bfdfe97f67495c0af4ff6adafdd54aba9bd45ceb28f`
- Bytes: 11309
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 17 -- 17_SYSTEM_TASK_ORCHESTRATOR.md

- Selected source path: `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `51199defd75d6a4c12b646039e2e3349d3fe1c3e`
- Content SHA-256: `3df644136cb1475cfa49ba47e6256f25382af8f0beee2b8ee014d03daf7f22b5`
- Bytes: 13858
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 18 -- 18_SYSTEM_CONPORT.md

- Selected source path: `docs/03-reference/systems/conport/system-conport.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `fddf579a946fe42ea67e7d0dd1b83a9f1c9cbd60`
- Content SHA-256: `4b87ea1843bef321b6a42f939ca65576e5f65e9b3b890f7ac51944faa53eb89e`
- Bytes: 13606
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 19 -- 19_SYSTEM_DOPE_MEMORY.md

- Selected source path: `docs/03-reference/systems/dope-memory/system-dopememory.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `73697f998853fa9c23f140d5e5bf4a95d88c05d5`
- Content SHA-256: `8e26fd3b4234ed9f706d6c3b19f6ba9df7d8262dab41d7d35d91875b8243fcaf`
- Bytes: 12716
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 20 -- 20_SYSTEM_DOPE_CONTEXT.md

- Selected source path: `docs/03-reference/systems/dope-context/system-dopecontext.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `475ecbd329eaca81d88b105a07716d03289f0caf`
- Content SHA-256: `424ebf49db05454d2463be7e9e3d7d8e19a23460b4fb72cc448053f6d397415a`
- Bytes: 12335
- Rationale: Sole tracked candidate. Note: open PR #1126 (dope-context Voyage/vector repair) touches an adjacent doc (vector-profiles-and-migration.md) and heavy runtime code without directly editing this file; classified SOURCE_CONTENT_REFRESH_IF_MERGED in the open-PR ledger.
- Rejected candidates: none (single tracked candidate)

## Slot 21 -- 21_SYSTEM_DOPECON_BRIDGE.md

- Selected source path: `docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `cf40bb836bdac80a94ed7d978b6f7e4d2ad1396a`
- Content SHA-256: `8d744c5d074bfd97b34982a8ce84ae32b674fb5a8a1862273f6924671b6ece1f`
- Bytes: 10913
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 22 -- 22_SYSTEM_ADHD_ENGINE.md

- Selected source path: `docs/03-reference/systems/adhd-engine/system-adhdengine.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `5f696339e761c2c7ff3d88fb42d920b8973783c7`
- Content SHA-256: `551ed37400ae4737e557b0809d157218f425e108c33845921b87c6f8941967b1`
- Bytes: 20547
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 23 -- 23_SYSTEM_REPO_TRUTH_EXTRACTOR.md

- Selected source path: `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
- Authority class: system_reference
- Freshness class: SYSTEM_SNAPSHOT_30_DAYS
- Source blob SHA: `d5c672746b8f001a4a1b921e608605bb2945bd82`
- Content SHA-256: `532f5d67fe9b0f40e76641715a00c4e3e8588f3c201c0c7a5073c7d5e9ead50c`
- Bytes: 11755
- Rationale: Sole tracked candidate. Note: open PR #1136 directly touches this file; classified SOURCE_CONTENT_REFRESH_IF_MERGED in the open-PR ledger.
- Rejected candidates: none (single tracked candidate)

## Slot 24 -- 24_PAL_EXECUTION_RULES.md

- Selected source path: `docs/03-reference/execution/pal-execution-rules.md`
- Authority class: execution_contract
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `69e747e235987d7f00b232eb4fc8a4c9b668b26e`
- Content SHA-256: `bb654339ab1cf200e114cb2fddc03099b5345874894a2cc2883369256bf30c57`
- Bytes: 4166
- Rationale: Root PAL_EXECUTION_RULES.md absent at EXECUTION_BASE_SHA; tracked docs/03-reference/execution path is the sole remaining candidate and is the compressed operational PAL rules the packet asks for.
- Rejected candidates:
    - `PAL_EXECUTION_RULES.md` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent

## Slot 25 -- 25_TASK_PACKET_SCHEMA.json

- Selected source path: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- Authority class: schema
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `a4620a828b55769a96c9287673ee2a652215bd7a`
- Content SHA-256: `62abd93a27b7307e5b78aa8a46d967937e257817e41822f2edfc73162d4535ed`
- Bytes: 5342
- Rationale: Root dopetask-canonical-spec.json and dopetask-cannonical-spec.json (misspelled variant) are both absent at EXECUTION_BASE_SHA; the tracked docs/03-reference/spec/dopetask path is the sole remaining candidate and is the canonical schema referenced by CLAUDE.md validation commands.
- Rejected candidates:
    - `dopetask-canonical-spec.json` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent
    - `dopetask-cannonical-spec.json` -- BLOCKED_SOURCE_MISSING: git cat-file -e confirms absent (also a known misspelling variant)

## Slot 26 -- 26_TASK_PACKET_TEMPLATE.md

- Selected source path: `task-packets/TEMPLATE_TASK_PACKET.md`
- Authority class: authoring_template
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `9e0aac4cbc4272ee22de284c833cf009608ffd01`
- Content SHA-256: `804e60ded097aa086a86e2f132f5064f8810591f0e31b10c4a0ca65673cb3cd6`
- Bytes: 8063
- Rationale: Sole canonical authoring template for contributors. Other TEMPLATE_TASK_PACKET.md copies under src/dopemux/templates/init/** are installer-scaffolding copies for newly initialized repos, not the authoring template for this repo's own packet authors; docs/03-reference/fast-dev-os/task-packet-template.json is a JSON structural template distinct from the canonical spec already selected in slot 25. No PAL_PACKET_TEMPLATE.md exists in the current tree.
- Rejected candidates:
    - `src/dopemux/templates/init/docs/task-packets/TEMPLATE_TASK_PACKET.md` -- TOOL_SPECIFIC_OUT_OF_SCOPE: Installer scaffolding copy shipped to newly-initialized repos, not this repo's own authoring template.
    - `src/dopemux/templates/init/task-packets/TEMPLATE_TASK_PACKET.md` -- DUPLICATE: Second installer scaffolding copy, duplicate of the above.
    - `docs/03-reference/fast-dev-os/task-packet-template.json` -- WRONG_IDENTITY: JSON structural template distinct in scope/format from the canonical authoring template requested by slot 26.

## Slot 27 -- 27_PROOF_CONTRACT.md

- Selected source path: `docs/03-reference/governance/proof-contract.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `bf621ad1dd5bc68f6e960a9b95bb27014b72ad58`
- Content SHA-256: `37a2535b6b93082d86c834da41bf862ac1fbcfd6de9baa1e36a7f4dd7f4c9b7e`
- Bytes: 6581
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 28 -- 28_PROOF_BUNDLE_SCHEMA.md

- Selected source path: `docs/03-reference/governance/proof-bundle-schema.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `b11db11ef3fd80b34b0c6f2c479904091610e596`
- Content SHA-256: `49692d5ddd370987593d9a0a7c1dfa1d8721a18b95fc6b27a7f99d370601297f`
- Bytes: 5773
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 29 -- 29_HANDOFF_CONTRACT.md

- Selected source path: `docs/03-reference/governance/handoff-contract.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `20fe4682acc669098140ef57bdb86e50b8dcfe10`
- Content SHA-256: `a1364337fa9df08757faeab3d1c3d3c34a08350e2ec26142defb2159707ac81f`
- Bytes: 6802
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 30 -- 30_EMBEDDED_AUDIT.md

- Selected source path: `docs/ops/embedded-audit.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `4547e40a6a7a76012f8b3086139cbad2de45773d`
- Content SHA-256: `c5d9fd91fdd9d80a767a05afe14f6226b6b3db716d93dca6e3319b866903d8d2`
- Bytes: 15570
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 31 -- 31_EMBEDDED_AUDIT_SCHEMA.json

- Selected source path: `schemas/proof/embedded_audit.schema.json`
- Authority class: schema
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `578d60d2defab5a49a8f8b0d28e1fc118d9b53f9`
- Content SHA-256: `a6610b227246f6843ebaef8e8624806ec536d783ccbf12dc632939a8c97a61bf`
- Bytes: 6219
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 32 -- 32_PR_STEWARD.md

- Selected source path: `docs/ops/pr-steward.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `00b009bf4d2caade841e6347596f553cbd829c4b`
- Content SHA-256: `e33b1600706c6c3c3154886e465bbb44e3c9278c3984c37ec65c90d4729901fc`
- Bytes: 6908
- Rationale: Sole tracked candidate. Confirmed the doc does not describe solo-owner/org-member authorization mechanics, so open PR #1140 (which changes exactly that mechanic) does not make this file's content stale; classified NO_PROJECT_SOURCE_IMPACT in the open-PR ledger.
- Rejected candidates: none (single tracked candidate)

## Slot 33 -- 33_MERGE_READINESS_SCHEMA.json

- Selected source path: `schemas/pr_steward/merge_readiness.schema.json`
- Authority class: schema
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `1d34587eda4085ef8b1ddfe33ae51ff9350a8c94`
- Content SHA-256: `fd58f33cb7793325339ec5376e304425700c986962b1485d29c41874bccba061`
- Bytes: 7800
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

## Slot 34 -- 34_MODEL_ROUTING_POLICY.yaml

- Selected source path: `config/ai/model-routing.policy.yaml`
- Authority class: advisory_governance
- Freshness class: VOLATILE_14_DAYS
- Source blob SHA: `a6be914a913a7ae270ada7f09a32258893c9ffe5`
- Content SHA-256: `184509b1a92529c73dec7add73bd3eff405c0982d74ba06c80b7d5256d362e26`
- Bytes: 14781
- Rationale: Sole tracked candidate. File's own header states STATUS: proposed governance policy and AUTHORITY: advisory_until_runtime_wiring_verified; this status is preserved verbatim and must not be upgraded to runtime authority in any generated description.
- Rejected candidates: none (single tracked candidate)

## Slot 35 -- 35_DOPETASK_ADAPTER_CONTRACT.md

- Selected source path: `docs/02-how-to/integrations/dopetask/adapter-contract.md`
- Authority class: integration_contract
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `67a1763d2911bbdb197c47b43c83eb22b37e017e`
- Content SHA-256: `5b2e5158e48f4a71112190fd331f4e7b1cca39e65392681a2ce30bf388f7d465`
- Bytes: 3391
- Rationale: Byte-identical copies exist at docs/02-how-to/integrations/dopetask/adapter-contract.md and docs/integrations/dopetask/adapter-contract.md (same git blob SHA). doc-trust-map.md explicitly cites the docs/02-how-to path family as the reference location for this contract documentation ('Contract and proof documentation' row cites docs/02-how-to/integrations/dopetask/adapter-schema.md), so the docs/02-how-to path is treated as canonical for the sibling contract file too.
- Rejected candidates:
    - `docs/integrations/dopetask/adapter-contract.md` -- DUPLICATE: Identical blob SHA to the selected docs/02-how-to path; doc-trust-map.md does not cite this path.

## Slot 36 -- 36_DOPETASK_ADAPTER_SCHEMA.md

- Selected source path: `docs/02-how-to/integrations/dopetask/adapter-schema.md`
- Authority class: integration_contract
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `ce9e878c903cf8a969e3ecdf23922b3cb6a0eab8`
- Content SHA-256: `c11e8bc334bb203bfaebbe6573bf8bbc694d11d633fdb7d8718f74e7ce4626cc`
- Bytes: 4971
- Rationale: Byte-identical copies exist at docs/02-how-to/integrations/dopetask/adapter-schema.md and docs/integrations/dopetask/adapter-schema.md (same git blob SHA). doc-trust-map.md explicitly cites the docs/02-how-to path as the reference location for this exact file.
- Rejected candidates:
    - `docs/integrations/dopetask/adapter-schema.md` -- DUPLICATE: Identical blob SHA to the selected docs/02-how-to path; doc-trust-map.md cites only the docs/02-how-to path.

## Slot 37 -- 37_GOVERNANCE_MODEL.md

- Selected source path: `docs/03-reference/governance/governance-model.md`
- Authority class: governance
- Freshness class: STABLE_CONTRACT_90_DAYS
- Source blob SHA: `61b12bd8a5bd03acfef2ef743d1dcbf7507c5020`
- Content SHA-256: `7f680e987e77dc2a08c5f78d84ef9bbc172b05afea0e9b5adf04d5658b46a49a`
- Bytes: 3309
- Rationale: Sole tracked candidate.
- Rejected candidates: none (single tracked candidate)

