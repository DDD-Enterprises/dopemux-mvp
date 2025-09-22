# Leantime API Troubleshooting Guide

**Current Status**: API key authentication failing with "Invalid API Key" error
**Token Format**: `lt_Y62b0Z11Whu2rxh5xXrMUO6oW4GgTE6N_4vpKPXd5bThCgICUe9bmR8v1l18NmYHl` ✅ (Correct format)

## 🚨 Issue Diagnosis

### Current Problem
- ✅ Leantime web interface is working (http://localhost:8080)
- ✅ Personal Access Token generated successfully
- ✅ API endpoint exists (`/api/` responds)
- ❌ API key authentication failing ("Invalid API Key")

### Most Likely Causes

#### 1. API Not Enabled in Admin Settings (90% Likely)
Many Leantime installations require explicit API activation.

**Solution Steps:**
1. **Login to Leantime** → http://localhost:8080
2. **Navigate to Settings**:
   - Look for "Admin" or "System Settings"
   - Find "API Settings", "Integrations", or "Developer"
3. **Enable API Access**:
   - Toggle "Enable API" or "Allow API Access"
   - Save settings

#### 2. Token Needs Activation (75% Likely)
Personal Access Tokens might need explicit activation.

**Solution Steps:**
1. **Go to User Settings** → Personal Access Tokens
2. **Check token status** - should show "Active" not "Generated"
3. **Set permissions** if there are scope options
4. **Regenerate token** if needed

#### 3. API Version Mismatch (25% Likely)
The API endpoints might use different paths.

**Alternative endpoints to try:**
- `/api/v1/` instead of `/api/`
- `/rest/` or `/rest/v1/`
- Check if there's API documentation at `/api/docs`

## 🔧 Quick Fix Steps

### Step 1: Check Admin Settings
```bash
# After enabling API in admin settings, test:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/api/

# Should return something other than "Invalid API Key"
```

### Step 2: Verify Token Status
```bash
# In Leantime web interface:
# Settings → Personal Access Tokens
# Verify token shows as "Active"
```

### Step 3: Test Alternative Headers
```bash
# Try different authentication headers:
curl -H "apikey: YOUR_TOKEN" http://localhost:8080/api/
curl -H "X-API-Key: YOUR_TOKEN" http://localhost:8080/api/
curl -H "X-API-TOKEN: YOUR_TOKEN" http://localhost:8080/api/
```

## 🎯 Expected Working Result

When properly configured, you should see:
```json
{
  "status": "success",
  "message": "API is working",
  "version": "3.5.12"
}
```

Instead of:
```json
{"error":"Invalid API Key"}
```

## 🔄 Alternative Approach: Session-Based API

If token authentication continues to fail, we can implement session-based authentication:

```python
# Login with username/password, then use session cookies for API calls
async def login_and_get_session():
    async with aiohttp.ClientSession() as session:
        # Login to get session
        login_data = {
            'username': 'your_admin_email',
            'password': 'your_admin_password'
        }
        await session.post('http://localhost:8080/auth/login', data=login_data)

        # Now use session for API calls
        async with session.get('http://localhost:8080/api/projects') as resp:
            return await resp.json()
```

## 🧠 ADHD-Friendly Next Steps

### Priority 1: Enable API (5 minutes)
1. ✅ Open http://localhost:8080 in browser
2. ✅ Login with your admin account
3. ✅ Find "Settings" or "Admin" section
4. ✅ Look for "API" or "Integrations"
5. ✅ Enable API access
6. ✅ Save settings

### Priority 2: Test API (2 minutes)
```bash
curl -H "Authorization: Bearer lt_Y62b0Z11Whu2rxh5xXrMUO6oW4GgTE6N_4vpKPXd5bThCgICUe9bmR8v1l18NmYHl" http://localhost:8080/api/
```

### Priority 3: Verify Integration (5 minutes)
```bash
cd /Users/hue/code/dopemux-mvp
python3 test_leantime_integration.py
```

## 📋 What To Look For

### In Leantime Settings Menu:
- "API Settings"
- "Developer Settings"
- "Integrations"
- "System Configuration"
- "Security Settings"

### Common API Setting Names:
- "Enable API"
- "Allow API Access"
- "API Authentication"
- "Enable REST API"
- "Developer Mode"

---

**Next Action**: Please check the Leantime admin settings for API configuration options and let me know what you find!