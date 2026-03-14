# Leantime Truth Pack — Discovery Notes

## Phase 1 Baseline Summary

### Repository Identity
- **URL**: https://github.com/Leantime/leantime.git
- **Ref**: 555803d3da0f81ba232d5f38fc11268fdf317511 (master)
- **Latest release**: v3.7.1 (tag), AppSettings v3.7.2 / dbVersion 3.5.0
- **Stack**: PHP 8.2+, Laravel 11.44, MySQL 8.0+/MariaDB 10.6+/PostgreSQL
- **Frontend**: Laravel Mix 6.x, jQuery 3.7.1, HTMX 1.9.12, Tailwind 3.4.x, Tiptap editor
- **MCP**: php-mcp/laravel 3.0.0 installed, /mcp endpoint registered, early-stage

### Active Integration Surfaces
1. **JSON-RPC 2.0** — Primary API. All 48 service classes' public methods callable via `leantime.rpc.{module}.{service}.{method}`. Controller: `App\Domain\Api\Controllers\Jsonrpc`
2. **MCP** — Endpoint `/mcp` registered in IncomingRequest. Uses php-mcp/laravel 3.0.0. No custom tools/resources found in codebase — relies on package defaults.
3. **Event/Filter system** — `EventDispatcher` with string-based names, wildcard matching. 8 register.php files with event listeners. `DispatchesEvents` trait on most classes.
4. **Plugin system** — Folder + PHAR formats. Registration via `register.php`. Middleware pipeline hook. Route loading. Menu items. JS/CSS injection.
5. **CLI** — 17 commands via `php bin/leantime [command]`
6. **Legacy REST API** — 37 controllers in `Api/Controllers/` (deprecated, not recommended for new integrations)

### Excluded/Legacy Surfaces
- Legacy REST API controllers (deprecated per codebase docs)
- Frontcontroller routing (legacy, still functional but Laravel routes preferred)
- jQuery AJAX patterns (being replaced by HTMX)

### Key Domain Entities Found (24)
Ticket, Project, Client, User, Sprint, Milestone, Goal, Idea, Risk, Retrospective, Wiki/Article, Comment, File, Timesheet, Notification, Audit, Reaction, EntityRelation, Canvas (16 variants), Integration/Connector, Plugin, Setting, Queue, PunchClock

### Key Schema Facts
- 30 database tables with `zp_` prefix
- No Laravel migrations — schema managed by `SchemaBuilder.php`
- Supports MySQL, PostgreSQL, MS SQL Server
- Status codes are integer-based for tickets, string-based for goals
- Role system is numeric-key-based (5-50 scale)

### Notable Dependencies
- `php-mcp/laravel` 3.0.0 — Model Context Protocol
- `prism-php/prism` 0.57.0 — AI/LLM integration
- `inspector-apm/neuron-ai` 1.12.8 — AI agent framework
- `hkulekci/qdrant` 0.5.8 — Vector database client
- `sabre/dav` 4.7 — CalDAV/CardDAV server
- `stripe/stripe-php` — Payment processing
- `laravel/socialite` + 15 providers — Social auth

### Potential Drift Areas (to investigate in Phase 2)
- CLAUDE.md says "TinyMCE 5.10.9" but package.json shows Tiptap editor dependencies — likely migrated
- CLAUDE.md says "~198 .tpl.php files" — need to verify current count
- CLAUDE.md says version "3.6.2" but AppSettings shows 3.7.2
- MCP integration status unclear — package installed but no custom implementation visible
