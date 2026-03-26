# REPO_IDENTITY.md — Leantime

> Generated from commit `555803d3da0f81ba232d5f38fc11268fdf317511` (HEAD of `master`).
> Every claim cites its source file.

---

## Repository URL & Ref

| Field | Value | Source |
|---|---|---|
| Origin URL | `https://github.com/Leantime/leantime.git` | `git remote -v` |
| Analyzed commit | `555803d3da0f81ba232d5f38fc11268fdf317511` | `git rev-parse HEAD` |
| Default branch | `master` | `git rev-parse --abbrev-ref HEAD` |

---

## Version & Release Info

| Field | Value | Source |
|---|---|---|
| `AppSettings::$appVersion` | `3.7.2` | `app/Core/Configuration/AppSettings.php:10` |
| `AppSettings::$dbVersion` | `3.5.0` | `app/Core/Configuration/AppSettings.php:12` |
| Latest semver tag | `v3.7.1` (commit `ae8678d73`) | `git tag --sort=-v:refname \| head -1` |
| `latest` tag | Points to same commit as `v3.7.1` (`ae8678d73`) | `git log --oneline -1 latest` |
| CHANGELOG top entry | `Version: 3.7.2` (bug-fix release) | `CHANGELOG.md:1` |

> **Note:** HEAD (`555803d3d`) is 8 commits ahead of the `v3.7.1` / `latest` tag.
> The `appVersion` has already been bumped to `3.7.2` in source, but no `v3.7.2` tag exists yet.

---

## Primary Languages & Framework Stack

| Layer | Technology | Version | Source |
|---|---|---|---|
| Primary language | PHP | `^8.2` (requires); runtime image uses `8.3` | `composer.json` (`"php": "^8.2"`), `.docker/Dockerfile:2` |
| Framework | Laravel | `11.44.*` | `composer.json` (`"laravel/framework"`) |
| Template engine | Blade (`.blade.php`) + legacy `.tpl.php` | — | `app/Domain/*/Templates/` |
| Frontend JS | jQuery `3.7.1`, HTMX `1.9.12` | Bundled | `package.json`, `webpack.mix.js` |
| Rich-text editor | Tiptap (replaced TinyMCE in v3.7.0) | — | `CHANGELOG.md:34-36`, `package.json` |
| CSS framework | Tailwind CSS `3.4.x` (prefix `tw-`), Bootstrap 2.x (legacy) | — | `tailwind.config.js`, `package.json` |
| Secondary languages | JavaScript, CSS/LESS, Blade templates | — | `webpack.mix.js`, `app/Domain/*/Js/` |

---

## Build & Package System

| Tool | Role | Source |
|---|---|---|
| Composer | PHP dependency manager | `composer.json`, `composer.lock` |
| npm | JS/CSS dependency manager | `package.json`, `package-lock.json` |
| Laravel Mix 6.x (Webpack 5.x) | JS/CSS build pipeline; output → `public/dist/` | `webpack.mix.js` |
| Makefile | Orchestrates `install-deps`, `build`, `build-dev`, `package`, `test-*`, Docker dev commands | `makefile` |
| `npx mix` | Direct invocation of Laravel Mix | `webpack.mix.js` |

Build commands (from `makefile`):

```
make install-deps-dev   # composer + npm install (dev)
make build-dev          # mix build with source maps
make build              # production build
make package            # create release tarball
```

---

## Deployment & Container Outputs

| Field | Value | Source |
|---|---|---|
| Production Dockerfile | `.docker/Dockerfile` | `.docker/Dockerfile` |
| Base image | `php:8.3-fpm-alpine` (multi-stage) | `.docker/Dockerfile:2,50` |
| Runtime services | PHP-FPM 8.3, nginx, supervisor | `.docker/Dockerfile:55,58,115,117` |
| Dev compose file | `.dev/docker-compose.yaml` | `.dev/docker-compose.yaml` |
| Dev MySQL | `mysql:8.4` | `.dev/docker-compose.yaml` (image line) |
| Dev Redis | `redis:4.0` | `.dev/docker-compose.yaml` (image line) |
| Dev Selenium | `selenium/standalone-chromium` | `.dev/docker-compose.yaml` |
| Dev MailDev | `maildev/maildev` | `.dev/docker-compose.yaml` |
| Dev S3Ninja | `scireum/s3-ninja` | `.dev/docker-compose.yaml` |

Dev ports (from `makefile` / compose):

| Service | Port |
|---|---|
| Leantime app | `8090` |
| MailDev | `8081` |
| phpMyAdmin | `8082` |
| S3Ninja | `8083` |

---

## Plugin Mechanism / Extension System

| Aspect | Detail | Source |
|---|---|---|
| Plugin directory | `app/Plugins/` (git submodule → private repo for commercial plugins) | `app/Plugins/` |
| Plugin infrastructure | `app/Core/Plugins/Plugins.php`, `app/Domain/Plugins/Services/` | Core & Domain code |
| Registration | Each plugin has `register.php`; uses `EventDispatcher::add_event_listener()` / `add_filter_listener()` | `app/Domain/*/register.php` pattern |
| Plugin types | **System** (env config, loads at boot), **Custom** (folder), **Marketplace** (PHAR + license key) | `app/Domain/Plugins/Services/Plugins.php` |
| Fluent registration API | `Registration::registerMiddleware()`, `addMenuItem()`, `addCss()`, `addHeaderJs()`, `addFooterJs()` | `app/Domain/Plugins/Services/Registration.php` |
| Lifecycle | `discoverNewPlugins()` → `installPlugin()` → `enablePlugin()` → `disablePlugin()` → `removePlugin()` | `app/Domain/Plugins/Services/Plugins.php` |
| License validation | Daily cron; marketplace plugins require license key; disabled if user count exceeds license | `app/Domain/Plugins/Services/Plugins.php` |

---

## API / RPC Surfaces

### 1. JSON-RPC 2.0 (primary)

| Field | Value | Source |
|---|---|---|
| Controller | `app/Domain/Api/Controllers/Jsonrpc.php` | Source file |
| Method format | `leantime.rpc.{module}.{service}.{method}` | `Jsonrpc.php` routing logic |
| Auth | Leantime API key (`x-api-key` header, format `lt_{user}_{key}`) or Laravel Sanctum Bearer token | `app/Core/Middleware/AuthCheck.php` |

### 2. MCP Endpoint

| Field | Value | Source |
|---|---|---|
| URL | `/mcp` | `composer.json` dep `php-mcp/laravel ^3.0.0` |
| Server package | `php-mcp/server dev-main` | `composer.json` |

### 3. Legacy REST Controllers (deprecated)

| Field | Value | Source |
|---|---|---|
| Location | `app/Domain/Api/Controllers/` | 37 controller files |
| Status | Deprecated; new work uses JSON-RPC | CLAUDE.md guidance |

### 4. Event / Filter Dispatch System

| Field | Value | Source |
|---|---|---|
| Dispatcher | `app/Core/Events/EventDispatcher.php` | Source file |
| Name convention | `leantime.domain.{module}.{layer}.{class}.{method}.{eventName}` | Auto-generated from namespace |
| Registration | `register.php` files in domains | `app/Domain/*/register.php` |
| Blade directives | `@dispatchEvent()`, `@dispatchFilter()` | Template system |

### 5. CLI

| Field | Value | Source |
|---|---|---|
| Entry point | `php bin/leantime` | `bin/leantime` |
| Commands dir | `app/Command/` | 17 command classes |
| Examples | `system:update`, `plugin:enable`, `user:add`, `setting:save` | `app/Command/` files |

### 6. CalDAV / CardDAV

| Field | Value | Source |
|---|---|---|
| Library | `sabre/dav` | `composer.json` |

---

## Notable Dependencies

| Package | Purpose | Source |
|---|---|---|
| `prism-php/prism` | AI / LLM integration | `composer.json` |
| `inspector-apm/neuron-ai` | AI agent framework | `composer.json` |
| `qdrant/qdrant-php` | Vector database client | `composer.json` |
| `sabre/dav` | CalDAV / CardDAV server | `composer.json` |
| `stripe/stripe-php` | Payment processing | `composer.json` |
| `laravel/socialite` | OAuth authentication (+ 15 provider packages) | `composer.json` |
| `laravel/sanctum ^4.0` | API token authentication | `composer.json` |
| `php-mcp/laravel ^3.0.0` | MCP (Model Context Protocol) endpoint | `composer.json` |
| `php-mcp/server dev-main` | MCP server implementation | `composer.json` |
| `robmorgan/phinx` | Database migrations | `composer.json` |

---

## License

| Field | Value | Source |
|---|---|---|
| License | **GNU Affero General Public License v3.0** (AGPL-3.0) | `LICENSE` (line 1: "GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007") |

---

## CI / CD

All CI runs on **GitHub Actions**. Workflow files live in `.github/workflows/`.

| Workflow file | Name | Purpose |
|---|---|---|
| `staticAnalysis.yml` | Static Analysis | PHPStan (level 0) |
| `codeStyleAnalysis.yml` | Code Style Analysis | Laravel Pint |
| `unittests.yml` | Unit Tests | Codeception unit tests |
| `acceptancetests.yml` | Acceptance Tests (Selenium) | Codeception acceptance tests (WebDriver + Selenium) |
| `makefile.yml` | Makefile CI | Validates Makefile build targets |
| `release.yml` | Create Release | Builds release tarball, creates GitHub Release on tag push |
| `version-bump.yml` | Version Bump | Automates version bumping |
| `update-latest-tag.yml` | Updated Latest Tag | Moves the `latest` tag to the newest release |

Supporting config:

| File | Purpose | Source |
|---|---|---|
| `.github/release.yml` | Release drafter config | `.github/release.yml` |
| `.github/changelogConfig.yml` | Changelog generation config | `.github/changelogConfig.yml` |
| `.github/FUNDING.yml` | GitHub Sponsors / funding links | `.github/FUNDING.yml` |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Bug report template | `.github/ISSUE_TEMPLATE/bug_report.yml` |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | Feature request template | `.github/ISSUE_TEMPLATE/feature_request.yml` |
