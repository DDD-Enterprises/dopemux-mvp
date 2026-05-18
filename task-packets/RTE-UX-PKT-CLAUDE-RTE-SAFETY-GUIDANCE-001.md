---
id: RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001
title: RTE UX Claude RTE Safety Guidance 001
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Add narrow Claude and agent-facing RTE safety guidance without runtime changes.
---
# RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001

This task packet uses a Markdown transport because the requested artifact path is
`.md`. The fenced JSON payload below is the canonical schema payload for
validation against
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

```json
{
  "id": "RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001",
  "project": "dopemux-mvp",
  "target": "Update Claude and agent-facing guidance so Repo Truth Extractor safety invariants are explicit, actionable, and aligned with the merged authority-order reconciliation.",
  "invariants": [
    "Guidance-only packet.",
    "No runtime/provider/promptset/schema/routing/pricing behavior changes are allowed.",
    "Do not edit src/**.",
    "Do not edit services/**.",
    "Do not edit promptsets/**.",
    "Do not edit schemas/**.",
    "Do not change provider clients, routing, pricing, live extraction scripts, or runtime dispatch code.",
    "No provider calls.",
    "No live extraction.",
    "No live preflight or network/provider validation.",
    "Do not start CLI tone cleanup, validator error-shape cleanup, run-help progressive disclosure, accepted-later, or deferred work.",
    "Runtime/source truth governs behavior claims.",
    "Missing source, missing artifacts, missing provider evidence, and absent audit bundles remain UNKNOWN.",
    "Generated, advisory, extracted, valuation, Deep Research, and external artifacts do not prove runtime behavior.",
    "DPMX_LIVE_OK and pre-live validation remain live-execution boundaries.",
    "Proof and output must not include secrets, local credentials, raw tokens, or unredacted provider metadata.",
    "Repo Truth Extractor remains extraction/audit runtime only, not PM, memory, retrieval, provider, or replacement source truth authority."
  ],
  "depends_on": [
    "RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001",
    "RTE-UX-VAL-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "https://github.com/DDD-Enterprises/dopemux-mvp.git",
    "require_identity_match": true
  },
  "series": {
    "id": "RTE-UX-CLAUDE-RTE-SAFETY-GUIDANCE",
    "base_branch": "origin/main",
    "parent_tp_id": "RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/rte-claude-safety-guidance",
    "base_branch": "origin/main"
  },
  "commit": {
    "message": "RTE UX Claude safety guidance",
    "allowlist": [
      ".claude/PROJECT_INSTRUCTIONS.md",
      "AGENTS.md",
      "task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md",
      "out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md",
      "proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json"
    ],
    "verify": [
      "python -m json.tool proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json",
      "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
      "git diff --check",
      "git status --short",
      "git diff --name-only",
      "git status --porcelain --untracked-files=all | rg '^( M|A |AM|MM|\\?\\?) (src/|services/)' || true",
      "git status --porcelain --untracked-files=all | rg '^( M|A |AM|MM|\\?\\?) (promptsets/|schemas/|services/repo-truth-extractor/promptsets/)' || true",
      "pre-commit run --files .claude/PROJECT_INSTRUCTIONS.md AGENTS.md task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json"
    ]
  },
  "pr": {
    "title": "docs(rte): add Claude safety guidance",
    "body": "## Summary\n- add narrow RTE safety invariants to Claude and agent-facing guidance\n- preserve authority-order reconciliation: task packets scope work, runtime/source truth governs behavior claims\n- create packet, audit note, and proof for the guidance-only change\n\n## Scope\n- guidance, task packet, audit note, and proof only\n- no runtime, provider, promptset, schema, routing, pricing, or live-extraction behavior changes\n\n## Validation\n- proof JSON syntax\n- task packet JSON payload schema validation\n- git diff whitespace check\n- scope guards for forbidden paths\n- pre-commit on touched files when safe",
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
      "task": "Verify the origin/main merge gate and create the dedicated packet worktree.",
      "requirements": [
        "Fetch origin/main without mutating the dirty primary checkout.",
        "Verify PR #640 is merged into main at 3bdb146813ad34de44078d86900c3fdbb971ef25.",
        "Verify the required authority-order proof artifacts exist on origin/main.",
        "Create codex/rte-claude-safety-guidance from origin/main only after the gate passes.",
        "Verify the worktree root, branch, HEAD, remote, marker, and clean status."
      ],
      "commands": [
        "git fetch origin main",
        "git rev-parse origin/main",
        "gh pr view 640 --json state,mergedAt,mergeCommit,baseRefName,url",
        "git cat-file -e origin/main:proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
        "git cat-file -e origin/main:out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md",
        "git ls-tree -d origin/main:out/rte-ux-valuation-opus-audit",
        "git worktree add -b codex/rte-claude-safety-guidance /Users/hue/code/dopemux-mvp-rte-claude-safety-guidance origin/main"
      ],
      "expected_files": [
        "task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md"
      ],
      "validation": [
        "Gate facts are recorded in the audit note and proof.",
        "Primary checkout is not modified.",
        "Worktree is clean and not the primary checkout."
      ],
      "context_files": [
        "proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
        "out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md"
      ]
    },
    {
      "id": "S2",
      "task": "Inspect valuation, authority, and RTE runtime/source evidence before editing.",
      "requirements": [
        "Confirm the seven RTE-UX-VAL-001 valuation artifacts are present.",
        "Confirm whether out/rte-opus-uiux-claude-design-audit/ exists.",
        "If the Opus bundle is missing, mark exact finding-ledger recovery as UNKNOWN.",
        "Inspect merged authority-order reconciliation before editing.",
        "Inspect runtime/source files only for safety-invariant grounding."
      ],
      "commands": [
        "find out/rte-ux-valuation-opus-audit -maxdepth 1 -type f -print | sort",
        "test -d out/rte-opus-uiux-claude-design-audit",
        "rg -n \"R-OPUS-3|R-OPUS-14|CRIT-3|UNKNOWN|valuation-derived|DPMX_LIVE_OK|validate-live|provider|redact\" AGENTS.md .claude/PROJECT_INSTRUCTIONS.md docs/03-reference/governance/rules.md docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md out/rte-ux-valuation-opus-audit services/repo-truth-extractor src/dopemux/cli.py docs/02-how-to/extraction"
      ],
      "expected_files": [
        ".claude/PROJECT_INSTRUCTIONS.md",
        "AGENTS.md"
      ],
      "validation": [
        "Authority files read are listed in proof.",
        "Runtime files read-only are listed in proof.",
        "Source audit bundle presence is recorded."
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
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_DEFERRED_ITEMS.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_NO_RUNTIME_CHANGE_ATTESTATION.md",
        "src/dopemux/cli.py",
        "services/repo-truth-extractor/run_extraction_v5.py",
        "services/repo-truth-extractor/validate_pre_live_gate_v25.py",
        "services/repo-truth-extractor/llm_runtime.py",
        "services/repo-truth-extractor/output_safety.py",
        "services/repo-truth-extractor/README.md",
        "docs/02-how-to/extraction/repo-truth-extractor-user-guide.md",
        "docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md"
      ]
    },
    {
      "id": "S3",
      "task": "Add narrow RTE safety guidance where Claude and agents will read it.",
      "requirements": [
        "Add explicit MUST, MUST NOT, and UNKNOWN language.",
        "Cross-reference the merged authority-order rule instead of duplicating broad governance text.",
        "State that runtime/source truth governs behavior claims and Task Packets cannot authorize unsupported runtime claims.",
        "State that missing evidence remains UNKNOWN.",
        "State that generated and advisory artifacts are lower authority.",
        "State that provider calls, live extraction, live preflight, network/provider validation, and account-specific claims require explicit authorization and direct evidence.",
        "State that DPMX_LIVE_OK and pre-live validation are live-execution boundaries.",
        "State that secrets, local credentials, raw tokens, and unredacted provider metadata must not enter proof or output.",
        "State that RTE scope is extraction/audit only.",
        "Keep future packets separated."
      ],
      "commands": [
        "rg -n \"RTE Safety|Repo Truth Extractor|DPMX_LIVE_OK|UNKNOWN|provider calls|runtime/source truth\" .claude/PROJECT_INSTRUCTIONS.md AGENTS.md"
      ],
      "expected_files": [
        ".claude/PROJECT_INSTRUCTIONS.md",
        "AGENTS.md"
      ],
      "validation": [
        "Diff is limited to allowlisted guidance files.",
        "No runtime/provider/promptset/schema/routing/pricing files are touched.",
        "Guidance remains terse and procedural."
      ]
    },
    {
      "id": "S4",
      "task": "Create audit note and proof for the guidance-only packet.",
      "requirements": [
        "Audit note records what changed and what did not change.",
        "Audit note records authority read, runtime/source evidence used for guidance only, unknowns preserved, no-runtime-change attestation, and validation results.",
        "Proof JSON includes all requested packet, gate, scope, unknown, validation, commit, and rollback fields.",
        "Proof records provider_calls_run=false and live_extraction_run=false."
      ],
      "commands": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json"
      ],
      "expected_files": [
        "out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md",
        "proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json"
      ],
      "validation": [
        "Proof JSON parses.",
        "Proof files_touched matches actual diff scope.",
        "Forbidden paths list is empty."
      ]
    },
    {
      "id": "S5",
      "task": "Validate, inspect diff scope, and commit only scoped files.",
      "requirements": [
        "Run proof JSON validation.",
        "Validate the embedded Task Packet JSON payload against dopetask-canonical-spec.json.",
        "Run git diff --check.",
        "Run scope guards for src/**, services/**, promptsets/**, and schemas/**.",
        "Run pre-commit on touched files if configured and safe.",
        "Inspect git status, diff name-only, and staged files before commit.",
        "Commit only scoped files with the requested message.",
        "Do not push or open a PR."
      ],
      "commands": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json",
        "git diff --check",
        "git status --short",
        "git diff --name-only",
        "git add .claude/PROJECT_INSTRUCTIONS.md AGENTS.md task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md",
        "git add -f proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json",
        "git commit -m \"RTE UX Claude safety guidance\""
      ],
      "expected_files": [
        ".claude/PROJECT_INSTRUCTIONS.md",
        "AGENTS.md",
        "task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md",
        "out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md",
        "proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json"
      ],
      "validation": [
        "All validation outcomes are recorded with exit codes.",
        "No forbidden path changes are present.",
        "Commit contains only allowlisted files."
      ]
    }
  ]
}
```

## Objective

Add concise RTE safety guidance for Claude and agent-style repo work so agents
do not convert advisory RTE artifacts into unsupported runtime claims or bypass
live-execution boundaries.

## Authority Order

Use the merged authority-order reconciliation: active Task Packets control the
current execution slice, allowlist, validation obligations, and stop conditions;
runtime code, config, compose wiring, tests, and active entrypoints govern
behavior claims. Generated, advisory, extracted, valuation, Deep Research, and
external artifacts are lower authority unless runtime/source truth supports
them. Missing evidence remains `UNKNOWN`.

## Allowlist

- `.claude/PROJECT_INSTRUCTIONS.md`
- `AGENTS.md`
- `task-packets/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001.md`
- `out/rte-ux-claude-rte-safety-guidance/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001_AUDIT_NOTE.md`
- `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json`

## Forbidden Files And Directories

- `src/**`
- `services/**`
- `promptsets/**`
- `schemas/**`
- routing, pricing, provider config, provider clients, runtime dispatch code,
  live-extraction scripts, unrelated dirty files, and follow-on packet artifacts

## Validation Plan

Run proof JSON validation, embedded Task Packet JSON schema validation,
`git diff --check`, `git status --short`, `git diff --name-only`, forbidden-path
scope guards, follow-on packet grep guards, and pre-commit on touched files when
configured and safe.

## Proof Plan

Create `PROOF.json` with the PR #640 merge gate, origin/main base, worktree and
branch, source audit bundle presence, valuation and authority files read,
runtime files read-only, touched files, forbidden path attestations, unknowns,
validation commands, validation results, commit plan, and rollback plan.

## Commit Plan

Commit only allowlisted files with message:
`RTE UX Claude safety guidance`.

Do not push or open a PR unless explicitly requested after local commit closeout.

## Rollback Plan

Pre-commit local rollback (no longer reachable; packet is merged): would have
removed the newly created task packet, audit note, and proof file, then
restored guidance files from `HEAD` in the dedicated packet worktree.

Post-merge rollback (current state): PR #643 was squash-merged to main as
`0083f50a58ffa5e9d34eb3c9c620bf28076541e5`. From a fresh worktree off
`origin/main`, revert with `git revert
0083f50a58ffa5e9d34eb3c9c620bf28076541e5` and open a follow-up PR.

Do not mutate the dirty primary checkout at `/Users/hue/code/dopemux-mvp`.

## No Runtime Behavior Statement

This packet must not change runtime, provider, promptset, schema, routing,
pricing, live-extraction, dispatch, account, or validation behavior.
