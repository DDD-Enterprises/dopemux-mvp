---
id: RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001
title: RTE UX CLI Tone Emoji Cleanup 001
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-18'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Contain RTE/operator CLI voice on safety-sensitive surfaces without removing Dopemux personality globally.
---
# RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001

This task packet uses a Markdown transport because the requested artifact path is
`.md`. The fenced JSON payload below is the canonical schema payload for
validation against
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

```json
{
  "id": "RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001",
  "project": "dopemux-mvp",
  "target": "Contain RTE/operator CLI voice so safety-sensitive, failure, refusal, proof, live/provider, auth, and UNKNOWN-handling output is terse and procedural while preserving restrained Dopemux personality where clarity is not harmed.",
  "invariants": [
    "Copy-only CLI packet.",
    "Voice containment, not global voice sterilization.",
    "Dopemux personality may remain in low-risk surfaces where clarity is not harmed.",
    "Safety gates, live execution boundaries, provider/auth failures, preflight blockers, refusal paths, proof/audit output, and UNKNOWN-handling output must be terse, procedural, and unambiguous.",
    "Do not remove all emoji by default.",
    "Do not sanitize unrelated commands.",
    "Do not edit AGENTS.md.",
    "Do not edit .claude/PROJECT_INSTRUCTIONS.md.",
    "Do not edit .claude/brand-voice-guidelines.md.",
    "Do not edit docs/03-reference/**.",
    "Do not edit docs/02-how-to/**.",
    "Do not edit services/**.",
    "Do not edit promptsets/**.",
    "Do not edit schemas/**.",
    "Do not change provider clients, routing, pricing, live extraction scripts, pre-live validator logic, command dispatch, Click options, command names, arguments, exit behavior, validation behavior, or runner calls.",
    "Do not reorganize dopemux rte run --help or implement progressive disclosure.",
    "Do not change DPMX_LIVE_OK behavior.",
    "Do not start follow-on RTE UX packets.",
    "Runtime/source truth governs behavior claims.",
    "Missing source, missing artifacts, missing provider evidence, and absent audit bundles remain UNKNOWN.",
    "CRIT-1 remains valuation-derived unless the missing Opus audit bundle exists locally.",
    "No provider calls.",
    "No live extraction.",
    "No live preflight or network/provider validation.",
    "Primary checkout must not be modified beyond the required fetch/read gate."
  ],
  "depends_on": [
    "RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001",
    "RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001",
    "RTE-UX-VAL-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "https://github.com/DDD-Enterprises/dopemux-mvp.git",
    "require_identity_match": true
  },
  "series": {
    "id": "RTE-UX-CLI-TONE-EMOJI-CLEANUP",
    "base_branch": "origin/main",
    "parent_tp_id": "RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/rte-cli-tone-emoji-cleanup-after-pr644",
    "base_branch": "origin/main"
  },
  "commit": {
    "message": "RTE UX CLI tone emoji cleanup",
    "allowlist": [
      "src/dopemux/cli.py",
      "src/dopemux/commands/extractor_commands.py",
      "tests/unit/test_cli_upgrades_commands.py",
      "tests/unit/test_cli_repscan_passthrough.py",
      "tests/unit/test_extractor_command_authority.py",
      "task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md",
      "out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md",
      "proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json"
    ],
    "verify": [
      "python -m json.tool proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json",
      "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
      "git diff --check",
      "git status --short",
      "git diff --name-only",
      "git diff --name-only | rg '^services/' && exit 1 || true",
      "git diff --name-only | rg '^(promptsets/|schemas/|services/repo-truth-extractor/promptsets/)' && exit 1 || true",
      "git diff --name-only | rg '(^|/)(routing|pricing|provider).*\\.(py|yaml|yml|json)$|src/dopemux/(routing_config|litellm_proxy|profile_models|claude_config)\\.py' && exit 1 || true",
      "git -C /Users/hue/code/dopemux-mvp status --short --branch",
      "python -m compileall -q src tests",
      "pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py",
      "pre-commit run --files src/dopemux/cli.py src/dopemux/commands/extractor_commands.py tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json"
    ]
  },
  "pr": {
    "title": "RTE UX CLI tone emoji cleanup",
    "body": "## Summary\n- contain RTE/operator CLI voice on safety-sensitive, failure, refusal, live/provider, auth, and UNKNOWN-handling surfaces\n- preserve command behavior, dispatch, options, validation behavior, live gates, provider behavior, pricing, routing, schemas, and promptsets\n- create packet, audit note, proof, and before/after operator-string inventory\n\n## Scope\n- copy-only CLI/operator text and exact expected test text where required\n- no runtime, provider, promptset, schema, routing, pricing, validator, DPMX_LIVE_OK, or progressive-disclosure changes\n\n## Validation\n- proof JSON syntax\n- embedded task-packet schema validation\n- focused CLI tests for touched command surfaces\n- compileall\n- diff/scope guards\n- pre-commit on touched files when safe",
    "base": "main"
  },
  "pal_chain": {
    "enabled": false,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "challenge",
      "implement",
      "codereview",
      "precommit",
      "challenge"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Run the PR #644 merge gate and create the dedicated origin/main worktree only if all gate checks pass.",
      "requirements": [
        "Fetch origin/main from the primary checkout without resolving, resetting, stashing, cleaning, rebasing, pulling, staging, or otherwise mutating dirty local work.",
        "Verify PR #644 is merged, non-draft, merged into main, and has a merge commit.",
        "Verify origin/main contains the PR #644 merge commit.",
        "Verify packet 2 cleanup artifacts and earlier authority-order gate artifacts exist on origin/main.",
        "Verify the requested fresh worktree path and branch are clear before creating them.",
        "Create the worktree from origin/main and verify it is not the primary checkout."
      ],
      "commands": [
        "git fetch origin main",
        "gh pr view 644 --json state,isDraft,mergedAt,mergeCommit,baseRefName,headRefName,headRefOid,url",
        "git merge-base --is-ancestor \"$PR_644_MERGE_COMMIT\" origin/main",
        "git cat-file -e origin/main:proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json",
        "git cat-file -e origin/main:out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md",
        "git cat-file -e origin/main:task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md",
        "git cat-file -e origin/main:proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
        "git cat-file -e origin/main:out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md",
        "git ls-tree -d origin/main:out/rte-ux-valuation-opus-audit",
        "git worktree add -b codex/rte-cli-tone-emoji-cleanup-after-pr644 /Users/hue/code/dopemux-mvp-rte-cli-tone-emoji-cleanup-after-pr644 origin/main"
      ],
      "expected_files": [
        "task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md"
      ],
      "validation": [
        "Gate facts are recorded in the audit note and proof.",
        "Primary checkout is not modified.",
        "Worktree is clean and not the primary checkout."
      ],
      "context_files": [
        "proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
        "proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json",
        "out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md",
        "out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md"
      ]
    },
    {
      "id": "S2",
      "task": "Inspect valuation, authority, prior packets, and runtime CLI source before editing.",
      "requirements": [
        "Confirm all seven RTE-UX-VAL-001 valuation artifacts are present.",
        "Confirm whether out/rte-opus-uiux-claude-design-audit/ exists.",
        "If the Opus bundle is missing, mark exact finding-ledger recovery as UNKNOWN.",
        "Inspect packet 1, packet 2, and packet 2 cleanup artifacts.",
        "Inspect RTE/operator CLI surfaces and exact-text tests.",
        "Confirm no follow-on packet files already exist for packet 3 in the fresh worktree."
      ],
      "commands": [
        "find out/rte-ux-valuation-opus-audit -maxdepth 1 -type f -name 'RTE-UX-VAL-001_*' | sort",
        "test -d out/rte-opus-uiux-claude-design-audit",
        "rg -n \"R-OPUS-1|R-OPUS-4|CRIT-1|UNKNOWN|valuation-derived|dopemux rte|dopemux truth|dopemux extractor|DPMX_LIVE_OK|provider|preflight|validate-live\" AGENTS.md .claude/PROJECT_INSTRUCTIONS.md .claude/brand-voice-guidelines.md docs/03-reference/governance/rules.md docs/03-reference/truth docs/03-reference/systems out/rte-ux-valuation-opus-audit proof/rte-ux out src/dopemux/cli.py src/dopemux/commands/extractor_commands.py tests/unit"
      ],
      "expected_files": [
        "src/dopemux/cli.py"
      ],
      "validation": [
        "Authority files read are listed in proof.",
        "Runtime/operator files inspected are listed in proof.",
        "Source audit bundle presence is recorded.",
        "Follow-on packet work is not present before implementation."
      ],
      "context_files": [
        "AGENTS.md",
        ".claude/PROJECT_INSTRUCTIONS.md",
        ".claude/brand-voice-guidelines.md",
        "docs/03-reference/governance/rules.md",
        "docs/03-reference/truth/truth-canonicals.md",
        "docs/03-reference/truth/truth-scope.md",
        "docs/03-reference/systems/system-boundaries.md",
        "docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_MANIFEST.json",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_PACKET_SEQUENCE.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_ACCEPTED_SCOPE.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_VALUATION_MATRIX.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_REMAINING_UNKNOWNS.md",
        "proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
        "proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json",
        "out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md",
        "out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md",
        "src/dopemux/cli.py",
        "src/dopemux/commands/extractor_commands.py",
        "tests/unit/test_cli_upgrades_commands.py",
        "tests/unit/test_cli_repscan_passthrough.py",
        "tests/unit/test_extractor_command_authority.py"
      ]
    },
    {
      "id": "S3",
      "task": "Apply minimal copy-only RTE/operator CLI changes and text-only test updates.",
      "requirements": [
        "Replace only confusing, ritualized, over-ornamented, or safety-hostile operator copy in scoped RTE/truth/upgrades/extractor surfaces.",
        "Avoid jokes, metaphor, ornament, or emoji only in safety-critical, failure, refusal, proof, live/provider, auth, and UNKNOWN-handling output.",
        "Preserve restrained Dopemux personality in low-risk operator copy where clarity is not harmed.",
        "Do not change Click option definitions beyond help text strings.",
        "Do not change command names, arguments, subprocess calls, exception classes, return paths, exit codes, validation logic, or live gate semantics.",
        "Update tests only where exact expected CLI text changes require it."
      ],
      "commands": [
        "git diff -- src/dopemux/cli.py src/dopemux/commands/extractor_commands.py tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py"
      ],
      "expected_files": [
        "src/dopemux/cli.py"
      ],
      "validation": [
        "Diff is copy-only or test-expectation-only.",
        "No runtime dispatch, provider, routing, pricing, validator, schema, promptset, or live gate behavior changes are present.",
        "Before/after changed-string inventory is recorded in the audit note."
      ],
      "context_files": [
        "src/dopemux/cli.py",
        "src/dopemux/commands/extractor_commands.py",
        "tests/unit/test_cli_upgrades_commands.py",
        "tests/unit/test_cli_repscan_passthrough.py",
        "tests/unit/test_extractor_command_authority.py"
      ]
    },
    {
      "id": "S4",
      "task": "Create audit note and proof for the copy-only packet.",
      "requirements": [
        "Audit note records what changed, what did not change, authority read, operator surfaces inspected, changed-string before/after inventory, behavior-preservation attestation, unknowns preserved, no-provider/no-live-extraction attestation, validation results, origin/main base confirmation, primary checkout preservation, and PR #644 merge gate evidence.",
        "Proof JSON includes all requested gate, source-bundle, scope, validation, unknown, no-runtime-change, commit-plan, and rollback-plan fields.",
        "Proof file notes final commit SHA is reported in closeout because the proof file is committed inside the final commit."
      ],
      "commands": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json"
      ],
      "expected_files": [
        "out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md",
        "proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json"
      ],
      "validation": [
        "Proof JSON parses.",
        "Audit note contains the required before/after table.",
        "UNKNOWNs and no-provider/no-live attestations are explicit."
      ]
    },
    {
      "id": "S5",
      "task": "Run focused validation, scope guards, precommit, and commit only scoped files.",
      "requirements": [
        "Run narrow-first validation and compileall.",
        "Run focused CLI tests for touched command surfaces.",
        "Run diff and forbidden-scope guards.",
        "Run pre-commit on touched files if configured and safe.",
        "Inspect status and diff before staging.",
        "Commit only scoped files with message: RTE UX CLI tone emoji cleanup.",
        "Do not push or open a PR."
      ],
      "commands": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json",
        "python - <<'PY' ... task packet payload schema validation ... PY",
        "git diff --check",
        "pytest -q tests/unit/test_cli_upgrades_commands.py tests/unit/test_cli_repscan_passthrough.py tests/unit/test_extractor_command_authority.py",
        "python -m compileall -q src tests",
        "pre-commit run --files <touched files>",
        "git status --short",
        "git diff --name-only",
        "git commit -m \"RTE UX CLI tone emoji cleanup\""
      ],
      "expected_files": [
        "src/dopemux/cli.py",
        "task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md",
        "out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md",
        "proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json"
      ],
      "validation": [
        "Validation results are recorded in proof and closeout.",
        "Forbidden paths touched is empty.",
        "Primary checkout status is reported and unchanged by this packet.",
        "Commit SHA is reported in closeout.",
        "PR remains not opened unless explicitly requested."
      ]
    }
  ]
}
```

## Objective

Contain RTE/operator CLI voice where it can obscure high-stakes instructions:
command replacement guidance, safety gates, live/provider boundaries, auth or
preflight failures, refusal messages, proof/audit claims, UNKNOWN handling, and
runtime/source authority rules.

This is not a global Dopemux personality removal packet. Copy-only CLI changes
are allowed. Runtime behavior changes are forbidden.

## Authority Order

1. Latest user instruction, including the voice policy amendment.
2. This task packet for scoped execution and allowlists.
3. `AGENTS.md` and merged RTE safety invariants.
4. Runtime code, config, tests, and active entrypoints.
5. Merged authority-order and Claude/RTE safety packets.
6. Valuation artifacts as advisory sequencing evidence only.
7. Docs/comments where not contradicted by runtime/source truth.

Missing source audit bundle evidence remains `UNKNOWN`. `CRIT-1` remains
valuation-derived unless the Opus audit bundle exists locally.

## Voice Zones

GREEN ZONE: branding, non-critical status, friendly summaries, local dev flavor,
human docs, and low-risk success messages may keep Dopemux voice, including
tasteful emoji and irreverent flavor where appropriate.

YELLOW ZONE: normal operator CLI messages may keep light personality if the
instruction remains clear, short, and unambiguous. Emoji should be sparse and
functional, not ornamental spam.

RED ZONE: safety gates, live execution boundaries, provider/auth failures,
preflight blockers, refusal paths, proof/audit output, and anything involving
UNKNOWN evidence must be terse, procedural, and unambiguous. No jokes, no chaos
voice, no decorative emoji, no ritual phrasing.

## Allowlist

- `src/dopemux/cli.py`
- `src/dopemux/commands/extractor_commands.py` only if runtime evidence shows
  operator-facing RTE/extractor copy requires cleanup
- `tests/unit/test_cli_upgrades_commands.py` only for exact expected output
- `tests/unit/test_cli_repscan_passthrough.py` only for exact expected output
- `tests/unit/test_extractor_command_authority.py` only for exact expected output
- `task-packets/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001.md`
- `out/rte-ux-cli-tone-emoji-cleanup/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001_AUDIT_NOTE.md`
- `proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json`

## Forbidden Files And Directories

- `AGENTS.md`
- `.claude/PROJECT_INSTRUCTIONS.md`
- `.claude/brand-voice-guidelines.md`
- `docs/03-reference/**`
- `docs/02-how-to/**`
- `README*`
- `services/**`
- `promptsets/**`
- `schemas/**`
- routing, pricing, provider config, provider clients
- live-extraction behavior
- pre-live validator logic
- help progressive-disclosure implementation
- unrelated dirty files
- follow-on packet artifacts

## Implementation Steps

1. Complete PR #644 gate and worktree setup from `origin/main`.
2. Inspect required authority, prior packet, valuation, runtime/operator, and test
   surfaces before editing.
3. Replace only confusing or safety-hostile RTE/operator copy.
4. Update exact-text tests only where necessary.
5. Create audit note and proof.
6. Run required validations and scope guards.
7. Commit scoped files only; do not push or open a PR.

## Validation Plan

- Parse proof JSON.
- Validate embedded task-packet JSON against the canonical dopetask schema.
- Run `git diff --check`.
- Run focused CLI tests for touched command surfaces.
- Run `python -m compileall -q src tests`.
- Run forbidden-scope guards for `services/**`, promptsets/schemas, and
  routing/pricing/provider config.
- Verify primary checkout status was not modified by this packet.
- Run `pre-commit run --files <touched files>` if configured and safe.

## Proof Plan

Create `proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json` with
gate evidence, source-bundle status, read authorities, inspected operator files,
changed strings, no-runtime-change attestations, validation results, commit plan,
rollback plan, and final-commit capture note.

## Commit Plan

Commit only scoped files with:

```text
RTE UX CLI tone emoji cleanup
```

Do not push. Do not open a PR unless explicitly requested after local commit
closeout.

## Rollback Plan

Before commit: revert only this packet's scoped files in the dedicated worktree.

After commit: use `git revert <commit-sha>` on
`codex/rte-cli-tone-emoji-cleanup-after-pr644`. Do not touch the dirty primary
checkout.
