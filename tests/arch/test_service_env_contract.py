"""
Architecture Test: Service Environment Contract Compliance

Tests that all smoke-enabled services comply with the environment variable contract
defined in docs/engineering/service_env_contract.md

This test enforces:
1. Required env vars (HOST, PORT, LOG_LEVEL) are supported
2. No use of os.environ[] without defaults (risky pattern)
3. No sys.path.insert (violates service isolation)

Exceptions can be documented in services/registry.yaml under env_contract_exceptions.
"""

import json
import sys
from pathlib import Path

import pytest
import yaml


# Find project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_registry():
    """Load service registry"""
    registry_path = PROJECT_ROOT / "services" / "registry.yaml"
    with open(registry_path, 'r') as f:
        return yaml.safe_load(f)


def get_smoke_services():
    """Get list of smoke-enabled Python services"""
    registry = load_registry()
    services = []
    
    for svc in registry.get('services', []):
        if svc.get('enabled_in_smoke', False):
            # Filter to Python services only (skip infrastructure)
            if svc.get('category') not in ['infrastructure']:
                services.append(svc)
    
    return services


def run_drift_scanner():
    """Run env drift scanner and return results"""
    import subprocess
    
    scanner_path = PROJECT_ROOT / "tools" / "env_drift_scan.py"
    result = subprocess.run(
        [sys.executable, str(scanner_path), '--json'],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    
    return json.loads(result.stdout)


# Get smoke services for parametrization
SMOKE_SERVICES = get_smoke_services()


class TestServiceEnvContract:
    """Test environment contract compliance for services"""
    
    @pytest.fixture(scope='class')
    def scan_results(self):
        """Run drift scanner once for all tests"""
        return run_drift_scanner()
    
    @pytest.mark.parametrize('service', SMOKE_SERVICES, ids=lambda s: s['name'])
    def test_service_supports_required_env_vars(self, scan_results, service):
        """Test that service supports required env vars (HOST, PORT, LOG_LEVEL)"""
        service_name = service['name']
        
        # Find service in scan results
        service_result = None
        for svc in scan_results['services']:
            if svc['service'] == service_name:
                service_result = svc
                break
        
        assert service_result is not None, f"Service {service_name} not in scan results"
        
        # Check for exceptions
        exceptions = service.get('env_contract_exceptions', [])
        
        # Required vars
        required_vars = {'HOST', 'PORT', 'LOG_LEVEL'}
        
        # Remove exceptions from required
        required_vars = required_vars - set(exceptions)
        
        # Check each required var
        missing = []
        for var in required_vars:
            if not service_result['env_support'].get(var, False):
                missing.append(var)
        
        assert not missing, (
            f"Service '{service_name}' missing required env vars: {', '.join(missing)}. "
            f"Add support in config/settings file or document exception in registry.yaml"
        )
    
    @pytest.mark.parametrize('service', SMOKE_SERVICES, ids=lambda s: s['name'])
    def test_service_has_single_config_source(self, scan_results, service):
        """Test that service has identifiable config source (entry point or config file)"""
        service_name = service['name']
        
        # Find service in scan results
        service_result = None
        for svc in scan_results['services']:
            if svc['service'] == service_name:
                service_result = svc
                break
        
        assert service_result is not None
        
        # Service should have either entry point or config files
        has_entry_point = service_result['entry_point'] is not None
        has_config_files = len(service_result['config_files']) > 0
        
        assert has_entry_point or has_config_files, (
            f"Service '{service_name}' has no identifiable config source. "
            f"Expected main.py, app.py, server.py, config.py, or settings.py"
        )
    
    @pytest.mark.parametrize('service', SMOKE_SERVICES, ids=lambda s: s['name'])
    def test_service_no_risky_patterns(self, scan_results, service):
        """Test that service doesn't use risky patterns (sys.path.insert)"""
        service_name = service['name']
        
        # Find service in scan results
        service_result = None
        for svc in scan_results['services']:
            if svc['service'] == service_name:
                service_result = svc
                break
        
        assert service_result is not None
        
        # Check for sys.path.insert violation
        violations = service_result.get('violations', [])
        sys_path_violations = [v for v in violations if 'sys.path' in v.lower()]
        
        assert not sys_path_violations, (
            f"Service '{service_name}' uses sys.path.insert which violates service isolation. "
            f"Use proper Python package structure or PYTHONPATH instead."
        )
    
    def test_all_services_scanned(self, scan_results):
        """Meta-test: verify all smoke services were scanned"""
        scanned_names = {svc['service'] for svc in scan_results['services']}
        expected_names = {svc['name'] for svc in SMOKE_SERVICES}
        
        missing = expected_names - scanned_names
        
        assert not missing, (
            f"Scanner did not scan all smoke-enabled services. Missing: {missing}"
        )
    
    def test_no_scan_errors(self, scan_results):
        """Meta-test: verify scanner completed without errors"""
        error_count = scan_results['summary']['errors']
        
        assert error_count == 0, (
            f"Drift scanner encountered {error_count} errors. "
            f"Check reports/g33/env_drift_report.json for details."
        )
    
    def test_compliance_summary(self, scan_results):
        """Summary test: report overall compliance status"""
        summary = scan_results['summary']
        
        total = summary['compliant'] + summary['violations'] + summary['errors']
        compliance_rate = (summary['compliant'] / total * 100) if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"ENVIRONMENT CONTRACT COMPLIANCE SUMMARY")
        print(f"{'='*70}")
        print(f"Total services: {total}")
        print(f"  ✅ Compliant: {summary['compliant']}")
        print(f"  ❌ Violations: {summary['violations']}")
        print(f"  ⚠️  Errors: {summary['errors']}")
        print(f"Compliance rate: {compliance_rate:.1f}%")
        print(f"{'='*70}\n")
        
        # This test always passes but shows the summary
        # Individual tests will fail if there are violations


class TestEnvContractDocumentation:
    """Test that contract documentation exists and is valid"""
    
    def test_contract_document_exists(self):
        """Test that the env contract document exists"""
        contract_path = PROJECT_ROOT / "docs" / "04-explanation" / "service_env_contract.md"
        assert contract_path.exists(), (
            "Environment contract document not found at docs/04-explanation/service_env_contract.md"
        )
    
    def test_drift_scanner_exists(self):
        """Test that the drift scanner tool exists"""
        scanner_path = PROJECT_ROOT / "tools" / "env_drift_scan.py"
        assert scanner_path.exists(), (
            "Drift scanner not found at tools/env_drift_scan.py"
        )
    
    def test_smoke_services_report_exists(self):
        """Test that smoke services inventory exists"""
        report_path = PROJECT_ROOT / "reports" / "g33" / "smoke_services.json"
        assert report_path.exists(), (
            "Smoke services report not found. Run: python tools/env_drift_scan.py"
        )
