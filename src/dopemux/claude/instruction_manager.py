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
        return [
            f.stem.replace(".agent", "") for f in self.personas_dir.glob("*.agent.md")
        ]

    # Canonical mapping from catalog role keys (and common aliases) to the best
    # matching persona file stem (without the .agent.md suffix).  The alias table
    # is checked first; if not present the name is used verbatim.  Entries added
    # here cover every key in ROLE_CATALOG so catalog-default roles (developer,
    # architect, reviewer, debugger, ops) are no longer silently unmapped.
    ROLE_ALIASES: dict = {
        # pre-existing aliases
        "research": "task-researcher",
        "plan": "task-planner",
        "act": "principal-software-engineer",
        "dev": "principal-software-engineer",
        "quickfix": "janitor",
        "workflow": "workflow-manager",
        "manager": "workflow-manager",
        "executor": "workflow-executor",
        # catalog keys now covered (F1)
        "developer": "principal-software-engineer",
        "architect": "se-system-architecture-reviewer",
        # "reviewer" maps to wg-code-sentinel (general code-review sentinel,
        # broader than se-security-reviewer which is security-specialised).
        "reviewer": "wg-code-sentinel",
        "debugger": "principal-software-engineer",
        "ops": "devops-expert",
    }

    # Packaged fallback personas directory (used when project .claude/personas/
    # is absent or does not contain the resolved name).  Populated during install
    # via pyproject.toml package-data.
    _PACKAGED_PERSONAS_DIR: Optional[Path] = None

    @classmethod
    def _get_packaged_personas_dir(cls) -> Optional[Path]:
        """Return the packaged personas directory, or None if not found."""
        if cls._PACKAGED_PERSONAS_DIR is not None:
            return cls._PACKAGED_PERSONAS_DIR
        candidate = Path(__file__).parent.parent / "personas"
        if candidate.is_dir():
            cls._PACKAGED_PERSONAS_DIR = candidate
            return candidate
        return None

    def get_persona_content(self, persona_name: str) -> Optional[str]:
        """Get the raw content of a specific persona guideline.

        Resolution order:
        1. Apply the alias table to map catalog keys and common shorthands to a
           canonical persona file stem.
        2. Look up ``<project>/.claude/personas/<stem>.agent.md``.
        3. Fall back to the packaged personas bundled with the dopemux package
           (F3), so ``dopemux init`` projects resolve personas without needing a
           local personas directory.
        """
        normalized = persona_name.lower()
        aliased_name = self.ROLE_ALIASES.get(normalized)
        # Candidates in priority order:
        # 1. Alias target (e.g. developer → principal-software-engineer)
        # 2. Verbatim name (preserves local overrides like developer.agent.md)
        candidates = [aliased_name, persona_name] if aliased_name else [persona_name]

        # 1. Project-local personas directory (highest precedence for each candidate).
        for name in candidates:
            if name is None:
                continue
            persona_path = self.personas_dir / f"{name}.agent.md"
            if persona_path.exists():
                return persona_path.read_text(encoding="utf-8")

        # 2. Packaged fallback (F3) — resolves for dopemux init projects that
        #    have no local personas directory.
        packaged_dir = self._get_packaged_personas_dir()
        if packaged_dir is not None:
            for name in candidates:
                if name is None:
                    continue
                packaged_path = packaged_dir / f"{name}.agent.md"
                if packaged_path.exists():
                    return packaged_path.read_text(encoding="utf-8")

        return None

    def get_global_instructions(self) -> str:
        """Collect and merge all global instructions from config/instructions."""
        merged = []
        if self.instructions_dir.exists():
            for f in sorted(self.instructions_dir.glob("*.instructions.md")):
                content = f.read_text(encoding="utf-8")
                merged.append(
                    f"### {f.stem.replace('.instructions', '').title()}\n{content}"
                )
        return "\n\n".join(merged)

    def assemble_instructions(
        self, role: Optional[str] = None, project_type: str = "python"
    ) -> str:
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
