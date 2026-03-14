# Documentation Drift Report

**Generated**: 2025-07-17
**Sources compared**: `CLAUDE.md` (primary), `README.md` vs actual codebase
**Method**: Every factual claim verified against source code, file counts, and configuration files

---

## Summary

| Category | Count |
|---|---|
| Version / numeric drift | 5 |
| Stale technology references | 3 |
| Count mismatches | 6 |
| Undocumented surfaces | 4 |
| Incorrect specifics | 3 |
| **Total drift items** | **21** |

---

## Drift Items

### DRIFT-01: Application Version
**Category**: docs-incorrect
**Documentation says**: "Current version: 3.6.2"
**Code shows**: `app/Core/Configuration/AppSettings.php` → `appVersion = '3.7.2'`, `dbVersion = '3.5.0'`. Latest git tag: `v3.7.1`.
**Impact**: high
**Notes**: The documented version is two minor releases behind. Any tooling relying on this claim will misjudge compatibility.

---

### DRIFT-02: Editor — TinyMCE Replaced by Tiptap
**Category**: docs-incorrect
**Documentation says**: "TinyMCE 5.10.9 is 3.6MB alone" and references a `compiled-editor-component` bundle for TinyMCE.
**Code shows**: `package.json` has zero TinyMCE references. Instead, 13+ `@tiptap/*` packages are present. `webpack.mix.js` compiles `compiled-tiptap-editor` and `compiled-tiptap-toolbar` — no `compiled-editor-component` bundle exists. The "3.6MB" JS size claim is now false.
**Impact**: high
**Notes**: TinyMCE has been fully replaced by Tiptap. Every CLAUDE.md mention of TinyMCE is stale: the bundle name, the version number, the file size, and the "~20 custom plugins" claim.

---

### DRIFT-03: JS Bundle Names
**Category**: docs-incorrect
**Documentation says**: Bundle list includes `compiled-editor-component` (TinyMCE).
**Code shows** (`webpack.mix.js`): The actual bundles are:
- `compiled-htmx`, `compiled-htmx-extensions`
- `compiled-frameworks`, `compiled-framework-plugins`
- `compiled-global-component`
- `compiled-tiptap-editor`, `compiled-tiptap-toolbar`, `compiled-tiptap-tests`
- `compiled-calendar-component`, `compiled-table-component`
- `compiled-gantt-component`, `compiled-chart-component`
- `compiled-app`, `compiled-footer`, `compiled-lottieplayer`

Missing from docs: `compiled-tiptap-*`, `compiled-footer`, `compiled-lottieplayer`.
Documented but nonexistent: `compiled-editor-component`.
**Impact**: medium
**Notes**: Bundle inventory in CLAUDE.md needs a full refresh.

---

### DRIFT-04: Domain Count
**Category**: docs-incorrect
**Documentation says**: "56 domain modules in `app/Domain/`" and "56 modules" in multiple places.
**Code shows**: `ls -d app/Domain/*/` yields **57** directories.
**Impact**: low
**Notes**: Off by one. The 57th may have been added after the doc was written.

---

### DRIFT-05: HxController Count and Domain List
**Category**: docs-incorrect
**Documentation says**: "8 of 56 domains have dedicated `Hxcontrollers/` with 19 total HxControllers" and lists: Tickets, Projects, Timesheets, Widgets, Menu, Notifications, Plugins, Help.
**Code shows**: **10 domains** have `Hxcontrollers/` directories with **22 total HxController files**. The two missing from docs:
- `Comments/Hxcontrollers/Reactions.php`
- `Wiki/Hxcontrollers/ArticleActivity.php`, `ArticleContent.php`
**Impact**: medium
**Notes**: Comments and Wiki have been HTMX-enabled since the doc was written.

---

### DRIFT-06: Template File Counts
**Category**: docs-incorrect
**Documentation says**: "~198 `.tpl.php` files" and "~91 `.blade.php` files in domains + ~33 in shared Views"
**Code shows**:
- `.tpl.php`: **198** (exact match — still accurate)
- `.blade.php` in domains: **95** (doc says ~91, off by 4)
- `.blade.php` in Views: **33** (exact match)
**Impact**: low
**Notes**: The tpl count is still accurate. Blade count has grown slightly.

---

### DRIFT-07: HTMX Template Usage Counts
**Category**: docs-incorrect
**Documentation says**: "~57 Blade templates and ~14 tpl.php files use HTMX attributes"
**Code shows**: Only **29 Blade** and **9 tpl.php** files contain `hx-` attributes (plus 1 in shared Views = 30 total Blade).
**Impact**: medium
**Notes**: Docs overstate HTMX adoption by ~2x. The 57/14 figures may have counted something broader than `hx-` attributes.

---

### DRIFT-08: Partially Modernized Domains List Incomplete
**Category**: docs-incorrect
**Documentation says**: Partially modernized (mix of tpl + blade): "Auth, Calendar, Comments, Help, Projects, Tickets, Timesheets, Users"
**Code shows**: **Wiki** also has both `.tpl.php` (6) and `.blade.php` (1) files, plus 2 HxControllers. Wiki is not listed in either the "partially modernized" or "fully legacy" categories — it's missing entirely.
**Impact**: low
**Notes**: Wiki should be added to the "partially modernized" list.

---

### DRIFT-09: Canvas Variant Count
**Category**: docs-incorrect
**Documentation says**: "14 variants extending `Canvas` base" and lists 18 names (Canvas base + 17 variants).
**Code shows**: **18 total canvas-related directories** in `app/Domain/`. Excluding the `Canvas` base = **17 variant domains**. The header says "14 variants" but the listed names show 17, and the actual filesystem confirms 17.
**Impact**: low
**Notes**: The "14" number in the prose contradicts both the list in the same doc and the actual code.

---

### DRIFT-10: Bootstrap Version
**Category**: docs-incorrect
**Documentation says**: "Bootstrap 2.x (ancient)" in multiple places.
**Code shows**: `public/assets/css/libs/bootstrap.css` file header reads `Bootstrap v3.0.0`. Bootstrap is not an npm dependency — it's vendored as static CSS/JS files.
**Impact**: low
**Notes**: It's Bootstrap 3.0.0, not 2.x. Still ancient, but the version number is wrong.

---

### DRIFT-11: Middleware Count
**Category**: docs-incorrect
**Documentation says**: "16 middlewares" in `Core/Middleware/`.
**Code shows**: **13 PHP files** in `app/Core/Middleware/`. One of those (`RateLimiter.php`) is a ServiceProvider, not a middleware. The actual middleware stack in `HttpKernel.php` has 13 entries (including 2 from Illuminate).
**Impact**: low
**Notes**: "16" never matched; the actual count is 13 files, 12 true middleware classes.

---

### DRIFT-12: Controller Pattern Counts
**Category**: docs-incorrect
**Documentation says**: "~55 controllers" use `run()` pattern and "~83 controllers" use `get()/post()` pattern.
**Code shows**: **60** controller files contain `function run(`, **85** contain `function get(`. Total controller files: **278**.
**Impact**: low
**Notes**: Minor drift — counts are slightly higher than documented.

---

### DRIFT-13: Ticket Type List Incomplete
**Category**: docs-incorrect
**Documentation says**: Lists ticket types implicitly as story, task, subtask, bug (via `typeIcons` array in Repositories).
**Code shows**: `app/Domain/Tickets/Models/TicketDesignTokens.php` defines **9 types**: story, task, subtask, bug, **feature, epic, documentation, improvement, research**. The `typeIcons` array in `Repositories/Tickets.php` still only has 4, creating an internal inconsistency.
**Impact**: medium
**Notes**: The TicketDesignTokens model has expanded the type system but the repository `typeIcons` hasn't caught up. CLAUDE.md doesn't mention ticket types explicitly but references the repository as authoritative.

---

### DRIFT-14: Undocumented MCP Server Integration
**Category**: undocumented-surface
**Documentation says**: Nothing — MCP is not mentioned anywhere in CLAUDE.md or README.md.
**Code shows**: `composer.json` includes `php-mcp/server` (dev-main) and `php-mcp/laravel` (3.0.0), using a custom fork at `github.com/leantime/php-mcp-server.git`. The `/mcp` endpoint is registered in `app/Core/Http/IncomingRequest.php` as a valid API endpoint. However, `php-mcp/laravel` is in `dont-discover`, and no `#[McpTool]` attributes or MCP service providers are registered in app code — suggesting this is wired up at the framework level but not yet exposing domain tools.
**Impact**: high
**Notes**: MCP is a significant integration surface (AI agent tool access to the PM system) that is completely undocumented.

---

### DRIFT-15: Undocumented AI/LLM Dependencies
**Category**: undocumented-surface
**Documentation says**: Nothing — no mention of AI, LLM, embeddings, or vector search.
**Code shows**: `composer.json` includes:
- `prism-php/prism` ^0.57.0 (LLM abstraction layer)
- `inspector-apm/neuron-ai` 1.12.8 (AI agent framework)
- `hkulekci/qdrant` ^0.5.8 (vector database client)

No `use` statements for these packages exist in `app/` — they are likely consumed by the private plugins submodule.
**Impact**: medium
**Notes**: These dependencies indicate AI/RAG capabilities exist (likely in commercial plugins) but are invisible in the OSS documentation.

---

### DRIFT-16: Undocumented CalDAV/CardDAV (Sabre/DAV)
**Category**: undocumented-surface
**Documentation says**: Nothing about CalDAV or Sabre/DAV.
**Code shows**: `composer.json` includes `sabre/dav` ^4.7. Usage in app code is limited to template comments referencing "CalDAV" as a plugin-managed calendar provider. Like the AI packages, the actual integration likely lives in the private plugins submodule.
**Impact**: medium
**Notes**: CalDAV/CardDAV is a significant integration (native calendar sync) that is undocumented.

---

### DRIFT-17: Undocumented Lottie Player
**Category**: undocumented-surface
**Documentation says**: Not mentioned in JS bundle documentation.
**Code shows**: `webpack.mix.js` compiles `compiled-lottieplayer` from `@lottiefiles/lottie-player`. This bundle is loaded but not documented.
**Impact**: low
**Notes**: Minor omission in the JS architecture section.

---

### DRIFT-18: CSS Build Uses LESS, Not Mentioned
**Category**: docs-incorrect
**Documentation says**: The CSS architecture section describes "Three-layer system" with third-party CSS, custom components, and Tailwind. No mention of LESS.
**Code shows**: `webpack.mix.js` compiles two LESS files (`main.less`, `app.less`) from `public/assets/less/`. The main.less imports Bootstrap CSS. LESS is the primary CSS preprocessor, not just raw CSS.
**Impact**: low
**Notes**: The doc implies CSS is static files + Tailwind. In reality, LESS compiles the core stylesheets.

---

### DRIFT-19: Routes File Claim
**Category**: docs-incorrect
**Documentation says**: "Standard `routes.php` files in domains and plugins, loaded by `RouteLoader`" (implies multiple domains have routes.php).
**Code shows**: Only **1** domain has a `routes.php` file: `app/Domain/Files/routes.php`. All other routing goes through the legacy Frontcontroller.
**Impact**: medium
**Notes**: The doc makes Laravel routing sound like an established pattern across domains. In reality, only Files has adopted it — the migration has barely started.

---

### DRIFT-20: Register.php Domain List
**Category**: docs-incorrect
**Documentation says**: "Domains that have `register.php`: Auth, CsvImport, Help, Install, Notifications, Plugins, Queue, Reports"
**Code shows**: Exactly those 8 domains have `register.php` — this is **accurate**.
**Impact**: none (verified correct)
**Notes**: Included for completeness since it was investigated.

---

### DRIFT-21: JS Domain File Count
**Category**: docs-incorrect
**Documentation says**: "46 total" domain JS files in `app/Domain/*/Js/`.
**Code shows**: **46 files** found — this is **accurate**.
**Impact**: none (verified correct)
**Notes**: Included for completeness since it was investigated.

---

## Verified-Accurate Claims

The following CLAUDE.md claims were verified as correct:

| Claim | Evidence |
|---|---|
| `.tpl.php` count ~198 | Exact: 198 |
| Blade in Views: ~33 | Exact: 33 |
| Domain JS files: 46 | Exact: 46 |
| `.sub.php` files: ~19 | Exact: 19 |
| `.inc.php` files: ~10 | Exact: 10 |
| register.php domains: 8 listed | All 8 confirmed |
| jQuery 3.7.1 | Confirmed in `package.json` |
| Tailwind 3.4.x with `tw-` prefix | Confirmed: `^3.4.1`, prefix `tw-` |
| Font Awesome 6.5.2 | Confirmed: `@fortawesome/fontawesome-free: ^6.5.2` |
| Moment.js and Luxon both included | Confirmed: both in `package.json` |
| 5 layout files in Views | Confirmed: app, blank, entry, error, registration |
| Blade-only domains | Confirmed: Dashboard, Gamecenter, Goalcanvas, Menu, Notifications, Plugins, Widgets |
| Only 1 class-based event (FileUploaded) | Confirmed: `app/Domain/Files/Events/FileUploaded.php` only |
| Only 1 HTMX event enum (Tickets) | Confirmed: `app/Domain/Tickets/Htmx/HtmxTicketEvents.php` only |
| Files domain has routes.php | Confirmed |
| Plugins is git submodule | Confirmed: submodule at commit `b475002` |

---

## High-Priority Fixes

1. **DRIFT-02 (Editor)**: Replace all TinyMCE references with Tiptap throughout CLAUDE.md. Update bundle names, remove "3.6MB" and "~20 custom plugins" claims.
2. **DRIFT-01 (Version)**: Update version to 3.7.2 (or make it dynamic).
3. **DRIFT-14 (MCP)**: Add section documenting MCP server integration, the `/mcp` endpoint, and its current state.
4. **DRIFT-15 (AI)**: Add section noting AI/LLM dependencies and their plugin-only usage pattern.
5. **DRIFT-19 (Routes)**: Clarify that only Files domain has adopted Laravel routes; all others use Frontcontroller.
