#!/usr/bin/env python3
"""
MCP System Validation Script
Validates the complete MCP optimization system implementation
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

class MCPSystemValidator:
    def __init__(self):
        self.project_root = Path('.')
        self.claude_dir = self.project_root / '.claude'
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'unknown',
            'recommendations': []
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run comprehensive system validation"""
        print("🚀 Starting MCP System Validation")
        print("=" * 50)

        validations = [
            ('directory_structure', self.validate_directory_structure),
            ('todo_system', self.validate_todo_system),
            ('mcp_configuration', self.validate_mcp_configuration),
            ('hooks_system', self.validate_hooks_system),
            ('monitoring_system', self.validate_monitoring_system),
            ('conport_integration', self.validate_conport_integration),
            ('workflow_patterns', self.validate_workflow_patterns)
        ]

        for test_name, test_func in validations:
            print(f"\n🔍 Validating {test_name}...")
            try:
                result = test_func()
                self.validation_results['tests'][test_name] = result
                status = "✅ PASS" if result['status'] == 'pass' else "❌ FAIL"
                print(f"   {status}: {result['message']}")
                if 'details' in result:
                    print(f"   Details: {result['details']}")
            except Exception as e:
                self.validation_results['tests'][test_name] = {
                    'status': 'error',
                    'message': f'Validation failed: {str(e)}'
                }
                print(f"   ❌ ERROR: {str(e)}")

        # Calculate overall status
        self.calculate_overall_status()

        # Generate recommendations
        self.generate_recommendations()

        return self.validation_results

    def validate_directory_structure(self) -> Dict[str, Any]:
        """Validate directory structure is properly set up"""
        required_dirs = [
            '.claude/todos',
            '.claude/todos/high',
            '.claude/todos/medium',
            '.claude/todos/low',
            '.claude/templates',
            '.claude/monitoring',
            '.claude/workflows',
            '.claude/scripts'
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            return {
                'status': 'fail',
                'message': f'Missing {len(missing_dirs)} required directories',
                'details': f'Missing: {", ".join(missing_dirs)}'
            }

        return {
            'status': 'pass',
            'message': f'All {len(required_dirs)} required directories present'
        }

    def validate_todo_system(self) -> Dict[str, Any]:
        """Validate todo system is properly implemented"""
        required_files = [
            '.claude/todos/README.md',
            '.claude/todos/active.md',
            '.claude/todos/completed.md',
            '.claude/todos/backlog.md',
            '.claude/templates/task.md',
            '.claude/commands/todo-manager.py'
        ]

        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            return {
                'status': 'fail',
                'message': f'Missing {len(missing_files)} todo system files',
                'details': f'Missing: {", ".join(missing_files)}'
            }

        # Check for migrated tasks
        total_tasks = 0
        for priority in ['high', 'medium', 'low']:
            priority_dir = self.project_root / '.claude' / 'todos' / priority
            if priority_dir.exists():
                total_tasks += len(list(priority_dir.glob('*.md')))

        if total_tasks == 0:
            return {
                'status': 'warning',
                'message': 'Todo system files present but no tasks found',
                'details': 'Consider adding sample tasks or checking migration status'
            }

        return {
            'status': 'pass',
            'message': f'Todo system complete with {total_tasks} tasks'
        }

    def validate_mcp_configuration(self) -> Dict[str, Any]:
        """Validate MCP configuration is properly set up"""
        config_file = self.claude_dir / 'mcp-config.json'

        if not config_file.exists():
            return {
                'status': 'fail',
                'message': 'MCP configuration file missing',
                'details': 'mcp-config.json not found in .claude directory'
            }

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            required_keys = ['version', 'server_priorities', 'memory_cache']
            missing_keys = []

            for key in required_keys:
                if key not in config:
                    missing_keys.append(key)

            if missing_keys:
                return {
                    'status': 'fail',
                    'message': f'MCP config missing required keys',
                    'details': f'Missing: {", ".join(missing_keys)}'
                }

            return {
                'status': 'pass',
                'message': 'MCP configuration valid',
                'details': f'Version {config.get("version", "unknown")}, {len(config.get("server_priorities", {}))} server priorities configured'
            }

        except json.JSONDecodeError as e:
            return {
                'status': 'fail',
                'message': 'MCP configuration JSON invalid',
                'details': str(e)
            }

    def validate_hooks_system(self) -> Dict[str, Any]:
        """Validate hooks system is optimized"""
        settings_file = self.claude_dir / 'settings.json'

        if not settings_file.exists():
            return {
                'status': 'fail',
                'message': 'Settings file missing',
                'details': 'Cannot validate hook configuration'
            }

        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            hooks = settings.get('hooks', {}).get('PreToolUse', [])

            if not hooks:
                return {
                    'status': 'fail',
                    'message': 'No PreToolUse hooks configured',
                    'details': 'System needs hook configuration for MCP optimization'
                }

            # Check for taskmaster/devdocs references (should be removed)
            hook_text = json.dumps(hooks)
            if 'taskmaster' in hook_text.lower() or 'devdocs' in hook_text.lower():
                return {
                    'status': 'warning',
                    'message': 'Taskmaster/DevDocs references still present in hooks',
                    'details': 'Consider removing outdated hook references'
                }

            return {
                'status': 'pass',
                'message': f'Hooks system configured with {len(hooks)} hook groups'
            }

        except json.JSONDecodeError as e:
            return {
                'status': 'fail',
                'message': 'Settings JSON invalid',
                'details': str(e)
            }

    def validate_monitoring_system(self) -> Dict[str, Any]:
        """Validate monitoring system is properly set up"""
        required_files = [
            '.claude/monitoring/config.yaml',
            '.claude/monitoring/performance-tracker.py'
        ]

        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            return {
                'status': 'fail',
                'message': f'Missing {len(missing_files)} monitoring files',
                'details': f'Missing: {", ".join(missing_files)}'
            }

        return {
            'status': 'pass',
            'message': 'Monitoring system files present'
        }

    def validate_conport_integration(self) -> Dict[str, Any]:
        """Validate ConPort integration configuration"""
        conport_file = self.claude_dir / 'conport-integration.yaml'

        if not conport_file.exists():
            return {
                'status': 'fail',
                'message': 'ConPort integration config missing',
                'details': 'conport-integration.yaml not found'
            }

        try:
            import yaml
            with open(conport_file, 'r') as f:
                config = yaml.safe_load(f)

            if 'conport_config' not in config:
                return {
                    'status': 'fail',
                    'message': 'ConPort config missing required sections',
                    'details': 'conport_config section not found'
                }

            return {
                'status': 'pass',
                'message': 'ConPort integration configured',
                'details': f'Workspace: {config["conport_config"].get("workspace_id", "unknown")}'
            }

        except ImportError:
            return {
                'status': 'warning',
                'message': 'PyYAML not available for ConPort validation',
                'details': 'Cannot fully validate YAML configuration'
            }
        except Exception as e:
            return {
                'status': 'fail',
                'message': 'ConPort config validation failed',
                'details': str(e)
            }

    def validate_workflow_patterns(self) -> Dict[str, Any]:
        """Validate workflow patterns documentation"""
        workflow_file = self.claude_dir / 'workflows' / 'optimized-patterns.md'

        if not workflow_file.exists():
            return {
                'status': 'fail',
                'message': 'Workflow patterns documentation missing',
                'details': 'optimized-patterns.md not found'
            }

        try:
            with open(workflow_file, 'r') as f:
                content = f.read()

            required_patterns = [
                'Memory-First Development',
                'Research-Driven Implementation',
                'Multi-Model Validation'
            ]

            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)

            if missing_patterns:
                return {
                    'status': 'warning',
                    'message': f'Missing {len(missing_patterns)} workflow patterns',
                    'details': f'Missing: {", ".join(missing_patterns)}'
                }

            return {
                'status': 'pass',
                'message': 'Workflow patterns documented',
                'details': f'{len(required_patterns)} core patterns present'
            }

        except Exception as e:
            return {
                'status': 'fail',
                'message': 'Workflow patterns validation failed',
                'details': str(e)
            }

    def calculate_overall_status(self):
        """Calculate overall system status"""
        test_results = self.validation_results['tests']

        if not test_results:
            self.validation_results['overall_status'] = 'unknown'
            return

        statuses = [result['status'] for result in test_results.values()]

        if 'fail' in statuses:
            self.validation_results['overall_status'] = 'fail'
        elif 'warning' in statuses:
            self.validation_results['overall_status'] = 'warning'
        elif 'error' in statuses:
            self.validation_results['overall_status'] = 'error'
        else:
            self.validation_results['overall_status'] = 'pass'

    def generate_recommendations(self):
        """Generate system improvement recommendations"""
        recommendations = []

        test_results = self.validation_results['tests']

        if test_results.get('directory_structure', {}).get('status') == 'pass':
            recommendations.append("✅ Core directory structure is solid")

        if test_results.get('todo_system', {}).get('status') == 'pass':
            recommendations.append("✅ Todo system successfully migrated from taskmaster")

        if test_results.get('mcp_configuration', {}).get('status') == 'pass':
            recommendations.append("✅ MCP server optimization configuration is ready")

        if test_results.get('monitoring_system', {}).get('status') == 'pass':
            recommendations.append("✅ Performance monitoring system is configured")

        if test_results.get('conport_integration', {}).get('status') == 'pass':
            recommendations.append("✅ ConPort integration provides persistent memory")

        # Always include these final recommendations
        recommendations.extend([
            "🚀 Start using /todo-add for new tasks",
            "📊 Monitor performance with python .claude/monitoring/performance-tracker.py",
            "🔄 Use optimized workflow patterns from .claude/workflows/optimized-patterns.md",
            "💾 ConPort automatically tracks all decisions and progress"
        ])

        self.validation_results['recommendations'] = recommendations

    def save_validation_report(self):
        """Save validation results to file"""
        report_file = self.claude_dir / 'system-validation-report.json'

        try:
            with open(report_file, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)

            print(f"\n📋 Validation report saved to: {report_file}")

        except Exception as e:
            print(f"Warning: Could not save validation report: {e}")

def main():
    """Main validation function"""
    validator = MCPSystemValidator()
    results = validator.run_all_validations()

    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)

    print(f"Overall Status: {results['overall_status'].upper()}")

    print("
Test Results:")
    for test_name, test_result in results['tests'].items():
        status_icon = {'pass': '✅', 'fail': '❌', 'warning': '⚠️', 'error': '🚫'}.get(test_result['status'], '❓')
        print(f"  {status_icon} {test_name}: {test_result['message']}")

    if results['recommendations']:
        print("
💡 Recommendations:")
        for rec in results['recommendations']:
            print(f"  {rec}")

    print(f"\n📅 Validation completed at: {results['timestamp']}")

    # Save report
    validator.save_validation_report()

    return 0 if results['overall_status'] == 'pass' else 1

if __name__ == '__main__':
    sys.exit(main())