import json
import fnmatch
import os
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

    Provenance-aware failure policy (TP-2 / MCP1-02):
    - repo_profile servers are ALWAYS mandatory: unreachable or missing-glob -> BLOCK.
    - env_var / global_fallback servers are non-mandatory. Previously their failures
      were silently fail-open. They now ALWAYS emit a clearly-labeled WARNING in the
      report. With ``strict_optional=True`` (or env DOPEMUX_MCP_GATE_STRICT=1) those
      warnings additionally escalate to a hard BLOCK (fail-closed opt-in).
    """
    def __init__(
        self,
        project_root: Optional[Path] = None,
        run_id: str = "latest",
        strict_optional: Optional[bool] = None,
    ):
        self.project_root = project_root or Path.cwd()
        self.run_id = run_id
        self.resolver = InstanceResolver(self.project_root)
        self.discovery = ToolDiscoveryClient()
        self.proof_dir = self.project_root / "proof" / run_id
        # Opt-in fail-closed for non-mandatory servers. Default is loud-warn (safe,
        # non-breaking for existing optional-server setups). Env var lets operators
        # turn on strict mode without code changes.
        if strict_optional is None:
            strict_optional = os.environ.get(
                "DOPEMUX_MCP_GATE_STRICT", ""
            ).strip().lower() in ("1", "true", "yes", "on")
        self.strict_optional = strict_optional
        self.report = {
            "status": "INIT",
            "reachable_transport": [],
            "unreachable_transport": [],
            "tools_discoverable": {},
            "missing_required_tools": {},
            "warnings": [],
            "strict_optional": self.strict_optional,
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
                
                # If transport is ok but requires handshake, we consider it REACHABLE.
                # Globs can't be validated if no tools returned yet, so we only FAIL if mandatory.
                handshake_required = srv_discovery.get("warning") == "transport active, handshake required"

                # Validate globs
                required_globs = config.get("required_tool_globs", [])
                missing_globs = []
                for glob in required_globs:
                    matches = fnmatch.filter(discovered_tools, glob)

                    if not matches and not handshake_required:
                        missing_globs.append(glob)
                
                if missing_globs:
                    self.report["missing_required_tools"][name] = missing_globs
                    if is_mandatory:
                        passed = False
                    else:
                        # Non-mandatory (env_var / global_fallback): ALWAYS WARN; escalate
                        # to a hard BLOCK only under strict_optional (fail-closed opt-in).
                        self.report["warnings"].append(
                            f"Non-mandatory server '{name}' is missing required tool(s): "
                            f"{', '.join(missing_globs)}"
                        )
                        if self.strict_optional:
                            passed = False
            else:
                self.report["unreachable_transport"].append(name)
                if is_mandatory:
                    passed = False
                else:
                    # Non-mandatory (env_var / global_fallback): ALWAYS WARN; escalate
                    # to a hard BLOCK only under strict_optional (fail-closed opt-in).
                    self.report["warnings"].append(
                        f"Non-mandatory server '{name}' is unreachable (transport failed)"
                    )
                    if self.strict_optional:
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
