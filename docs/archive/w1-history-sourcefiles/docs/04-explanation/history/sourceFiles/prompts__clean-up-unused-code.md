
DesktopCommander Logo
DesktopCommander
Prompts
Installation
Testimonials
Resources
Sponsor
Install Desktop Commander
Prompt Library
Discover powerful AI workflows and automation prompts for Desktop Commander

All Categories
Explore codebase
Deploy
Write documentation
Automate tasks
Optimize workflow
For all
Content makers
Data analysts
DevOps
Developers
Professionals
Vibe Coders
Explain Codebase or Repository

Step-by-Step
🔥
Understand, analyze, and document your codebase - whether you're inheriting legacy code, joining a new project, or diving into unfamiliar technology.
Clean Up Unused Code

Step-by-Step
Scan your codebase to find unused imports, dead functions, and redundant code that can be safely removed.
Explain React Component Architecture

Instant
🔥
Get a clear breakdown of how your React component works, including props flow, state management, and dependencies.
Create Project Documentation

Step-by-Step
Build structured knowledge repositories that capture the "why" behind your code - project specifications, architecture decisions, and technical rationale. Use them later for referring AI to your project and generate better results.
Create Team Onboarding Documentation

Step-by-Step
Generate comprehensive onboarding guide for new developers including setup, architecture overview, and contribution guidelines.
Compare Config Files to Baseline

Instant
🔥
Detect configuration drift by comparing current configs to standards.
Analyze Error Handling Strategy

Instant
Understand and document the error handling and logging approaches used in your project.
Analyze Test Coverage Gaps

Instant
Review existing tests and identify missing coverage areas with specific recommendations for improvement.
Assess Project's Security

Step-by-Step
Identify and document all security measures implemented in your codebase.
Browse All Explore codebase Prompts
Submit your own prompt
Explore our complete library of 50+ prompts
What users are saying
“Absolutely loving Desktop Commander! It writes real code into my project and fixes issues faster than I could on my own.”
Community member · Developer
“I had 76 errors across many files. Desktop Commander fixed them in hours. I've never resolved type errors this quickly.”
Community member · Svelte Developer
“It’s a life saver. It writes code with the latest updates and removes tool duplication for me.”
Community member · Engineer
“I asked it to organize my downloads and it did everything automatically and showed a clear summary.”
Community member · Entrepreneur
“Great for exploring unfamiliar repos. I got an architectural overview in minutes instead of hours.”
Community member · Developer
“Set up a full dev environment for me and verified everything with a sample app—zero guesswork.”
Community member · Developer
“It automated my weekly newsletter pipeline end-to-end on my computer. Massive time saver.”
Community member · Entrepreneur
“I finally cleaned up unused code across a large project without manual hunting.”
Community member · Developer
Previous slideNext slide
Found Something That Works? Share It!

Join thousands of developers contributing to the Desktop Commander community

Submit Your Prompt
Logo
Desktop Commander
AI automation tool for Claude Desktop app.

Prompt Library

Browse All Prompts
Use Cases

AI Software Engineer
AI DevOps
AI Data Analyst
AI Technical Writer
AI UX/UI Designer
Resources

GitHub Repository
Documentation
Testimonials
Media
FAQ
© 2025 Desktop Commander MCP. Open-source software under MIT license.
Clean Up Unused Code

Detailed information and actions for this prompt.
Step-by-step flow
Explore codebase
Optimize code
DC team
Growing

Description
Scan your codebase to find unused imports, dead functions, and redundant code that can be safely removed.
Target Roles

Developers
Vibe Coders
Complete Prompt
# Code Analysis & Cleanup Workflow

## Important: Multi-Chat Workflow

**Code analysis and cleanup requires multiple chat sessions to avoid context limits and ensure thorough review.**

### Progress Tracking System
I'll create and continuously update a `code-analysis-progress.md` file after each major step. This file contains:
- **Complete workflow instructions** - Full prompt context and guidelines for new chats
- **Analysis guidelines** - What to identify, safety protocols, confirmation requirements
- **Project context** - Your codebase structure, technology stack, and specific requirements
- **Completed phases** - What has been analyzed and documented
- **Current findings** - Discovered unused imports, dead code, and potential issues
- **Next steps** - Specific cleanup tasks and priorities for continuation
- **File locations** - Where all analysis reports and backup recommendations are stored

This ensures any new chat session has complete context to continue the analysis seamlessly.

### When to Start a New Chat
Start a new chat session when:
- This conversation becomes long and responses slow down
- You want to focus on a different part of the codebase
- Moving from analysis to cleanup implementation
- You're returning to the analysis after a break

### Continuing in a New Chat
Simply start your new conversation with:
*"Continue code analysis - please read `code-analysis-progress.md` to understand where we left off, then proceed with the next phase."*

**I'll update the progress file after every major step to ensure seamless continuity.**

---

## My Working Method

I work in phases with strict safety protocols and confirmation points:

### Phase-Based Approach
1. **Discovery Phase**: Explore project structure, identify technologies, understand architecture
2. **Scanning Phase**: Systematically analyze files for unused imports and dead code
3. **Analysis Phase**: Categorize findings, assess impact, identify dependencies
4. **Review Phase**: Present findings with detailed reports and recommendations
5. **Cleanup Phase**: Execute approved changes with backup and rollback plans

### Safety Protocols
- **NEVER DELETE OR MODIFY CODE** without explicit confirmation
- Always create backup recommendations before any changes
- Provide detailed impact analysis for each proposed change
- Show exactly what will be removed/modified before taking action
- Implement changes incrementally with testing checkpoints

**Approval Checkpoint**: I'll show you comprehensive analysis reports and get your explicit approval before making ANY changes.

---

I use Desktop Commander for file system operations and code analysis.

---

## Getting Started

To begin, please provide:

1. **Project Root Path**: Full absolute path to your project directory

2. **Project Context**: 
   - What type of application/system is this? (web app, API, library, etc.)
   - What's the main technology stack? (JavaScript/TypeScript, Python, Java, etc.)
   - What's your goal with this cleanup?
   - Any areas you're particularly concerned about?
   - Your familiarity level with the codebase

3. **Analysis Scope**: 
   - **Full analysis** (entire codebase) or **targeted analysis** (specific directories/files)
   - **Conservative** (only obvious unused code) or **aggressive** (potential dead code)
   - **Focus areas**: unused imports, dead functions, unreachable code, unused variables
   - **Exclusions**: files/directories to skip (tests, config, generated code, etc.)

4. **Safety Preferences**:
   - Backup strategy preference
   - Testing requirements before cleanup
   - Incremental vs batch changes

### Analysis Features

**Unused Import Detection:**
- Identifies imported modules/packages never referenced
- Detects partially unused imports (specific functions/classes)
- Handles complex import patterns (aliases, destructuring, etc.)
- Cross-references with dynamic imports and string-based imports

**Dead Code Identification:**
- Unreferenced functions, classes, and variables
- Unreachable code blocks (after returns, in impossible conditions)
- Unused configuration and constants
- Orphaned files with no external references

**Smart Analysis:**
- Respects framework conventions (React hooks, lifecycle methods, etc.)
- Handles dynamic references (reflection, string-based calls, etc.)
- Considers build-time and runtime dependencies
- Analyzes across module boundaries

**Comprehensive Reporting:**
- Detailed file-by-file breakdown
- Impact assessment for each finding
- Dependency analysis and removal safety
- Statistics on potential space/complexity savings
- Prioritized cleanup recommendations

### Example Usage

After providing the information above, I'll:

1. **Map your project structure** and understand the architecture
2. **Scan systematically** through all relevant files
3. **Generate detailed reports** of findings with impact analysis
4. **Present cleanup plan** with step-by-step safety protocols
5. **Execute approved changes** with full backup and rollback capabilities

Ready to help you clean up your codebase safely and effectively!

Close

Share

Use Prompt
Close