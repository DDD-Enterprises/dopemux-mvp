#!/usr/bin/env python3
"""
Environment Drift Scanner (G33 Phase 2)

Scans services for compliance with the unified service environment contract.
Detects missing mandatory env vars, undocumented variables, and contract violations.

Usage:
    python tools/env_drift_scan.py
    python tools/env_drift_scan.py --services conport,dopecon-bridge
    python tools/env_drift_scan.py --json reports/g33/env_drift_report.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

import yaml

# Mandatory env vars per contract
MANDATORY_ENV_VARS = {
    "PORT": "Container-internal HTTP port",
    "LOG_LEVEL": "Logging verbosity level",
    "ENVIRONMENT": "Deployment environment (dev/staging/prod)",
    "HEALTH_CHECK_PATH": "Health check endpoint path",
    "SERVICE_NAME": "Canonical service name",
}

# Category-specific required vars
CATEGORY_ENV_VARS = {
    "infrastructure": set(),  # Infrastructure uses native config
    "mcp": {"MCP_SERVER_PORT"},
    "coordination": {"REDIS_URL"},
    "cognitive": {"DATABASE_URL", "REDIS_URL", "CONPORT_URL"},
}

# Env vars that should have defaults
OPTIONAL_ENV_VARS = {
    "METRICS_ENABLED": "Enable Prometheus metrics",
    "METRICS_PORT": "Prometheus metrics port",
    "SERVICE_VERSION": "Semantic version",
}


class EnvDriftScanner:
    """Scans services for environment variable contract compliance."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.registry = self._load_registry()
        self.violations = []
        self.warnings = []

    def _load_registry(self) -> Dict:
        """Load service registry."""
        registry_path = self.repo_root / "services" / "registry.yaml"
        if not registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {registry_path}")

        with open(registry_path) as f:
            return yaml.safe_load(f)

    def scan_service(self, service_name: str) -> Dict[str, Any]:
        """Scan a single service for env var compliance."""
        # Find service in registry
        service_info = None
        for svc in self.registry.get("services", []):
            if svc["name"] == service_name:
                service_info = svc
                break

        if not service_info:
            return {
                "service": service_name,
                "status": "ERROR",
                "error": "Service not found in registry"
            }

        # Check if service should be scanned
        if not service_info.get("enabled_in_smoke", False):
            return {
                "service": service_name,
                "status": "SKIPPED",
                "reason": "Not enabled in smoke stack"
            }

        # Find service directory
        service_dir = self.repo_root / "services" / service_name
        if not service_dir.exists():
            return {
                "service": service_name,
                "status": "ERROR",
                "error": f"Service directory not found: {service_dir}"
            }

        # Scan for env var usage
        env_vars_found = self._scan_env_usage(service_dir)

        # Get exceptions from registry
        exceptions = {
            exc["variable"]
            for exc in service_info.get("env_contract_exceptions", [])
        }

        # Check mandatory vars
        missing_mandatory = []
        for var in MANDATORY_ENV_VARS:
            if var not in exceptions and var not in env_vars_found:
                missing_mandatory.append(var)

        # Check category-specific vars
        category = service_info.get("category", "unknown")
        required_category_vars = CATEGORY_ENV_VARS.get(category, set())
        missing_category = []
        for var in required_category_vars:
            if var not in exceptions and var not in env_vars_found:
                missing_category.append(var)

        # Check for undocumented vars
        documented_vars = set(MANDATORY_ENV_VARS.keys())
        documented_vars.update(OPTIONAL_ENV_VARS.keys())
        documented_vars.update(required_category_vars)

        # Common acceptable vars (not violations)
        acceptable_vars = {
            "DATABASE_URL", "REDIS_URL", "CONPORT_URL", "DOPECON_BRIDGE_URL",
            "MCP_SERVER_PORT", "TASK_ORCHESTRATOR_API_KEY", "WORKSPACE_ID",
            "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
            "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_PORT",
        }

        undocumented = [
            var for var in env_vars_found
            if var not in documented_vars and var not in acceptable_vars
        ]

        # Determine compliance status
        compliant = not missing_mandatory and not missing_category

        result = {
            "service": service_name,
            "category": category,
            "status": "COMPLIANT" if compliant else "VIOLATION",
            "env_vars_found": sorted(list(env_vars_found)),
            "env_vars_count": len(env_vars_found),
            "missing_mandatory": missing_mandatory,
            "missing_category": missing_category,
            "undocumented": undocumented[:10],  # Limit to avoid noise
            "exceptions": list(exceptions),
            "recommendation": self._generate_recommendation(
                service_name, missing_mandatory, missing_category
            )
        }

        if not compliant:
            self.violations.append(result)
        if undocumented:
            self.warnings.append({
                "service": service_name,
                "undocumented_count": len(undocumented),
                "vars": undocumented[:5]
            })

        return result

    def _scan_env_usage(self, service_dir: Path) -> Set[str]:
        """Scan service files for env var usage."""
        env_vars = set()

        # Scan Python files
        for py_file in service_dir.rglob("*.py"):
            try:
                content = py_file.read_text()

                # Match os.getenv("VAR_NAME") and os.environ["VAR_NAME"]
                matches = re.findall(
                    r'os\.(?:getenv|environ(?:\.get)?)\(["\']([A-Z_][A-Z0-9_]*)["\']',
                    content
                )
                env_vars.update(matches)

            except Exception:
                continue  # Skip unreadable files

        # Scan Dockerfile
        dockerfile = service_dir / "Dockerfile"
        if dockerfile.exists():
            try:
                content = dockerfile.read_text()
                # Match ENV declarations
                matches = re.findall(r'^ENV\s+([A-Z_][A-Z0-9_]*)', content, re.MULTILINE)
                env_vars.update(matches)

            except Exception:
                pass

        return env_vars

    def _generate_recommendation(
        self, service: str, missing_mandatory: List[str], missing_category: List[str]
    ) -> str:
        """Generate fix recommendation."""
        if not missing_mandatory and not missing_category:
            return "Service is compliant with env contract"

        fixes = []
        if missing_mandatory:
            fixes.append(
                f"Add mandatory env vars to service config: {', '.join(missing_mandatory)}"
            )
        if missing_category:
            fixes.append(
                f"Add category-specific env vars: {', '.join(missing_category)}"
            )

        fixes.append(
            f"See migration guide: docs/engineering/service_env_contract.md"
        )

        return " | ".join(fixes)

    def scan_all_smoke_services(self) -> Dict[str, Any]:
        """Scan all smoke-enabled services."""
        results = []

        smoke_services = [
            svc["name"]
            for svc in self.registry.get("services", [])
            if svc.get("enabled_in_smoke", False)
        ]

        for service_name in smoke_services:
            result = self.scan_service(service_name)
            results.append(result)

        # Generate summary
        total = len(results)
        compliant = sum(1 for r in results if r.get("status") == "COMPLIANT")
        violations = sum(1 for r in results if r.get("status") == "VIOLATION")
        errors = sum(1 for r in results if r.get("status") == "ERROR")

        summary = {
            "total_services": total,
            "compliant": compliant,
            "violations": violations,
            "errors": errors,
            "compliance_rate": f"{(compliant/total*100):.1f}%" if total > 0 else "N/A"
        }

        return {
            "summary": summary,
            "services": results,
            "violations": self.violations,
            "warnings": self.warnings
        }

    def print_report(self, report: Dict[str, Any]):
        """Print human-readable report to stdout."""
        print("\n" + "="*60)
        print("🔍 Environment Drift Scan Report (G33)")
        print("="*60 + "\n")

        summary = report["summary"]
        print("📊 Summary:")
        print(f"  Total Services:    {summary['total_services']}")
        print(f"  Compliant:         {summary['compliant']} ✅")
        print(f"  Violations:        {summary['violations']} ❌")
        print(f"  Errors:            {summary['errors']} ⚠️")
        print(f"  Compliance Rate:   {summary['compliance_rate']}")
        print()

        # Print violations
        if report["violations"]:
            print("❌ Contract Violations:\n")
            for violation in report["violations"]:
                print(f"  • {violation['service']} ({violation['category']})")
                if violation["missing_mandatory"]:
                    print(f"    Missing mandatory: {', '.join(violation['missing_mandatory'])}")
                if violation["missing_category"]:
                    print(f"    Missing category-specific: {', '.join(violation['missing_category'])}")
                print(f"    → {violation['recommendation']}")
                print()

        # Print warnings
        if report["warnings"]:
            print("⚠️  Warnings:\n")
            for warning in report["warnings"][:5]:  # Limit warnings
                print(f"  • {warning['service']}: {warning['undocumented_count']} undocumented vars")
            print()

        # Print compliant services
        compliant_services = [
            s for s in report["services"]
            if s.get("status") == "COMPLIANT"
        ]
        if compliant_services:
            print("✅ Compliant Services:\n")
            for svc in compliant_services:
                print(f"  • {svc['service']} ({svc['category']}) - {svc['env_vars_count']} env vars")
            print()

        print("="*60)
        print(f"📋 Full report: reports/g33/env_drift_report.json")
        print("📖 Migration guide: docs/engineering/service_env_contract.md")
        print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scan services for env contract compliance")
    parser.add_argument(
        "--services",
        help="Comma-separated list of services to scan (default: all smoke services)"
    )
    parser.add_argument(
        "--json",
        default="reports/g33/env_drift_report.json",
        help="Output JSON report path"
    )

    args = parser.parse_args()

    # Detect repo root
    repo_root = Path(__file__).parent.parent
    if not (repo_root / "services" / "registry.yaml").exists():
        print("❌ Error: Could not find services/registry.yaml")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Repo root: {repo_root}")
        sys.exit(1)

    # Create scanner
    scanner = EnvDriftScanner(repo_root)

    # Scan services
    if args.services:
        # Scan specific services
        service_names = [s.strip() for s in args.services.split(",")]
        results = []
        for name in service_names:
            result = scanner.scan_service(name)
            results.append(result)

        report = {
            "summary": {
                "total_services": len(results),
                "compliant": sum(1 for r in results if r.get("status") == "COMPLIANT"),
                "violations": sum(1 for r in results if r.get("status") == "VIOLATION"),
            },
            "services": results,
            "violations": scanner.violations,
            "warnings": scanner.warnings
        }
    else:
        # Scan all smoke services
        report = scanner.scan_all_smoke_services()

    # Print report to stdout
    scanner.print_report(report)

    # Save JSON report
    output_path = Path(args.json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ JSON report saved to: {output_path}\n")

    # Exit with error code if violations found
    if report["summary"]["violations"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
