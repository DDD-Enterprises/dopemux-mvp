# Dopemux Multi-Language Support Architecture

**Version**: 1.0.0
**Date**: 2025-10-04
**Supported Languages**: Python, TypeScript, JavaScript, C, C++, Go, PHP
**Integration**: Language-specific personas + language-agnostic agents

---

## Executive Summary

**Key Principle**: **Language-specific personas + language-agnostic infrastructure**

- **Personas**: Language-specific behavioral guidelines (Python Expert, TypeScript Expert, C++ Expert, etc.)
- **Agents**: Language-agnostic infrastructure (work with ANY language)
- **Tools**: Multi-language support (Serena LSP supports Python/TS/JS/Go/Rust, ConPort language-agnostic)

**Current Coverage**:
- ✅ Python → Python Expert persona
- ✅ TypeScript/JavaScript → Frontend Architect, Backend Architect personas
- ⚠️ Go → Backend Architect (needs Go-specific enhancement)
- ⚠️ PHP → Backend Architect (needs PHP-specific enhancement)
- ❌ C/C++ → Missing dedicated persona (needs creation)

---

## How Multi-Language Works

### Layer 1: Language-Specific Personas (Behavioral Guidelines)

Each language has specialized persona(s) that know:
- Language idioms and best practices
- Language-specific tooling
- Framework patterns
- Testing approaches
- Common pitfalls

**Persona Mapping**:

```yaml
Python:
  primary_persona: "Python Expert"
  knowledge:
    - Modern Python (3.11+): type hints, dataclasses, async/await
    - Testing: pytest, unittest
    - Frameworks: FastAPI, Django, Flask
    - Tools: Black, mypy, ruff, poetry, uv

TypeScript:
  primary_persona: "Frontend Architect"
  knowledge:
    - TypeScript: generics, utility types, strict mode
    - Testing: Vitest, Jest
    - Frameworks: React, Vue, Next.js, Svelte
    - Tools: TypeScript compiler, ESLint, Prettier

JavaScript:
  primary_persona: "Frontend Architect" | "Backend Architect"
  knowledge:
    - Modern JS: ES2023+, async/await, modules
    - Testing: Jest, Mocha, Vitest
    - Frontend: React, Vue, vanilla
    - Backend: Node.js, Express, Fastify
    - Tools: ESLint, Prettier

Go:
  primary_persona: "Backend Architect" (needs Go enhancement)
  knowledge:
    - Go idioms: interfaces, goroutines, channels
    - Testing: go test, testify
    - Frameworks: Gin, Echo, standard library
    - Tools: gofmt, golangci-lint

PHP:
  primary_persona: "Backend Architect" (needs PHP enhancement)
  knowledge:
    - Modern PHP (8.2+): typed properties, attributes, enums
    - Testing: PHPUnit, Pest
    - Frameworks: Laravel, Symfony
    - Tools: Composer, PHPStan, PHP-CS-Fixer

C:
  primary_persona: "Systems Engineer" (needs creation)
  knowledge:
    - C standards: C11, C17, C23
    - Memory management, pointers
    - Testing: Unity, CUnit
    - Build: Make, CMake
    - Tools: GCC, Clang, Valgrind

C++:
  primary_persona: "Systems Engineer" (needs creation)
  knowledge:
    - Modern C++: C++17, C++20, C++23
    - RAII, smart pointers, templates
    - Testing: Google Test, Catch2
    - Build: CMake, Bazel
    - Tools: Clang, GCC, Clang-Tidy
```

### Layer 2: Language-Agnostic Infrastructure (7 Agents)

**Critical Understanding**: All 7 agents are language-agnostic - they work with ANY language.

#### 1. MemoryAgent (Language-Agnostic)

**Why Language-Agnostic**:
- Stores context in ConPort (text-based, no language parsing)
- Saves "current focus", "next steps", "decisions" - language-independent concepts
- Works same way for Python, TypeScript, C++, etc.

```python
# Python project
await memory_agent.save_checkpoint(
    context="Implementing JWT auth in FastAPI",
    language="python"
)

# TypeScript project
await memory_agent.save_checkpoint(
    context="Implementing JWT auth in Next.js",
    language="typescript"
)

# Same agent, different language metadata
```

#### 2. CognitiveGuardian (Language-Agnostic)

**Why Language-Agnostic**:
- ADHD accommodations apply to ALL programming (break reminders, complexity scoring)
- Attention states (focused, scattered, hyperfocus) are language-independent
- Complexity scoring uses Serena's language-aware analysis but presents results uniformly

```python
# Complexity scoring works for any language
complexity = await cognitive_guardian.estimate_complexity(
    file="src/auth/manager.py",  # Python
    language="python"
)
# → Returns 0.0-1.0 score (language-agnostic scale)

complexity = await cognitive_guardian.estimate_complexity(
    file="src/auth/manager.ts",  # TypeScript
    language="typescript"
)
# → Returns 0.0-1.0 score (same scale)
```

#### 3. TwoPlaneOrchestrator (Language-Agnostic)

**Why Language-Agnostic**:
- Two-plane architecture is organizational, not language-specific
- PM Plane (Leantime, Task-Master) doesn't care about language
- Cognitive Plane (Serena, ConPort) handles all languages

```python
# Works identically for any language
await two_plane_orchestrator.update_task_status(
    task_id="TASK-123",
    status="implemented",
    language="python"  # Metadata only
)
```

#### 4. TaskDecomposer (Language-Agnostic)

**Why Language-Agnostic**:
- Breaks tasks by complexity/duration, not by language
- ADHD chunking (15-90 min) applies to all languages
- Language only affects complexity estimation (delegated to Serena)

```python
# Decomposes tasks for any language
tasks = await task_decomposer.decompose(
    prd="Implement authentication system",
    language="go"  # Used for complexity estimation
)
# → Returns ADHD-sized chunks regardless of language
```

#### 5. DopemuxEnforcer (Language-Agnostic)

**Why Language-Agnostic**:
- Validates dopemux architecture rules (two-plane, authority matrix)
- These rules apply regardless of language
- Uses Serena for language-specific code analysis, but validates architecture patterns

```python
# Validates architecture rules for any language
compliance = await dopemux_enforcer.validate_change(
    file="src/auth/manager.cpp",
    language="cpp"
)
# → Checks: two-plane boundaries, tool usage, ADHD patterns
# Same rules for C++ as for Python
```

#### 6. ToolOrchestrator (Language-Aware Routing)

**Why Language-Agnostic with Language-Aware Routing**:
- Tool selection logic is language-agnostic
- Routes to language-specific tools where needed

```python
# Language-aware tool selection
tools = await tool_orchestrator.select_tools({
    "task": "implementation",
    "language": "python"
})
# → Returns: Serena (Python LSP), PAL apilookup (Python docs)

tools = await tool_orchestrator.select_tools({
    "task": "implementation",
    "language": "typescript"
})
# → Returns: Serena (TypeScript LSP), PAL apilookup (TypeScript docs)

# Same orchestration logic, different tool instances
```

#### 7. WorkflowCoordinator (Language-Agnostic)

**Why Language-Agnostic**:
- Workflows (Design → Implement → Test → Document) are language-independent
- Delegates to language-specific personas for execution

```python
# Same workflow pattern for any language
workflow = await workflow_coordinator.execute_workflow(
    workflow_name="feature_implementation",
    language="go"
)

# Workflow steps:
# 1. Design → System Architect persona
# 2. Implement → Backend Architect persona (with Go knowledge)
# 3. Test → Quality Engineer persona (with go test knowledge)
# 4. Document → Technical Writer persona

# Workflow structure is identical, persona knowledge differs
```

---

## Multi-Language Project Example

**Scenario**: Dopemux itself (Python backend + TypeScript dashboard)

### File Structure
```
dopemux-mvp/
├── services/
│   ├── conport/          # Python (FastAPI + PostgreSQL)
│   ├── serena/v2/        # Python (LSP server)
│   └── adhd-engine/      # Python (session management)
├── dashboard/            # TypeScript (Next.js + React)
├── shared/
│   └── types/           # TypeScript (shared types)
└── docs/                # Markdown
```

### How Claude Handles This (Multi-Language Session)

**Task 1: "Fix authentication bug in ConPort API"**

```python
# Step 1: Command recognition
command = "/dx:implement fix auth bug in ConPort"

# Step 2: Language detection (via file analysis)
language = detect_language("services/conport/")  # → "python"

# Step 3: Persona selection
persona = select_persona(language, task_type="debugging")
# → "Python Expert" (knows FastAPI, pytest, async/await)

# Step 4: Apply Python Expert guidelines
# - Use Serena with Python LSP
# - Follow Python testing patterns
# - Use FastAPI best practices

# Step 5: Agents support (language-agnostic)
# - MemoryAgent saves context
# - CognitiveGuardian monitors complexity
# - DopemuxEnforcer validates compliance
```

**Task 2: "Add new dashboard component"**

```typescript
// Step 1: Command recognition
command = "/dx:implement add dashboard component"

// Step 2: Language detection
language = detect_language("dashboard/")  // → "typescript"

// Step 3: Persona selection
persona = select_persona(language, task_type="implementation")
// → "Frontend Architect" (knows React, Next.js, TypeScript)

// Step 4: Apply Frontend Architect guidelines
// - Use Serena with TypeScript LSP
// - Follow React patterns
// - Use Next.js conventions

// Step 5: Same agents support (language-agnostic)
// - MemoryAgent saves context
// - CognitiveGuardian monitors complexity
// - DopemuxEnforcer validates compliance
```

**Task 3: "Refactor shared types"**

```typescript
// Step 1: Command recognition
command = "/dx:improve refactor shared types"

// Step 2: Multi-language detection
files_affected = [
    "services/conport/models.py",      // Python
    "dashboard/types/api.ts",          // TypeScript
    "shared/types/common.ts"           // TypeScript
]

// Step 3: Multi-persona coordination
personas_needed = {
    "python": "Python Expert",
    "typescript": "Frontend Architect"
}

// Step 4: WorkflowCoordinator orchestrates
workflow = {
    steps: [
        {
            persona: "Frontend Architect",
            task: "Define shared TypeScript types",
            language: "typescript"
        },
        {
            persona: "Python Expert",
            task: "Update Python models to match",
            language: "python"
        },
        {
            persona: "Quality Engineer",
            task: "Validate type compatibility",
            languages: ["python", "typescript"]
        }
    ]
}

// Step 5: Agents support across all languages
// - MemoryAgent tracks cross-language changes
// - DopemuxEnforcer validates consistency
```

---

## Language-Specific Tool Integration

### Serena LSP (Multi-Language Code Intelligence)

**Supported Languages**:
- Python: `pylsp` (Python Language Server Protocol)
- TypeScript/JavaScript: `typescript-language-server`
- Go: `gopls`
- Rust: `rust-analyzer`
- C/C++: `clangd`

**How It Works**:

```python
# Serena auto-detects language from file extension
file = "src/auth/manager.py"
# → Uses pylsp for Python analysis

file = "src/auth/manager.ts"
# → Uses typescript-language-server for TypeScript

file = "src/auth/manager.go"
# → Uses gopls for Go

# Same Serena API, different LSP backends
symbol = await serena.find_symbol(
    query="AuthManager",
    file=file  # Language detected from extension
)
```

### PAL apilookup (Multi-Language Documentation)

**Library Support**:

```python
# Python libraries
docs = await mcp__pal__apilookup(
    prompt="/pallets/flask",
    topic="authentication"
)

# TypeScript/JavaScript libraries
docs = await mcp__pal__apilookup(
    prompt="/vercel/next.js",
    topic="authentication"
)

# Go libraries
docs = await mcp__pal__apilookup(
    prompt="/gin-gonic/gin",
    topic="middleware"
)

# PHP libraries
docs = await mcp__pal__apilookup(
    prompt="/laravel/laravel",
    topic="authentication"
)
```

### ConPort (Language-Agnostic Knowledge Graph)

```python
# Decision logging works for any language
await conport.log_decision(
    summary="Use JWT tokens for auth",
    rationale="Stateless, scalable, standard",
    tags=["authentication", "python", "fastapi"]  # Language as metadata
)

await conport.log_decision(
    summary="Use JWT tokens for auth (frontend)",
    rationale="Match backend approach, httpOnly cookies",
    tags=["authentication", "typescript", "nextjs"]  # Different language, same pattern
)

# ConPort links cross-language decisions
await conport.link_items(
    source=("decision", "143"),  # Python backend decision
    target=("decision", "144"),  # TypeScript frontend decision
    relationship="implements_in_different_language"
)
```

---

## Persona Enhancement for Missing Languages

### C/C++ Systems Engineer Persona (NEW)

```markdown
# Systems Engineer Persona (Dopemux-Enhanced)

**Languages**: C, C++
**Focus**: Systems programming, performance-critical code, memory management

## Core Expertise

**C Knowledge**:
- Modern C: C11, C17, C23 features
- Memory management: malloc/free, custom allocators
- Pointers, pointer arithmetic, function pointers
- Build systems: Make, CMake, Autotools

**C++ Knowledge**:
- Modern C++: C++17, C++20, C++23 features
- RAII, smart pointers (unique_ptr, shared_ptr)
- Templates, metaprogramming, concepts
- STL, ranges, coroutines

## Dopemux Integration

### Tool Preferences
- Code navigation: Serena with `clangd` LSP
- Documentation: PAL apilookup (cppreference, C++ docs)
- Build: CMake, Bazel
- Testing: Google Test, Catch2

### ADHD Accommodations
- Complexity scoring: Memory management = +0.2 to base complexity
- Break reminders: Pointer-heavy code triggers extra caution
- Progressive disclosure: Show function signature → implementation → memory patterns
```

### Backend Architect Enhancement (Go + PHP)

```markdown
# Backend Architect Persona (Dopemux-Enhanced)

**Languages**: Node.js, Go, PHP, Python (backend)

## Language-Specific Knowledge

### Go
- Idioms: goroutines, channels, interfaces
- Standard library patterns
- Testing: go test, testify
- Tools: gofmt, golangci-lint
- Frameworks: Gin, Echo, standard library

### PHP
- Modern PHP (8.2+): typed properties, attributes, enums
- Frameworks: Laravel, Symfony
- Testing: PHPUnit, Pest
- Tools: Composer, PHPStan, PHP-CS-Fixer

### Node.js/TypeScript Backend
- Modern Node: ESM, async/await, streams
- Frameworks: Express, Fastify, NestJS
- Testing: Jest, Vitest
- Tools: TypeScript, ESLint, Prettier
```

---

## Language Detection and Routing

### Automatic Language Detection

```python
async def detect_language(file_path: str) -> str:
    """Detect language from file extension and content"""

    extension_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".h": "c",
        ".hpp": "cpp"
    }

    ext = Path(file_path).suffix
    return extension_map.get(ext, "unknown")

async def select_persona_for_language(
    language: str,
    task_type: str
) -> str:
    """Select appropriate persona based on language and task"""

    persona_map = {
        "python": {
            "implementation": "python_expert",
            "debugging": "python_expert",
            "refactoring": "python_expert",
            "testing": "quality_engineer"
        },
        "typescript": {
            "implementation": "frontend_architect",
            "debugging": "frontend_architect",
            "refactoring": "refactoring_expert",
            "testing": "quality_engineer"
        },
        "go": {
            "implementation": "backend_architect",
            "debugging": "backend_architect",
            "refactoring": "backend_architect",
            "testing": "quality_engineer"
        },
        "c": {
            "implementation": "systems_engineer",
            "debugging": "systems_engineer",
            "refactoring": "systems_engineer",
            "testing": "quality_engineer"
        },
        "cpp": {
            "implementation": "systems_engineer",
            "debugging": "systems_engineer",
            "refactoring": "systems_engineer",
            "testing": "quality_engineer"
        }
    }

    return persona_map[language][task_type]
```

---

## Usage Tracking Across Languages

```python
# Track persona usage with language metadata
await conport.log_custom_data(
    category="persona_usage",
    key=f"python_expert_{timestamp}",
    value={
        "persona": "python_expert",
        "language": "python",
        "task_type": "implementation",
        "complexity": 0.6
    }
)

# Query: Which languages are we working in most?
usage = await conport.get_custom_data(category="persona_usage")
language_distribution = Counter(u["language"] for u in usage)
# → python: 45, typescript: 32, go: 8, php: 3

# Query: Which persona handles which languages?
persona_language_map = {}
for u in usage:
    persona = u["persona"]
    language = u["language"]
    persona_language_map.setdefault(persona, Counter())[language] += 1

# → python_expert: {python: 45}
# → frontend_architect: {typescript: 28, javascript: 4}
# → backend_architect: {typescript: 8, go: 8, php: 3}
```

---

## Summary: Multi-Language Support

### What Makes It Work

1. **Language-Specific Personas**:
   - Python Expert (Python)
   - Frontend Architect (TypeScript, JavaScript)
   - Backend Architect (Go, PHP, Node.js)
   - Systems Engineer (C, C++) ← needs creation
   - Each knows language-specific patterns, tools, idioms

2. **Language-Agnostic Infrastructure**:
   - All 7 agents work with ANY language
   - ADHD accommodations apply universally
   - Architecture rules (two-plane, authority) are language-independent

3. **Multi-Language Tools**:
   - Serena LSP: Python, TS, JS, Go, Rust, C/C++ via different LSP backends
   - PAL apilookup: Documentation for all popular libraries
   - ConPort: Language-agnostic knowledge graph

4. **Intelligent Routing**:
   - Auto-detect language from file extension
   - Select appropriate persona based on language + task
   - Coordinate across languages for multi-language features

### What Needs Enhancement

- ✅ Python Expert: Fully enhanced (template exists)
- ⚠️ Frontend Architect: Needs TypeScript-specific dopemux enhancements
- ⚠️ Backend Architect: Needs Go/PHP-specific dopemux enhancements
- ❌ Systems Engineer: Needs creation for C/C++

**Next Steps**:
1. Create Systems Engineer persona for C/C++
2. Enhance Frontend Architect with TypeScript specifics
3. Enhance Backend Architect with Go/PHP specifics
4. Test multi-language project (dopemux itself!)

---

**Status**: Multi-language support is inherent in the architecture
**Key**: Language-specific personas + language-agnostic agents = full coverage
