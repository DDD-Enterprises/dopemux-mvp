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
        # Reset per-call state. Without this, a reused InstanceResolver instance
        # would retain servers/provenance from a prior resolve() call, which
        # (post-F018-fix) could let stale repo_profile provenance leak into an
        # otherwise env-only service on a later call -- violating both
        # determinism (same effective inputs -> same output) and the
        # authority invariant the F018 fix establishes.
        self.resolution_report = {
            "project_id": "unknown",
            "instance_profile": "default",
            "servers": {},
            "provenance": {}
        }

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
                    
                    # New: Opt-in global fallback to prevent cross-project contamination
                    allow_global = proj.get("allow_global_fallback", False)
                    
                    if "mcp" in config:
                        for name, details in config["mcp"].items():
                            self.resolution_report["servers"][name] = details.copy()
                            self.resolution_report["provenance"][name] = "repo_profile"
                except Exception as e:
                    # If repo profile fails to parse, we should probably know
                    self.resolution_report["error"] = f"Failed to parse repo profile: {str(e)}"
                    allow_global = False # Default safe
        else:
            allow_global = False # No repo profile, don't guess global

        # 2. Env vars override
        for env_key, env_val in os.environ.items():
            if env_key.startswith("DOPMUX_") and env_key.endswith("_URL"):
                # Extract server name: DOPMUX_CONPORT_URL -> conport
                # or DOPMUX_DOPE_CONTEXT_URL -> dope-context
                name = env_key[7:-4].lower().replace('_', '-')
                if name not in self.resolution_report["servers"]:
                    self.resolution_report["servers"][name] = {}
                self.resolution_report["servers"][name]["url"] = env_val
                # An env URL override changes the endpoint address only. It must not
                # erase repo-profile authority (DMX-W1-04-F018): a service already
                # declared authoritative by the repo profile stays repo_profile even
                # when its URL is overridden here. A service with no prior provenance
                # is genuinely env-only and is recorded as such.
                if self.resolution_report["provenance"].get(name) != "repo_profile":
                    self.resolution_report["provenance"][name] = "env_var"

        # 3. Global fallback (~/.vibe/config.toml) - ONLY if allowed
        if allow_global:
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
