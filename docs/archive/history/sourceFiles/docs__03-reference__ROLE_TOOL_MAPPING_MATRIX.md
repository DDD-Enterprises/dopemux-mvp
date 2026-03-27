# Role-Based Tool Mapping Matrix

## 🎯 Overview

This matrix defines the optimal tool combinations for each development role, designed to minimize cognitive load while maximizing development efficiency. Each role is limited to 3-5 tools to prevent ADHD decision paralysis while ensuring all necessary capabilities are available.

## 📊 Master Tool Mapping Matrix

| Tool/Server | Developer | Researcher | Architect | Reviewer | Debugger | Planner | Ops | Priority | Token Cost |
|-------------|-----------|------------|-----------|----------|----------|---------|-----|----------|------------|
| **Context7** | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | Critical | 🟢 Very Low |
| **ConPort** | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | Critical | 🟢 Very Low |
| **Claude Context** | ✅ Primary | 🟡 Secondary | 🟡 Secondary | ✅ Primary | ✅ Primary | ❌ | 🟡 Secondary | High | 🟡 Medium |
| **Serena** | ✅ Primary | ❌ | ❌ | 🟡 Secondary | ✅ Primary | ❌ | ❌ | Medium | 🟢 Low-Med |
| **MorphLLM** | ✅ Primary | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Primary | Medium | 🟢 Very Low |
| **MAS Sequential** | ❌ | ❌ | ✅ Primary | ❌ | ❌ | 🟡 On-Demand | ❌ | High | 🔴 Very High |
| **Zen: Chat** | 🟡 On-Demand | ✅ Primary | 🟡 Secondary | ❌ | ❌ | ❌ | ❌ | Medium | 🟡 Medium |
| **Zen: ThinkDeep** | ❌ | ✅ Primary | ✅ Primary | ❌ | ❌ | ❌ | ❌ | Medium | 🟡 Med-High |
| **Zen: Planner** | ❌ | ❌ | ✅ Primary | ❌ | ❌ | ✅ Primary | ❌ | High | 🟡 Medium |
| **Zen: Consensus** | ❌ | ❌ | ✅ Primary | ❌ | ❌ | 🟡 Secondary | ❌ | High | 🔴 High |
| **Zen: CodeReview** | 🟡 On-Demand | ❌ | 🟡 Secondary | ✅ Primary | 🟡 Secondary | ❌ | ❌ | High | 🟡 Med-High |
| **Zen: Debug** | 🟡 On-Demand | ❌ | ❌ | 🟡 Secondary | ✅ Primary | ❌ | ❌ | High | 🟡 Medium |
| **Zen: TestGen** | 🟡 On-Demand | ❌ | ❌ | ✅ Primary | 🟡 Secondary | ❌ | ❌ | Medium | 🟡 Medium |
| **Zen: SecAudit** | ❌ | ❌ | ❌ | ✅ Primary | ❌ | ❌ | ❌ | Medium | 🟡 Med-High |
| **Zen: PreCommit** | 🟡 On-Demand | ❌ | ❌ | ✅ Primary | ❌ | ❌ | ❌ | High | 🟡 Medium |
| **Zen: Refactor** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Primary | Medium | 🟡 Med-High |
| **Zen: DocGen** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Primary | Low | 🟡 Medium |
| **Zen: Tracer** | ❌ | ❌ | ❌ | ❌ | ✅ Primary | ❌ | 🟡 Secondary | Medium | 🟡 Medium |
| **Task Master AI** | ❌ | ❌ | 🟡 Secondary | ❌ | ❌ | ✅ Primary | ❌ | High | 🟡 Medium |
| **ClearThought** | ❌ | ❌ | ✅ Primary | ❌ | ❌ | ✅ Primary | ❌ | Medium | 🟡 Medium |
| **DocRAG** | ❌ | ✅ Primary | ❌ | ❌ | ❌ | ❌ | ❌ | Medium | 🟡 Medium |
| **Exa** | ❌ | 🟡 Fallback | ❌ | ❌ | ❌ | ❌ | ❌ | Low | 🟡 Medium |
| **Desktop Commander** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Primary | Low | 🟢 Low |

**Legend:**
- ✅ Primary: Core tool for this role, always available
- 🟡 Secondary: Available but limited usage
- 🟡 On-Demand: Available on request with approval
- 🟡 Fallback: Only when primary option fails
- ❌ Not available for this role

## 🧑‍💻 Developer Role (Implementation Focus)

### **Primary Tools (Always Active)**
1. **Context7** - API documentation and references
   - **Usage:** ALWAYS query before writing any code
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Reduces uncertainty and API hallucinations

2. **ConPort** - Context preservation and session management
   - **Usage:** Automatic saving every 30 seconds
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Seamless context switching and interruption recovery

3. **Claude Context** - Semantic code search
   - **Usage:** Finding similar patterns, understanding existing code
   - **Token Cost:** ~1,000-3,000 per search
   - **ADHD Benefit:** Pattern-based learning, reduced "reinventing wheel"

4. **Serena** - Code navigation and refactoring
   - **Usage:** Go-to-definition, find references, basic refactoring
   - **Token Cost:** ~200-1,000 per operation
   - **ADHD Benefit:** Fast IDE-like navigation maintains flow state

5. **MorphLLM** - Pattern-based bulk transformations
   - **Usage:** Bulk renames, style updates, pattern replacements
   - **Token Cost:** ~100-500 per bulk operation
   - **ADHD Benefit:** Eliminates tedious repetitive work

### **On-Demand Tools (Request Required)**
- **Zen: Chat** - Quick discussions and brainstorming
- **Zen: CodeReview** - Self-review before commits
- **Zen: Debug** - Complex debugging assistance
- **Zen: TestGen** - Test generation when needed
- **Zen: PreCommit** - Final validation before commits

### **Token Budget:** 15,000 per session
### **Tool Limit:** 5 active tools maximum
### **ADHD Profile:** Fast iteration, minimal interruption, flow state protection

---

## 🔬 Researcher Role (Information Gathering)

### **Primary Tools (Always Active)**
1. **Context7** - Official documentation and API references
   - **Usage:** Primary source for all official information
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Authoritative sources reduce information anxiety

2. **ConPort** - Research progress tracking
   - **Usage:** Track findings, maintain research continuity
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Prevents losing research progress during interruptions

3. **DocRAG** - Internal documentation search
   - **Usage:** Search existing internal docs and knowledge base
   - **Token Cost:** ~500-2,000 per search
   - **ADHD Benefit:** Semantic search for vague queries

4. **Zen: Chat** - Multi-model discussions
   - **Usage:** Get different perspectives on research questions
   - **Token Cost:** ~1,000-5,000 per conversation
   - **ADHD Benefit:** Multiple viewpoints reduce research uncertainty

5. **Zen: ThinkDeep** - Extended analysis
   - **Usage:** Deep exploration of complex topics
   - **Token Cost:** ~2,000-8,000 per analysis
   - **ADHD Benefit:** Structured deep thinking approach

### **Fallback Tools (When Primary Fails)**
- **Exa** - External web research (only when Context7 insufficient)

### **Secondary Tools (Limited Usage)**
- **Claude Context** - Finding code examples related to research

### **Token Budget:** 10,000 per session
### **Tool Limit:** 3-4 active tools maximum
### **ADHD Profile:** Controlled exploration, time-boxed research, progress tracking

---

## 🏗️ Architect Role (Deep Analysis & Design)

### **Primary Tools (Always Active)**
1. **Context7** - Technical reference and constraints
   - **Usage:** API capabilities, technical limitations, best practices
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Grounded decisions in real capabilities

2. **ConPort** - Decision documentation and architectural reasoning
   - **Usage:** Track architectural decisions and their rationale
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Maintains decision history and context

3. **MAS Sequential** - Deep architectural analysis
   - **Usage:** Complex system design, multi-perspective analysis
   - **Token Cost:** ~5,000-15,000 per analysis
   - **ADHD Benefit:** Structured multi-agent approach to complex problems

4. **Zen: ThinkDeep** - Extended reasoning and exploration
   - **Usage:** Deep analysis of design trade-offs
   - **Token Cost:** ~2,000-8,000 per session
   - **ADHD Benefit:** Systematic exploration of alternatives

5. **Zen: Planner** - Task and implementation breakdown
   - **Usage:** Convert architecture into actionable plans
   - **Token Cost:** ~1,000-3,000 per plan
   - **ADHD Benefit:** Breaks complex designs into manageable tasks

6. **Zen: Consensus** - Multi-model validation
   - **Usage:** Critical architectural decisions validation
   - **Token Cost:** ~3,000-10,000 per consensus
   - **ADHD Benefit:** Reduces decision anxiety through validation

7. **ClearThought** - Decision frameworks and structured analysis
   - **Usage:** Complex trade-off analysis and decision making
   - **Token Cost:** ~1,000-3,000 per framework
   - **ADHD Benefit:** Structured approach to complex decisions

### **Secondary Tools (Limited Usage)**
- **Task Master AI** - Project planning integration
- **Zen: CodeReview** - Architecture validation through code review
- **Claude Context** - Understanding existing architectural patterns

### **Token Budget:** 25,000 per session (highest of all roles)
### **Tool Limit:** 4-5 active tools maximum
### **ADHD Profile:** Deep work mode, minimal interruptions, structured frameworks

---

## 👀 Reviewer Role (Quality Assurance)

### **Primary Tools (Always Active)**
1. **Context7** - API correctness validation
   - **Usage:** Verify API usage and best practices
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Authoritative validation reduces review uncertainty

2. **ConPort** - Review process tracking and findings documentation
   - **Usage:** Track review progress and findings
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Systematic review process with progress tracking

3. **Claude Context** - Code understanding and pattern analysis
   - **Usage:** Understand code context and find similar patterns
   - **Token Cost:** ~1,000-3,000 per search
   - **ADHD Benefit:** Better code understanding for thorough reviews

4. **Zen: CodeReview** - Professional multi-pass code review
   - **Usage:** Systematic code quality analysis
   - **Token Cost:** ~2,000-6,000 per review
   - **ADHD Benefit:** Structured review process with clear criteria

5. **Zen: TestGen** - Test coverage analysis and generation
   - **Usage:** Ensure adequate test coverage
   - **Token Cost:** ~1,000-3,000 per generation
   - **ADHD Benefit:** Systematic test coverage validation

6. **Zen: SecAudit** - Security vulnerability analysis
   - **Usage:** Security-focused review with OWASP checks
   - **Token Cost:** ~1,500-4,000 per audit
   - **ADHD Benefit:** Structured security checklist approach

7. **Zen: PreCommit** - Final validation before approval
   - **Usage:** Last quality gate before code acceptance
   - **Token Cost:** ~500-1,500 per check
   - **ADHD Benefit:** Final confidence boost before approval

### **Secondary Tools (Limited Usage)**
- **Serena** - Code navigation during review
- **Zen: Debug** - Understanding complex issues found during review

### **Token Budget:** 15,000 per session
### **Tool Limit:** 5 active tools maximum
### **ADHD Profile:** Systematic validation, checklist-based approach, clear criteria

---

## 🐛 Debugger Role (Problem Investigation)

### **Primary Tools (Always Active)**
1. **Context7** - API documentation for debugging context
   - **Usage:** Understand expected behavior and API constraints
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Clear understanding of expected vs actual behavior

2. **ConPort** - Investigation progress and hypothesis tracking
   - **Usage:** Track debugging steps and findings
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Maintains investigation context across interruptions

3. **Claude Context** - Find similar issues and solutions
   - **Usage:** Search for similar bug patterns and fixes
   - **Token Cost:** ~1,000-3,000 per search
   - **ADHD Benefit:** Pattern-based debugging reduces investigation time

4. **Serena** - Code navigation and exploration
   - **Usage:** Navigate code flow and understand relationships
   - **Token Cost:** ~200-1,000 per operation
   - **ADHD Benefit:** Fast navigation maintains investigation flow

5. **Zen: Debug** - Systematic debugging methodology
   - **Usage:** Root cause analysis with hypothesis tracking
   - **Token Cost:** ~2,000-5,000 per investigation
   - **ADHD Benefit:** Structured debugging approach prevents getting lost

6. **Zen: Tracer** - Call flow analysis and static analysis
   - **Usage:** Understand complex call flows and dependencies
   - **Token Cost:** ~1,000-3,000 per trace
   - **ADHD Benefit:** Visual understanding of complex systems

### **Secondary Tools (Limited Usage)**
- **Zen: CodeReview** - Review code for potential issues
- **Zen: TestGen** - Generate tests to reproduce issues

### **Token Budget:** 12,000 per session
### **Tool Limit:** 4-5 active tools maximum
### **ADHD Profile:** Systematic investigation, hypothesis tracking, visual understanding

---

## 📋 Planner Role (Task Management & Organization)

### **Primary Tools (Always Active)**
1. **Context7** - Technical feasibility validation
   - **Usage:** Ensure planned tasks are technically feasible
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Reality-check planning with actual capabilities

2. **ConPort** - Planning context and decision tracking
   - **Usage:** Track planning decisions and task evolution
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Maintains planning context across sessions

3. **Task Master AI** - Task decomposition and management
   - **Usage:** Break down projects into manageable tasks
   - **Token Cost:** ~1,000-3,000 per breakdown
   - **ADHD Benefit:** ADHD-optimized task chunking and prioritization

4. **Zen: Planner** - Structured project planning
   - **Usage:** Create detailed implementation plans
   - **Token Cost:** ~1,000-3,000 per plan
   - **ADHD Benefit:** Structured approach to complex project planning

5. **ClearThought** - Decision frameworks for prioritization
   - **Usage:** Structured decision making for task priorities
   - **Token Cost:** ~1,000-3,000 per framework
   - **ADHD Benefit:** Clear criteria for difficult prioritization decisions

### **Secondary Tools (Limited Usage)**
- **Zen: Consensus** - Validation of planning decisions

### **On-Demand Tools (Special Cases)**
- **MAS Sequential** - For complex architectural planning

### **Token Budget:** 8,000 per session
### **Tool Limit:** 3-4 active tools maximum
### **ADHD Profile:** Structured organization, clear hierarchies, manageable chunks

---

## ⚙️ Ops Role (Automation & Deployment)

### **Primary Tools (Always Active)**
1. **Context7** - Tool documentation and deployment guides
   - **Usage:** Understand deployment tools and infrastructure APIs
   - **Token Cost:** ~100-500 per query
   - **ADHD Benefit:** Reliable documentation for operations tasks

2. **ConPort** - Operations documentation and process tracking
   - **Usage:** Document operational procedures and decisions
   - **Token Cost:** ~50-200 per save
   - **ADHD Benefit:** Maintains operational knowledge and procedures

3. **Desktop Commander** - System automation and control
   - **Usage:** Automate deployment and system management tasks
   - **Token Cost:** ~200-800 per automation
   - **ADHD Benefit:** Reduces manual work and human error

4. **MorphLLM** - Configuration file updates and bulk operations
   - **Usage:** Update configurations across multiple files
   - **Token Cost:** ~100-500 per bulk operation
   - **ADHD Benefit:** Fast, reliable bulk configuration changes

5. **Zen: Refactor** - Infrastructure code refactoring
   - **Usage:** Improve and maintain infrastructure code
   - **Token Cost:** ~1,500-4,000 per refactoring
   - **ADHD Benefit:** Systematic approach to infrastructure improvements

6. **Zen: DocGen** - Operations documentation generation
   - **Usage:** Generate and maintain operational documentation
   - **Token Cost:** ~1,000-3,000 per generation
   - **ADHD Benefit:** Automated documentation reduces manual work

### **Secondary Tools (Limited Usage)**
- **Claude Context** - Find similar operational patterns
- **Zen: Tracer** - Understand system dependencies

### **Token Budget:** 6,000 per session
### **Tool Limit:** 3-4 active tools maximum
### **ADHD Profile:** Automation focus, predictable processes, reduced manual work

---

## 🔄 Dynamic Role Switching

### **Context Preservation During Switches**
When switching between roles, ConPort automatically:
1. Saves current role context and tool state
2. Loads target role context and available tools
3. Maintains conversation history across roles
4. Preserves decision tracking and progress

### **Switch Time Targets**
- **Developer ↔ Debugger:** <5 seconds (similar toolsets)
- **Researcher ↔ Architect:** <10 seconds (different focus, some overlap)
- **Any Role ↔ Planner:** <5 seconds (lightweight toolset)
- **Cold start (no previous context):** <15 seconds

### **ADHD Optimizations**
- **Visual role indicator:** Clear display of current role and available tools
- **Gentle transitions:** No jarring changes or lost context
- **Quick access:** Most recently used roles are faster to access
- **Smart suggestions:** Suggests role switches based on current task

---

## 📊 Tool Usage Analytics

### **Success Metrics to Track**
1. **Token efficiency:** Actual vs estimated token usage per role
2. **Task completion rate:** How often roles complete intended tasks
3. **Context switch frequency:** How often users need to switch tools/roles
4. **Flow state maintenance:** Time spent in uninterrupted work
5. **Decision time:** How quickly users choose appropriate tools

### **ADHD-Specific Metrics**
1. **Cognitive load score:** Based on number of active tools and decisions
2. **Context preservation effectiveness:** Recovery time after interruptions
3. **Tool discovery time:** How quickly users find the right tool
4. **Overwhelm indicators:** Signs of too many choices or options
5. **Productivity patterns:** Most effective tool combinations per user

### **Optimization Triggers**
- **High token usage:** Suggest more efficient tool combinations
- **Frequent role switching:** Recommend broader tool access
- **Long decision times:** Simplify tool choices or provide better guidance
- **Low completion rates:** Adjust tool availability or provide training

This matrix provides the foundation for implementing ADHD-optimized development workflows that maximize productivity while minimizing cognitive load and decision fatigue.