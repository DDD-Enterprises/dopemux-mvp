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
2. Follow the installation wizard
3. Create your admin account

### Step 2: Generate API Key in Settings

1. Log in as administrator
2. Navigate to **Company Settings** (gear icon → Company Settings)
3. Look for **API** or **API Keys** section
4. Click **"Create New API Key"** or similar button
5. Fill in:
   - **Key Name**: "Dopemux MCP Bridge" (or descriptive name)
   - **Role**: Admin (for full access)
   - **Projects**: Select projects this key can access (or "All Projects")
6. Click **Save/Create**
7. **IMPORTANT**: Copy the full API key immediately - it's only shown once!

### Step 3: Configure MCP Bridge

```bash
# Update the bridge environment variable
nano docker/mcp-servers/leantime-bridge/.env

# Set the API token (replace with your actual key):
LEANTIME_API_TOKEN=lt_a1b2c_xyz789abc123def456...

# Restart the bridge
docker-compose -f docker/mcp-servers/docker-compose.yml restart leantime-bridge
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
   
2. **API Service**: `/app/Domain/Api/Services/Api.php`
   - `createAPIKey()` - Creates API keys
   - `getAPIKeyUser()` - Validates API keys
   - Key validation splits on `_` and verifies: `lt_<user>_<secret>`

3. **JSON-RPC Handler**: `/app/Domain/Api/Controllers/Jsonrpc.php`
   - Routes JSON-RPC 2.0 requests to appropriate services
   
4. **User Repository**: `/app/Domain/Users/Repositories/Users.php`
   - Stores API keys as users with `source='api'`

## Testing the Integration

After creating your API key:

```bash
# 1. Update bridge config
echo "LEANTIME_API_TOKEN=lt_your_key_here" >> docker/mcp-servers/leantime-bridge/.env

# 2. Restart bridge
docker-compose -f docker/mcp-servers/docker-compose.yml restart leantime-bridge

# 3. Test from bridge container
docker exec mcp-leantime-bridge python -c "
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
python test_http_server.py
```

## Recommended Approach

**For Development/Testing:**
1. ✅ Complete Leantime installation via web UI (http://localhost:8080)
2. ✅ Create API key in Company Settings
3. ✅ Copy key to `.env` file
4. ✅ Restart bridge

**For Production/Automation:**
1. Complete installation first
2. Use the web UI to create keys with proper permissions
3. Store keys securely (env vars, secrets manager)
4. Monitor API usage and rotate keys periodically

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
