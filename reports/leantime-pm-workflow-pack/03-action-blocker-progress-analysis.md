# 03 Action Blocker Progress Analysis

## Next-Action Computation
- Classification: `absent/no evidence found`; search evidence: `rg -n --hidden --glob '!vendor/**' --glob '!.git/**' "next action|next_action|nextAction|suggest(ed)? action|recommended action" app config` returned `NO_MATCH` (scope: `app`, `config`).

## Blockers
- Classification: `partially implemented`; implemented representation exists as a ticket status (`status.blocked`) and as dependency links (`dependingTicketId`) (`app/Domain/Tickets/Repositories/Tickets.php:41`, `app/Domain/Tickets/Repositories/Tickets.php:43`, `app/Domain/Install/Services/SchemaBuilder.php:443`).
- Evidence indicates these are modeled and displayed/sorted, not enforced as mandatory gates in transition writes (`app/Domain/Tickets/Services/Tickets.php:1482`, `app/Domain/Tickets/Repositories/Tickets.php:1525`, `app/Domain/Tickets/Repositories/Tickets.php:1530`).

## Dependency Gates
- Classification: `advisory/display only`; dependency relationships affect hierarchy and ordering (`buildTicketTree`, milestone sorting) (`app/Domain/Tickets/Services/Tickets.php:1393`, `app/Domain/Tickets/Services/Tickets.php:1404`, `app/Domain/Tickets/Services/Tickets.php:1478`, `app/Domain/Tickets/Services/Tickets.php:1482`).
- Status mutation path writes status directly without dependency precondition checks (`app/Domain/Tickets/Repositories/Tickets.php:1525`, `app/Domain/Tickets/Repositories/Tickets.php:1530`, `app/Domain/Tickets/Repositories/Tickets.php:1540`).

## Progress Tracking
- Classification: `partially implemented`; project progress is computed from closed/total tickets and effort heuristics, which is analytical output rather than a write gate (`app/Domain/Projects/Services/Projects.php:96`, `app/Domain/Projects/Services/Projects.php:115`, `app/Domain/Projects/Services/Projects.php:122`, `app/Domain/Projects/Services/Projects.php:162`).
- Milestone progress is computed from child ticket statuses/effort-weighting (`app/Domain/Tickets/Services/Tickets.php:1589`, `app/Domain/Tickets/Services/Tickets.php:1631`, `app/Domain/Tickets/Services/Tickets.php:1651`).
- Sprint burndown/cumulative reporting is computed from report snapshots (`app/Domain/Sprints/Services/Sprints.php:167`, `app/Domain/Sprints/Services/Sprints.php:174`, `app/Domain/Sprints/Services/Sprints.php:237`, `app/Domain/Sprints/Services/Sprints.php:269`).
- A project checklist/progress-step completion state is persisted in settings (`projectsettings.{id}.stepsComplete`) (`app/Domain/Projects/Services/Projects.php:1879`, `app/Domain/Projects/Services/Projects.php:1892`, `app/Domain/Projects/Services/Projects.php:1894`).

## Decision Tracking
- Classification: `advisory/display only`; canvas items persist fields that can capture decision-like content (`assumptions`, `conclusion`, `action`, `status`) and are editable, but no dedicated decision registry/legality engine was found (`app/Domain/Install/Services/SchemaBuilder.php:165`, `app/Domain/Install/Services/SchemaBuilder.php:167`, `app/Domain/Install/Services/SchemaBuilder.php:174`, `app/Domain/Install/Services/SchemaBuilder.php:197`, `app/Domain/Canvas/Repositories/Canvas.php:315`, `app/Domain/Canvas/Repositories/Canvas.php:325`, `app/Domain/Canvas/Repositories/Canvas.php:327`, `app/Domain/Canvas/Repositories/Canvas.php:342`).
- Search evidence for explicit decision log constructs: `rg -n --hidden --glob '!vendor/**' --glob '!.git/**' "decision log|decision register|recordDecision|decisionId|governance decision" app config` returned `NO_MATCH` (scope: `app`, `config`).

## Note/Comment Gates
- Classification: `advisory/display only`; comments are first-class records with optional `status` and notification fan-out (`app/Domain/Comments/Repositories/Comments.php:108`, `app/Domain/Comments/Repositories/Comments.php:117`, `app/Domain/Comments/Services/Comments.php:45`, `app/Domain/Comments/Services/Comments.php:99`).
- No evidence that comment/note presence blocks or authorizes status transitions in ticket/project mutation methods scanned; search evidence: `rg -n "invalid status|status.*not allowed|cannot.*status|forbid.*status|disallow.*status|allowed status|status transition|transition" app/Domain/Tickets app/Domain/Projects app/Domain/Sprints` returned only UI/JS transition strings, no backend legality checks (scope: tickets/projects/sprints domains).
