---
id: RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001
title: Rte Ux Pkt Authority Order Reconciliation 001
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-16'
last_review: '2026-05-16'
next_review: '2026-08-14'
prelude: Reconcile authority order wording across checked-in authority docs for the first accepted RTE UX packet.
---
# RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001

This task packet uses a Markdown transport because the requested artifact path is `.md`.
The fenced JSON payload below is the canonical schema payload for validation against
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

```json
{
  "id": "RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001",
  "project": "dopemux-mvp",
  "target": "Reconcile authority and truth-order wording across checked-in authority docs so future RTE UX packets inherit one clear authority model.",
  "invariants": [
    "Reconcile wording only.",
    "Do not edit src/**.",
    "Do not edit services/**.",
    "Do not edit promptsets or schemas.",
    "Do not change routing, pricing, provider, or runtime dispatch behavior.",
    "Do not run provider calls.",
    "Do not run live extraction.",
    "Active task packets control scoped execution and allowlists only.",
    "Runtime code, config, tests, compose wiring, and active entrypoints govern behavior claims.",
    "Truth docs describe repo truth but do not outrank runtime behavior.",
    "Generated, advisory, extracted, exploratory, and external artifacts never outrank runtime/source truth.",
    "Preserve UNKNOWN where evidence is missing.",
    "Task packets do not authorize unsupported runtime claims."
  ],
  "depends_on": [
    "RTE-UX-VAL-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "https://github.com/DDD-Enterprises/dopemux-mvp.git",
    "require_identity_match": true
  },
  "series": {
    "id": "RTE-UX-AUTHORITY-ORDER-RECONCILIATION",
    "base_branch": "main",
    "parent_tp_id": "RTE-UX-VAL-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/rte-authority-order-reconciliation",
    "base_branch": "main"
  },
  "commit": {
    "message": "docs(rte): reconcile authority order wording",
    "allowlist": [
      "AGENTS.md",
      ".claude/PROJECT_INSTRUCTIONS.md",
      ".claude/brand-voice-guidelines.md",
      "docs/03-reference/governance/rules.md",
      "docs/03-reference/truth/truth-canonicals.md",
      "docs/03-reference/truth/truth-scope.md",
      "docs/03-reference/systems/system-boundaries.md",
      "docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md",
      "task-packets/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001.md",
      "out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md",
      "proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json"
    ],
    "verify": [
      "python -m json.tool proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
      "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
      "git diff --check",
      "pre-commit run --files AGENTS.md .claude/PROJECT_INSTRUCTIONS.md .claude/brand-voice-guidelines.md docs/03-reference/governance/rules.md docs/03-reference/truth/truth-canonicals.md docs/03-reference/truth/truth-scope.md docs/03-reference/systems/system-boundaries.md docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md task-packets/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001.md out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json"
    ]
  },
  "pr": {
    "title": "docs(rte): reconcile authority order wording",
    "body": "## Summary\n- reconcile authority/truth-order wording across checked-in authority docs\n- clarify that active task packets control scoped execution and allowlists, while runtime code/config/tests/active entrypoints govern behavior claims\n- preserve UNKNOWN around the missing Opus audit bundle and valuation-derived finding labels\n\n## Scope\n- docs, task packet, audit note, and proof only\n- no runtime, provider, promptset, schema, routing, or pricing changes\n\n## Validation\n- proof JSON syntax\n- task packet JSON payload schema validation\n- git diff whitespace check\n- pre-commit on touched files when safe",
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
      "task": "Preflight the repo, source bundles, and authority files before editing.",
      "requirements": [
        "Verify repo root, branch, HEAD, remote, and dirty status.",
        "Confirm whether out/rte-ux-valuation-opus-audit/ exists.",
        "Confirm whether out/rte-opus-uiux-claude-design-audit/ exists.",
        "If the Opus bundle is missing, mark exact finding-ledger recovery as UNKNOWN.",
        "Identify authority-order docs before edits."
      ],
      "commands": [
        "git rev-parse --show-toplevel",
        "git rev-parse --abbrev-ref HEAD",
        "git rev-parse HEAD",
        "git remote -v",
        "git status --short --branch",
        "test -d out/rte-ux-valuation-opus-audit",
        "test -d out/rte-opus-uiux-claude-design-audit"
      ],
      "expected_files": [
        "task-packets/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001.md"
      ],
      "validation": [
        "Preflight facts are recorded in the audit note and proof.",
        "Missing source audit bundle is recorded as UNKNOWN when absent.",
        "Authority files inspected are listed explicitly."
      ],
      "context_files": [
        "AGENTS.md",
        ".claude/PROJECT_INSTRUCTIONS.md",
        ".claude/brand-voice-guidelines.md",
        "docs/03-reference/governance/rules.md",
        "docs/03-reference/truth/truth-canonicals.md",
        "docs/03-reference/truth/truth-scope.md",
        "docs/03-reference/systems/system-boundaries.md",
        "docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md"
      ]
    },
    {
      "id": "S2",
      "task": "Reconcile only wording in checked-in authority docs.",
      "requirements": [
        "Make clear that active task packets control scoped execution and allowlists.",
        "Make clear that runtime code, config, tests, compose wiring, and active entrypoints govern behavior claims.",
        "Make clear that truth docs describe repo truth but do not outrank runtime behavior.",
        "Make clear that generated, advisory, extracted, exploratory, and external artifacts never outrank runtime/source truth.",
        "Preserve UNKNOWN where evidence is missing.",
        "Do not let task packets authorize unsupported runtime claims."
      ],
      "commands": [
        "rg -n \"Truth Hierarchy|Truth Order|Task Packet|runtime code|extracted artifacts|UNKNOWN\" AGENTS.md .claude/PROJECT_INSTRUCTIONS.md .claude/brand-voice-guidelines.md docs/03-reference/governance/rules.md docs/03-reference/truth/truth-canonicals.md docs/03-reference/truth/truth-scope.md docs/03-reference/systems/system-boundaries.md docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md"
      ],
      "expected_files": [
        "AGENTS.md",
        ".claude/PROJECT_INSTRUCTIONS.md",
        ".claude/brand-voice-guidelines.md",
        "docs/03-reference/governance/rules.md",
        "docs/03-reference/truth/truth-canonicals.md",
        "docs/03-reference/truth/truth-scope.md",
        "docs/03-reference/systems/system-boundaries.md",
        "docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md"
      ],
      "validation": [
        "Diff is limited to wording in allowlisted authority docs.",
        "No runtime, service, promptset, schema, routing, pricing, or provider files changed.",
        "UNKNOWN around the missing Opus source audit bundle is preserved."
      ],
      "context_files": [
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_MANIFEST.json",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_PACKET_SEQUENCE.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_ACCEPTED_SCOPE.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_VALUATION_MATRIX.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_REMAINING_UNKNOWNS.md",
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_NO_RUNTIME_CHANGE_ATTESTATION.md"
      ]
    },
    {
      "id": "S3",
      "task": "Write the audit note and proof bundle for this packet.",
      "requirements": [
        "Audit note records observed authority inputs, inferred reconciliation need, and unknowns.",
        "Proof JSON includes all fields requested by the implementation request.",
        "Proof records no runtime files changed, no provider calls run, and no live extraction run."
      ],
      "commands": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json"
      ],
      "expected_files": [
        "out/rte-ux-authority-order-reconciliation/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001_AUDIT_NOTE.md",
        "proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json"
      ],
      "validation": [
        "Proof JSON parses.",
        "Proof files_touched matches the actual diff scope.",
        "Audit note preserves observed, inferred, proposed, and unknown states separately."
      ],
      "context_files": [
        "out/rte-ux-valuation-opus-audit/RTE-UX-VAL-001_REMAINING_UNKNOWNS.md"
      ]
    },
    {
      "id": "S4",
      "task": "Run narrow validation, inspect diff scope, and prepare closeout.",
      "requirements": [
        "Validate proof JSON.",
        "Validate task packet schema payload when safe.",
        "Run git diff --check.",
        "Run pre-commit on touched files when configured and safe.",
        "Record validation outcomes honestly in proof and closeout."
      ],
      "commands": [
        "python -m json.tool proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json",
        "python - <<'PY'\nimport json, re\nfrom pathlib import Path\nfrom jsonschema import Draft7Validator\npacket = Path('task-packets/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001.md').read_text()\nmatch = re.search(r'```json\\n(.*?)\\n```', packet, re.S)\nassert match, 'missing fenced json payload'\npayload = json.loads(match.group(1))\nschema = json.loads(Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text())\nerrors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda e: list(e.path))\nif errors:\n    raise SystemExit('\\n'.join('%s: %s' % (('/'.join(map(str, e.path)) or '<root>'), e.message) for e in errors))\nprint('PASS task packet payload schema validation')\nPY",
        "git diff --check",
        "git status --short --branch"
      ],
      "expected_files": [
        "proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json"
      ],
      "validation": [
        "Validation command results are recorded with exit codes.",
        "Diff scope contains only allowlisted files.",
        "Commit and rollback plans are explicit."
      ],
      "context_files": [
        ".pre-commit-config.yaml",
        "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
      ]
    }
  ]
}
```
