# 05 Integration Seams

## API Surfaces
- JSON-RPC 2.0 endpoint routes methods like `leantime.rpc.{domain}.{service}.{method}` (or 4-part form) and reflects service method signatures for invocation (`app/Domain/Api/Controllers/Jsonrpc.php:255`, `app/Domain/Api/Controllers/Jsonrpc.php:270`, `app/Domain/Api/Controllers/Jsonrpc.php:274`, `app/Domain/Api/Controllers/Jsonrpc.php:282`, `app/Domain/Api/Controllers/Jsonrpc.php:221`, `app/Domain/Api/Controllers/Jsonrpc.php:227`, `app/Domain/Api/Controllers/Jsonrpc.php:234`).
- Service/method existence is validated, but code comments show API-annotation gating is not implemented (`app/Domain/Api/Controllers/Jsonrpc.php:205`, `app/Domain/Api/Controllers/Jsonrpc.php:209`, `app/Domain/Api/Controllers/Jsonrpc.php:210`).
- Legacy API controllers still expose mutation endpoints (ticket/project kanban sorting, gantt sorting, patch) (`app/Domain/Api/Controllers/Tickets.php:67`, `app/Domain/Api/Controllers/Tickets.php:80`, `app/Domain/Api/Controllers/Tickets.php:111`, `app/Domain/Api/Controllers/Projects.php:85`, `app/Domain/Api/Controllers/Projects.php:103`, `app/Domain/Api/Controllers/Projects.php:121`, `app/Domain/Api/Controllers/Projects.php:130`).

## Routing and Dispatch Seams
- HTTP dispatch runs core middleware, then plugin middleware pipeline, then router/frontcontroller dispatch (`app/Core/Http/HttpKernel.php:155`, `app/Core/Http/HttpKernel.php:163`, `app/Core/Http/HttpKernel.php:168`).
- Laravel route matching has precedence, with fallback to legacy frontcontroller (`app/Core/Http/HttpKernel.php:196`, `app/Core/Http/HttpKernel.php:201`, `app/Core/Http/HttpKernel.php:212`, `app/Core/Http/HttpKernel.php:213`).
- Frontcontroller resolves domain/plugin controller classes and supports `/hx/...` mapping (`app/Core/Controller/Frontcontroller.php:112`, `app/Core/Controller/Frontcontroller.php:115`, `app/Core/Controller/Frontcontroller.php:251`, `app/Core/Controller/Frontcontroller.php:264`, `app/Core/Controller/Frontcontroller.php:285`).
- `RouteLoader` loads domain routes, system plugin routes, and user plugin routes via plugin event (`app/Core/Routing/RouteLoader.php:23`, `app/Core/Routing/RouteLoader.php:27`, `app/Core/Routing/RouteLoader.php:30`, `app/Core/Routing/RouteLoader.php:77`, `app/Core/Routing/RouteLoader.php:90`).

## Event/Filter Hook System
- Event bus supports string hooks, filter pipelines, wildcard/regex matching, and dynamic listener discovery from `register.php` files (`app/Core/Events/EventDispatcher.php:62`, `app/Core/Events/EventDispatcher.php:80`, `app/Core/Events/EventDispatcher.php:87`, `app/Core/Events/EventDispatcher.php:127`, `app/Core/Events/EventDispatcher.php:149`, `app/Core/Events/EventDispatcher.php:465`, `app/Core/Events/EventDispatcher.php:485`).
- Event names are context-derived from class namespace + caller function via `DispatchesEvents` trait (`app/Core/Events/DispatchesEvents.php:12`, `app/Core/Events/DispatchesEvents.php:42`, `app/Core/Events/DispatchesEvents.php:70`, `app/Core/Events/DispatchesEvents.php:82`).

## Plugin Extension Points
- Plugins can register middleware into both plugin-event and kernel plugin-middleware hooks (`app/Domain/Plugins/Services/Registration.php:25`, `app/Domain/Plugins/Services/Registration.php:28`, `app/Domain/Plugins/Services/Registration.php:34`).
- Plugins can inject language files, menu items, route section mapping, JS/CSS assets via event/filter hooks (`app/Domain/Plugins/Services/Registration.php:42`, `app/Domain/Plugins/Services/Registration.php:50`, `app/Domain/Plugins/Services/Registration.php:165`, `app/Domain/Plugins/Services/Registration.php:170`, `app/Domain/Plugins/Services/Registration.php:216`, `app/Domain/Plugins/Services/Registration.php:283`).
- Plugin lifecycle middleware emits plugin start/events/terminate hooks (`app/Core/Middleware/LoadPlugins.php:26`, `app/Core/Middleware/LoadPlugins.php:30`, `app/Core/Middleware/LoadPlugins.php:34`).

## Jobs and Scheduled Adapters
- Queue workers are scheduled via `register.php` event hook into Laravel scheduler (`app/Domain/Queue/register.php:9`, `app/Domain/Queue/register.php:17`, `app/Domain/Queue/register.php:22`, `app/Domain/Queue/register.php:27`).
- Queue service/repository provide async channels (`email`, `httprequest`, default) backed by `zp_queue` (`app/Domain/Queue/Services/Queue.php:30`, `app/Domain/Queue/Services/Queue.php:66`, `app/Domain/Queue/Repositories/Queue.php:49`, `app/Domain/Queue/Repositories/Queue.php:66`).
- Additional scheduled hooks exist for reports and plugin license checks (`app/Domain/Reports/register.php:9`, `app/Domain/Reports/register.php:35`, `app/Domain/Plugins/register.php:10`, `app/Domain/Plugins/register.php:36`).

## Import/Connector Seams
- Connector flow is a staged import pipeline (`connect -> entity -> fields -> parse -> import`) restricted to owner/admin in controller init (`app/Domain/Connector/Controllers/Integration.php:38`, `app/Domain/Connector/Controllers/Integration.php:72`, `app/Domain/Connector/Controllers/Integration.php:96`, `app/Domain/Connector/Controllers/Integration.php:133`, `app/Domain/Connector/Controllers/Integration.php:152`).
- Connector service maps/parses source fields and imports directly into core services for tickets/projects/users/ideas/goals/milestones (`app/Domain/Connector/Services/Connector.php:89`, `app/Domain/Connector/Services/Connector.php:586`, `app/Domain/Connector/Services/Connector.php:612`, `app/Domain/Connector/Services/Connector.php:650`, `app/Domain/Connector/Services/Connector.php:667`, `app/Domain/Connector/Services/Connector.php:683`).
- Provider list is extensible through a filter seam; CSV provider registers through this mechanism (`app/Domain/Connector/Services/Providers.php:27`, `app/Domain/CsvImport/register.php:6`, `app/Domain/CsvImport/register.php:7`, `app/Domain/CsvImport/register.php:10`).
- Integration persistence exists (`zp_integration` + generic repo), but service coverage is partial (`create/get/patch` implemented, `delete/getAll` TODO false) (`app/Domain/Install/Services/SchemaBuilder.php:734`, `app/Domain/Connector/Repositories/Integrations.php:12`, `app/Domain/Connector/Services/Integrations.php:21`, `app/Domain/Connector/Services/Integrations.php:36`, `app/Domain/Connector/Services/Integrations.php:43`, `app/Domain/Connector/Services/Integrations.php:49`, `app/Domain/Connector/Services/Integrations.php:53`).

## Webhook Surface
- Outbound webhook adapters exist for Slack/Mattermost/Zulip/Discord notifications (`app/Domain/Notifications/Services/Messengers.php:21`, `app/Domain/Notifications/Services/Messengers.php:73`, `app/Domain/Notifications/Services/Messengers.php:110`, `app/Domain/Notifications/Services/Messengers.php:149`, `app/Domain/Notifications/Services/Messengers.php:203`).
- Per-project webhook URLs are mutable in project settings controller (`app/Domain/Projects/Controllers/ShowProject.php:119`, `app/Domain/Projects/Controllers/ShowProject.php:126`, `app/Domain/Projects/Controllers/ShowProject.php:165`, `app/Domain/Projects/Controllers/ShowProject.php:176`).
- No inbound webhook handler/controller evidence found; search evidence: `rg -n "function .*webhook|/webhook|WebhookController|incoming webhook|webhook handler" app/Core app/Domain` returned `NO_MATCH` (scope: `app/Core`, `app/Domain`).
