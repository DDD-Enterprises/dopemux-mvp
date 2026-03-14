# Leantime Truth Pack — Command Log

## Session Info
- Date: 2026-03-09
- Analyzed ref: 555803d3da0f81ba232d5f38fc11268fdf317511
- Branch: master
- Latest tag: v3.7.1

## Commands Executed

### Git State
```
git log -1 --format="%H %D"
git describe --tags --always
git remote -v
git tag --sort=-creatordate | head -10
git log --oneline -5
```

### Directory Surveys
```
ls app/Domain/
find app/Domain -name "*.php" -path "*/Controllers/*" | wc -l
find app/Domain -name "*.php" -path "*/Services/*" | wc -l
find app/Domain -name "*.php" -path "*/Repositories/*" | wc -l
find app/Domain -name "*.php" -path "*/Models/*" | wc -l
find app/Domain -name "*.php" -path "*/Hxcontrollers/*" | wc -l
find app/Domain -name "routes.php"
find app/Domain -name "register.php"
find app/Domain/Api -name "*.php"
find app/Domain -name "*.php" -path "*/Models/*" -exec basename {} .php \;
find app -name "*.php" -path "*/Command/*" -o -name "*.php" -path "*/Commands/*"
find database -name "*.php" -o -name "*.sql"
find . -name "mcp*.php" -o -name "mcp*.json" -o -name "*mcp*" (excluding .git, vendor, node_modules)
```

### File Reads (via sub-agents)
- All 48 service class files surveyed for class names and public methods
- All 21 model files surveyed for properties
- app/Domain/Api/Controllers/Jsonrpc.php — full read for RPC routing logic
- app/Domain/Install/Services/SchemaBuilder.php — full read for database schema (30 tables)
- app/Core/Http/HttpKernel.php — full read for middleware stack
- app/Core/Events/EventDispatcher.php — full read for event system
- app/Domain/Auth/Models/Roles.php — role definitions
- app/Domain/Tickets/Repositories/Tickets.php — status/type/priority definitions
- app/Domain/Projects/Repositories/Projects.php — project state definitions
- app/Domain/Goalcanvas/Repositories/Goalcanvas.php — goal status definitions
- config/sample.env — all environment variables
- composer.json — full dependency list
- package.json — frontend dependencies
- All 8 register.php files — event registrations
- All Hxcontroller files — $view properties
- All Htmx enum files
- app/Core/Configuration/ — all config files
- .dev/ — Docker configuration

### Grep Searches
```
grep -r "php-mcp" composer.json
grep -r "class.*Controller" app/Domain/Api/Controllers/Jsonrpc.php
grep -n "rpc|jsonrpc|method|dispatch" app/Domain/Api/Controllers/Jsonrpc.php
```
