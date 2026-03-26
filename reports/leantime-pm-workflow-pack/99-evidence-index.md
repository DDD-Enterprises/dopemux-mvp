# 99 Evidence Index

## A. File Line Citations Used
- `app/Domain/Install/Services/SchemaBuilder.php`: 251-264, 312-317, 325-345, 374-383, 391-401, 409-418, 426-477, 485-507, 558-567, 630-643, 651-662, 690-705, 713-727, 734-747, 813-829.
- `app/Domain/Tickets/Repositories/Tickets.php`: 30-75, 120-179, 189-229, 1422-1457, 1462-1483, 1488-1523, 1525-1543, 1553-1611, 1623-1654, 1648-1651, 1710-1747.
- `app/Domain/Tickets/Repositories/TicketHistory.php`: 20-31.
- `app/Domain/Tickets/Services/Tickets.php`: 130-152, 1393-1407, 1478-1505, 1589-1654, 1768-1813, 1871-1888, 1942-1974, 2047-2123, 2160-2207, 2416-2433.
- `app/Domain/Projects/Repositories/Projects.php`: 31-34, 71-75, 382-428, 699-742, 747-781, 807-829, 864-903, 1010-1025.
- `app/Domain/Projects/Services/Projects.php`: 96-170, 1363-1384, 1404-1416, 1565-1568, 1879-1895, 1946-1983, 2022-2043.
- `app/Domain/Projects/Controllers/ShowProject.php`: 101-104, 119-128, 147-178, 196-205, 227-250.
- `app/Domain/Sprints/Repositories/Sprints.php`: 191-228.
- `app/Domain/Sprints/Services/Sprints.php`: 103-160, 167-262, 269-358.
- `app/Domain/Timesheets/Services/Timesheets.php`: 93-143, 162-212, 261-282.
- `app/Domain/Timesheets/Repositories/Timesheets.php`: 584-645, 650-731, 738-792, 797-857, 871-907, 920-934, 942-947.
- `app/Domain/Comments/Repositories/Comments.php`: 17-47, 108-135.
- `app/Domain/Comments/Services/Comments.php`: 45-55, 57-106, 113-125.
- `app/Domain/Notifications/Repositories/Notifications.php`: 23-60, 65-87, 89-101.
- `app/Domain/Read/Repositories/Read.php`: 17-33.
- `app/Domain/Audit/Repositories/Audit.php`: 29-42, 72-96, 98-105.
- `app/Domain/Wiki/Services/Wiki.php`: 127-143, 222-244, 249-331.
- `app/Core/Support/EntityRelationshipEnum.php`: 10-16.
- `app/Core/Events/DispatchesEvents.php`: 12-15, 27-30, 42-63, 70-73, 82-89.
- `app/Core/Events/EventDispatcher.php`: 62-96, 101-115, 127-147, 149-179, 465-555.
- `app/Core/Middleware/LoadPlugins.php`: 26-35.
- `app/Core/Middleware/AuthCheck.php`: 26-43, 56-74, 89-94, 131-142.
- `app/Core/Http/HttpKernel.php`: 50-75, 153-169, 190-214.
- `app/Core/Controller/Frontcontroller.php`: 112-117, 124-166, 219-240, 247-291, 306-333.
- `app/Core/Routing/RouteLoader.php`: 14-35, 40-55, 60-71, 77-93.
- `app/Domain/Api/Controllers/Jsonrpc.php`: 180-207, 209-211, 221-235, 255-288, 313-349.
- `app/Domain/Api/Controllers/Tickets.php`: 67-103, 111-134.
- `app/Domain/Api/Controllers/Projects.php`: 85-113, 121-142.
- `app/Domain/Connector/Controllers/Integration.php`: 32-44, 72-75, 87-94, 96-124, 133-149, 151-166.
- `app/Domain/Connector/Services/Providers.php`: 19-28, 30-45.
- `app/Domain/Connector/Services/Connector.php`: 89-106, 586-610, 612-664, 667-695, 697-729, 731-787.
- `app/Domain/Connector/Services/Integrations.php`: 21-24, 36-39, 41-51, 53-56.
- `app/Domain/Connector/Repositories/Integrations.php`: 10-14.
- `app/Core/Db/Repository.php`: 199-229, 234-278.
- `app/Domain/CsvImport/register.php`: 6-14.
- `app/Domain/CsvImport/Services/CsvImport.php`: 22-28, 38-44, 59-64, 82-85, 117-121.
- `app/Domain/Queue/register.php`: 9-29.
- `app/Domain/Queue/Services/Queue.php`: 30, 66-87, 89-113.
- `app/Domain/Queue/Repositories/Queue.php`: 22-57, 66-76, 92-110.
- `app/Domain/Reports/register.php`: 9-40.
- `app/Domain/Plugins/register.php`: 10-37.
- `app/Domain/Notifications/register.php`: 6.
- `app/Domain/Plugins/Services/Registration.php`: 25-39, 42-71, 165-213, 216-302.
- `app/Domain/Notifications/Services/Messengers.php`: 21, 47-64, 73-102, 110-141, 149-195, 203-262.
- `app/Domain/Canvas/Repositories/Canvas.php`: 52-58, 82-85, 315-347, 349-367.

## B. Negative-Evidence Searches (Command + Scope + Result)

### NEG-01 Formal workflow legality/state machine constructs
- Command:
- `rg -n --hidden --glob '!vendor/**' --glob '!.git/**' "allowed transition|allowedTransitions|state machine|state_machine|workflow rule|transition rule|canTransition|validTransition" app config`
- Scope: `app`, `config`.
- Result: `NO_MATCH: workflow legality engine terms in app config`.

### NEG-02 Next-action computation constructs
- Command:
- `rg -n --hidden --glob '!vendor/**' --glob '!.git/**' "next action|next_action|nextAction|suggest(ed)? action|recommended action" app config`
- Scope: `app`, `config`.
- Result: `NO_MATCH: next-action terms in app config`.

### NEG-03 Decision-register constructs
- Command:
- `rg -n --hidden --glob '!vendor/**' --glob '!.git/**' "decision log|decision register|recordDecision|decisionId|governance decision" app config`
- Scope: `app`, `config`.
- Result: `NO_MATCH: decision-tracking terms in app config`.

### NEG-04 Inbound webhook handlers
- Command:
- `rg -n "function .*webhook|/webhook|WebhookController|incoming webhook|webhook handler" app/Core app/Domain`
- Scope: `app/Core`, `app/Domain`.
- Result: `NO_MATCH: inbound webhook handlers/controllers`.

### NEG-05 Note runtime usage outside install/schema
- Command:
- `rg -n "zp_note|note table|createNote|addNote|getNote" app/Domain app/Core`
- Scope: `app/Domain`, `app/Core`.
- Result: matches only install/schema files (`SchemaBuilder`, `Install`), no non-install runtime usage found.

### NEG-06 Recurring pattern runtime usage outside install
- Command:
- `rg -n "zp_recurring_patterns|RecurringPattern|nextProcessingDate|lastProcessed" app/Core app/Domain --glob '!app/Domain/Install/**'`
- Scope: `app/Core`, `app/Domain` minus install domain.
- Result: `NO_MATCH: recurring pattern runtime usage outside Install domain`.

### NEG-07 Explicit approvals runtime usage outside install
- Command:
- `rg -n "\bzp_approvals\b|\bapprovalStatus\b|\bapproverId\b|\brequestorId\b" app/Core app/Domain --glob '!app/Domain/Install/**' --glob '!app/Domain/Tickets/Repositories/Tickets.php'`
- Scope: `app/Core`, `app/Domain` minus install and an unrelated `requestorId`-heavy ticket file.
- Result: `NO_MATCH: explicit approvals fields/table usage outside install`.

### NEG-08 Read repository usage breadth
- Commands:
- `rg -n -F "Leantime\\Domain\\Read\\Repositories\\Read" app/Domain app/Core`
- `rg -n "readRepo|markAsRead\(|isRead\(" app/Domain app/Core`
- Scope: `app/Domain`, `app/Core`.
- Result: no FQCN references; method-name query only matched `app/Domain/Read/Repositories/Read.php`.

### NEG-09 Backend status-transition legality phrasing
- Command:
- `rg -n "invalid status|status.*not allowed|cannot.*status|forbid.*status|disallow.*status|allowed status|status transition|transition" app/Domain/Tickets app/Domain/Projects app/Domain/Sprints`
- Scope: ticket/project/sprint domains.
- Result: matches were UI/JS transition wording, no backend transition legality engine in scanned files.
