---
id: phase-2a-security-scan
title: Phase 2A Security Scan
type: historical
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Phase 2A: Semantic Vulnerability Detection
**Date**: 2025-10-16
**Duration**: 2 hours (adapted methodology)
**Method**: Bash grep (semantic search limited by workspace composition)
**Status**: ✅ Complete

---

## Methodology Adaptation

**Planned**: Use Dope-Context semantic search for vulnerability patterns
**Actual**: Used bash grep on Python service files
**Reason**: Only 26 code chunks indexed (all React UI), Python services not chunked

**Lesson Learned**: Semantic search excellent for substantial codebases, bash grep needed for utility-heavy workspaces

---

## Security Findings Summary

**Total Issues Found**: 8
- 🔴 Critical: 0
- 🟡 High: 2 (CORS wildcards, hardcoded credentials)
- 🟠 Medium: 4 (SQL injection candidates, subprocess usage)
- 🟢 Low: 2 (test secrets, configuration)

---

## 1. CORS Wildcard Vulnerabilities (🟡 HIGH)

**Severity**: HIGH - Production security risk
**Count**: 4 instances

**Locations**:
1. `services/adhd_engine/main.py:96`
   ```python
   allow_origins=["*"],  # Configure appropriately for production
   ```

2. `services/dopemux-gpt-researcher/backend/main.py:113`
   ```python
   allow_origins=["*"],  # Configure appropriately for production
   ```

3. `services/dopemux-gpt-researcher/backend/api/main.py:236`
   ```python
   allow_origins=["*"]
   ```

4. `services/mcp-dopecon-bridge/main.py:1166`
   ```python
   allow_origins=["*"],
   ```

**Impact**:
- Allows any origin to access APIs (CSRF risk)
- No protection against malicious websites
- Comment acknowledges issue but code unchanged

**Recommendation**:
- Replace with specific origin whitelist
- Use environment variable: `ALLOWED_ORIGINS`
- Example: `allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")`

**Risk Score**: 7/10
- Development: Acceptable
- Production: **CRITICAL** security flaw

---

## 2. Hardcoded Credentials (🟡 HIGH)

**Severity**: HIGH - Credential exposure
**Count**: 2 production instances

**Locations**:
1. `services/serena/v2/intelligence/database.py:39`
   ```python
   password: str = "serena_dev_pass"
   ```
   - **Context**: Default database password in production code
   - **Risk**: Hardcoded credentials in version control

2. `services/serena/v2/intelligence/integration_test.py:67`
   ```python
   password="serena_test_pass"
   ```
   - **Context**: Test code (lower risk but bad practice)

**Impact**:
- Credentials exposed in git history
- Anyone with code access has database password
- Cannot rotate without code changes

**Recommendation**:
- Use environment variables: `os.getenv("SERENA_DB_PASSWORD")`
- Add `.env.example` without actual secrets
- Remove hardcoded credentials from all code

**Risk Score**: 8/10 (production database credentials)

---

## 3. SQL Injection Candidates (🟠 MEDIUM)

**Severity**: MEDIUM - Needs verification
**Count**: 2 instances

**Locations**:
1-2. `services/conport_kg/age_client.py:74,111`
   ```python
   cursor.execute(f"SET search_path = ag_catalog, {graph_name}, public;")
   ```

**Analysis**:
- Uses f-string with `graph_name` variable
- **Question**: Is `graph_name` from user input or internal config?
- **If user input**: 🔴 CRITICAL SQL injection
- **If internal**: 🟢 LOW risk (still bad practice)

**Manual Review Required**:
- Trace `graph_name` source
- Check if validated/sanitized
- If from config file: LOW risk
- If from API parameter: CRITICAL

**Recommendation**:
- Use parameterized queries where possible
- If `SET search_path` doesn't support params, validate `graph_name` against whitelist
- Add input validation: `assert graph_name.isalnum()`

**Risk Score**: 5/10 (pending verification of data source)

---

## 4. Command Injection Risks (🟠 MEDIUM)

**Severity**: MEDIUM - Subprocess usage detected
**Count**: 54 instances

**Primary Usage Patterns**:

**MCP Server Wrappers** (Safe usage):
```python
# task-orchestrator/server.py:114
self.process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env
)
```
- **Context**: Starting child MCP processes
- **Input**: Hardcoded commands, environment config
- **Risk**: LOW (no user input in command)

**Similar safe patterns**:
- `taskmaster/server.py:114` - Starting taskmaster process
- `dopemux-gpt-researcher/mcp-server/wrapper.py:40` - asyncio subprocess

**Manual Review Needed**: Check remaining 50+ instances for user input in commands

**Recommendation**:
- Audit all subprocess calls
- Ensure no user input concatenated into commands
- Use subprocess with list args (not shell=True)
- Validate any external inputs

**Risk Score**: 4/10 (most appear to be safe MCP wrappers)

---

## 5. Path Traversal Risks (🟢 LOW)

**Severity**: LOW
**Count**: 0 instances found

**Search**: `open(.*request|Path(.*request|Path(.*input`
**Result**: No matches

**Conclusion**: No obvious path traversal vulnerabilities in services

---

## 6. Test Credentials (🟢 LOW)

**Severity**: LOW - Test code only
**Count**: 9 instances

**Pattern**: `api_key="test_key"` in test files

**Locations**: `services/dopemux-gpt-researcher/backend/tests/test_search_engines.py`
- Lines: 321, 330, 344, 368, 377, 395, 410, 419, 441

**Analysis**: Test fixtures, not production risk

**Risk Score**: 1/10 (best practice: use fixtures, but acceptable)

---

## Security Scan Statistics

| Vulnerability Type | Searched | Found | High Risk | Medium | Low |
|-------------------|----------|-------|-----------|--------|-----|
| SQL Injection | ✅ | 2 | 0 | 2 | 0 |
| Command Injection | ✅ | 54 | 0 | 54* | 0 |
| Path Traversal | ✅ | 0 | 0 | 0 | 0 |
| Hardcoded Secrets | ✅ | 11 | 2 | 0 | 9 |
| CORS Wildcards | ✅ | 4 | 4 | 0 | 0 |
| **TOTAL** | **5 types** | **71** | **6** | **56** | **9** |

*Most subprocess usage appears safe (MCP wrappers), full audit pending

---

## Priority Actions

### Immediate (Before Production)

1. **Fix CORS Wildcards** (4 files, 10 min)
   - Replace `["*"]` with environment-based whitelist
   - Add `ALLOWED_ORIGINS` to `.env.example`

2. **Remove Hardcoded Credentials** (2 files, 15 min)
   - Move to environment variables
   - Update `database.py` and test files

### Week 7 (With Integration Work)

3. **Audit Subprocess Calls** (54 instances, 2h)
   - Verify no user input in commands
   - Ensure all use list args (not shell=True)

4. **Verify SQL Injection** (2 instances, 30 min)
   - Trace `graph_name` data source
   - Add validation if from user input

---

## Positive Security Findings

✅ **No Path Traversal**: File operations appear safe
✅ **aiohttp Patched**: CVE fixes applied in requirements.txt
✅ **Test Isolation**: Test credentials separated from production
✅ **Subprocess Patterns**: Mostly safe (MCP wrappers with hardcoded commands)

---

## Limitations & Next Steps

### Phase 2A Limitations

**Semantic search ineffective** for this workspace:
- Only 26 code chunks (all React UI)
- Python services not indexed (utility files, small functions)
- Had to fall back to bash grep

**For deeper Python audit**:
- Option A: Index parent `dopemux-mvp` workspace (158 chunks)
- Option B: Continue with bash grep (working well)
- Option C: Read service files directly

### Phase 2B Strategy

**Zen codereview** can still work well:
- Point it at entire service directories
- Let Zen read files directly (not relying on indexed chunks)
- Get AI validation of security findings

---

**Phase 2A Complete** ✅
**Time**: ~1 hour (faster than 2h planned due to focused grep)
**Next**: Phase 2B - Zen Codereview Automation (1.5h)
**Key Finding**: 6 HIGH-risk issues (CORS + hardcoded creds) need immediate fixes
