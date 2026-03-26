from pathlib import Path

from dopemux.claude.instruction_manager import InstructionManager


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_instruction_manager_resolves_workflow_aliases():
    manager = InstructionManager(REPO_ROOT)

    workflow_content = manager.get_persona_content("workflow")
    executor_content = manager.get_persona_content("executor")

    assert workflow_content is not None
    assert executor_content is not None
    assert "workflow-checkpoint" in workflow_content
    assert "workflow-checkpoint" in executor_content


def test_workflow_personas_and_skills_avoid_imported_franchise_voice():
    files = [
        REPO_ROOT / ".claude/personas/workflow-manager.agent.md",
        REPO_ROOT / ".claude/personas/workflow-executor.agent.md",
        REPO_ROOT / "templates/skills/brief-drafter/SKILL.md",
        REPO_ROOT / "templates/skills/task-breakdown/SKILL.md",
        REPO_ROOT / "templates/skills/code-researcher/SKILL.md",
        REPO_ROOT / "templates/skills/research-reviewer/SKILL.md",
        REPO_ROOT / "templates/skills/implementation-planner/SKILL.md",
        REPO_ROOT / "templates/skills/plan-reviewer/SKILL.md",
        REPO_ROOT / "templates/skills/code-implementer/SKILL.md",
        REPO_ROOT / "templates/skills/quality-refactorer/SKILL.md",
    ]
    forbidden_terms = (
        "pickle rick",
        "morty",
        "jerry",
        "gemini extension",
    )

    for file_path in files:
        text = file_path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            assert term not in text, f"{term!r} leaked into {file_path}"
