<!--
GOVERNANCE — READ BEFORE USE

This template is a READ-ONLY scaffold for presenting implementer-role repair
items to GitHub Copilot. The following operations are PROHIBITED:

  1. Copilot MUST NOT post this content as a PR comment.
  2. Copilot MUST NOT approve the PR.
  3. Copilot MUST NOT merge the PR or enqueue it in a merge queue.
  4. Copilot MUST NOT alter readiness state or check status.
  5. Copilot MUST NOT import or invoke tools/pr_merge.
  6. Copilot MUST NOT act on supervisor-role items (harvest-incomplete,
     pr-is-draft, pr-closed, mixed-sha, unknown-reviewer, proof-stale,
     unknown-check, needs-supervisor, embedded-audit-failed).
  7. Copilot MUST NOT act on ci-role items (pending-check).

Copilot authority: implementer-only (L1-L2 code changes only).
Supervisor actions require human operator intervention.
-->

# PR Repair Packet

**Repo**: {{ repo }}
**PR**: #{{ pr_number }}
**Generated**: {{ generated_at }}
**Copilot authority**: implementer-only

---

## Governance

Copilot is a **bounded implementer** for this repair packet.

| Operation | Permitted |
|---|---|
| Read this packet | YES |
| Propose code changes locally | YES |
| Post PR comment | **NO** |
| Approve PR | **NO** |
| Merge PR or enqueue merge queue | **NO** |
| Alter readiness / check status | **NO** |
| Import tools/pr_merge | **NO** |
| Act on supervisor-role items | **NO** |
| Act on ci-role items | **NO** |

Supervisor-role and CI-role blockers are out of scope. Only the
implementer-role items below are presented.

---

## Repair Items

{% for item in items %}
### {{ item.id }} — `{{ item.category }}`

- **Blocker**: `{{ item.source_blocker }}`
{% if item.source_item_id %}
- **Source item**: `{{ item.source_item_id }}`
{% endif %}
- **Rationale**: {{ item.rationale }}
- **Suggested action**: {{ item.suggested_action }}

{% endfor %}
{% if not items %}
No implementer-role repair items. If the PR is still blocked, review
supervisor-role or CI-role items in the full ACTION_PLAN.
{% endif %}
