List tasks from TaskMaster with token-efficient defaults.

**Token-Optimized Usage:**
- Default: `status=pending withSubtasks=false` (recommended)
- If more needed: `status=pending,in-progress limit=10`
- Full context only when explicitly requested

Use TaskMaster get_tasks with smart filtering:

1. **Default Efficient Query** (saves ~5k tokens vs unlimited):
   ```
   mcp__task-master-ai__get_tasks:
   - projectRoot: /Users/hue/code/Dopemux-ChatRipperXXX
   - status: pending
   - withSubtasks: false
   ```

2. **Extended Query** (when you need more context):
   ```
   mcp__task-master-ai__get_tasks:
   - projectRoot: /Users/hue/code/Dopemux-ChatRipperXXX  
   - status: pending,in-progress
   - withSubtasks: false
   - limit: 10
   ```

3. **Full Context** (use sparingly - high token cost):
   ```
   mcp__task-master-ai__get_tasks:
   - projectRoot: /Users/hue/code/Dopemux-ChatRipperXXX
   - withSubtasks: true
   ```

**Token Impact**: 
- Default approach: ~500 tokens (90% savings)
- Extended approach: ~1,500 tokens (75% savings)  
- Full context: ~6,000 tokens (baseline)
