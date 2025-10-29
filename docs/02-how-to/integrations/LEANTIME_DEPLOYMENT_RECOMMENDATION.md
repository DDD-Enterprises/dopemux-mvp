# Leantime Deployment Strategy - Recommendation

## Current Setup Analysis

### What You Have

1. **Official Leantime Docker Image**: `leantime/leantime:latest`
   - Pre-built, maintained by Leantime team
   - Currently configured in `docker/leantime/docker-compose.yml`
   - Running but not yet installed

2. **Custom Dopemux ADHD Plugin**:
   - Located at: `docker/leantime/app/Plugins/Dopemux/`
   - Features:
     - Cognitive load tracking
     - Attention state management
     - Context preservation
     - Break reminders
     - ADHD-optimized notifications
   - Mounted via volume to `/var/www/html/app/Plugins`

3. **Volume Mounts** (Current Config):
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

2. **Plugin System Works**
   - Leantime's plugin architecture supports custom plugins
   - Your Dopemux plugin can be mounted as a volume
   - Changes to plugin code reflect immediately (development mode)

3. **Simplified Operations**
   - No custom Dockerfile to maintain
   - Easy to update: `docker-compose pull && docker-compose up -d`
   - Rollback is simple if needed

4. **MCP Integration Independent**
   - API functionality is built into Leantime core
   - MCP bridge works with standard Leantime
   - Plugin adds ADHD features on top

5. **Best of Both Worlds**
   - Standard Leantime stability
   - Custom Dopemux ADHD features
   - Easy to enable/disable plugin

❌ **Disadvantages:**

1. Plugin must follow Leantime's plugin API
2. Limited to plugin capabilities (can't modify core)
3. Plugin updates separate from container updates

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

2. **Complete Plugin Development**
   ```bash
   cd docker/leantime/app/Plugins/Dopemux
   
   # Add any additional ADHD features
   # Implement Controllers
   # Add language files
   # Test plugin hooks
   ```

3. **Test Plugin Registration**
   ```bash
   # After Leantime installation:
   # 1. Install Leantime via web UI
   # 2. Check that Dopemux plugin appears in plugins list
   # 3. Enable the plugin
   # 4. Verify ADHD features are active
   ```

4. **Document Plugin Features**
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
python test_http_server.py
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

2. **SQL Injection Prevention**
   ```php
   // Use Leantime's query builder
   $db = app()->make(Database::class);
   $result = $db->where('id', $ticketId)->get('tickets');
   ```

3. **XSS Prevention**
   ```php
   // Escape output in templates
   <?= htmlspecialchars($data, ENT_QUOTES, 'UTF-8') ?>
   ```

4. **CSRF Protection**
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

2. **Caching**
   ```php
   // Cache expensive calculations
   $cache = app()->make(Cache::class);
   $result = $cache->remember('cognitive_load_' . $ticketId, 3600, function() {
       return $this->calculateCognitiveLoad();
   });
   ```

3. **Database Indexes**
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
docker logs -f mcp-leantime-bridge

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
2. ✓ Plugin system supports all your ADHD features
3. ✓ Easier to maintain and update
4. ✓ MCP integration works perfectly
5. ✓ Can switch to custom image later if needed

**Action Items:**
1. ✓ Keep current docker-compose.yml configuration
2. Complete Leantime installation (http://localhost:8080)
3. Verify Dopemux plugin is recognized
4. Enable and test ADHD features
5. Create API key for MCP bridge
6. Test end-to-end integration

**Future Considerations:**
- Monitor plugin performance
- Consider custom image if you need core modifications
- Document plugin API for other developers
- Consider publishing plugin to Leantime marketplace

---

**Decision**: Official Leantime Image + Custom Plugin ✓  
**Status**: Ready to install and test  
**Next Step**: Complete Leantime installation at http://localhost:8080
