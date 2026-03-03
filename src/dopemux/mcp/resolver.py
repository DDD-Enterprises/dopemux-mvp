import os
import json
import tomllib
from pathlib import Path
from typing import Dict, Any, Optional

class InstanceResolver:
    """
    Resolves MCP instance endpoints via strict priority:
    1. repo profile (.dopemux/mcp.instances*.toml)
    2. env vars (e.g. DOPMUX_CONPORT_URL)
    3. global config fallback (~/.vibe/config.toml)
    """
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.resolution_report = {
            "project_id": "unknown",
            "instance_profile": "default",
            "servers": {},
            "provenance": {}
        }

    def resolve(self, profile_name: str = "default") -> Dict[str, Any]:
        # 1. Start with repo profile
        repo_profile_path = self.project_root / ".dopemux" / "mcp.instances.toml"
        
        # Check if there's a profile-specific one
        if profile_name != "default":
            specific_path = self.project_root / ".dopemux" / f"mcp.instances.{profile_name}.toml"
            if specific_path.exists():
                repo_profile_path = specific_path

        if repo_profile_path.exists():
            with open(repo_profile_path, "rb") as f:
                try:
                    config = tomllib.load(f)
                    proj = config.get("project", {})
                    self.resolution_report["project_id"] = proj.get("project_id", "unknown")
                    self.resolution_report["instance_profile"] = proj.get("instance_profile", profile_name)
                    
                    if "mcp" in config:
                        for name, details in config["mcp"].items():
                            self.resolution_report["servers"][name] = details.copy()
                            self.resolution_report["provenance"][name] = "repo_profile"
                except Exception as e:
                    # If repo profile fails to parse, we should probably know
                    self.resolution_report["error"] = f"Failed to parse repo profile: {str(e)}"

        # 2. Env vars override
        for env_key, env_val in os.environ.items():
            if env_key.startswith("DOPMUX_") and env_key.endswith("_URL"):
                # Extract server name: DOPMUX_CONPORT_URL -> conport
                # or DOPMUX_DOPE_CONTEXT_URL -> dope-context
                name = env_key[7:-4].lower().replace('_', '-')
                if name not in self.resolution_report["servers"]:
                    self.resolution_report["servers"][name] = {}
                self.resolution_report["servers"][name]["url"] = env_val
                self.resolution_report["provenance"][name] = "env_var"

        # 3. Global fallback (~/.vibe/config.toml)
        global_config_path = Path.home() / ".vibe" / "config.toml"
        if global_config_path.exists():
            try:
                with open(global_config_path, "rb") as f:
                    global_config = tomllib.load(f)
                    if "mcp_servers" in global_config:
                        for srv in global_config["mcp_servers"]:
                            name = srv.get("name")
                            if name and name not in self.resolution_report["servers"]:
                                self.resolution_report["servers"][name] = {
                                    "url": srv.get("url"),
                                    "transport": srv.get("transport", "http"),
                                }
                                self.resolution_report["provenance"][name] = "global_fallback"
            except Exception:
                pass

        # Normalize and sort
        self.resolution_report["servers"] = dict(sorted(self.resolution_report["servers"].items()))
        return self.resolution_report

    def save_report(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.resolution_report, f, indent=2, sort_keys=True)
