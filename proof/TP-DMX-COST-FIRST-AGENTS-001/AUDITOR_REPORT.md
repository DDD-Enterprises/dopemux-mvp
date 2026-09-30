# Independent auditor report

Packet: `TP-DMX-COST-FIRST-AGENTS-001`
Audited content head: `7763bfdb47456b78216d71109412bf7e7f791ab9`
Actual auditor: `claude-sonnet-5-5`; canonical schema alias: `sonnet`.
Verdict: **PASS_WITH_RISKS**
One independent CLI attempt; exit code 0; tools/MCP/session persistence disabled.

## Auditor rationale

The diff implements its stated goal. Codex roles and defaults are pinned, the YAML matches the TOML and the front matter, the formal-audit exclusion for Codex is kept and tested, and evidence-economy budgets are preserved. The trusted validation receipt shows focused tests, the change contract, diff check, and precommit all passing with exit code 0. Runtime identity and availability were not exercised, the new non-dmx Codex roles lack an enforced read-only sandbox, and the optionalization of PAL review steps is a real policy relaxation. These justify PASS_WITH_RISKS rather than an unqualified PASS. Nothing rises to FAIL. No candidate content attempted to redirect the audit.

## Auditor findings

1. Scope matches the packet allowlist. All 25 changed files are listed in commit.allowlist in task-packets/generated/TP-DMX-COST-FIRST-AGENTS-001.json. The diff contains no changes to schemas, runtime code, or secrets.
2. Codex role pinning is explicit and consistent. Every .codex/agents/*.toml sets model and model_reasoning_effort, and none inherits the supervisor or uses an 'astra' model. .codex/config.toml adds default_subagent_model=gpt-6-luna and default_subagent_reasoning_effort=medium. The role_models map in config/ai/model-routing.policy.yaml matches the TOML pins. tests/test_model_routing_policy.py asserts this match for both the Codex and Claude providers.
3. Formal-audit boundary is preserved. provider_routes.codex.self_audit is FORBIDDEN_FORMAL_AUDITOR, and dmx-reviewer.toml adds 'never the formal embedded auditor'. A test asserts both. The docs and AGENTS.md §5 repeat that Codex review is advisory only. The Claude self_audit alias 'sonnet' is tested for membership in the embedded_audit schema auditor_model enum. The schema file itself was not in the diff, so I could not inspect it.
4. Read-only roles keep their safety boundaries. dmx-explorer and dmx-housekeeper keep sandbox_mode=read-only. dmx-reviewer is unchanged apart from the model bump and the advisory wording. The new architect and project-manager TOMLs state read-only in their instructions but set no sandbox_mode. See risk 2.
5. Preserved gates: explicit user and packet restrictions take precedence. There is no hidden fallback or upgrade, and escalation returns to the supervisor with a recorded reason. Evidence-economy budgets are L0=0, L1<=1, and L2/L3=1 implementer + 1 final audit. The last is asserted by test_cost_first_policy_preserves_evidence_economy_budget.
6. The audit-model choice departs from the old docs. The example proof changes auditor_model from claude-opus-4 to the alias 'sonnet'. The docs say the alias is kept separate from actual-ID evidence, and the actual model ID must still be recorded in real proof bundles.
7. proof/TP-DMX-COST-FIRST-AGENTS-001/LOCAL_SETTINGS_PLAN.json is a machine-local plan. It names a global supervisor 'gpt-6-astra' low and ~/.codex role files. It is a plan only; nothing in the diff applies it. Its portability depends on the guarded apply step, which is outside this diff and was not audited.

## Auditor residual risks

1. Actual model identity and availability (gpt-6-luna, gpt-6.1-sol, claude-sonnet-5-5, claude-haiku-4-5, gemini-3.8-flash) are NOT_RUN. The diff declares them as configuration only, and the trusted context confirms no runtime evidence. Vendor selector syntax was checked in vendor docs per the trusted context, but I could not independently confirm it.
2. Two new Codex roles omit sandbox_mode: architect.toml and project-manager.toml, which are described as read-only. Their read-only status rests on instruction text rather than a sandbox. Unlike dmx-* roles, there is no enforced boundary, and developer.toml likewise inherits the default workspace-write sandbox. Recommend setting sandbox_mode='read-only' on architect and project-manager.
3. Claude agent front matter uses model: claude-sonnet-5-5 and claude-haiku-4-5. The Claude Code subagent docs were said to be checked, but the Haiku ID form (claude-haiku-4-5 vs. the dated 'claude-haiku-4-5-20251001') was not verified here. An unresolved ID could fail or fall back silently, which conflicts with the no-hidden-fallback stance.
4. The policy is advisory; nothing enforces pins. Declared pins can be overridden by explicit spawn selection, and the docs describe precedence inconsistently (AGENTS.md says role pins override explicit spawn selection). This was not verified against Codex runtime behavior.
5. Weakened mandatory review chain: PAL codereview, precommit, and challenge are now optional (config/instructions/pal-opencode-guide.md; .claude/modules/shared/governance-principles.md). Deterministic precommit and an L2/L3 final audit remain required. This is an intentional policy change, but it reduces the intermediate assurance layers and should be acknowledged by the supervisor.
6. GEMINI.md contains the sentence 'Sequence examples above are not merge/execution authorization'. I could not confirm that the examples it refers to exist in the file. This is a minor documentation risk.
7. Existing gpt-5.x to gpt-6.x model IDs are new strings that only vendor evidence can validate. The test asserts internal consistency but not that the model IDs exist.

## Audit limits

PASS for the trusted receipt checks (focused_tests, change_contract, diff_check, configured_precommit). NOT_RUN for runtime model identity and availability, and for the apply step of LOCAL_SETTINGS_PLAN.json. This audit did not run or check out candidate code.

The deterministic scanner reported no instruction-like content (detected=false, match_count=0). The diff does contain policy and governance prose addressed to agents, such as AGENTS.md text and developer_instructions. I treated all of it as data under review and was not directed by it.

## Supervisor evidence and disposition

These clarifications are supervisor verification, not a replacement auditor verdict. The original result is preserved in review_bundle/CLAUDE_AUDIT_RESULT.json.

- **Read-only imported roles** — ACCEPTED_RISK. The four imported roles were existing untracked local settings. Their permissions and instruction bodies were preserved; architect/project-manager/researcher have instruction-only read-only restrictions. No sandbox enforcement or live launch is claimed.

- **Codex role precedence** — DOCUMENTATION_VERIFIED; runtime NOT_RUN. Official Codex subagent documentation states explicit spawn overrides defaults, but custom role TOML model/effort pins override per-spawn choices. This source resolves the auditor uncertainty; no live runtime precedence proof is claimed. Source: https://learn.chatgpt.com/docs/agent-configuration/subagents

- **Claude model IDs** — DOCUMENTATION_VERIFIED; role launch NOT_RUN. Official model catalog lists claude-sonnet-5-5 and claude-haiku-4-5. The audit itself returned canonical claude-sonnet-5-5. Haiku role launches remain NOT_RUN. Source: https://platform.claude.com/docs/en/models/overview

- **PAL intermediate chains** — CANONICAL_AUTHORITY_ALIGNMENT. Unchanged AGENTS.md section 5 already makes PAL optional and requires one final L2/L3 audit; evidence-economy.md already specifies lane budgets. Subsidiary mandatory intermediate rituals were aligned to that existing canonical rule. Deterministic precommit and final audit remain required.

- **GEMINI.md reference** — SOURCE_VERIFIED. The full GEMINI.md contains a Sequence section before the new delegation section.

- **Machine-local plan execution** — DEPLOYMENT_READBACK_PASS; helper not independently audited. All 41 planned file writes passed before-hash guards and byte readback. Independent readback verified all hashes, 16 global role pins, and eight repo role pins. Private backups and the apply helper are deliberately not published.
