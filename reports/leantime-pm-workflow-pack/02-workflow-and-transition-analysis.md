# 02 Workflow and Transition Analysis

## Verdict: Formal Workflow Legality Is Mostly Not Enforced Centrally
- Ticket transitions are performed by direct field mutation APIs rather than a central legality engine. Kanban updates iterate posted status columns and call direct status writes (`app/Domain/Tickets/Services/Tickets.php:2416`, `app/Domain/Tickets/Services/Tickets.php:2423`, `app/Domain/Tickets/Repositories/Tickets.php:1525`, `app/Domain/Tickets/Repositories/Tickets.php:1530`, `app/Domain/Tickets/Repositories/Tickets.php:1540`).
- Generic ticket patch allows arbitrary sanitized columns, including `status`, with no transition matrix check in that method (`app/Domain/Tickets/Repositories/Tickets.php:1462`, `app/Domain/Tickets/Repositories/Tickets.php:1468`, `app/Domain/Tickets/Repositories/Tickets.php:1480`).
- Project status transitions are similarly direct in kanban updates and repository patch (`app/Domain/Projects/Services/Projects.php:2022`, `app/Domain/Projects/Services/Projects.php:2037`, `app/Domain/Projects/Repositories/Projects.php:1010`, `app/Domain/Projects/Repositories/Projects.php:1016`, `app/Domain/Projects/Repositories/Projects.php:1021`).

## Where State Changes Occur
- Ticket create/update paths set `status` directly from provided values/defaults (`app/Domain/Tickets/Services/Tickets.php:1800`, `app/Domain/Tickets/Services/Tickets.php:1955`, `app/Domain/Tickets/Repositories/Tickets.php:1431`, `app/Domain/Tickets/Repositories/Tickets.php:1499`).
- Ticket status changes write history rows (`zp_tickethistory`) for changed tracked fields (`app/Domain/Tickets/Repositories/Tickets.php:1527`, `app/Domain/Tickets/Repositories/Tickets.php:1553`, `app/Domain/Tickets/Repositories/Tickets.php:1609`).
- Project edit path writes `state` directly (`app/Domain/Projects/Repositories/Projects.php:761`, `app/Domain/Projects/Repositories/Projects.php:768`).

## Existing Transition Constraints (Localized, Not Global)
- A controller-level guard prevents closing a project in one UI path when the project still has tickets (`hasTickets` + `state == 1`) (`app/Domain/Projects/Controllers/ShowProject.php:246`, `app/Domain/Projects/Controllers/ShowProject.php:247`, `app/Domain/Projects/Repositories/Projects.php:822`, `app/Domain/Projects/Repositories/Projects.php:828`).
- That guard is not a universal invariant because other mutation paths patch `state` directly without that same check (service/API/repository patch flow) (`app/Domain/Projects/Services/Projects.php:2022`, `app/Domain/Projects/Services/Projects.php:2037`, `app/Domain/Api/Controllers/Projects.php:103`, `app/Domain/Projects/Repositories/Projects.php:1010`).
- Ticket patch on status change performs a side-effect reset of `sprint`, `dependingTicketId`, and `milestoneid`; this is mutation coupling, not a pre-transition validator (`app/Domain/Tickets/Services/Tickets.php:2182`, `app/Domain/Tickets/Services/Tickets.php:2206`).

## Dependencies and Blockers vs Legality
- Dependencies are represented (`dependingTicketId`) and used for hierarchy/sorting computations (`app/Domain/Tickets/Services/Tickets.php:1403`, `app/Domain/Tickets/Services/Tickets.php:1482`, `app/Domain/Tickets/Repositories/Tickets.php:1648`).
- Blocked is a status label (`status.blocked`) in the status taxonomy (`app/Domain/Tickets/Repositories/Tickets.php:41`, `app/Domain/Tickets/Repositories/Tickets.php:43`).
- No evidence in transition write paths that dependency/blocker state blocks status mutation before write (`app/Domain/Tickets/Repositories/Tickets.php:1525`, `app/Domain/Tickets/Repositories/Tickets.php:1530`, `app/Domain/Tickets/Repositories/Tickets.php:1540`).

## State Semantics Consistency
- Project closed/open semantics are internally mixed: state map uses `1 => CLOSED`, while major query filters use `-1` for closed checks (`app/Domain/Projects/Repositories/Projects.php:33`, `app/Domain/Projects/Repositories/Projects.php:423`, `app/Domain/Projects/Repositories/Projects.php:427`).

## Absent Evidence (Scoped Searches)
- No central workflow legality/state-machine constructs were found in scanned runtime code; search evidence: `rg -n --hidden --glob '!vendor/**' --glob '!.git/**' "allowed transition|allowedTransitions|state machine|state_machine|workflow rule|transition rule|canTransition|validTransition" app config` returned `NO_MATCH` (scope: `app`, `config`).
