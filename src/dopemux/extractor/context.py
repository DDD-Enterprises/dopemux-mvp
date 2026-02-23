import os
from pathlib import Path
from typing import List, Optional, Set
import fnmatch

class ContextGatherer:
    """Helper to gather file context for LLM prompts."""

    DEFAULT_EXCLUDES = {
        '.git', '__pycache__', '.DS_Store', 'node_modules',
        '.venv', '.taskx_venv', 'dist', 'build', '.coverage',
        '.pytest_cache', '.mypy_cache', 'htmlcov'
    }

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def gather_file_list(self,
                        include_patterns: Optional[List[str]] = None,
                        exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """
        Recursively list files matching patterns.

        Args:
            include_patterns: List of glob patterns to include (e.g. ["*.py", "*.md"]).
                              If None, includes everything not excluded.
            exclude_patterns: List of glob patterns to exclude (e.g. ["tests/*"]).

        Returns:
            List of Path objects relative to root_path.
        """
        matches = []
        exclude_patterns = exclude_patterns or []

        for root, dirs, files in os.walk(self.root_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.DEFAULT_EXCLUDES]

            for file in files:
                if file in self.DEFAULT_EXCLUDES:
                    continue

                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(self.root_path)
                str_path = str(rel_path)

                # Check exclusions first
                if any(fnmatch.fnmatch(str_path, p) for p in exclude_patterns):
                    continue

                # Check inclusions
                if include_patterns:
                    if any(fnmatch.fnmatch(str_path, p) for p in include_patterns):
                        matches.append(rel_path)
                else:
                    matches.append(rel_path)

        return sorted(matches)

    def read_files(self, files: List[Path]) -> str:
        """
        Read content of multiple files and format as markdown code blocks.

        Args:
            files: List of paths relative to root_path.

        Returns:
            String containing formatted file contents.
        """
        output = []
        for file_path in files:
            abs_path = self.root_path / file_path
            try:
                content = abs_path.read_text(encoding='utf-8', errors='replace')
                output.append(f"File: {file_path}\n```\n{content}\n```\n")
            except Exception as e:
                output.append(f"File: {file_path}\n[Error reading file: {e}]\n")

        return "\n".join(output)

    def get_context_for_phase(self, phase: str) -> str:
        """
        Get context specific to a pipeline phase.

        Args:
            phase: One of 'A', 'H', 'D', 'C', 'R', 'S'.

        Returns:
            String containing relevant file contents/lists.
        """
        if phase == 'A':
            # Repo Control Plane
            patterns = [
                ".github/workflows/*.yml",
                "compose.yml",
                "litellm.config.yaml",
                "mcp-proxy-config.yaml",
                ".pre-commit-config.yaml",
                "pyproject.toml",
                "package.json",
                "src/dopemux/config.py"
            ]
            files = self.gather_file_list(include_patterns=patterns)
            # Add src/dopemux/cli.py but truncated? It's huge.
            # For now, let's just include the full list and key files.

            context = "## Repository Structure\n"
            all_files = self.gather_file_list(exclude_patterns=["*.pyc", "*.lock"])
            context += "\n".join([str(f) for f in all_files[:500]]) # Limit to first 500 to avoid huge context
            if len(all_files) > 500:
                context += f"\n... ({len(all_files) - 500} more files)"

            context += "\n\n## Key Configuration Files\n"
            context += self.read_files(files)

            # Special handling for cli.py imports (per prompt A)
            cli_path = Path("src/dopemux/cli.py")
            if (self.root_path / cli_path).exists():
                try:
                    lines = (self.root_path / cli_path).read_text().splitlines()
                    imports = [l for l in lines if l.startswith("import ") or l.startswith("from ")]
                    context += f"\nFile: {cli_path} (Imports Only)\n```\n" + "\n".join(imports) + "\n```\n"
                except Exception:
                    pass

            return context

        elif phase == 'H':
            # Home Control Plane - difficult to access outside repo in some envs
            # We will try to scan ~/.dopemux if allowed
            home_dir = Path.home()
            dopemux_home = home_dir / ".dopemux"
            config_home = home_dir / ".config" / "dopemux"

            context = "## Home Directory Configuration\n"

            paths_to_check = [
                dopemux_home / "config.yaml",
                config_home / "litellm.config.yaml",
                config_home / "mcp-router-config.yaml",
                home_dir / ".claude" / "claude_config.json"
            ]

            for path in paths_to_check:
                if path.exists():
                    try:
                        content = path.read_text(encoding='utf-8', errors='replace')
                        # MASK API KEYS
                        masked = []
                        for line in content.splitlines():
                            if "key" in line.lower() or "token" in line.lower():
                                parts = line.split(":")
                                if len(parts) > 1:
                                    masked.append(f"{parts[0]}: sk-*** (masked)")
                                else:
                                    masked.append(line) # Can't parse easily
                            else:
                                masked.append(line)
                        context += f"File: {path}\n```\n" + "\n".join(masked) + "\n```\n"
                    except Exception as e:
                        context += f"File: {path}\n[Error reading file: {e}]\n"
                else:
                    context += f"File: {path} (Not Found)\n"

            return context

        elif phase == 'C':
            # Code Surfaces - list key files and interfaces
            # This would ideally be a more smart AST parse, but for now list files
            patterns = [
                "src/**/*.py",
                "services/**/*.py"
            ]
            files = self.gather_file_list(include_patterns=patterns)
            context = "## Codebase Files\n"
            context += "\n".join([str(f) for f in files])

            # Read __init__.py files to see exposed interfaces
            init_files = [f for f in files if f.name == "__init__.py"]
            context += "\n\n## Package Interfaces (__init__.py)\n"
            context += self.read_files(init_files)

            return context

        elif phase == 'D':
             # Docs - list docs
            files = self.gather_file_list(include_patterns=["docs/**/*.md"])
            context = "## Documentation Files\n"
            context += "\n".join([str(f) for f in files])
            return context

        # R and S depend on outputs of previous phases, which are passed in as args usually
        # TODO: Implement logic to gather outputs from previous phases (A, H, D, C)
        # once the output structure is finalized.
        return ""
