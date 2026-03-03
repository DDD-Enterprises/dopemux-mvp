import json
import fnmatch
from pathlib import Path
from typing import Optional
from .resolver import InstanceResolver
from .discovery import ToolDiscoveryClient

class DiscoveryGate:
    """
    Phase 0 Tool Discovery Gate:
    - Runs Instance Resolver
    - Runs Tool Discovery (JSON-RPC POST tools/list)
    - Validates required tool globs are satisfied
    - Fails closed with structured report
    """
    def __init__(self, project_root: Optional[Path] = None, run_id: str = "latest"):
        self.project_root = project_root or Path.cwd()
        self.run_id = run_id
        self.resolver = InstanceResolver(self.project_root)
        self.discovery = ToolDiscoveryClient()
        self.proof_dir = self.project_root / "proof" / run_id
        self.report = {
            "status": "INIT",
            "reachable_transport": [],
            "unreachable_transport": [],
            "tools_discoverable": {},
            "missing_required_tools": {},
            "resolved_endpoints": {},
            "provenance": {}
        }

    async def run(self, profile_name: str = "default") -> bool:
        # 1. Resolve
        resolution = self.resolver.resolve(profile_name)
        self.report["resolved_endpoints"] = resolution["servers"]
        self.report["provenance"] = resolution["provenance"]
        
        # 2. Discover
        discovery_report = await self.discovery.discover(resolution["servers"])
        
        # 3. Validate
        passed = True
        for name, config in resolution["servers"].items():
            srv_discovery = next((s for s in discovery_report["servers"] if s["name"] == name), None)
            
            # If server is unreachable AND it was sourced from repo profile, it's a hard FAIL.
            # If it was from global fallback or env var, it's considered OPTIONAL/AUXILIARY.
            is_mandatory = resolution["provenance"].get(name) == "repo_profile"

            if srv_discovery and srv_discovery["reachable"]:
                self.report["reachable_transport"].append(name)
                discovered_tools = srv_discovery.get("tools", [])
                self.report["tools_discoverable"][name] = len(discovered_tools)
                
                # Validate globs
                required_globs = config.get("required_tool_globs", [])
                missing_globs = []
                for glob in required_globs:
                    matches = fnmatch.filter(discovered_tools, glob)
                    
                    # Special case for ConPort: handle both spellings if one fails
                    if not matches and (glob.startswith("conport_") or glob.startswith("conport_")):
                        if "conport_" in glob:
                            alt_glob = glob.replace("conport_", "conport_")
                        else:
                            alt_glob = glob.replace("conport_", "conport_")
                        matches = fnmatch.filter(discovered_tools, alt_glob)

                    if not matches:
                        missing_globs.append(glob)
                
                if missing_globs:
                    self.report["missing_required_tools"][name] = missing_globs
                    if is_mandatory:
                        passed = False
            else:
                self.report["unreachable_transport"].append(name)
                if is_mandatory:
                    passed = False

        self.report["status"] = "PASS" if passed else "BLOCK"
        self._save_report()
        return passed

    def _save_report(self):
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        # Standard filename per TP
        with open(self.proof_dir / "PHASE0_REPORT.json", "w") as f:
            json.dump(self.report, f, indent=2, sort_keys=True)
        
        # Also save legacy for compatibility if needed
        with open(self.proof_dir / "GATE_RESULT.json", "w") as f:
            json.dump(self.report, f, indent=2, sort_keys=True)

    def print_block_report(self):
        print("\n" + "="*60)
        print(f"MCP PHASE 0 DISCOVERY GATE: {self.report['status']}")
        print("="*60)
        
        if self.report["unreachable_transport"]:
            print(f"Unreachable transport (JSON-RPC failed): {', '.join(self.report['unreachable_transport'])}")
        
        if self.report["missing_required_tools"]:
            print("Missing required tools (globs not satisfied):")
            for srv, globs in self.report["missing_required_tools"].items():
                print(f"  - {srv}: {', '.join(globs)}")
        
        print(f"\nSee full report in: {self.proof_dir}/PHASE0_REPORT.json")
        print("="*60 + "\n")
