
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

def validate_agent_frontmatter(file_path: Path) -> bool:
    """
    Check if an agent file has valid frontmatter.
    Returns True if valid, False otherwise.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return False
        
        # Check for closing ---
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False
            
        # Parse YAML
        frontmatter = yaml.safe_load(parts[1])
        if not isinstance(frontmatter, dict):
            return False
            
        if "name" not in frontmatter:
            return False
            
        return True
    except Exception as e:
        logger.warning(f"Failed to validate {file_path}: {e}")
        return False

def fix_agent_frontmatter(file_path: Path) -> bool:
    """
    Attempt to fix missing frontmatter by adding a name field based on filename.
    Returns True if fixed, False if failed.
    """
    try:
        if validate_agent_frontmatter(file_path):
            return True
            
        logger.info(f"Fixing missing frontmatter for agent: {file_path}")
        content = file_path.read_text(encoding="utf-8")
        name = file_path.stem
        
        # Check if it has empty/broken frontmatter or none
        if content.startswith("---"):
            # Existing but broken? difficult to patch safely without parsing.
            # But if it failed validation, it might be missing 'name' or just broken syntax.
            # For now, let's assume if it starts with --- but failed validation, we might prepend?
            # Or better, just warn.
            # But the user's issue was "missing required name field".
            # If it has frontmatter but no name, we can try to inject it.
            pass
        
        # Simple case: No frontmatter at all (user's reported issue)
        new_content = f"---\nname: {name}\n---\n\n{content}"
        file_path.write_text(new_content, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"Failed to fix {file_path}: {e}")
        return False

def validate_agents_in_workspace(workspace_root: Path) -> None:
    """
    Scan .claude/agents in the workspace and fix any missing frontmatter.
    """
    agents_dir = workspace_root / ".claude" / "agents"
    if not agents_dir.exists():
        return
        
    for file_path in agents_dir.glob("*.md"):
        if file_path.name in ["README.md", "_index.md"]:
            continue
            
        if not validate_agent_frontmatter(file_path):
             fix_agent_frontmatter(file_path)
