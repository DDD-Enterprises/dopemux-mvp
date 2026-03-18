# Write Classification

| method | path | classification | canonical authority | notes |
|---|---|---|---|---|
| `POST` | `/auth/token` | `policy_wrapped` | bridge auth | login surface, not PM authority |
| `POST` | `/auth/refresh` | `policy_wrapped` | bridge auth | refresh surface, token-bound |
| `POST` | `/events` | `policy_wrapped` | Redis/event transport | authenticated event publish |
| `POST` | `/events/tasks-imported` | `policy_wrapped` | Redis/event transport | authenticated convenience publish |
| `POST` | `/events/session-started` | `policy_wrapped` | Redis/event transport | authenticated convenience publish |
| `POST` | `/events/progress-updated` | `policy_wrapped` | Redis/event transport | authenticated convenience publish |
| `POST` | `/route/pm` | `policy_wrapped` | Leantime via adapter | rejects workflow-significant mutations |
| `POST` | `/kg/custom_data` | `policy_wrapped` | ConPort | canonical durable-context proxy |
| `POST` | `/kg/decisions` | `policy_wrapped` | ConPort | canonical decision proxy |
| `POST` | `/kg/progress` | `policy_wrapped` | ConPort | canonical progress proxy |
| `POST` | `/tasks/parse-prd` | `never_expose_directly` | none | blocked fail-closed |
| `PATCH` | `/tasks/{task_id}/status` | `never_expose_directly` | none | blocked fail-closed |

Read-only compatibility or health routes remain `safe_read_only` and are excluded from this write-focused table.
