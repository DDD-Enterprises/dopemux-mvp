import asyncio
import json
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional
from .resolver import InstanceResolver
from .discovery import ToolDiscoveryClient

class DiscoveryGate:
    """
    Phase 0 Tool Discovery Gate:
    - Runs Instance Resolver
    - Runs Tool Discovery
    - Validates required tool globs are satisfied
    - Blocks if missing/unreachable
    """
    def __init__(self, project_root: Optional[Path] = None, run_id: str = "latest"):
        self.project_root = project_root or Path.cwd()
        self.run_id = run_id
        self.resolver = InstanceResolver(self.project_root)
        self.discovery = ToolDiscoveryClient()
        self.proof_dir = self.project_root / "proof" / run_id
        self.gate_report = {
            "status": "INIT",
            "missing_required_servers": [],
            "missing_required_tools": {},
            "resolved_endpoints": {},
            "reachable_servers": [],
            "unreachable_servers": []
        }

    async def run(self, profile_name: str = "default") -> bool:
        # 1. Resolve
        resolution = self.resolver.resolve(profile_name)
        self.resolver.save_report(self.proof_dir / "INSTANCE_RESOLUTION.json")
        
        # 2. Discover
        discovery_report = await self.discovery.discover(resolution["servers"])
        self.discovery.save_report(self.proof_dir / "DISCOVERY_REPORT.json")
        
        # 3. Validate
        self.gate_report["resolved_endpoints"] = resolution["servers"]
        passed = True
        
        # Servers defined in repo profile are considered REQUIRED by default
        repo_servers = resolution.get("servers", {})
        
        for name, config in repo_servers.items():
            required_globs = config.get("required_tool_globs", [])
            discovered_tools = discovery_report["tools"].get(name, [])
            status = discovery_report["status"].get(name)
            
            if status != "ok":
                # Check if it was resolved from repo profile
                if resolution["provenance"].get(name) == "repo_profile":
                    self.gate_report["unreachable_servers"].append(name)
                    passed = False
            else:
                self.gate_report["reachable_servers"].append(name)
                
                # Check tool globs
                missing_globs = []
                for glob in required_globs:
                    matches = fnmatch.filter(discovered_tools, glob)
                    if not matches:
                        missing_globs.append(glob)
                
                if missing_globs:
                    self.gate_report["missing_required_tools"][name] = missing_globs
                    passed = False

        self.gate_report["status"] = "PASS" if passed else "BLOCK"
        self._save_gate_report()
        return passed

    def _save_gate_report(self):
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        with open(self.proof_dir / "GATE_RESULT.json", "w") as f:
            json.dump(self.gate_report, f, indent=2, sort_keys=True)

    def print_block_report(self):
        print("\n" + "="*60)
        print("MCP PHASE 0 DISCOVERY GATE: BLOCK")
        print("="*60)
        if self.gate_report["unreachable_servers"]:
            print(f"Unreachable required servers: {', '.join(self.gate_report['unreachable_servers'])}")
        
        if self.gate_report["missing_required_tools"]:
            print("Missing required tools (globs not satisfied):")
            for srv, globs in self.gate_report["missing_required_tools"].items():
                print(f"  - {srv}: {', '.join(globs)}")
        
        print(f"\nSee full reports in: {self.proof_dir}")
        print("="*60 + "\n")
