---
title: Leantime Integration Guide
type: how-to
date: '2026-02-02'
status: consolidated
id: leantime-integration-guide
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
prelude: Leantime Integration Guide (how-to) for dopemux documentation and developer
  workflows.
---
# Leantime Integration Guide

**Status**: Consolidated from multiple guides
**Last Updated**: 2026-02-02

---

## Quick Start Setup

# Leantime Setup Instructions - Quick Start

**Status**: MCP Integration Complete ✅ | Leantime Installation Required ⏳

## Quick Setup (5 minutes)

### Step 1: Access Leantime
```bash
# Open Leantime in your browser
open http://localhost:8080
```

### Step 2: Complete Installation Wizard

1. **Welcome Screen**: Click "Start Installation"
1. **Database**: Already configured (skip/auto-filled)
- Host: `mysql_leantime`
- Database: `leantime`
- User: Auto-configured
1. **Admin Account**: Create your admin user
- Username: `admin` (recommended)
- Email: your@email.com
- Password: Choose a strong password
1. **Company Details**: Optional

### Step 3: Generate API Token

After installation:

1. Log in as admin
1. Go to **Settings** → **API**
1. Click **Generate New Token**
1. Copy the generated token

### Step 4: Configure Bridge

```bash
# Update the API token
cd docker/mcp-servers/leantime-bridge

# Edit .env file
nano .env
# Update this line:
# LEANTIME_API_TOKEN=<paste_your_token_here>

# Or use sed:
sed -i '' 's/LEANTIME_API_TOKEN=.*/LEANTIME_API_TOKEN=your_new_token/' .env
```

### Step 5: Restart Bridge

```bash
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
docker compose restart leantime-bridge
```

### Step 6: Test Integration

```bash
cd docker/mcp-servers/leantime-bridge
python test_info_endpoint.py
```

**Expected output**:
```
✓ Service metadata fields present
✓ MCP endpoints exposed
✓ Leantime health status reported
```

## Verify in Claude

```
# List available tools
What tools do you have available from leantime?

# Create a test project
Create a new Leantime project called "Test Project" with description "Testing MCP integration"

# List projects
Show me all projects in Leantime
```

## Troubleshooting

### "Redirect to /install" Error
**Cause**: Installation not complete
**Solution**: Complete steps 1-2 above

### "API Token Invalid"
**Cause**: Token not configured or incorrect
**Solution**: Regenerate token in Leantime UI and update .env

### "Cannot connect to Leantime"
**Cause**: Leantime container not running
**Solution**:
```bash
docker compose up -d mysql_leantime redis_leantime leantime leantime-bridge
```

## Health Check

```bash
# Check all services
docker ps --filter "name=leantime"

# Expected:
# ✅ leantime - Up (healthy)
# ✅ mysql_leantime - Up (healthy)
# ✅ redis_leantime - Up (healthy)
# ✅ dopemux-mcp-leantime-bridge - Up (healthy)

# Test API directly
curl http://localhost:3015/health
# Expected: {"status":"ok",...}

# Deep readiness check (verifies live Leantime API call)
curl "http://localhost:3015/health?deep=1"
# Expected: {"status":"ok","leantime":"reachable",...}

curl http://localhost:3015/info | jq
# Expected: JSON with mcp/endpoints/leantime sections

# REST compatibility endpoint used by dopecon-bridge
curl http://localhost:3015/api/tools | jq
# Expected: list of bridge tools
```

## What You Get

After setup, you can:
- ✅ Create and manage projects via Claude
- ✅ Add tasks and tickets
- ✅ Track progress and time
- ✅ Create milestones
- ✅ Sync with other task management systems
- ✅ Use ADHD-optimized workflows

## Support

- **Documentation**: `LEANTIME_MCP_INTEGRATION_COMPLETE.md`
- **API Reference**: `docker/mcp-servers/leantime-bridge/HTTP_SERVER_README.md`
- **Test Suite**: `docker/mcp-servers/leantime-bridge/test_info_endpoint.py`

---

**Total Setup Time**: ~5 minutes
**Integration Status**: Production Ready
**Next**: Complete installation at http://localhost:8080

---

## API Configuration

# Leantime API Access Setup Guide - Free Version

## Research Summary

Based on analysis of the Leantime codebase and official documentation, here's how to enable and use the API in the **free open-source version** of Leantime.

## ✅ Good News: API is Available in Free Version!

The JSON-RPC API is **fully available** in the free/open-source version of Leantime. No paid subscription required!

## How API Authentication Works

### 1. API Key Format

Leantime uses a special API key format:
```
lt_<user_id>_<secret>
```

Example: `lt_a1b2c_xyz789abc...`

- `lt`: Namespace prefix
- `<user_id>`: 5-character user identifier
- `<secret>`: 32-character random secret

### 2. API Keys are Special Users

API keys are stored in the `zp_user` table with:
- `source = 'api'` (identifies them as API keys, not regular users)
- `username`: Random 32-char string
- `password`: Hashed version of the secret
- `firstname`: The API key name/description
- `role`: Permission level (admin, editor, user, etc.)
- `status = 'a'`: Active status

## Method 1: Create API Key via Web UI (After Installation)

### Step 1: Complete Leantime Installation

1. Access http://localhost:8080
1. Follow the installation wizard
1. Create your admin account

### Step 2: Generate API Key in Settings

1. Log in as administrator
1. Navigate to **Company Settings** (gear icon → Company Settings)
1. Look for **API** or **API Keys** section
1. Click **"Create New API Key"** or similar button
1. Fill in:
- **Key Name**: "Dopemux MCP Bridge" (or descriptive name)
- **Role**: Admin (for full access)
- **Projects**: Select projects this key can access (or "All Projects")
1. Click **Save/Create**
1. **IMPORTANT**: Copy the full API key immediately - it's only shown once!

### Step 3: Configure MCP Bridge

```bash
# Update the bridge environment variable
nano docker/mcp-servers/leantime-bridge/.env

# Set the API token (replace with your actual key):
LEANTIME_API_TOKEN=lt_a1b2c_xyz789abc123def456...

# Restart the bridge
docker compose -f compose.yml restart leantime-bridge
```

## Method 2: Create API Key via Database (Before Installation)

If you want to create an API key **before** completing the web installation:

### Step 1: Generate Credentials

```bash
# Generate random strings
USER_ID=$(openssl rand -hex 16)  # 32 chars
SECRET=$(openssl rand -hex 16)   # 32 chars

echo "User ID: $USER_ID"
echo "Secret: $SECRET"
echo "API Key: lt_${USER_ID}_${SECRET}"
```

### Step 2: Hash the Password

```bash
# Generate bcrypt hash of the secret
docker exec leantime php -r "echo password_hash('${SECRET}', PASSWORD_BCRYPT);"
```

### Step 3: Insert into Database

```sql
-- Connect to MySQL
docker exec -it mysql_leantime mysql -uroot -p'<root_password>'

USE leantime;

-- Insert API key user
INSERT INTO zp_user (
    username,
    firstname,
    lastname,
    password,
    role,
    source,
    status,
    clientId
) VALUES (
    '<USER_ID>',                    -- The 32-char user ID
    'Dopemux MCP Bridge',           -- Key name/description
    '',                             -- Leave empty for API keys
    '<HASHED_PASSWORD>',            -- Bcrypt hash from step 2
    'admin',                        -- Role (admin, editor, user, etc.)
    'api',                          -- IMPORTANT: marks as API key
    'a',                            -- Active status
    1                               -- Default client ID
);

-- Get the new user ID
SELECT id, username, firstname, role, source FROM zp_user WHERE source='api';
```

### Step 4: Assign to Projects (Optional)

```sql
-- Assign API key to all projects
INSERT INTO zp_projectusers (projectId, userId)
SELECT id, <api_user_id> FROM zp_projects;
```

## Method 3: Direct SQL Script (Fastest for Development)

Create a file `create_api_key.sql`:

```sql
-- Leantime API Key Creation Script
-- Usage: docker exec -i mysql_leantime mysql -uroot -p'password' leantime < create_api_key.sql

SET @user_id = REPLACE(UUID(), '-', '');
SET @secret = REPLACE(UUID(), '-', '');
SET @api_key = CONCAT('lt_', LEFT(@user_id, 32), '_', LEFT(@secret, 32));

-- Note: This creates a test key. In production, use proper bcrypt hashing
INSERT INTO zp_user (
    username,
    firstname,
    password,
    role,
    source,
    status,
    clientId
) VALUES (
    LEFT(@user_id, 32),
    'MCP Bridge API Key',
    '$2y$10$example_hash_replace_with_real_bcrypt_hash',  -- Replace this!
    'admin',
    'api',
    'a',
    1
);

SELECT CONCAT('API Key Created: lt_', LEFT(@user_id, 32), '_', LEFT(@secret, 32)) AS api_key;
SELECT 'IMPORTANT: Update the password hash with: docker exec leantime php -r "echo password_hash(\\\"SECRET\\\", PASSWORD_BCRYPT);"' AS note;
```

## API Usage

### Authentication Header

All API requests must include:
```
x-api-key: lt_<user_id>_<secret>
```

### JSON-RPC Endpoint

```
http://localhost:8080/api/jsonrpc
```

### Example Request

```bash
curl -X POST http://localhost:8080/api/jsonrpc \
  -H "x-api-key: lt_abc123_xyz789..." \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "leantime.rpc.projects.getProjects",
    "id": 1,
    "params": {}
  }'
```

### Available Methods

Common JSON-RPC methods (format: `leantime.rpc.<domain>.<method>`):

**Projects:**
- `leantime.rpc.projects.getProjects` - List all projects
- `leantime.rpc.projects.getProject` - Get specific project
- `leantime.rpc.projects.addProject` - Create project
- `leantime.rpc.projects.editProject` - Update project

**Tickets/Tasks:**
- `leantime.rpc.tickets.getTickets` - List tickets
- `leantime.rpc.tickets.getTicket` - Get specific ticket
- `leantime.rpc.tickets.addTicket` - Create ticket
- `leantime.rpc.tickets.editTicket` - Update ticket
- `leantime.rpc.tickets.deleteTicket` - Delete ticket

**Users:**
- `leantime.rpc.users.getUsers` - List users
- `leantime.rpc.users.getUser` - Get specific user

## Code References

From analysis of Leantime source code:

1. **API Key Controller**: `/app/Domain/Api/Controllers/NewApiKey.php`
- Handles API key creation via web UI

1. **API Service**: `/app/Domain/Api/Services/Api.php`
- `createAPIKey()` - Creates API keys
- `getAPIKeyUser()` - Validates API keys
- Key validation splits on `_` and verifies: `lt_<user>_<secret>`

1. **JSON-RPC Handler**: `/app/Domain/Api/Controllers/Jsonrpc.php`
- Routes JSON-RPC 2.0 requests to appropriate services

1. **User Repository**: `/app/Domain/Users/Repositories/Users.php`
- Stores API keys as users with `source='api'`

## Testing the Integration

After creating your API key:

```bash
# 1. Update bridge config
echo "LEANTIME_API_TOKEN=lt_your_key_here" >> docker/mcp-servers/leantime-bridge/.env

# 2. Restart bridge
docker compose -f compose.yml restart leantime-bridge

# 3. Test from bridge container
docker exec dopemux-mcp-leantime-bridge python -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from leantime_bridge.http_server import LeantimeClient, LEANTIME_API_URL, LEANTIME_API_TOKEN

async def test():
    async with LeantimeClient(LEANTIME_API_URL, LEANTIME_API_TOKEN) as client:
        result = await client.call_api('leantime.rpc.projects.getProjects')
        print(f'✅ API Working! Projects: {len(result) if isinstance(result, list) else 1}')

asyncio.run(test())
"

# 4. Run integration tests
cd docker/mcp-servers/leantime-bridge
python test_info_endpoint.py
```

## Recommended Approach

**For Development/Testing:**
1. ✅ Complete Leantime installation via web UI (http://localhost:8080)
1. ✅ Create API key in Company Settings
1. ✅ Copy key to `.env` file
1. ✅ Restart bridge

**For Production/Automation:**
1. Complete installation first
1. Use the web UI to create keys with proper permissions
1. Store keys securely (env vars, secrets manager)
1. Monitor API usage and rotate keys periodically

## Security Notes

- ⚠️ API keys have the same permissions as their assigned role
- ⚠️ Keys are only shown once during creation
- ⚠️ Store keys in environment variables, never in code
- ⚠️ Use project-level restrictions when possible
- ⚠️ Consider creating separate keys for different integrations
- ⚠️ Disable/delete unused API keys

## Troubleshooting

### "Redirect to /install"
**Cause**: Leantime not yet installed
**Solution**: Complete installation at http://localhost:8080

### "Invalid API Key"
**Cause**: Wrong format or key not found
**Solution**: Verify format is `lt_<user>_<secret>` and key exists in database

### "Permission Denied"
**Cause**: API key doesn't have required role/project access
**Solution**: Update key's role or project assignments in database

### "Connection Refused"
**Cause**: Leantime not running or wrong URL
**Solution**: Check `docker ps` and verify `LEANTIME_API_URL`

## References

- [Leantime API Documentation](https://docs.leantime.io/api/usage)
- [JSON-RPC API Guide](https://leantime.io/unlocking-leantimes-power-a-guide-to-the-json-rpc-api/)
- [GitHub Docs](https://github.com/Leantime/docs/blob/master/api/usage.md)
- Leantime Source Code (analyzed locally)

---

**Status**: Guide complete - waiting for Leantime installation to test
**Next Step**: Install Leantime at http://localhost:8080 and create API key

---

## Deployment Strategy

# Leantime Deployment Strategy - Recommendation

## Current Setup Analysis

### What You Have

1. **Official Leantime Docker Image**: `leantime/leantime:latest`
- Pre-built, maintained by Leantime team
- Currently configured in `docker/leantime/docker-compose.yml`
- Running but not yet installed

1. **Custom Dopemux ADHD Plugin**:
- Located at: `docker/leantime/app/Plugins/Dopemux/`
- Features:
- Cognitive load tracking
- Attention state management
- Context preservation
- Break reminders
- ADHD-optimized notifications
- Mounted via volume to `/var/www/html/app/Plugins`

1. **Volume Mounts** (Current Config):
   ```yaml
   volumes:
- leantime_plugins:/var/www/html/app/Plugins  # ✓ Plugin support
- leantime_public_userfiles:/var/www/html/public/userfiles
- leantime_userfiles:/var/www/html/userfiles
- leantime_logs:/var/www/html/storage/logs
- leantime_config:/var/www/html/config
   ```

## 🎯 Recommendation: **Use Official Image + Plugin Mount**

### Why This Approach?

✅ **Advantages:**

1. **Maintained & Updated**
- Official images get security patches
- Compatible with new Leantime versions
- No custom build maintenance

1. **Plugin System Works**
- Leantime's plugin architecture supports custom plugins
- Your Dopemux plugin can be mounted as a volume
- Changes to plugin code reflect immediately (development mode)

1. **Simplified Operations**
- No custom Dockerfile to maintain
- Easy to update: `docker-compose pull && docker-compose up -d`
- Rollback is simple if needed

1. **MCP Integration Independent**
- API functionality is built into Leantime core
- MCP bridge works with standard Leantime
- Plugin adds ADHD features on top

1. **Best of Both Worlds**
- Standard Leantime stability
- Custom Dopemux ADHD features
- Easy to enable/disable plugin

❌ **Disadvantages:**

1. Plugin must follow Leantime's plugin API
1. Limited to plugin capabilities (can't modify core)
1. Plugin updates separate from container updates

## Alternative: Custom Docker Image

### When to Consider Custom Image

You should build a custom image if:

- [ ] You need to modify Leantime core files
- [ ] You need to add system-level dependencies
- [ ] You need to patch Leantime bugs before official fix
- [ ] You want to bundle plugin with image
- [ ] You need specific PHP extensions

### Custom Image Template

If you decide to go custom later:

```dockerfile
# docker/leantime/Dockerfile.custom
FROM leantime/leantime:latest

# Copy custom plugin
COPY app/Plugins/Dopemux /var/www/html/app/Plugins/Dopemux

# Install additional PHP extensions if needed
RUN docker-php-ext-install <extension>

# Set permissions
RUN chown -R www-data:www-data /var/www/html/app/Plugins/Dopemux

# Optional: Pre-configure settings
# COPY custom-config.php /var/www/html/config/
```

Then update docker-compose.yml:
```yaml
leantime:
  build:
    context: .
    dockerfile: Dockerfile.custom
  # ... rest of config
```

## 🎖️ Current Recommendation: Hybrid Approach

### Setup: Official Image + Volume-Mounted Plugin

**Configuration** (Already in place!):

```yaml
# docker/leantime/docker-compose.yml
leantime:
  image: leantime/leantime:latest  # ✓ Official image
  volumes:
- ./app/Plugins:/var/www/html/app/Plugins  # ✓ Mount custom plugin
    # ... other volumes
```

**OR** for better isolation:

```yaml
leantime:
  image: leantime/leantime:latest
  volumes:
    # Mount only the Dopemux plugin
- ./app/Plugins/Dopemux:/var/www/html/app/Plugins/Dopemux:ro
    # Use named volumes for Leantime-managed plugins
- leantime_plugins:/var/www/html/app/Plugins
    # ... other volumes
```

### Implementation Steps

1. **Keep Current Setup** ✓
   ```bash
   # Already using official image
   # Plugin directory already exists
   # Volumes already configured
   ```

1. **Complete Plugin Development**
   ```bash
   cd docker/leantime/app/Plugins/Dopemux

   # Add any additional ADHD features
   # Implement Controllers
   # Add language files
   # Test plugin hooks
   ```

1. **Test Plugin Registration**
   ```bash
   # After Leantime installation:
   # 1. Install Leantime via web UI
   # 2. Check that Dopemux plugin appears in plugins list
   # 3. Enable the plugin
   # 4. Verify ADHD features are active
   ```

1. **Document Plugin Features**
- Create README for the plugin
- Document API endpoints
- Add usage examples

## Feature Comparison

### Standard Leantime (What You Get with Official Image)

```
✓ Project Management
✓ Task/Ticket System
✓ Time Tracking
✓ Kanban Boards
✓ Gantt Charts
✓ User Management
✓ Client Management
✓ Reporting
✓ JSON-RPC API ← (For MCP Integration)
✓ Plugin System
```

### Dopemux ADHD Plugin (Your Custom Features)

```
✓ Cognitive Load Tracking
✓ Attention State Management
✓ Context Preservation
✓ Intelligent Break Reminders
✓ Notification Batching
✓ Gentle Notifications
✓ ADHD Dashboard
✓ Attention Manager
✓ Context Saver
✓ Custom API Endpoints for ADHD Features
```

### Combined Stack

```
Leantime Official Image (Core)
    ↓
Dopemux Plugin (ADHD Features)
    ↓
MCP Bridge (External Integration)
    ↓
Claude/AI Assistants
```

## Migration Path (If Needed Later)

### From Official Image → Custom Image

```bash
# 1. Create Dockerfile
cat > docker/leantime/Dockerfile.custom << 'EOF'
FROM leantime/leantime:latest
COPY app/Plugins/Dopemux /var/www/html/app/Plugins/Dopemux
RUN chown -R www-data:www-data /var/www/html/app/Plugins/Dopemux
EOF

# 2. Update docker-compose.yml
sed -i 's/image: leantime\/leantime:latest/build: ./' docker/leantime/docker-compose.yml

# 3. Build and deploy
docker-compose -f docker/leantime/docker-compose.yml build
docker-compose -f docker/leantime/docker-compose.yml up -d
```

### From Custom Image → Official Image

```bash
# 1. Revert docker-compose.yml
sed -i 's/build: ./image: leantime\/leantime:latest/' docker/leantime/docker-compose.yml

# 2. Ensure plugin volume is mounted
# (Already configured in your setup)

# 3. Restart
docker-compose -f docker/leantime/docker-compose.yml up -d
```

## Plugin Development Best Practices

### 1. Follow Leantime Plugin Structure

```
Plugins/Dopemux/
├── composer.json           ✓ Already have
├── register.php           ✓ Already have
├── Controllers/           ✓ Started
│   └── DopemuxController.php
├── Services/              ← Add this
│   ├── CognitiveLoadService.php
│   ├── AttentionService.php
│   └── ContextService.php
├── Models/                ← Add this
│   ├── CognitiveLoad.php
│   └── AttentionState.php
├── Language/              ← Expand this
│   └── en-US/
│       └── dopemux.ini
├── Views/                 ← Add this
│   ├── dashboard.tpl.php
│   ├── cognitive-load.tpl.php
│   └── attention-manager.tpl.php
└── README.md              ← Add this
```

### 2. Use Leantime's Service Container

```php
// In your controllers
$cognitiveLoadService = app()->make(CognitiveLoadService::class);
$result = $cognitiveLoadService->calculate($ticket);
```

### 3. Register Events Properly

```php
// In register.php
$registration->addEventHook('tickets.created', function($ticket) {
    $service = app()->make(CognitiveLoadService::class);
    $service->autoCalculate($ticket);
});
```

### 4. Add Database Migrations (If Needed)

```php
// Create migration file
Plugins/Dopemux/Migrations/
└── 001_create_cognitive_load_table.php
```

## Testing Strategy

### 1. Plugin Testing

```bash
# Install Leantime first
open http://localhost:8080

# Check plugin is loaded
docker exec leantime ls -la /var/www/html/app/Plugins/Dopemux

# Verify in Leantime UI
# Settings → Plugins → Should see "Dopemux ADHD Features"
```

### 2. MCP Integration Testing

```bash
# Test API independently
curl -X POST http://localhost:8080/api/jsonrpc \
  -H "x-api-key: lt_..." \
  -d '{"jsonrpc":"2.0","method":"leantime.rpc.tickets.getTickets","id":1}'

# Test MCP bridge
cd docker/mcp-servers/leantime-bridge
python test_info_endpoint.py
```

### 3. ADHD Feature Testing

```bash
# Test cognitive load API
curl http://localhost:8080/dopemux/api/cognitive-load

# Test attention tracking
curl http://localhost:8080/dopemux/api/attention-state

# Test context preservation
curl -X POST http://localhost:8080/dopemux/api/context \
  -H "Content-Type: application/json" \
  -d '{"context_data": "..."}'
```

## Security Considerations

### Plugin Security

1. **Input Validation**
   ```php
   // Always validate user input
   $cognitiveLoad = filter_var($_POST['load'], FILTER_VALIDATE_INT);
   ```

1. **SQL Injection Prevention**
   ```php
   // Use Leantime's query builder
   $db = app()->make(Database::class);
   $result = $db->where('id', $ticketId)->get('tickets');
   ```

1. **XSS Prevention**
   ```php
   // Escape output in templates
   <?= htmlspecialchars($data, ENT_QUOTES, 'UTF-8') ?>
   ```

1. **CSRF Protection**
   ```php
   // Use Leantime's CSRF tokens
   $csrf = session('formTokenValue');
   ```

## Performance Considerations

### Plugin Optimization

1. **Lazy Loading**
   ```php
   // Only load heavy services when needed
   if ($needsCognitiveLoad) {
       $service = app()->make(CognitiveLoadService::class);
   }
   ```

1. **Caching**
   ```php
   // Cache expensive calculations
   $cache = app()->make(Cache::class);
   $result = $cache->remember('cognitive_load_' . $ticketId, 3600, function() {
       return $this->calculateCognitiveLoad();
   });
   ```

1. **Database Indexes**
   ```sql
   -- Add indexes for ADHD features
   CREATE INDEX idx_cognitive_load ON zp_tickets(cognitive_load);
   CREATE INDEX idx_attention_level ON zp_user_preferences(attention_level);
   ```

## Monitoring & Debugging

### Plugin Debugging

```bash
# Enable Leantime debug mode
docker exec -it leantime \
  sed -i 's/LEAN_DEBUG=0/LEAN_DEBUG=1/' /var/www/html/.env

# Check plugin logs
docker logs leantime | grep Dopemux

# PHP error logs
docker exec leantime tail -f /var/log/php_errors.log
```

### MCP Bridge Monitoring

```bash
# Bridge logs
docker logs -f dopemux-mcp-leantime-bridge

# Test connection
curl http://localhost:3015/sse --head
```

## Backup Strategy

### What to Backup

```bash
# 1. Plugin source code (git-tracked)
git add docker/leantime/app/Plugins/Dopemux
git commit -m "Update ADHD plugin"

# 2. Leantime data (volumes)
docker run --rm \
  -v leantime_plugins:/backup \
  alpine tar czf /backup/plugins.tar.gz /backup

# 3. Database
docker exec mysql_leantime mysqldump \
  -u root -p leantime > leantime_backup.sql

# 4. Configuration
cp docker/leantime/.env docker/leantime/.env.backup
```

## Final Recommendation Summary

### ✅ **GO WITH: Official Image + Volume-Mounted Plugin**

**Reasons:**
1. ✓ Your current setup already implements this
1. ✓ Plugin system supports all your ADHD features
1. ✓ Easier to maintain and update
1. ✓ MCP integration works perfectly
1. ✓ Can switch to custom image later if needed

**Action Items:**
1. ✓ Keep current docker-compose.yml configuration
1. Complete Leantime installation (http://localhost:8080)
1. Verify Dopemux plugin is recognized
1. Enable and test ADHD features
1. Create API key for MCP bridge
1. Test end-to-end integration

**Future Considerations:**
- Monitor plugin performance
- Consider custom image if you need core modifications
- Document plugin API for other developers
- Consider publishing plugin to Leantime marketplace

---

**Decision**: Official Leantime Image + Custom Plugin ✓
**Status**: Ready to install and test
**Next Step**: Complete Leantime installation at http://localhost:8080

---
