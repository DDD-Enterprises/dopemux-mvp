# Dopemux User Guide

Complete guide to using Dopemux with Leantime and Task-Master AI integration for ADHD-optimized project management.

## Getting Started

### First Launch
After installation, access Leantime at: `http://localhost:8080`

**Default Credentials:**
- Username: `admin`
- Password: `admin`

⚠️ **Change default password immediately in production**

### ADHD Dashboard Overview
The Dopemux interface provides:
- 🎯 **Focus Status**: Current attention state and remaining focus time
- 📊 **Progress Bars**: Visual completion indicators
- 🧠 **Cognitive Load**: Current mental workload assessment
- ⏰ **Next Break**: Countdown to next recommended break

## Core Workflows

### 1. PRD-to-Tasks Workflow

Transform Product Requirements Documents into actionable tasks:

#### Step 1: Upload PRD
```python
# Via Python API
from src.integrations.sync_manager import LeantimeTaskMasterSyncManager

sync_manager = LeantimeTaskMasterSyncManager()
result = sync_manager.process_prd("/path/to/prd.md", project_id="proj-123")
```

#### Step 2: Review Generated Tasks
- Task-Master AI analyzes PRD complexity
- Generates ADHD-friendly task breakdown
- Estimates cognitive load per task
- Suggests optimal work sequences

#### Step 3: Sync to Leantime
- Tasks automatically appear in Leantime project
- ADHD metadata preserved (focus level, break hints)
- Dependencies and priorities set

### 2. ADHD-Optimized Task Management

#### Focus Session Management
```bash
# Start focused work session
dopemux start-focus --task="Implement user authentication"

# Current status
dopemux status
# Output: 🎯 Focus: 18/25 minutes | Task: User auth | Load: Medium
```

#### Attention State Detection
The system monitors:
- ⚡ **High Focus**: Complex tasks, minimal interruptions
- 🔄 **Medium Focus**: Regular tasks, some context switching
- 🌊 **Low Focus**: Simple tasks, frequent breaks needed
- 😴 **Break Needed**: Immediate rest recommended

#### Smart Task Scheduling
```python
# Get ADHD-optimized task sequence
from src.utils.adhd_optimizations import ADHDTaskOptimizer

optimizer = ADHDTaskOptimizer()
schedule = optimizer.optimize_schedule(
    tasks=project_tasks,
    current_attention="medium",
    available_time=120  # minutes
)
```

### 3. Bidirectional Sync

#### Leantime → Task-Master
Changes in Leantime automatically sync:
- Task status updates
- Priority changes
- Due date modifications
- Comments and notes

#### Task-Master → Leantime
AI-driven updates sync back:
- Complexity reassessments
- Subtask generation
- Dependency discovery
- Optimization suggestions

### 4. Context Preservation

#### Auto-Save Features
- Work context saved every 30 seconds
- Mental model preserved across breaks
- Decision history maintained
- Progress checkpoints created

#### Manual Context Management
```bash
# Save current context
dopemux save-context "Working on user auth, completed login form"

# Restore previous context
dopemux restore-context --session="2024-01-15-morning"

# List saved contexts
dopemux list-contexts
```

## ADHD Features Deep Dive

### Attention Management

#### Focus Duration Adaptation
```python
# System learns your optimal focus periods
{
    "morning": {"avg_focus": 35, "confidence": 0.8},
    "afternoon": {"avg_focus": 20, "confidence": 0.9},
    "evening": {"avg_focus": 15, "confidence": 0.7}
}
```

#### Break Optimization
- **Micro-breaks**: 2-3 minutes every 15-20 minutes
- **Standard breaks**: 5-10 minutes every 25-30 minutes
- **Long breaks**: 15-30 minutes every 2 hours
- **Activity suggestions**: Walk, stretch, hydrate, breathe

### Cognitive Load Management

#### Task Complexity Scoring
- **Low (1-3)**: Documentation, simple fixes, routine tasks
- **Medium (4-6)**: Feature implementation, testing, refactoring
- **High (7-9)**: Architecture design, complex debugging
- **Critical (10)**: Major system changes, crisis resolution

#### ADHD Metadata Fields
Each task includes specialized ADHD metadata:

```python
# Task ADHD metadata structure
adhd_metadata = {
    "cognitive_load": 7,           # 1-10 complexity scale
    "focus_level": "high",         # "low", "medium", "high"
    "break_reminder": True,        # Automatic break prompts
    "context_switch_cost": 3,      # 1-5 switching difficulty
    "optimal_time_of_day": ["morning", "afternoon"],
    "estimated_focus_duration": 25 # minutes
}
```

#### Load Balancing
```python
# Example daily schedule optimization
{
    "morning_high_focus": ["Complex debugging (8/10)", "Architecture design (9/10)"],
    "afternoon_medium": ["Feature implementation (5/10)", "Code reviews (4/10)"],
    "evening_low": ["Documentation (2/10)", "Email responses (1/10)"]
}
```

#### Focus Level Management
- **High Focus Tasks**: Require sustained attention, minimal interruptions
  - Architecture decisions, complex problem solving
  - Best scheduled during peak attention periods
  - Automatic break reminders every 25-30 minutes

- **Medium Focus Tasks**: Regular development work with some flexibility
  - Feature implementation, code reviews, testing
  - Can handle minor interruptions
  - Break reminders every 20-25 minutes

- **Low Focus Tasks**: Routine work, can be done during scattered attention
  - Documentation, email responses, simple fixes
  - Good for context switching periods
  - Flexible break timing

### Executive Function Support

#### Decision Reduction
- Maximum 3 options presented at once
- Clear recommendations highlighted
- Pros/cons analysis for complex choices
- Default selections for routine decisions

#### Task Activation Support
```python
# Clear first steps provided for every task
{
    "task": "Implement user authentication",
    "first_step": "Create user model with email/password fields",
    "time_estimate": "15 minutes",
    "difficulty": "Medium",
    "prerequisites": ["Database setup complete", "User stories reviewed"]
}
```

## Advanced Features

### Multi-Model Integration

#### Claude Integration
- PRD analysis and task generation
- Code review and suggestions
- Documentation generation
- Problem-solving assistance

#### Claude Auto Responder 🤖
Automatic confirmation responses for Claude Code prompts, designed with ADHD accommodations:

**Quick Setup:**
```bash
# Setup auto responder
dopemux autoresponder setup

# Enable with default settings
dopemux autoresponder config --enabled

# Start monitoring
dopemux autoresponder start
```

**ADHD-Optimized Features:**
- 🎯 **Attention-Aware**: Adapts response timing based on focus state
- 🔍 **Terminal Scope Control**: Monitor current window, all windows, or project-specific
- ⏱️ **Timeout Protection**: Auto-stops after inactivity to prevent overwhelm
- ✅ **Tool Whitelisting**: Only responds to safe, pre-approved tools
- 📊 **Usage Analytics**: Track responses and productivity patterns

**Configuration Options:**
```bash
# Configure response behavior
dopemux autoresponder config \
  --terminal-scope all \
  --delay 1.0 \
  --timeout 45 \
  --whitelist \
  --debug

# Quick status check
dopemux autoresponder status
```

**Usage Patterns for ADHD:**
- **Hyperfocus Sessions**: Enable with 0-delay for uninterrupted flow
- **Scattered Attention**: Use 1-2 second delays to reduce cognitive overwhelm
- **Context Switching**: Project scope prevents interference between tasks

#### Task-Master AI
- Intelligent task decomposition
- Complexity assessment
- Dependency analysis
- Workflow optimization

### Performance Monitoring

#### Attention Analytics
```bash
dopemux analytics --period="last_week"
```

Output:
```
📊 Attention Analytics (Last Week)
==================================
Average Focus Duration: 23 minutes
Peak Performance: 10:00 AM - 12:00 PM
Optimal Task Types: Implementation, Testing
Recommended Adjustments: Extend morning focus blocks
```

#### Productivity Metrics
- Tasks completed per focus session
- Context switch frequency
- Break effectiveness scores
- Cognitive load distribution

### Team Collaboration

#### ADHD-Friendly Communication
- **Status Updates**: Automated, emoji-rich progress reports
- **Handoffs**: Clear context transfer between team members
- **Reviews**: Structured feedback with specific action items
- **Meetings**: Agenda-driven, time-boxed, outcome-focused

## API Reference

### Core Classes

#### LeantimeMCPClient
```python
from src.integrations.leantime_bridge import LeantimeMCPClient

client = LeantimeMCPClient(
    server_url="http://localhost:8080",
    api_key="your-api-key"
)

# Get projects
projects = await client.get_projects()

# Create task
task = await client.create_task(
    project_id="123",
    title="Implement feature",
    description="Detailed description",
    priority="high"
)
```

#### TaskMasterMCPClient
```python
from src.integrations.taskmaster_bridge import TaskMasterMCPClient

client = TaskMasterMCPClient()

# Parse PRD
analysis = await client.parse_prd("/path/to/prd.md")

# Get task breakdown
tasks = await client.get_task_breakdown(
    prd_content="...",
    complexity_level="medium"
)
```

#### ADHDTaskOptimizer
```python
from src.utils.adhd_optimizations import ADHDTaskOptimizer

optimizer = ADHDTaskOptimizer()

# Optimize task sequence
schedule = optimizer.optimize_schedule(
    tasks=task_list,
    current_attention="high",
    available_time=120
)

# Get attention recommendations
recommendations = optimizer.get_attention_recommendations(
    current_load="medium",
    recent_performance=performance_data
)
```

## Best Practices

### Daily Workflow
1. **Morning Setup** (5 minutes)
   - Review yesterday's context
   - Check attention state
   - Plan high-focus tasks

2. **Focus Blocks** (25 minutes each)
   - Single task focus
   - Minimize distractions
   - Trust the timer

3. **Break Optimization** (5 minutes)
   - Physical movement
   - Mental reset activities
   - Avoid decision-heavy tasks

4. **Evening Review** (10 minutes)
   - Save context for tomorrow
   - Celebrate completions
   - Adjust tomorrow's plan

### Task Management
- **Chunk Everything**: Break tasks into 15-25 minute pieces
- **Context Switch Wisely**: Group similar tasks together
- **Trust the System**: Let AI handle complexity assessment
- **Celebrate Wins**: Acknowledge every completion

### Attention Optimization
- **Know Your Patterns**: Track peak performance times
- **Respect Your Limits**: Don't push through attention fatigue
- **Use Visual Cues**: Progress bars and status indicators help
- **Plan for Interruptions**: Build buffer time into schedules

## ADHD Feature Reference

### Task Creation with ADHD Metadata
```python
# Creating tasks with full ADHD support
task = await client.create_task(
    project_id="123",
    title="Implement authentication",
    description="Add login/logout with JWT",
    priority="high",
    estimated_hours=4,
    adhd_metadata={
        "cognitive_load": 6,           # Medium complexity
        "focus_level": "medium",       # Can handle some interruptions
        "break_reminder": True,        # Enable break prompts
        "context_switch_cost": 4,      # High switching penalty
        "optimal_time_of_day": ["morning", "afternoon"],
        "estimated_focus_duration": 20 # 20-minute focus blocks
    }
)
```

### ADHD-Optimized Task Filtering
```python
# Get tasks by attention requirements
high_focus_tasks = await client.get_tasks_by_attention_level(
    project_id="123",
    attention_level="high"
)

# Get tasks within cognitive capacity
manageable_tasks = await client.get_tasks_by_cognitive_load(
    project_id="123",
    max_load=6  # Current capacity
)

# Get AI recommendations based on current state
recommendations = await client.get_recommended_tasks(
    project_id="123",
    current_attention="medium",
    available_time=30
)
```

### Context Preservation Features
```python
# Manual context saving
context_id = await optimizer.save_context(
    task_id="456",
    mental_model="Working on user auth flow, just completed login validation",
    decisions=["Using bcrypt for passwords", "JWT expires in 24 hours"],
    next_steps=["Add logout endpoint", "Test session cleanup"]
)

# Restore context after interruption
context = await optimizer.restore_context(context_id)
print(f"You were: {context.mental_model}")
print(f"Next: {context.next_steps[0]}")
```

### Attention State Management
```python
# Get current attention analysis
attention_state = optimizer.analyze_current_attention()
# Returns: "high", "medium", "low", or "break_needed"

# Get personalized recommendations
recommendations = optimizer.get_attention_recommendations(
    current_load="medium",
    recent_performance=performance_data,
    time_of_day="morning"
)
```

### Break Management
```python
# Check if break is needed
if optimizer.should_take_break():
    break_type = optimizer.recommend_break_type()
    print(f"Time for a {break_type} break!")
    # break_type: "micro", "standard", "long", or "restorative"

# Log break completion
await optimizer.log_break_taken(
    duration=5,  # minutes
    activity="walk",
    effectiveness_rating=8  # 1-10 scale
)
```

## Troubleshooting

### Common ADHD Challenges

#### "I Can't Start Tasks"
- Check if task is too large (break it down)
- Verify first step is clear and simple
- Ensure prerequisites are met
- Try the "2-minute rule" - commit to just 2 minutes

#### "I Keep Getting Distracted"
- Review current cognitive load (may be too high)
- Check break schedule (may need more frequent breaks)
- Verify environment setup (minimize distractions)
- Consider task switching to something more engaging

#### "I Forgot What I Was Doing"
- Check saved context in dopemux
- Review recent task history
- Use the restore-context command
- Start with the smallest next step

### Technical Issues
See [INSTALLATION.md](INSTALLATION.md) for technical troubleshooting.

---

**Happy productive coding!** 🎉 Remember: progress over perfection, accommodation over adaptation.