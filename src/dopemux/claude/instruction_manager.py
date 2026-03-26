"""
Dopemux Instruction Manager.

Handles the dynamic assembly of Claude Code instruction sets by merging
global guidelines, project-specific standards, and role-based personas.
"""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class InstructionManager:
    """
    Manages the lifecycle and assembly of AI instructions.
    
    Acts as the 'brain' for tailoring Claude Code's behavior based on the
    current task role and project context.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.personas_dir = project_root / ".claude" / "personas"
        self.instructions_dir = project_root / "config" / "instructions"
        
    def list_personas(self) -> List[str]:
        """List all available personas in the project."""
        if not self.personas_dir.exists():
            return []
        return [f.stem.replace(".agent", "") for f in self.personas_dir.glob("*.agent.md")]
        
    def get_persona_content(self, persona_name: str) -> Optional[str]:
        """Get the raw content of a specific persona guideline."""
        # Common aliases
        aliases = {
            "research": "task-researcher",
            "plan": "task-planner",
            "act": "principal-software-engineer",
            "dev": "principal-software-engineer",
            "quickfix": "janitor",
            "workflow": "workflow-manager",
            "manager": "workflow-manager",
            "executor": "workflow-executor",
        }
        target_name = aliases.get(persona_name.lower(), persona_name)
        
        persona_path = self.personas_dir / f"{target_name}.agent.md"
        if persona_path.exists():
            return persona_path.read_text(encoding='utf-8')
        return None
        
    def get_global_instructions(self) -> str:
        """Collect and merge all global instructions from config/instructions."""
        merged = []
        if self.instructions_dir.exists():
            for f in sorted(self.instructions_dir.glob("*.instructions.md")):
                content = f.read_text(encoding='utf-8')
                merged.append(f"### {f.stem.replace('.instructions', '').title()}\n{content}")
        return "\n\n".join(merged)
        
    def assemble_instructions(self, role: Optional[str] = None, project_type: str = "python") -> str:
        """
        Assemble a complete instruction set for Claude Code.
        
        Args:
            role: The specific persona/role to activate.
            project_type: The language/framework context.
        """
        # 1. Start with the project-specific base (provided by configurator)
        # 2. Add Global Instruction Set
        global_instr = self.get_global_instructions()
        
        # 3. Add Active Persona Guidelines
        role_content = ""
        if role:
            role_content = self.get_persona_content(role)
            if not role_content:
                # Try fallback names or fuzzy matching
                pass
                
        # 4. Assemble the final manifest
        sections = []
        if role_content:
            sections.append(f"## ACTIVE ROLE: {role.upper()}\n{role_content}")
            
        if global_instr:
            sections.append(f"## GLOBAL GUIDELINES\n{global_instr}")
            
        return "\n\n".join(sections)
