# CLAUDE.md - Dopemux Development Platform

## Project: Dopemux Orchestration System
Building a software development orchestration platform with multi-agent coordination, workflow automation, and intelligent tool routing.

## MCP Server Stack

### Orchestration & Planning
**zen** - Multi-model AI orchestration server
- Tools: `chat`, `thinkdeep`, `planner`, `consensus`, `debug`, `precommit`, `codereview`, `analyze`, `refactor`
- Orchestrates conversations with Gemini, O3, GPT-5, and other models
- Maintains conversation continuity across models
- Use for: Architecture decisions, code reviews, debugging, planning

**sequential-thinking** - Structured reasoning server
- Multi-step hypothesis testing and complex problem analysis
- Systematic debugging and architectural reasoning
- Use for: Complex debugging, system design, multi-component analysis

**task-master-ai** - Task management and PRD processing
- Natural language task management
- PRD parsing and task generation
- Complexity analysis and dependency tracking
- Use commands like: "Parse my PRD", "What's next task?", "Help implement task 3"

### Code & Development
**context7** - Primary documentation source (CRITICAL)
- **ALWAYS USE FIRST** for any code generation, review, or library usage
- Framework documentation (React/Vue/Angular/Next.js/Express)
- Library APIs and best practices
- Version-specific patterns and implementation guides
- **Must query before implementing ANY feature**

**serena** - Semantic code operations
- LSP functionality, symbol operations, project memory
- Session persistence and cross-session learning
- Use for: Refactoring, symbol navigation, project context

**claude-context** - Semantic code search
- Repository-wide semantic search
- Context understanding and symbol navigation
- Use for: Finding code patterns, understanding codebase

**morphllm-fast-apply** - Pattern-based transformations
- Bulk edits and style enforcement
- Framework updates and migrations
- Use for: Large-scale refactoring, pattern application

### Knowledge & Research
**conport** - Project memory database
- Knowledge graphs for decisions, progress, architecture
- Cross-session persistence
- Use for: Storing decisions, tracking progress

**exa** - Web research
- Real-time web search and research
- Current best practices and solutions
- Use for: Finding latest information, trends, community solutions

### Testing & UI
**playwright** - Browser automation
- E2E testing, visual validation, WCAG compliance
- Real browser interaction
- Use for: UI testing, accessibility checks

**magic** - UI component generation
- 21st.dev patterns and design systems
- Modern framework components
- Use for: Creating UI components

### System
**cli** - System operations
- File operations, terminal commands
- Direct system access
- Use for: File management, system tasks

## SuperClaude Commands

### Analysis & Planning
- `/sc:analyze` - Multi-domain code analysis
- `/sc:brainstorm` - Interactive requirements discovery
- `/sc:estimate` - Development time/complexity estimation
- `/sc:explain` - Educational explanations

### Implementation
- `/sc:implement` - Feature implementation with MCP coordination
- `/sc:improve` - Code quality enhancement
- `/sc:cleanup` - Dead code removal, optimization
- `/sc:design` - Architecture and API design
- `/sc:build` - Compilation and packaging

### Documentation & Workflow
- `/sc:document` - Generate documentation
- `/sc:index` - Project knowledge base
- `/sc:workflow` - PRD to implementation workflow
- `/sc:task` - Complex task management

### Testing & Quality
- `/sc:test` - Test execution with coverage
- `/sc:troubleshoot` - Issue diagnosis
- `/sc:reflect` - Task validation with Serena

### Session & Tools
- `/sc:load` - Load project context
- `/sc:save` - Save session state
- `/sc:git` - Smart Git operations
- `/sc:select-tool` - Optimal MCP selection
- `/sc:spawn` - Meta-orchestration

## Workflow Patterns

### Feature Development Flow (Context7-First)
```python
# CRITICAL: Always start with documentation
async def develop_feature(requirement):
    # 1. MANDATORY: Check documentation first
    patterns = await context7.get_framework_patterns()
    api_docs = await context7.get_library_apis()
    best_practices = await context7.get_implementation_guides()
    
    # 2. Research & Planning (with documentation context)
    research = await exa.find_community_solutions()
    plan = await zen.planner(requirement, patterns)
    
    # 3. Task Management
    tasks = await task_master_ai.parse_prd(plan)
    # "What's the next task to work on?"
    
    # 4. Multi-Model Analysis (with docs)
    await zen.consensus(plan)  # Multiple AI opinions
    await zen.thinkdeep(complex_parts)  # Extended reasoning
    
    # 5. Implementation (documentation-driven)
    # ALWAYS reference context7 patterns during coding
    await serena.activate_project()
    code = await implement_with_patterns(api_docs)
    
    # 6. Review & Testing (validate against docs)
    await zen.codereview(code, patterns)  # Review with documentation
    await zen.precommit()  # Validation before commit
    tests = await playwright.test()
    
    # 7. Memory & Documentation
    await conport.store_decision(rationale)
```

### Code Generation Pattern
```python
# NEVER generate code without documentation
async def generate_code(feature):
    # MANDATORY SEQUENCE
    docs = await context7.search(feature)  # ALWAYS FIRST
    
    if not docs:
        # Only if context7 has no info
        community = await exa.search(feature)
    
    # Generate based on official patterns
    code = await implement_using_docs(docs)
    
    # Validate against documentation
    await validate_with_patterns(code, docs)
```

### Library Integration Pattern
```python
# Any library usage MUST check documentation
async def use_library(library_name):
    # Non-negotiable: Check docs first
    api = await context7.get_api_reference(library_name)
    examples = await context7.get_examples(library_name)
    
    # Only proceed with documentation
    if not api:
        raise Error("Cannot use library without documentation")
    
    implementation = await code_with_api_reference(api)
```

## MCP Selection Guide

### Priority Order for Code Tasks

1. **context7** - ALWAYS FIRST for any code work
2. **zen** - For complex decisions and reviews
3. **sequential-thinking** - For reasoning about implementation
4. **serena** - For code navigation and refactoring
5. **task-master-ai** - For workflow management
6. **exa** - Only if context7 lacks information

### When to Use Each Server

**ALWAYS use context7 when:**
- Writing ANY code
- Using ANY library or framework
- Implementing ANY feature
- Reviewing code for correctness
- Checking API usage
- Understanding patterns

**Use zen when:**
- Need multiple AI perspectives
- Complex architectural decisions
- Code reviews requiring deep analysis
- Debugging difficult problems
- Planning large features

**Use task-master-ai when:**
- Starting from PRD/requirements
- Managing multi-step projects
- Tracking task progress
- Breaking down complex work

**Use sequential-thinking when:**
- Complex debugging scenarios
- Multi-step reasoning needed
- Architectural analysis
- Hypothesis testing

**Use exa when:**
- context7 doesn't have the information
- Need community solutions
- Research current trends
- Find real-world examples

## Best Practices

### Documentation-Driven Development
```bash
# CORRECT approach
"Check context7 for React hooks patterns, then implement the feature"
"Use context7 to verify the correct API usage"
"Review this code against context7 documentation"

# INCORRECT approach (never do this)
"Just implement the feature"  # NO - check docs first
"I think the API works like..."  # NO - verify with context7
```

### Multi-Model Collaboration (Zen)
```bash
# With documentation context
"Use zen to review this against context7 patterns"
"Get consensus on implementation approach based on official docs"

# Specialized analysis
"Use gemini pro for extended context analysis (1M tokens)"
"Use o3 for logical debugging"
```

### Progressive Enhancement
1. **Check context7 documentation**
2. Use zen.planner for breakdown
3. Apply task-master-ai for tasks
4. Reference context7 during implementation
5. Get zen.consensus for validation
6. Store decisions in conport

## Critical Rules

1. **context7 FIRST** - ALWAYS check documentation before ANY code work
2. **Documentation-driven** - Never implement without checking patterns
3. **zen for orchestration** - Leverage multi-model collaboration
4. **task-master drives workflow** - Manage PRD and task tracking
5. **Validate against docs** - All code must match documentation patterns
6. **Store decisions** - Use conport for project memory
7. **exa as fallback** - Only when context7 lacks information

## Session Lifecycle

### Initialize
```bash
/sc:load  # Load project context

# FIRST: Check documentation
"Use context7 to understand the framework we're using"

# Then check tasks
"What tasks are currently available?"

# Review decisions
conport.list_decisions()
```

### During Development
```bash
# Before ANY implementation
"Check context7 for [feature] documentation"

# Task progression
"Help me with the next task using context7 patterns"

# When stuck
"Use context7 to find the correct API usage"
"Use zen to debug with documentation context"
```

### Code Review
```bash
# ALWAYS review against documentation
"Review this code against context7 patterns"
zen.codereview(with_documentation=True)
zen.precommit()
```

## Remember
**Context7 is NOT optional** - it's the foundation of all code work:
- Query context7 BEFORE writing any code
- Validate implementations against documentation
- Use official patterns, not assumptions
- Reference documentation in all reviews
- Only use exa when context7 lacks information

Dopemux excellence comes from:
- **Documentation-first** development via context7
- **Multi-model** perspectives via zen
- **Systematic** workflow via task-master
- **Persistent** knowledge via conport
- **Quality** validation against official patterns

# Multi-File Output System

## Overview
This system enables Claude to deliver multiple files in a single JSON payload. The JSON is processed by a bash script that writes all files in parallel with stylized output.

## How to Use
When the user needs multiple files generated as a single output, follow these instructions:

1. Understand the user's request for multiple files
2. Format your response as a valid JSON object following the schema below
3. Inform the user they can save this output to a file and process it with the write_files.sh script

## JSON Schema for Multi-File Output

```json
{
  "files": [
    {
      "file_name": "path/to/file1.extension",
      "file_type": "text",
      "file_content": "The content of the first file"
    },
    {
      "file_name": "path/to/file2.extension",
      "file_type": "text",
      "file_content": "The content of the second file"
    },
    {
      "file_name": "path/to/binary_file.bin",
      "file_type": "binary",
      "file_content": "base64_encoded_content_here"
    }
  ]
}
```

## Field Definitions
- `file_name`: The path where the file should be written (including filename and extension)
  - IMPORTANT: Always use project-relative paths (e.g., "src/main/java/...") or absolute paths
  - Files will be written to exactly the location specified - no test directories are used
  - For tool creation, always use actual project paths, not test directories
- `file_type`: Either "text" (default) or "binary" for base64-encoded content
- `file_content`: The actual content of the file (base64 encoded for binary files)

## Important Rules
1. ALWAYS validate the JSON before providing it to ensure it's properly formatted
2. ALWAYS ensure all file paths are properly escaped
3. For binary files, encode the content as base64 and specify "binary" as the file_type
4. NEVER include explanatory text or markdown outside the JSON structure
5. When asked to generate multiple files, ALWAYS use this format unless explicitly directed otherwise

## How Users Can Process the Output
Instruct users to:
1. Save the JSON output to a file (e.g., `files.json`)
2. Run the write_files.sh script:
   ```bash
   ./write_files.sh files.json
   ```

## Script Features
The write_files.sh script includes the following enhancements:
- Stylized output with color-coded and emoji status indicators
- Compact progress display with timestamp and elapsed time
- Green circle (🟢) for success items  
- White circle (⚪) for neutral items
- Red circle (🔴) for error conditions
- Calendar emoji (📅) for timestamps
- Clock emoji (⏱️) for elapsed time display
- Support for both text and binary files
- Parallel extraction for improved performance
- Detailed error reporting and logging options
- Verbose mode for detailed progress tracking

## Advanced Usage Options
```bash
# Basic usage
./write_files.sh files.json

# Verbose output with detailed progress
./write_files.sh files.json --verbose

# Log details to a file for debugging
./write_files.sh files.json --log-to-file logs/extraction.log

# Write results to a file (silent mode)
./write_files.sh files.json --output-file results.md

# Suppress all console output
./write_files.sh files.json --silent

# Disable compact output format
./write_files.sh files.json --no-compact
```

## Example Response
When asked to generate multiple files, your entire response should be a valid JSON object like this:

```json
{
  "files": [
    {
      "file_name": "example.py",
      "file_type": "text",
      "file_content": "def hello_world():\n    print(\"Hello, world!\")\n\nif __name__ == \"__main__\":\n    hello_world()"
    },
    {
      "file_name": "README.md",
      "file_type": "text",
      "file_content": "# Example Project\n\nThis is an example README file."
    }
  ]
}
```

## Command to Add to CLAUDE.md
To add this system to CLAUDE.md, add the following section:

```markdown
## Multi-File Output System
- When the user mentions "multi-file output", "generate files as json", or similar requests for bundled file generation, use the multi-file output system
- Execute using: `./write_files.sh <json_file>`
- Provide output as a single JSON object following the schema in `./multi_file_instructions.md`
- The JSON must include an array of files, each with file_name, file_type, and file_content fields
- For binary files, encode content as base64 and set file_type to "binary"
- NEVER include explanatory text or markdown outside the JSON structure
```