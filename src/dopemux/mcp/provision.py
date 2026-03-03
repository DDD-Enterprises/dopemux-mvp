import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

PINNED_VERSION = "0.1.0"

class MCPProvisioner:
    """
    Handles auto-provisioning of MCP stack assets per project.
    Resolves source from project local, vendor, cache, or package data.
    """
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.vendor_dir = self.project_root / ".dopemux" / "vendor" / "mcp-servers" / PINNED_VERSION
        self.cache_dir = Path.home() / ".cache" / "dopemux" / "mcp-servers" / PINNED_VERSION
        self.report = {
            "source_resolved": None,
            "target_path": str(self.project_root / "docker" / "mcp-servers"),
            "method": None,
            "version": PINNED_VERSION
        }

    def resolve_stack_source(self) -> Optional[Path]:
        """
        Determine MCP stack source via strict priority:
        1. Project local: <repo>/docker/mcp-servers/
        2. Project vendor: <repo>/.dopemux/vendor/mcp-servers/<VERSION>/
        3. User cache: ~/.cache/dopemux/mcp-servers/<VERSION>/
        4. Package template: dopemux/docker/mcp-servers
        """
        # 1. Project local
        local_path = self.project_root / "docker" / "mcp-servers"
        if local_path.exists() and not local_path.is_symlink():
            if (local_path / "start-all-mcp-servers.sh").exists():
                self.report["source_resolved"] = "project_local"
                return local_path

        # 1b. Project source (internal vendor)
        source_path = self.project_root / "docker" / "mcp-servers-source"
        if source_path.exists():
            if (source_path / "start-all-mcp-servers.sh").exists():
                self.report["source_resolved"] = "project_source"
                return source_path

        # 2. Project vendor
        if self.vendor_dir.exists():
            if (self.vendor_dir / "start-all-mcp-servers.sh").exists():
                self.report["source_resolved"] = "project_vendor"
                return self.vendor_dir

        # 3. User cache
        if self.cache_dir.exists():
            if (self.cache_dir / "start-all-mcp-servers.sh").exists():
                self.report["source_resolved"] = "user_cache"
                return self.cache_dir

        # 4. Package template
        try:
            # Assumes dopemux is installed and has docker/mcp-servers in its data
            import dopemux
            pkg_root = Path(dopemux.__file__).resolve().parent
            pkg_mcp = pkg_root / "docker" / "mcp-servers"
            if pkg_mcp.exists() and (pkg_mcp / "start-all-mcp-servers.sh").exists():
                self.report["source_resolved"] = "package_template"
                return pkg_mcp
            
            # Fallback for editable install/source tree
            repo_root = pkg_root.parents[1]
            repo_mcp = repo_root / "docker" / "mcp-servers"
            if repo_mcp.exists() and (repo_mcp / "start-all-mcp-servers.sh").exists():
                self.report["source_resolved"] = "source_tree"
                return repo_mcp
        except Exception:
            pass

        return None

    def ensure_stack_present(self) -> Path:
        """
        Ensures docker/mcp-servers exists in project root.
        Returns the resolved path.
        """
        target_path = self.project_root / "docker" / "mcp-servers"
        
        # If already exists and valid, just return it
        if target_path.exists():
            if (target_path / "start-all-mcp-servers.sh").exists():
                self.report["method"] = "already_present"
                return target_path
            else:
                # Exists but invalid? Maybe it's a broken symlink or empty dir
                if target_path.is_symlink():
                    target_path.unlink()
                else:
                    # Rename it to avoid data loss but allow provisioning
                    backup_path = target_path.with_name("mcp-servers.bak")
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                    target_path.rename(backup_path)

        source_path = self.resolve_stack_source()
        if not source_path:
            raise RuntimeError("Could not resolve MCP stack source. Automatic provisioning failed.")

        # Create docker dir if missing
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Provision method: symlink preferred, copy fallback
        try:
            os.symlink(source_path, target_path)
            self.report["method"] = "symlink"
        except (OSError, NotImplementedError):
            shutil.copytree(source_path, target_path)
            self.report["method"] = "copy"

        logger.info(f"Provisioned MCP stack from {self.report['source_resolved']} via {self.report['method']}")
        return target_path

    def get_report(self) -> Dict[str, Any]:
        return self.report
