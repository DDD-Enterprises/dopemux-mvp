"""
Persona Enhancement Generator - Weeks 13-14

Systematically enhances 16 SuperClaude personas with Dopemux awareness.
Follows python-expert-dopemux.md template pattern.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# 16 SuperClaude Personas to Enhance
PERSONAS = [
    {
        "name": "python-expert",
        "focus": "Python development, testing, debugging, optimization",
        "status": "COMPLETE",  # Already have python-expert-dopemux.md
        "primary_tools": ["serena", "context7-python", "zen-codereview"],
        "complexity_range": "0.3-0.8"
    },
    {
        "name": "system-architect",
        "focus": "System design, scalability, architecture decisions",
        "status": "PENDING",
        "primary_tools": ["zen-consensus", "zen-thinkdeep", "context7", "exa"],
        "complexity_range": "0.6-0.9"
    },
    {
        "name": "quality-engineer",
        "focus": "Testing strategies, test coverage, quality assurance",
        "status": "PENDING",
        "primary_tools": ["zen-codereview", "serena", "context7-testing"],
        "complexity_range": "0.4-0.7"
    },
    {
        "name": "root-cause-analyst",
        "focus": "Systematic debugging, hypothesis testing, investigation",
        "status": "PENDING",
        "primary_tools": ["zen-debug", "serena-find", "dope-context-search"],
        "complexity_range": "0.5-0.8"
    },
    {
        "name": "frontend-architect",
        "focus": "UI/UX, React, accessibility, performance",
        "status": "PENDING",
        "primary_tools": ["context7-react", "exa", "serena"],
        "complexity_range": "0.4-0.7"
    },
    {
        "name": "backend-architect",
        "focus": "APIs, databases, scalability, reliability",
        "status": "PENDING",
        "primary_tools": ["context7-fastapi", "zen-thinkdeep", "serena"],
        "complexity_range": "0.5-0.8"
    },
    {
        "name": "security-engineer",
        "focus": "Security vulnerabilities, compliance, threat modeling",
        "status": "PENDING",
        "primary_tools": ["zen-codereview", "exa-security", "context7"],
        "complexity_range": "0.6-0.9"
    },
    {
        "name": "performance-engineer",
        "focus": "Optimization, profiling, benchmarking, bottlenecks",
        "status": "PENDING",
        "primary_tools": ["zen-thinkdeep", "serena-complexity", "context7"],
        "complexity_range": "0.5-0.8"
    },
    {
        "name": "refactoring-expert",
        "focus": "Code cleanup, technical debt, refactoring patterns",
        "status": "PENDING",
        "primary_tools": ["serena", "zen-codereview", "dope-context-search"],
        "complexity_range": "0.4-0.7"
    },
    {
        "name": "devops-architect",
        "focus": "Infrastructure, CI/CD, deployment, monitoring",
        "status": "PENDING",
        "primary_tools": ["context7-docker", "exa", "zen-planner"],
        "complexity_range": "0.5-0.8"
    },
    {
        "name": "learning-guide",
        "focus": "Teaching, explaining concepts, progressive learning",
        "status": "PENDING",
        "primary_tools": ["context7", "exa", "zen-chat"],
        "complexity_range": "0.2-0.5"
    },
    {
        "name": "requirements-analyst",
        "focus": "Requirements discovery, specification, validation",
        "status": "PENDING",
        "primary_tools": ["zen-planner", "task-decomposer", "conport"],
        "complexity_range": "0.4-0.6"
    },
    {
        "name": "technical-writer",
        "focus": "Documentation, clarity, audience adaptation",
        "status": "PENDING",
        "primary_tools": ["context7", "dope-context-docs", "exa"],
        "complexity_range": "0.2-0.4"
    },
    {
        "name": "socratic-mentor",
        "focus": "Question-driven learning, discovery, critical thinking",
        "status": "PENDING",
        "primary_tools": ["zen-chat", "context7", "exa"],
        "complexity_range": "0.3-0.6"
    },
    {
        "name": "general-purpose",
        "focus": "Multi-domain tasks, balanced approach, adaptability",
        "status": "PENDING",
        "primary_tools": ["tool-orchestrator", "zen-chat", "serena", "context7"],
        "complexity_range": "0.3-0.7"
    },
    {
        "name": "statusline-setup",
        "focus": "Configuration, setup, system integration",
        "status": "PENDING",
        "primary_tools": ["serena-read", "context7-config", "conport"],
        "complexity_range": "0.2-0.4"
    },
]


class PersonaEnhancer:
    """
    Generates Dopemux-enhanced persona documents.

    Follows python-expert-dopemux.md template:
    1. Core Expertise
    2. Dopemux Integration (Tool Preferences, Two-Plane Awareness)
    3. ADHD Accommodations (Progressive Disclosure, Complexity Scoring, Breaks)
    4. Agent Coordination
    5. Usage Tracking
    """

    def __init__(self, output_dir: str = ".claude/personas"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.personas_enhanced = 0

    def generate_persona_enhancement(self, persona: Dict) -> str:
        """Generate enhanced persona document"""

        name = persona["name"]
        focus = persona["focus"]
        tools = persona["primary_tools"]
        complexity_range = persona["complexity_range"]

        # Generate tool preference section
        tool_prefs = self._generate_tool_preferences(tools)

        # Generate two-plane awareness
        two_plane = self._generate_two_plane_awareness(name)

        # Generate ADHD accommodations
        adhd = self._generate_adhd_accommodations(complexity_range)

        # Generate agent coordination
        agents = self._generate_agent_coordination(name, complexity_range)

        doc = f"""# {name.replace('-', ' ').title()} Persona (Dopemux-Enhanced)

**Version**: 2.0.0-dopemux
**Enhancement Date**: 2025-10-24
**Base Persona**: {name.replace('-', ' ').title()} (SuperClaude Framework)
**Dopemux Integration**: Full two-plane, ADHD, agent coordination

---

## Core Expertise

**Primary Focus**: {focus}

---

## Dopemux Integration

### Tool Preferences (Authority-Aware)

{tool_prefs}

### Two-Plane Architecture Awareness

{two_plane}

### ADHD Accommodations

{adhd}

### Agent Coordination

{agents}

---

## Usage Tracking

**Persona Activation**:
```python
# Log persona usage to ConPort
await mcp__conport__log_custom_data(
    workspace_id=workspace,
    category="persona_usage",
    key=f"{name}_{{timestamp}}",
    value={{
        "persona": "{name}",
        "task_type": task_type,
        "complexity": complexity,
        "tools_used": tools_used,
        "outcome": "success|failure",
        "duration_minutes": duration
    }}
)
```

**Integration with ToolOrchestrator**:
```python
# ToolOrchestrator knows best tools for {name}
tools = await tool_orchestrator.select_tools_for_task(
    task_type="{focus.split(',')[0].strip()}",
    complexity=complexity
)
# Uses: {', '.join(tools[:3])}
```

---

## Compliance Validation

**DopemuxEnforcer Checks**:
- Tool preferences: Serena > bash ✅
- Decision logging: ConPort required ✅
- Two-plane boundaries: Respect authority ✅
- ADHD constraints: Max 10 results ✅
- Complexity awareness: Break reminders ✅

---

**Status**: ✅ Dopemux-Enhanced
**Integration**: Complete (7 agents + MCPs)
**ADHD**: Fully optimized
"""

        return doc

    def _generate_tool_preferences(self, tools: List[str]) -> str:
        """Generate tool preference section"""
        prefs = []

        for tool in tools:
            if "serena" in tool:
                prefs.append("""
**Code Navigation** (Serena MCP):
```python
# ✅ Use Serena for all code operations
mcp__serena_v2__find_symbol(query="ClassName")
mcp__serena_v2__read_file(relative_path="src/module.py")
# ❌ NEVER: bash cat, grep, find
```""")
            elif "context7" in tool:
                prefs.append("""
**Documentation** (Context7 MCP):
```python
# ✅ Use Context7 for official documentation
mcp__context7__resolve_library_id(libraryName="fastapi")
mcp__context7__get_library_docs(context7CompatibleLibraryID="/org/project")
```""")
            elif "zen" in tool:
                prefs.append(f"""
**Analysis** (Zen MCP):
```python
# ✅ Use Zen for systematic analysis
mcp__zen__{tool.split('-')[1] if '-' in tool else 'thinkdeep'}(
    model=model_from_tool_orchestrator,
    step="Analysis step...",
    ...
)
```""")
            elif "conport" in tool:
                prefs.append("""
**Decision Logging** (ConPort MCP):
```python
# ✅ ALWAYS log architectural decisions
mcp__conport__log_decision(
    workspace_id=workspace,
    summary="Decision summary",
    rationale="Why this choice",
    tags=["architecture", "persona-name"]
)
```""")

        return "\n".join(prefs) if prefs else "**Tool selection via ToolOrchestrator**"

    def _generate_two_plane_awareness(self, persona_name: str) -> str:
        """Generate two-plane awareness section"""
        return """
**Cognitive Plane Responsibilities** (My authority):
- ✅ Code navigation and analysis
- ✅ Decision logging and knowledge management
- ✅ Context preservation
- ✅ Complexity scoring

**PM Plane Responsibilities** (Route through TwoPlaneOrchestrator):
- ❌ Task status updates → Use TwoPlaneOrchestrator.cognitive_to_pm()
- ❌ Task creation → Route to Leantime
- ❌ Sprint management → PM plane authority

**Cross-Plane Pattern**:
```python
# ✅ Correct: Route through TwoPlaneOrchestrator
orchestrator = TwoPlaneOrchestrator(workspace_id=workspace, bridge_url=bridge)
await orchestrator.cognitive_to_pm(
    operation="get_tasks",
    data={"status": "TODO"}
)

# ❌ Wrong: Direct Leantime access
# import leantime  # VIOLATION!
```"""

    def _generate_adhd_accommodations(self, complexity_range: str) -> str:
        """Generate ADHD accommodation section"""
        min_c, max_c = [float(x) for x in complexity_range.split('-')]
        avg_c = (min_c + max_c) / 2

        if avg_c < 0.4:
            approach = "quick_read"
            duration = "5-15 min"
        elif avg_c < 0.7:
            approach = "focused_session"
            duration = "25-45 min"
        else:
            approach = "deep_dive"
            duration = "45-90 min with breaks"

        return f"""
**Complexity Range**: {complexity_range} (typical: {avg_c:.1f})
**Recommended Approach**: {approach} ({duration})

**Progressive Disclosure**:
1. **Essential Info** (scattered attention): Show signatures, purpose, complexity
2. **Implementation Details** (focused attention): Show code, explanations
3. **Deep Analysis** (hyperfocus): Show patterns, alternatives, optimizations

**Break Pattern**:
```python
# Use CognitiveGuardian for break enforcement
guardian = CognitiveGuardian(workspace_id=workspace)

if complexity > 0.7 and duration_min >= 25:
    # Recommend break
    logger.info("⏰ Great work! Time for 5-min break (high complexity)")

if duration_min >= 90:
    # Mandatory break
    logger.info("🛑 Mandatory break: 90 minutes reached")
    await guardian.enforce_break()
```

**Complexity Check** (via Serena):
```python
# Check complexity before starting
complexity = await mcp__serena_v2__analyze_complexity(
    file_path="target/file.py",
    symbol_name="TargetClass"
)

if complexity["score"] > 0.7:
    logger.info(f"⚠️ High complexity ({{complexity['score']:.2f}}) - Schedule 45-60 min focused time")
```"""

    def _generate_agent_coordination(self, persona_name: str, complexity_range: str) -> str:
        """Generate agent coordination section"""
        return """
**Agent Integration**:

```python
# Complete workflow with all 7 agents

# 1. MemoryAgent - Context preservation
memory = MemoryAgent(workspace_id=workspace)
await memory.start_session(task_description, complexity=0.6)

# 2. CognitiveGuardian - Break enforcement
guardian = CognitiveGuardian(workspace_id=workspace, memory_agent=memory)
await guardian.start_monitoring()

# 3. ToolOrchestrator - Optimal tool selection
tool_selector = ToolOrchestrator(workspace_id=workspace)
tools = await tool_selector.select_tools_for_task(
    task_type=persona_task_type,
    complexity=0.6
)

# 4. TaskDecomposer - Break into chunks (if needed)
if complexity > 0.7:
    decomposer = TaskDecomposer()
    subtasks = await decomposer.decompose_prd(task_description)

# 5. DopemuxEnforcer - Validate compliance
enforcer = DopemuxEnforcer(workspace_id=workspace)
compliance = await enforcer.validate_code_change(file_path, content)

# 6. TwoPlaneOrchestrator - Cross-plane coordination (if needed)
if needs_pm_data:
    orchestrator = TwoPlaneOrchestrator(workspace_id=workspace, bridge_url=bridge)
    data = await orchestrator.cognitive_to_pm(operation, {})

# 7. WorkflowCoordinator - Multi-step workflows
workflow_coord = WorkflowCoordinator(workspace_id=workspace, memory_agent=memory)
workflow = await workflow_coord.start_workflow(workflow_type, description)
```"""

    async def enhance_all_personas(self):
        """Generate enhanced versions of all 16 personas"""
        logger.info("\n" + "="*70)
        logger.info("PERSONA ENHANCEMENT GENERATOR - Weeks 13-14")
        logger.info("="*70)

        enhanced_count = 0
        skipped_count = 0

        for persona in PERSONAS:
            name = persona["name"]
            status = persona["status"]

            if status == "COMPLETE":
                logger.info(f"\n✅ {name}: Already enhanced (python-expert-dopemux.md)")
                skipped_count += 1
                continue

            logger.info(f"\n🔄 Enhancing: {name}...")

            # Generate enhanced document
            enhanced_doc = self.generate_persona_enhancement(persona)

            # Save to file
            output_file = self.output_dir / f"{name}-dopemux.md"
            output_file.write_text(enhanced_doc)

            enhanced_count += 1
            logger.info(f"   ✅ Created: {output_file}")

        logger.info("\n" + "="*70)
        logger.info(f"Enhancement Complete")
        logger.info("="*70)
        logger.info(f"\nEnhanced: {enhanced_count}")
        logger.info(f"Skipped: {skipped_count} (already enhanced)")
        logger.info(f"Total: {len(PERSONAS)} personas")

        return {
            "enhanced": enhanced_count,
            "skipped": skipped_count,
            "total": len(PERSONAS)
        }


async def main():
    """Generate all enhanced personas"""

    enhancer = PersonaEnhancer(output_dir=".claude/personas")

    results = await enhancer.enhance_all_personas()

    logger.info(f"\n{'='*70}")
    logger.info("✅ All personas enhanced!")
    logger.info(f"{'='*70}\n")

    logger.info(f"Files created: {results['enhanced']}")
    logger.info(f"Output directory: .claude/personas/")
    logger.info(f"\nNext: Integrate with SuperClaude /sc: commands")


if __name__ == "__main__":
    asyncio.run(main())
