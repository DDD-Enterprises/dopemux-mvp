#!/usr/bin/env python3
"""
Service Environment Drift Scanner

Scans smoke-enabled services for compliance with the environment variable contract.
Reports missing or inconsistent env var support.

Usage:
    python tools/env_drift_scan.py
    python tools/env_drift_scan.py --json  # JSON output only
    python tools/env_drift_scan.py --verbose  # Detailed output

Exit codes:
    0 - All services compliant
    1 - Drift detected (violations found)
    2 - Error running scanner
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


class EnvDriftScanner:
    """Scans services for environment variable contract compliance"""
    
    REQUIRED_VARS = {"HOST", "PORT", "LOG_LEVEL"}
    OPTIONAL_VARS = {"BASE_URL"}
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.registry_path = project_root / "services" / "registry.yaml"
        self.violations: List[Dict] = []
        
    def load_registry(self) -> Dict:
        """Load and parse service registry"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")
            
        with open(self.registry_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_smoke_services(self, registry: Dict) -> List[Dict]:
        """Extract smoke-enabled services from registry"""
        services = []
        for svc in registry.get('services', []):
            if svc.get('enabled_in_smoke', False):
                # Filter to Python services only (skip infrastructure)
                if svc.get('category') not in ['infrastructure']:
                    services.append(svc)
        return services
    
    def find_service_entry_point(self, service_path: Path) -> Optional[Path]:
        """Find main entry point for a service"""
        candidates = ['main.py', 'app.py', 'server.py', '__main__.py']
        
        for candidate in candidates:
            entry_path = service_path / candidate
            if entry_path.exists():
                return entry_path
        
        return None
    
    def find_config_files(self, service_path: Path) -> List[Path]:
        """Find config/settings files in service"""
        config_files = []
        
        for pattern in ['**/config.py', '**/settings.py', '**/env.py']:
            config_files.extend(service_path.glob(pattern))
        
        return config_files
    
    def scan_file_for_env_vars(self, file_path: Path) -> Dict[str, bool]:
        """Scan a Python file for env var references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': str(e)}
        
        results = {}
        
        for var in self.REQUIRED_VARS | self.OPTIONAL_VARS:
            # Look for os.getenv("VAR") or os.environ["VAR"] or VAR = patterns
            patterns = [
                rf'os\.getenv\(["\']{ var}["\']',  # os.getenv("VAR")
                rf'os\.environ\[["\']{ var}["\']',  # os.environ["VAR"]
                rf'env\[["\']{ var}["\']',  # env["VAR"]
                rf'{ var}\s*=',  # VAR = (weak heuristic)
            ]
            
            found = any(re.search(pattern, content) for pattern in patterns)
            results[var] = found
        
        # Check for risky patterns
        results['has_risky_environ'] = bool(re.search(r'os\.environ\[', content))
        results['has_sys_path_insert'] = bool(re.search(r'sys\.path\.insert', content))
        
        return results
    
    def check_port_consistency(self, service: Dict, scan_results: Dict) -> Optional[str]:
        """Check if PORT default matches registry"""
        service_path = self.project_root / service.get('compose_service_name', service['name'])
        
        # Find where PORT is defined
        for file_type, files in scan_results['scanned_files'].items():
            for file_path, env_support in files.items():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for PORT default value
                    port_matches = re.findall(r'os\.getenv\(["\']PORT["\'],\s*["\']?(\d+)["\']?\)', content)
                    if port_matches:
                        declared_port = int(port_matches[0])
                        registry_port = service.get('container_port', service['port'])
                        
                        if declared_port != registry_port:
                            return f"PORT default {declared_port} != registry {registry_port}"
                except Exception:
                    pass
        
        return None
    
    def scan_service(self, service: Dict) -> Dict:
        """Scan a single service for env contract compliance"""
        service_name = service['name']
        service_path = self.project_root / "services" / service.get('compose_service_name', service_name)
        
        if not service_path.exists():
            return {
                'service': service_name,
                'status': 'error',
                'error': f'Service directory not found: {service_path}',
                'violations': ['Service directory not found']
            }
        
        # Find entry point and config files
        entry_point = self.find_service_entry_point(service_path)
        config_files = self.find_config_files(service_path)
        
        scanned_files = {
            'entry_point': {},
            'config_files': {}
        }
        
        # Scan entry point
        if entry_point:
            scanned_files['entry_point'][str(entry_point)] = self.scan_file_for_env_vars(entry_point)
        
        # Scan config files
        for config_file in config_files[:3]:  # Limit to first 3 config files
            scanned_files['config_files'][str(config_file)] = self.scan_file_for_env_vars(config_file)
        
        # Aggregate results
        env_support = {var: False for var in self.REQUIRED_VARS | self.OPTIONAL_VARS}
        has_risky_patterns = {'environ': False, 'sys_path': False}
        
        for file_type, files in scanned_files.items():
            for file_path, results in files.items():
                for var in env_support:
                    if results.get(var, False):
                        env_support[var] = True
                
                if results.get('has_risky_environ', False):
                    has_risky_patterns['environ'] = True
                if results.get('has_sys_path_insert', False):
                    has_risky_patterns['sys_path'] = True
        
        # Check for violations
        violations = []
        missing_required = []
        
        for var in self.REQUIRED_VARS:
            if not env_support[var]:
                missing_required.append(var)
                violations.append(f"Missing required var: {var}")
        
        # Check for exceptions in registry
        exceptions = service.get('env_contract_exceptions', [])
        missing_required = [v for v in missing_required if v not in exceptions]
        
        if has_risky_patterns['environ']:
            violations.append("Uses risky os.environ[] without default")
        
        if has_risky_patterns['sys_path']:
            violations.append("Uses sys.path.insert (violates isolation)")
        
        # Check port consistency
        result = {
            'service': service_name,
            'registry_port': service.get('container_port', service['port']),
            'entry_point': str(entry_point.relative_to(self.project_root)) if entry_point else None,
            'config_files': [str(f.relative_to(self.project_root)) for f in config_files[:3]],
            'env_support': env_support,
            'scanned_files': scanned_files,
            'missing_required': missing_required,
            'violations': violations,
            'status': 'compliant' if not violations else 'violations',
            'exceptions': exceptions
        }
        
        port_inconsistency = self.check_port_consistency(service, result)
        if port_inconsistency:
            result['violations'].append(port_inconsistency)
            result['status'] = 'violations'
        
        return result
    
    def scan_all(self) -> Dict:
        """Scan all smoke-enabled services"""
        registry = self.load_registry()
        smoke_services = self.get_smoke_services(registry)
        
        results = {
            'scan_date': '2026-02-01',
            'total_services': len(smoke_services),
            'services': [],
            'summary': {
                'compliant': 0,
                'violations': 0,
                'errors': 0
            }
        }
        
        for service in smoke_services:
            result = self.scan_service(service)
            results['services'].append(result)
            
            if result['status'] == 'compliant':
                results['summary']['compliant'] += 1
            elif result['status'] == 'violations':
                results['summary']['violations'] += 1
            else:
                results['summary']['errors'] += 1
        
        return results
    
    def print_report(self, results: Dict, verbose: bool = False):
        """Print human-readable report"""
        print("\n" + "="*70)
        print("SERVICE ENVIRONMENT DRIFT SCAN REPORT")
        print("="*70)
        print(f"\nTotal services scanned: {results['total_services']}")
        print(f"  ✅ Compliant: {results['summary']['compliant']}")
        print(f"  ❌ Violations: {results['summary']['violations']}")
        print(f"  ⚠️  Errors: {results['summary']['errors']}")
        
        if results['summary']['violations'] > 0:
            print("\n" + "-"*70)
            print("VIOLATIONS DETECTED:")
            print("-"*70)
            
            for svc in results['services']:
                if svc['status'] == 'violations':
                    print(f"\n⚠️  {svc['service']} (port {svc['registry_port']})")
                    for violation in svc['violations']:
                        print(f"    • {violation}")
                    
                    if verbose and svc['missing_required']:
                        print(f"    Missing: {', '.join(svc['missing_required'])}")
        
        if verbose:
            print("\n" + "-"*70)
            print("DETAILED SCAN RESULTS:")
            print("-"*70)
            
            for svc in results['services']:
                print(f"\n📦 {svc['service']}")
                print(f"  Status: {svc['status'].upper()}")
                print(f"  Entry Point: {svc['entry_point'] or 'NOT FOUND'}")
                print(f"  Config Files: {len(svc['config_files'])}")
                
                print(f"  Env Support:")
                for var, supported in svc['env_support'].items():
                    status = "✅" if supported else "❌"
                    print(f"    {status} {var}")
        
        print("\n" + "="*70)
        print(f"Report saved to: reports/g33/env_drift_report.json")
        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Scan services for env contract compliance")
    parser.add_argument('--json', action='store_true', help='Output JSON only (no table)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run scanner
    scanner = EnvDriftScanner(project_root)
    
    try:
        results = scanner.scan_all()
    except Exception as e:
        print(f"ERROR: Scanner failed: {e}", file=sys.stderr)
        return 2
    
    # Save JSON report
    report_dir = project_root / "reports" / "g33"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = report_dir / "env_drift_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print report
    if not args.json:
        scanner.print_report(results, verbose=args.verbose)
    else:
        print(json.dumps(results, indent=2, default=str))
    
    # Exit with appropriate code
    if results['summary']['violations'] > 0:
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())
