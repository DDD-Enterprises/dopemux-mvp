# 04 History Audit and Chronicle

## Ticket Change History
- Ticket field changes are written to `zp_tickethistory` as per-field deltas (`changeType`, `changeValue`, `dateModified`) when tracked values change (`app/Domain/Tickets/Repositories/Tickets.php:1553`, `app/Domain/Tickets/Repositories/Tickets.php:1591`, `app/Domain/Tickets/Repositories/Tickets.php:1601`, `app/Domain/Tickets/Repositories/Tickets.php:1610`).
- Recent ticket history is queryable by date/ticket through a dedicated repository (`app/Domain/Tickets/Repositories/TicketHistory.php:20`, `app/Domain/Tickets/Repositories/TicketHistory.php:23`, `app/Domain/Tickets/Repositories/TicketHistory.php:29`).

## Audit Trail
- A generic audit table (`zp_audit`) exists with `action`, `entity`, `entityId`, `values`, `date` (`app/Domain/Install/Services/SchemaBuilder.php:630`, `app/Domain/Install/Services/SchemaBuilder.php:634`, `app/Domain/Install/Services/SchemaBuilder.php:636`, `app/Domain/Install/Services/SchemaBuilder.php:637`, `app/Domain/Install/Services/SchemaBuilder.php:638`).
- Audit repository supports store/query/prune operations (`app/Domain/Audit/Repositories/Audit.php:29`, `app/Domain/Audit/Repositories/Audit.php:33`, `app/Domain/Audit/Repositories/Audit.php:72`, `app/Domain/Audit/Repositories/Audit.php:98`).
- Concrete usage is visible in Wiki article lifecycle/audit activity feed (create + field-diff events) (`app/Domain/Wiki/Services/Wiki.php:127`, `app/Domain/Wiki/Services/Wiki.php:132`, `app/Domain/Wiki/Services/Wiki.php:222`, `app/Domain/Wiki/Services/Wiki.php:227`, `app/Domain/Wiki/Services/Wiki.php:249`, `app/Domain/Wiki/Services/Wiki.php:323`).

## Comments, Notifications, and Read Markers
- Comments provide timestamped module/entity discussion records and optional status fields (`app/Domain/Comments/Repositories/Comments.php:21`, `app/Domain/Comments/Repositories/Comments.php:29`, `app/Domain/Comments/Repositories/Comments.php:108`, `app/Domain/Comments/Repositories/Comments.php:117`).
- Notifications are persisted in `zp_notifications` with `read` state and metadata (`module`, `moduleId`, `message`, `authorId`) (`app/Domain/Install/Services/SchemaBuilder.php:690`, `app/Domain/Install/Services/SchemaBuilder.php:693`, `app/Domain/Install/Services/SchemaBuilder.php:695`, `app/Domain/Install/Services/SchemaBuilder.php:696`, `app/Domain/Install/Services/SchemaBuilder.php:700`, `app/Domain/Notifications/Repositories/Notifications.php:65`, `app/Domain/Notifications/Repositories/Notifications.php:89`).
- Read markers are implemented in `zp_read` repository APIs (`markAsRead`, `isRead`) (`app/Domain/Read/Repositories/Read.php:17`, `app/Domain/Read/Repositories/Read.php:19`, `app/Domain/Read/Repositories/Read.php:26`).

## Chronicle/Memory Authority Assessment
- `zp_tickethistory` and `zp_audit` are supporting historical logs; mutation legality and current PM truth still come from live project/ticket/sprint/timesheet tables and direct update paths (`app/Domain/Tickets/Repositories/Tickets.php:1422`, `app/Domain/Tickets/Repositories/Tickets.php:1488`, `app/Domain/Projects/Repositories/Projects.php:747`, `app/Domain/Sprints/Repositories/Sprints.php:191`, `app/Domain/Timesheets/Repositories/Timesheets.php:584`).
- This repo contains persistent notes table schema (`zp_note`) but no runtime usage in scanned non-install code (`app/Domain/Install/Services/SchemaBuilder.php:312`, `app/Domain/Install/Services/SchemaBuilder.php:317`).
- Search evidence: `rg -n "zp_note|note table|createNote|addNote|getNote" app/Domain app/Core` matched install/schema files only (scope: `app/Domain`, `app/Core`).

## Additional Absence Evidence
- Read-marker APIs appear repository-only in scanned runtime scope; search evidence: `rg -n -F "Leantime\\Domain\\Read\\Repositories\\Read" app/Domain app/Core` returned `NO_MATCH`, and `rg -n "readRepo|markAsRead\(|isRead\(" app/Domain app/Core` matched only `app/Domain/Read/Repositories/Read.php` (scope: `app/Domain`, `app/Core`).
