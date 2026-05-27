# Copilot PR Repair Lane

> **Status**: Scaffold only — no automatic posting, no GitHub mutation.
> Copilot authority: `implementer-only` (L1-L2 code changes).

---

## Overview

The Copilot PR repair lane presents **implementer-role** repair items to GitHub
Copilot as a bounded coding assistant. It does not enable Copilot as an
autonomous cloud agent, and it does not give Copilot authority to post comments,
approve PRs, merge PRs, or alter any GitHub state.

This lane surfaces a curated subset of the full ACTION_PLAN: only the four
implementer-role blocker categories that Copilot can meaningfully address with
code changes.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| `copilot_authority: const "implementer-only"` | Schema-level governance pin; cannot be changed by callers |
| `mutation_performed: const false` | Scaffold performs no GitHub mutations; pin is permanent |
| Category enum restricted to 4 implementer categories | Supervisor-role and CI-role items are out of scope for Copilot |
| `id` pattern `repair-XXXX` (not `action-XXXX`) | Distinguishes repair items from ACTION_PLAN actions; prevents ID collision |
| `additionalProperties: false` everywhere | Forward-compat schema discipline; callers cannot inject undeclared fields |
| Template is static Jinja2; no renderer yet | Renderer is a separate concern; template documents intent and governance |
| Governance prohibitions in template HTML comment | Visible in raw source before any rendering; cannot be stripped by caller |

---

## Implementer-Role Categories

These are the only categories that appear in a `CopilotRepairPacket`:

| Category | Source Blocker | What to do |
|---|---|---|
| `unresolved-thread` | `UNRESOLVED_REVIEW_THREAD` | Address the review thread and resolve it |
| `failed-check` | `FAILED_CHECK` | Investigate and fix the failing CI check |
| `request-changes` | `REQUEST_CHANGES` | Address reviewer-requested changes |
| `must-fix` | `REVIEW_ITEM_MUST_FIX` | Resolve the must-fix review item |

Supervisor-role categories (`harvest-incomplete`, `pr-is-draft`, `pr-closed`,
`mixed-sha`, `unknown-reviewer`, `proof-stale`, `proof-missing`,
`unknown-pr-author`, `unknown-check`, `needs-supervisor`, `embedded-audit-failed`)
and CI-role categories (`pending-check`) are **intentionally excluded**. They
require human operator attention.

---

## Usage Example

Produce a repair packet dict, validate it against the schema, then pass it to a
template renderer when one exists:

```python
import json
import pathlib
import jsonschema

schema = json.loads(
    pathlib.Path("schemas/copilot/repair_packet.schema.json").read_text()
)

packet = {
    "schema_version": "1.0.0",
    "generated_at": "2026-05-26T12:00:00Z",
    "pr_number": 99,
    "repo": "acme/widget",
    "copilot_authority": "implementer-only",
    "mutation_performed": False,
    "source_action_plan_id": None,
    "items": [
        {
            "id": "repair-0001",
            "category": "failed-check",
            "source_blocker": "FAILED_CHECK",
            "source_item_id": "ci-lint",
            "rationale": "CI check failed; implementer must investigate and fix.",
            "suggested_action": "Run lint locally and fix reported issues.",
        }
    ],
}

jsonschema.Draft202012Validator(schema).validate(packet)
# If no exception: packet is schema-valid and governance pins are satisfied.
```

---

## Governance — Forbidden Operations

Copilot operating on a repair packet **MUST NOT**:

1. Post this packet or any derived content as a PR comment.
2. Approve the PR.
3. Merge the PR or enqueue it in a merge queue.
4. Alter readiness state or check status.
5. Import or invoke `tools/pr_merge`.
6. Act on supervisor-role items.
7. Act on CI-role items.

These restrictions are enforced at three layers:

- **Schema**: `copilot_authority: const "implementer-only"` and
  `mutation_performed: const false` make governance violations schema-invalid.
- **Template**: HTML comment block at the top of `PR_REPAIR_PACKET.md` lists
  all prohibited operations explicitly.
- **Category enum**: Only the four implementer categories appear in the enum;
  supervisor and CI categories are excluded from the schema entirely.

Enabling Copilot as an autonomous cloud agent (GitHub Copilot Workspace /
Copilot cloud-agent features) is a **red-lane supervisor item** and is outside
the scope of this lane.
