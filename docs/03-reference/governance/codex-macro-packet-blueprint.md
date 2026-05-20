---
id: codex-macro-packet-blueprint
title: Codex Macro Packet Blueprint
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-20'
last_review: '2026-05-20'
next_review: '2026-08-18'
prelude: Reusable Codex macro-packet blueprint for schema-valid, proof-bound Dopemux packet work.
---
# Codex Macro Packet Blueprint

Use this blueprint for a bounded Codex macro-packet when one meaningful outcome can be completed in one branch, one allowlist, one validation set, and one proof trail. It does not replace `AGENTS.md`, runtime code, config, tests, compose wiring, active entrypoints, or `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.

## Authority Rule

The live dopeTask schema controls packet shape. Runtime code, config, tests, compose wiring, and active entrypoints control behavior claims. Docs can guide wording, but they cannot prove runtime behavior.

`execution.agent` currently supports only these schema enum values: `gemini`, `codex`, `vibe`, and `shell`. Do not add new execution agents in a packet unless the canonical schema is changed by a separately authorized schema packet.

## Macro-Packet Sizing Rules

- Use one macro-packet per meaningful outcome, not one packet per tiny cleanup step.
- Keep the packet commit-sized: the target, allowlist, validation commands, and PR summary must fit one reviewable branch.
- Include every file that may be edited in `commit.allowlist`; stop if the fix needs another file.
- Prefer same-packet evidence refresh when review finds proof, report, or PR-body gaps inside the same outcome.
- Split into a new packet only when the requested work changes the outcome, touches a new authority surface, adds runtime behavior, changes schema/contracts, or requires files outside the current allowlist.

## Acceptance Rules

- Validation-bound acceptance requires every declared validation either to pass with an exact exit code or to be labeled `NOT_RUN` or `BLOCKED` with a reason.
- Proof-bound acceptance requires exact command evidence, changed files, diff scope, codereview status, precommit status, commit SHA, PR URL or exact blocker, residual risks, `UNKNOWN`s, and cleanup status.
- `@codex review`, CI, and GitHub checks are review or delivery signals. They are not proof of correctness by themselves.
- Human acceptance remains separate from Codex proof and PR creation.

## Same-Packet Fix Rules

Use a same-packet fix when a review comment, validation failure, missing proof field, stale PR body, or template gap is inside the active packet target and `commit.allowlist`.

Same-packet fixes must:

- preserve the original failure or review finding in the proof trail;
- update the same proof artifact;
- rerun the smallest relevant validation first;
- rerun packet-required validation after the fix;
- run codereview before precommit;
- avoid introducing new files outside the allowlist.

Stop and request a new packet when a fix requires runtime/service validation, Docker startup, live provider calls, live extraction, account-specific checks, schema changes, dependency changes, or a broader authority claim not authorized by the packet.

## Schema-Aligned Packet Skeleton

```json
{
  "id": "TP-DMX-AREA-OUTCOME-001",
  "project": "dopemux-mvp",
  "target": "One verifiable outcome stated in operator language.",
  "invariants": [
    "Do not modify runtime code unless this packet explicitly authorizes it.",
    "Preserve UNKNOWN and CONFLICTING where repo evidence is unresolved."
  ],
  "depends_on": [],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "DDD-Enterprises/dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-SERIES-ID",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/dmx-area-outcome-001",
    "base_branch": "main"
  },
  "commit": {
    "message": "docs(scope): describe the outcome",
    "allowlist": [
      "docs/03-reference/governance/example.md",
      "task-packets/generated/TP-DMX-AREA-OUTCOME-001.json",
      "proof/example/TP-DMX-AREA-OUTCOME-001/PROOF.json"
    ],
    "verify": [
      "python -m json.tool task-packets/generated/TP-DMX-AREA-OUTCOME-001.json >/dev/null",
      "python -m jsonschema -i task-packets/generated/TP-DMX-AREA-OUTCOME-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json",
      "git diff --check",
      "git diff --cached --check"
    ]
  },
  "pr": {
    "title": "docs(scope): describe the outcome",
    "body": "## Summary\n- ...\n\n## Scope\n...\n\n## Validation\nInclude exact command outputs and exit codes.\n\n## NOT_RUN\n- ...\n\n## Residual Risks / UNKNOWNs\n- ...\n\n@codex review",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Preflight repo identity, marker, branch, dependencies, and schema.",
      "context_files": [
        "AGENTS.md",
        "docs/03-reference/spec/dopetask/dopetask-canonical-spec.json"
      ],
      "commands": [
        "git remote -v",
        "git branch --show-current",
        "git status --short",
        "test -f .dopetaskroot"
      ],
      "validation": [
        "Repo identity, marker, branch, and dependencies must match the packet or execution stops."
      ]
    },
    {
      "id": "S2",
      "task": "Implement the smallest allowlisted slice that completes the outcome.",
      "requirements": [
        "Use repo truth over stale prose.",
        "Do not touch files outside commit.allowlist."
      ],
      "expected_files": [
        "docs/03-reference/governance/example.md"
      ],
      "validation": [
        "Run the narrowest command that can falsify this slice."
      ]
    }
  ]
}
```

## Operator Fill-In Checklist

- Replace all example IDs, branch names, titles, paths, validation commands, and PR body text.
- Keep only schema-declared root fields: `id`, `project`, `target`, `invariants`, `depends_on`, `repo_binding`, `series`, `execution`, `commit`, `pr`, `pal_chain`, and `steps`.
- Keep only schema-declared step fields: `id`, `task`, `requirements`, `commands`, `expected_files`, `validation`, and `context_files`.
- Ensure every step has `id`, `task`, and non-empty `validation`.
- Validate the generated packet before implementation.
- Make proof creation part of the packet, not a follow-on cleanup.
