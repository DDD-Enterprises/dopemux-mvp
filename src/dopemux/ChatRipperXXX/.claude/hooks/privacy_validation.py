#!/usr/bin/env python3
"""
Privacy validation hook for ChatX development.
Validates ChatX-specific privacy engineering requirements.
"""
import sys
import os
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Privacy engineering validation rules for ChatX
PRIVACY_THRESHOLDS = {
    'policy_shield_min_coverage': 0.995,  # 99.5% default
    'policy_shield_strict_coverage': 0.999,  # 99.9% strict mode
    'dp_epsilon_max': 10.0,  # Maximum differential privacy epsilon
    'dp_delta_max': 0.01,    # Maximum differential privacy delta
    'confidence_tau_default': 0.7,  # Psychology analysis confidence threshold
}

def check_privacy_patterns(file_path: str) -> List[Tuple[str, str, int]]:
    """Check for privacy-sensitive patterns in code."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        # Check for hardcoded privacy thresholds
        for i, line in enumerate(lines, 1):
            # Look for Policy Shield threshold violations
            if re.search(r'threshold\s*[<>=]+\s*0\.\d+', line):
                threshold_match = re.search(r'0\.(\d+)', line)
                if threshold_match:
                    threshold = float(f"0.{threshold_match.group(1)}")
                    if threshold < PRIVACY_THRESHOLDS['policy_shield_min_coverage']:
                        issues.append(('policy_shield_low_threshold', 
                                     f"Policy Shield threshold {threshold} below minimum {PRIVACY_THRESHOLDS['policy_shield_min_coverage']}", 
                                     i))
            
            # Check for differential privacy parameter issues
            if re.search(r'epsilon\s*[>=]+\s*\d+', line):
                epsilon_match = re.search(r'epsilon\s*[>=]+\s*(\d+(?:\.\d+)?)', line)
                if epsilon_match:
                    epsilon = float(epsilon_match.group(1))
                    if epsilon > PRIVACY_THRESHOLDS['dp_epsilon_max']:
                        issues.append(('dp_epsilon_too_high',
                                     f"Differential privacy epsilon {epsilon} exceeds maximum {PRIVACY_THRESHOLDS['dp_epsilon_max']}",
                                     i))
            
            # Look for potential PII leakage in logging
            if re.search(r'log\.(?:info|debug|warn|error).*\b(?:user|sender|contact|name|email)\b', line, re.IGNORECASE):
                if not re.search(r'redact|sanitiz|hash|token', line, re.IGNORECASE):
                    issues.append(('potential_pii_logging',
                                 f"Potential PII logging without redaction: {line.strip()}",
                                 i))
            
            # Check for cloud service calls without explicit authorization
            cloud_patterns = ['openai', 'anthropic', 'google', 'azure', 'aws']
            for pattern in cloud_patterns:
                if re.search(rf'\b{pattern}\b.*(?:api|client|request)', line, re.IGNORECASE):
                    if not re.search(r'allow_cloud|cloud_authorized|explicit_consent', line, re.IGNORECASE):
                        issues.append(('cloud_without_authorization',
                                     f"Cloud service usage without explicit authorization check: {line.strip()}",
                                     i))
    
    except Exception as e:
        issues.append(('file_read_error', f"Error reading file: {e}", 0))
    
    return issues

def validate_differential_privacy_config(config_path: str) -> List[str]:
    """Validate differential privacy configuration parameters."""
    issues = []
    
    if not os.path.exists(config_path):
        return issues
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dp_config = config.get('differential_privacy', {})
        
        epsilon = dp_config.get('epsilon', 1.0)
        delta = dp_config.get('delta', 1e-6)
        
        if epsilon <= 0 or epsilon > PRIVACY_THRESHOLDS['dp_epsilon_max']:
            issues.append(f"Invalid epsilon value {epsilon}: must be in (0, {PRIVACY_THRESHOLDS['dp_epsilon_max']}]")
        
        if delta <= 0 or delta > PRIVACY_THRESHOLDS['dp_delta_max']:
            issues.append(f"Invalid delta value {delta}: must be in (0, {PRIVACY_THRESHOLDS['dp_delta_max']}]")
            
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON in config file: {e}")
    except Exception as e:
        issues.append(f"Error validating config: {e}")
    
    return issues

def check_test_privacy_coverage() -> List[str]:
    """Ensure privacy components have adequate test coverage."""
    issues = []
    
    privacy_modules = [
        'src/chatx/redaction/policy_shield.py',
        'src/chatx/privacy/differential_privacy.py',
        'src/chatx/enrichment/confidence_gating.py'
    ]
    
    test_modules = [
        'tests/unit/redaction/test_policy_shield.py',
        'tests/unit/privacy/test_differential_privacy.py', 
        'tests/unit/enrichment/test_confidence_gating.py'
    ]
    
    for module_path, test_path in zip(privacy_modules, test_modules):
        if os.path.exists(module_path) and not os.path.exists(test_path):
            issues.append(f"Privacy-critical module {module_path} missing corresponding test {test_path}")
    
    return issues

def main():
    """Main privacy validation hook."""
    print("[privacy-hook] Validating ChatX privacy engineering compliance...", file=sys.stderr)
    
    all_issues = []
    
    # Check Python files for privacy patterns
    python_files = []
    for root, dirs, files in os.walk('src/chatx'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for py_file in python_files:
        file_issues = check_privacy_patterns(py_file)
        if file_issues:
            all_issues.extend([(py_file, issue_type, message, line) for issue_type, message, line in file_issues])
    
    # Check differential privacy configuration
    config_files = ['config/privacy.json', '.chatx/privacy_config.json', 'src/chatx/config/privacy.json']
    for config_file in config_files:
        dp_issues = validate_differential_privacy_config(config_file)
        if dp_issues:
            all_issues.extend([(config_file, 'dp_config_error', issue, 0) for issue in dp_issues])
    
    # Check test coverage for privacy components
    test_issues = check_test_privacy_coverage()
    if test_issues:
        all_issues.extend([('tests/', 'missing_privacy_tests', issue, 0) for issue in test_issues])
    
    # Report issues
    if all_issues:
        print(f"[privacy-hook] Found {len(all_issues)} privacy compliance issues:", file=sys.stderr)
        for file_path, issue_type, message, line_num in all_issues:
            location = f"{file_path}:{line_num}" if line_num > 0 else file_path
            print(f"  🛡️  {issue_type.upper()}: {message} ({location})", file=sys.stderr)
        print("[privacy-hook] Privacy validation FAILED. Address issues before committing.", file=sys.stderr)
        sys.exit(1)
    else:
        print("[privacy-hook] Privacy compliance validation PASSED.", file=sys.stderr)

if __name__ == "__main__":
    main()