# Leantime Transport & Runbook

> Operational guide for developing, building, testing, deploying, and maintaining Leantime.
> All claims cite actual source files.

---

## Section 1: Development Setup

> Sources: `makefile`, `.dev/docker-compose.yaml`, `.dev/dockerfile`

### Quick Start

```bash
make clean build    # Clean target dir, install deps, build JS/CSS
make run-dev        # Build dev + start Docker Compose
```

### Docker Development Stack

The dev environment uses `.dev/docker-compose.yaml` with `.dev/dockerfile` (PHP 8.2-Apache, not FPM):

| Service | Container | Image | Port | Purpose |
|---------|-----------|-------|------|---------|
| **leantime-dev** | leantime-dev | `.dev/dockerfile` | 5080 (HTTP), 5443 (HTTPS) | App with Xdebug |
| **leantime-db** | leantime-db | mysql:8.4 | 3306 | MySQL database |
| **leantime-redis** | leantime-redis | redis:4.0 | 6379 | Cache/sessions |
| **selenium** | — | selenium/standalone-chromium | 4444, 7900 | Browser testing |

### Development Credentials

| Setting | Value |
|---------|-------|
| DB Host | leantime-db |
| DB User | leantime |
| DB Password | leantime |
| DB Name | leantime |
| DB Port | 3306 |

### Development Dockerfile Details (`.dev/dockerfile`)

- **Base**: `php:8.2-apache`
- **PHP extensions**: gd (with FreeType+JPEG), mysqli, pdo_mysql, mbstring, exif, pcntl, pdo, bcmath, opcache, ldap, zip, redis, xdebug
- **Apache modules**: ssl, rewrite
- **Self-signed SSL**: 4096-bit RSA, auto-generated at build
- **Volumes**: Source code mounted at `/var/www/html`, Xdebug config, error reporting config
- **Extra hosts**: `host.docker.internal:host-gateway` for host access from container

### Test Environment

The test stack extends the dev stack via `.dev/docker-compose.tests.yaml`:
- Separate database: `leantime_test`
- Port: 8002 (HTTP), 44302 (HTTPS)
- Environment: `LEAN_ENV=testing`
- Config from `.dev/test.env`

### Manual Local Development (Without Docker)

```bash
make install-deps-dev    # npm install && composer install
make build-dev           # Build with source maps
# Point web server document root to public/
# Create MySQL database
# Copy config/sample.env to config/.env and configure
# Navigate to <localdomain>/install
```

---

## Section 2: Production Deployment

> Sources: `.docker/Dockerfile`, `.docker/config/`, `.docker/start.sh`, `.docker/docker-compose.yml`

### Production Docker Image

| Setting | Value |
|---------|-------|
| **Base image** | `php:8.3-fpm-alpine` (multi-stage build) |
| **Web server** | nginx (port 8080) |
| **Process manager** | supervisord (PHP-FPM + nginx + scheduler) |
| **Healthcheck** | `curl -f http://localhost:8080` every 30s, 3 retries |
| **Exposed port** | 8080 |
| **Entrypoint** | `tini` → `/start.sh` → supervisord |
| **User** | `www-data` (non-root, configurable PUID/PGID) |

### Multi-Stage Build

**Stage 1 (builder)**: Compiles PHP extensions from source (gd, mysqli, pdo_mysql, bcmath, mbstring, exif, pcntl, opcache, ldap, zip, redis). Supports cross-platform builds (linux/amd64, linux/arm64).

**Stage 2 (production)**: Alpine-based with nginx, supervisor, mysql-client, openssl. Copies compiled extensions from builder. Downloads release tarball from GitHub.

### Supervised Processes (`.docker/config/supervisord.conf`)

| Process | Command | Priority | Auto-restart |
|---------|---------|----------|--------------|
| php-fpm | `php-fpm -F` | 5 | yes |
| nginx | `nginx -g 'daemon off;'` | 10 | yes |
| scheduler | `php /var/www/html/bin/leantime schedule:work` | — | yes |

### nginx Configuration (`.docker/config/nginx.conf`)

- Listens on port 8080
- Document root: `/var/www/html/public`
- PHP-FPM upstream: `127.0.0.1:9000`
- FastCGI read timeout: 300s
- Client max body size: 100M
- Static asset caching: 7 days for `/dist/`
- Gzip compression enabled
- Security headers: X-Frame-Options (DENY), X-XSS-Protection, X-Content-Type-Options, HSTS, CSP, Referrer-Policy

### Docker Secrets Support (`.docker/start.sh`)

The entrypoint reads secrets from files for Docker Swarm / Kubernetes compatibility:

| Secret Variable | Reads From |
|----------------|------------|
| `LEAN_DB_PASSWORD` | `LEAN_DB_PASSWORD_FILE` |
| `LEAN_EMAIL_SMTP_PASSWORD` | `LEAN_EMAIL_SMTP_PASSWORD_FILE` |
| `LEAN_S3_SECRET` | `LEAN_S3_SECRET_FILE` |
| `LEAN_SESSION_PASSWORD` | `LEAN_SESSION_PASSWORD_FILE` |
| `LEAN_REDIS_PASSWORD` | `LEAN_REDIS_PASSWORD_FILE` |
| `LEAN_DB_HOST` | `LEAN_DB_HOST_FILE` |
| `LEAN_DB_DATABASE` | `LEAN_DB_DATABASE_FILE` |
| `LEAN_DB_USER` | `LEAN_DB_USER_FILE` |
| `LEAN_EMAIL_SMTP_USERNAME` | `LEAN_EMAIL_SMTP_USERNAME_FILE` |

### Production Docker Compose (`.docker/docker-compose.yml`)

```yaml
services:
  leantime_db:
    image: mysql:8.4
    # Healthcheck: mysqladmin ping
    # Persistent volume: db_data
    
  leantime:
    image: leantime/leantime:3.4.12
    ports: "${LEAN_PORT:-8080}:8080"
    volumes:
      - public_userfiles:/var/www/html/public/userfiles
      - userfiles:/var/www/html/userfiles
      - plugins:/var/www/html/app/Plugins
      - logs:/var/www/html/storage/logs
    security_opt: [no-new-privileges:true]
    cap_add: [CAP_CHOWN, CAP_SETGID, CAP_SETUID]
```

### Writable Directories (Production)

| Path | Purpose |
|------|---------|
| `/var/www/html/userfiles` | File uploads (local storage) |
| `/var/www/html/public/userfiles` | Public file uploads |
| `/var/www/html/bootstrap/cache` | Framework bootstrap cache |
| `/var/www/html/storage/logs` | Application logs |
| `/var/www/html/storage/framework/cache` | Cache files |
| `/var/www/html/storage/framework/sessions` | Session files |
| `/var/www/html/storage/framework/views` | Compiled Blade views |
| `/var/www/html/app/Plugins` | Installed plugins |

---

## Section 3: Environment Variable Reference

> Source: `config/sample.env`, `app/Core/Configuration/DefaultConfig.php`

### Minimum Required

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_DB_HOST` | `localhost` | Database host |
| `LEAN_DB_USER` | — | Database username |
| `LEAN_DB_PASSWORD` | — | Database password |
| `LEAN_DB_DATABASE` | — | Database name |
| `LEAN_DB_PORT` | `3306` | Database port |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_APP_URL` | — | Base URL (required for subfolder installs) |
| `LEAN_APP_DIR` | — | Base path without trailing slash (e.g., `/leantime`) |
| `LEAN_DEBUG` | `0` | Debug mode (0 or 1) |
| `LEAN_SITENAME` | `Leantime` | Site name |
| `LEAN_LANGUAGE` | `en-US` | Default language |
| `LEAN_DEFAULT_TIMEZONE` | `America/Los_Angeles` | Default timezone |
| `LEAN_DISABLE_LOGIN_FORM` | `false` | Hide login form (for SSO-only setups) |

### Database Connection

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_DB_DEFAULT_CONNECTION` | `mysql` | `mysql` or `pgsql` |
| `LEAN_DB_SCHEMA` | `public` | PostgreSQL schema |
| `LEAN_DB_SSLMODE` | — | SSL: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full` |
| `LEAN_DB_PERSISTENT_CONNECTIONS` | `true` | Connection pooling |
| `LEAN_DB_MAX_CONNECTIONS` | `100` | Max pool size |
| `LEAN_DB_MIN_CONNECTIONS` | `1` | Min pool size |
| `LEAN_DB_CONNECTION_TIMEOUT` | `30` | Timeout (seconds) |
| `LEAN_DB_IDLE_TIMEOUT` | `300` | Idle timeout (seconds) |

### Session & Security

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_SESSION_PASSWORD` | `3evBlq9zdUEuz...` | Session salt — **MUST CHANGE** |
| `LEAN_SESSION_EXPIRATION` | `28800` | Inactivity timeout (seconds = 8 hours) |
| `LEAN_SESSION_SECURE` | `false` | HTTPS-only cookies |
| `LEAN_TRUSTED_PROXIES` | `127.0.0.1,REMOTE_ADDR` | Trusted proxy IPs |

### Look & Feel

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_LOGO_PATH` | `/dist/images/logo.svg` | Logo path |
| `LEAN_PRINT_LOGO_URL` | `/dist/images/logo.png` | Print logo (JPG/PNG) |
| `LEAN_DEFAULT_THEME` | `default` | Theme name |
| `LEAN_PRIMARY_COLOR` | `#006d9f` | Primary color |
| `LEAN_SECONDARY_COLOR` | `#00a886` | Secondary color |

### File Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_USER_FILE_PATH` | `userfiles/` | Local upload path |
| `LEAN_DB_BACKUP_PATH` | `backupdb/` | Backup file path |
| `LEAN_USE_S3` | `false` | Enable S3 storage |
| `LEAN_S3_KEY` | — | S3 access key |
| `LEAN_S3_SECRET` | — | S3 secret key |
| `LEAN_S3_BUCKET` | — | S3 bucket name |
| `LEAN_S3_REGION` | — | S3 region |
| `LEAN_S3_END_POINT` | — | Custom S3-compatible endpoint |
| `LEAN_S3_FOLDER_NAME` | — | Folder prefix in bucket |
| `LEAN_S3_USE_PATH_STYLE_ENDPOINT` | `false` | Path-style URLs |

### Email (SMTP)

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_EMAIL_RETURN` | — | Return/from address |
| `LEAN_EMAIL_USE_SMTP` | `false` | Enable SMTP (vs PHP `mail()`) |
| `LEAN_EMAIL_SMTP_HOSTS` | — | SMTP server hostname |
| `LEAN_EMAIL_SMTP_AUTH` | `true` | Require authentication |
| `LEAN_EMAIL_SMTP_USERNAME` | — | SMTP username |
| `LEAN_EMAIL_SMTP_PASSWORD` | — | SMTP password |
| `LEAN_EMAIL_SMTP_AUTO_TLS` | `true` | Auto-detect TLS |
| `LEAN_EMAIL_SMTP_SECURE` | — | Security: `TLS`, `SSL`, `STARTTLS` |
| `LEAN_EMAIL_SMTP_SSLNOVERIFY` | `false` | Skip cert verification |
| `LEAN_EMAIL_SMTP_PORT` | — | Port (25, 465, 587, 2526) |

### LDAP

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_LDAP_USE_LDAP` | `false` | Enable LDAP |
| `LEAN_LDAP_LDAP_DOMAIN` | — | Domain for login (user@domain) |
| `LEAN_LDAP_LDAP_TYPE` | `OL` | `OL` (OpenLDAP) or `AD` (Active Directory) |
| `LEAN_LDAP_HOST` | — | LDAP server FQDN |
| `LEAN_LDAP_PORT` | `389` | LDAP port |
| `LEAN_LDAP_URI` | — | LDAP URI (alternative to host:port) |
| `LEAN_LDAP_DN` | — | Base DN (e.g., `CN=users,DC=example,DC=com`) |
| `LEAN_LDAP_KEYS` | JSON | Attribute mapping object |
| `LEAN_LDAP_DEFAULT_ROLE_KEY` | `20` | Default role on creation (20=editor) |
| `LEAN_LDAP_GROUP_ASSIGNMENT` | JSON | Group-to-role mappings |

### OpenID Connect (OIDC)

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_OIDC_ENABLE` | `false` | Enable OIDC |
| `LEAN_OIDC_CLIENT_ID` | — | Client ID |
| `LEAN_OIDC_CLIENT_SECRET` | — | Client secret |
| `LEAN_OIDC_PROVIDER_URL` | — | Provider URL |
| `LEAN_OIDC_CREATE_USER` | `false` | Auto-create users |
| `LEAN_OIDC_DEFAULT_ROLE` | `20` | Default role (20=editor) |
| `LEAN_OIDC_AUTH_URL_OVERRIDE` | — | Custom auth endpoint |
| `LEAN_OIDC_TOKEN_URL_OVERRIDE` | — | Custom token endpoint |
| `LEAN_OIDC_JWKS_URL_OVERRIDE` | — | Custom JWKS endpoint |
| `LEAN_OIDC_USERINFO_URL_OVERRIDE` | — | Custom userinfo endpoint |
| `LEAN_OIDC_CERTIFICATE_STRING` | — | RSA cert for validation |
| `LEAN_OIDC_CERTIFICATE_FILE` | — | Cert file path |
| `LEAN_OIDC_SCOPES` | `openid profile email` | Requested scopes |
| `LEAN_OIDC_FIELD_EMAIL` | `email` | Email claim field |
| `LEAN_OIDC_FIELD_FIRSTNAME` | `given_name` | First name claim field |
| `LEAN_OIDC_FIELD_LASTNAME` | `family_name` | Last name claim field |
| `LEAN_OIDC_FIELD_PHONE` | — | Phone claim field |
| `LEAN_OIDC_FIELD_JOBTITLE` | — | Job title claim field |
| `LEAN_OIDC_FIELD_JOBLEVEL` | — | Job level claim field |
| `LEAN_OIDC_FIELD_DEPARTMENT` | — | Department claim field |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_USE_REDIS` | `false` | Enable Redis for cache/sessions |
| `LEAN_REDIS_URL` | — | Redis URL (`tcp://host:port[?auth=pw]`) |
| `LEAN_REDIS_HOST` | — | Redis hostname |
| `LEAN_REDIS_PORT` | `6379` | Redis port |
| `LEAN_REDIS_PASSWORD` | — | Redis password |
| `LEAN_REDIS_SCHEME` | — | Connection scheme |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_RATELIMIT_GENERAL` | `1000` | General requests/min |
| `LEAN_RATELIMIT_API` | `10` | API requests/min |
| `LEAN_RATELIMIT_AUTH` | `20` | Auth requests/min |

### Logging & Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_LOG_PATH` | `storage/logs/error.log` | Log file path |
| `LEAN_LOG_CHANNELS` | `single,syslog,sentry` | Comma-separated channels |
| `LEAN_SENTRY_LARAVEL_DSN` | — | Sentry DSN for error tracking |

### Miscellaneous

| Variable | Default | Description |
|----------|---------|-------------|
| `LEAN_NEWS_ENABLED` | `true` | Set `false` for airgapped environments |

---

## Section 4: Build Commands

> Source: `makefile`

| Command | What It Does |
|---------|-------------|
| `make install-deps-dev` | `npm install && composer install` (with dev packages) |
| `make install-deps` | `npm install && composer install --no-dev --optimize-autoloader` |
| `make build-dev` | Install dev deps → clear cache → `npx mix` → generate blocklist |
| `make build` | Install prod deps → clear cache → `npx mix --production` → generate blocklist |
| `make clean` | `rm -rf ./target/leantime` |
| `make clear-cache` | Remove files from `bootstrap/cache`, `storage/framework/cache`, `sessions`, `views` |
| `make package` | Clean → build → copy to `target/leantime/` → create `.zip` and `.tar.gz` archives |
| `make run-dev` | Build dev → `docker compose up --detach --build` (full dev stack) |
| `make get-version` | Echo the `VERSION` variable from makefile |
| `make gendocs` | Clone docs repo, generate PHPDoc, extract hooks |
| `make pushdocs` | Create PR in docs repo with generated documentation |
| `make update-carbon-macros` | Generate Carbon date macro documentation |

---

## Section 5: Test Commands

> Sources: `makefile`, `.dev/docker-compose.tests.yaml`

### Static Analysis & Code Style

| Command | Tool | Description |
|---------|------|-------------|
| `make phpstan` | PHPStan (level 0) | Static type analysis with 2G memory limit. Config: `.phpstan/phpstan.neon` |
| `make test-code-style` | Laravel Pint | Check code style (dry run). Config: `.pint/pint.json` |
| `make fix-code-style` | Laravel Pint | Auto-fix code style issues |
| `make codesniffer` | PHPCS | Code standards check (1G memory) |
| `make codesniffer-fix` | PHPCBF | Auto-fix PHPCS issues |

### Test Execution (Docker-based)

| Command | Description |
|---------|-------------|
| `make unit-test` | Build dev → start Docker stack → run `codecept run Unit` |
| `make acceptance-test` | Build dev → start Docker stack → run `codecept run Acceptance` |
| `make api-test` | Build dev → start Docker stack → run `codecept run Api` |
| `make acceptance-test-ci` | Same as acceptance-test (CI variant) |

### Running Specific Test Groups

```bash
# Inside Docker container:
docker compose --file .dev/docker-compose.yaml \
  --file .dev/docker-compose.tests.yaml \
  exec leantime-dev php vendor/bin/codecept run -g <group> --steps
```

Available test groups: `api`, `timesheet`, `login`, `ticket`, `user`

### Test Framework

- **Framework**: Codeception v5.1 (wraps PHPUnit)
- **Unit tests**: `tests/Unit/` — extend Laravel `TestCase`
- **Acceptance tests**: `tests/Acceptance/` — Cest format with WebDriver + Selenium (Chromium)
- **Configuration**: `codeception.yml`

---

## Section 6: Migration Commands

> Sources: `app/Command/MigrateCommand.php`, `app/Domain/Install/Services/Install.php`, `app/Domain/Install/Services/SchemaBuilder.php`

### Database Migration Command

```bash
php bin/leantime db:migrate [--email=EMAIL] [--password=PASS] [--company-name=NAME] [--first-name=FIRST] [--last-name=LAST]
```

**Aliases**: `db:install`, `db:update`

### How Migrations Work

Leantime uses a **custom migration system**, not Laravel's standard migrations:

1. **Fresh install** (`setupDB()`):
   - `SchemaBuilder` creates all 30 tables programmatically via Laravel Blueprint
   - Creates initial admin user with provided credentials
   - Sets installation version in `zp_settings`

2. **Updates** (`updateDB()`):
   - Reads current version from `zp_settings` key `version.mysql_version`
   - Finds all pending `update_sql_{VERSION}()` methods in `Install.php`
   - Executes each sequentially in version order
   - Version format: `{MAJOR}{MINOR}{PATCH}{REVISION}` (e.g., 20111 = v2.0.11.1)
   - Clears settings cache on completion

3. **No rollback support**: Migrations are forward-only. No down/rollback methods exist.

### Database Backup Before Migration

The `db:migrate` command does NOT automatically back up. Use `db:backup` manually before upgrading. The `system:update` command does auto-backup (skippable with `--skipDbBackup`).

---

## Section 7: CLI Command Reference

> Source: `app/Command/*.php` (17 files, 16 commands + 1 base class)

All commands are invoked via: `php bin/leantime <command>`

### Database Commands

| Command | Description |
|---------|-------------|
| `db:migrate` | Run pending database migrations. Aliases: `db:install`, `db:update`. Options: `--email`, `--password`, `--company-name`, `--first-name`, `--last-name` |
| `db:backup` | Back up database using `mysqldump`. Output to configured backup path (`LEAN_DB_BACKUP_PATH`) |

### System Commands

| Command | Description |
|---------|-------------|
| `system:update` | Update Leantime to latest version from GitHub. Downloads release, applies update, clears cache, manages plugins. Option: `--skipDbBackup` |
| `cache:clearAll` | Clear all caches (views, bootstrap, language files) |
| `language:clear` | Clear cached language files from installation cache |
| `setting:save` | Save/create a setting. Options: `--key` (required), `--value` (required) |

### User Commands

| Command | Description |
|---------|-------------|
| `user:add` | Add a new user. Options: `--email` (required), `--password` (required), `--role` (required), `--client-id`, `--first-name`, `--last-name`, `--phone` |

### Plugin Commands

| Command | Description |
|---------|-------------|
| `plugin:list` | List all plugins with filtering. Options: `--order-by`, `--installed`, `--enabled` |
| `plugin:enable` | Enable a plugin. Argument: plugin name |
| `plugin:disable` | Disable a plugin. Argument: plugin name |
| `plugin:install` | Install a plugin from the marketplace. Argument: plugin name |
| `plugin:remove` | Remove an installed plugin. Argument: plugin name |

### Email Commands

| Command | Description |
|---------|-------------|
| `email:testemail` | Send a test email to verify mail configuration. Option: `--address` (required) |

### File Commands

| Command | Description |
|---------|-------------|
| `files:cleanup` | Clean up orphaned files not referenced in the database. Processes local, public, and S3 storage. Option: `--dry-run` |

### Development/Diagnostic Commands

| Command | Description |
|---------|-------------|
| `event:check-listeners` | Validate event listener paths against available events. Options: `--debug`, `--clear-cache` |
| `translations:check-unused` | Scan codebase for unused translation strings. Options: `--debug`, `--export=FILE`, `--exclude=DIRS` |

### Built-in Laravel Commands

Standard Laravel artisan commands are also available (e.g., `schedule:run`, `schedule:work`, `queue:work`, etc.).

---

## Section 8: Backup & Reset

> Sources: `app/Command/BackupDbCommand.php`, `app/Core/Configuration/DefaultConfig.php`

### Database Backup

```bash
php bin/leantime db:backup
```

- Uses `mysqldump` to create a SQL dump file
- Output location: configurable via `LEAN_DB_BACKUP_PATH` (default: `userfiles/`)
- File naming: dated SQL file (e.g., `backup-2024-01-15.sql`)
- **No automated backup schedule** — must be run manually or via external cron

### File Backup

No built-in file backup command. Back up these directories manually:

| Path | Contents |
|------|----------|
| `userfiles/` | Uploaded files (local storage) |
| `public/userfiles/` | Public uploaded files |
| `app/Plugins/` | Installed plugins |
| `config/.env` | Environment configuration |
| `storage/logs/` | Application logs |

### Reset / Clean State

```bash
php bin/leantime cache:clearAll    # Clear all framework caches
php bin/leantime language:clear    # Clear language cache
make clear-cache                   # Clear cache files via makefile
```

For a full reset, drop and recreate the database, then run `php bin/leantime db:migrate` with initial admin credentials.

---

## Section 9: Cron & Background Jobs

> Sources: `app/Domain/Queue/register.php`, `app/Domain/Reports/register.php`, `app/Domain/Plugins/register.php`, `.docker/config/supervisord.conf`, `app/Domain/Cron/Services/Cron.php`

### Scheduled Jobs

All jobs register via event listeners on `leantime.core.console.consolekernel.schedule.cron`:

| Job Name | Domain | Frequency | Purpose |
|----------|--------|-----------|---------|
| `queue:emails` | Queue | Every minute | Process email notification queue |
| `queue:httprequests` | Queue | Every 5 minutes | Process outgoing HTTP request queue |
| `queue:default` | Queue | Every 5 minutes | Process default job queue |
| `reports:telemetry` | Reports | Daily | Send anonymous telemetry data |
| `reports:dailyIngestion` | Reports | Daily | Daily report/stats ingestion |
| `plugins:checkLicense` | Plugins | Daily | Validate marketplace plugin licenses; disables plugins exceeding user count |

### Running the Scheduler

**Production (Docker)**: The scheduler runs automatically via supervisord:
```
# .docker/config/supervisord.conf
[program:scheduler]
command=php /var/www/html/bin/leantime schedule:work
```

**Manual/Non-Docker**: Add to system crontab:
```bash
* * * * * cd /path/to/leantime && php bin/leantime schedule:run >> /dev/null 2>&1
```

**Poor Man's Cron**: When `LEAN_POOR_MANS_CRON=true` (default), the cron is triggered on web requests via `app/Domain/Cron/Controllers/Run.php` which calls `schedule:run`. The cron execution timer is 60 seconds (`$cronExecTimer` in `app/Domain/Cron/Services/Cron.php`).

### Queue Architecture

The custom queue system (separate from Laravel's queue system) uses the `zp_queue` table:

- **Workers**: Defined in `app/Domain/Queue/Workers/Workers.php` — `EMAILS`, `HTTPREQUESTS`, `DEFAULT`
- **Processing**: `app/Domain/Queue/Services/Queue::processQueue()` retrieves and processes messages by worker type
- **Deduplication**: `msghash` primary key prevents duplicate messages
- **No distributed locking**: Queue workers process independently — not safe for multi-instance deployments without external coordination

### Laravel Job Queue

The standard Laravel job queue (`zp_jobs` table) is also configured:

| Setting | Value |
|---------|-------|
| Default connection | `database` (configurable via `QUEUE_CONNECTION`) |
| Jobs table | `zp_jobs` |
| Retry after | 90 seconds |
| Redis support | Available via `LEAN_USE_REDIS` |
