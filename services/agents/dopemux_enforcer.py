"""
DopemuxEnforcer - Architectural Compliance Validation Agent

Validates dopemux-specific architecture rules and patterns.
Provides gentle, ADHD-friendly guidance for compliance.

Authority: Architectural compliance and pattern enforcement

Week: 7
Complexity: 0.6 (Medium-High)
Effort: 5 days (10 focus blocks)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ViolationSeverity(str, Enum):
    """Severity levels for compliance violations"""
    INFO = "info"  # Best practice suggestion
    WARNING = "warning"  # Should fix but not critical
    ERROR = "error"  # Should definitely fix
    CRITICAL = "critical"  # Must fix (blocks if strict_mode)


class ViolationType(str, Enum):
    """Types of compliance violations"""
    TWO_PLANE_BOUNDARY = "two_plane_boundary"  # Direct cross-plane access
    AUTHORITY_MATRIX = "authority_matrix"  # Wrong system for operation
    TOOL_PREFERENCE = "tool_preference"  # bash instead of Serena
    ADHD_CONSTRAINT = "adhd_constraint"  # Too many results, no progressive disclosure
    COMPLEXITY_WARNING = "complexity_warning"  # High complexity without break
    MISSING_LOGGING = "missing_logging"  # Decision not logged to ConPort


@dataclass
class ComplianceViolation:
    """A single compliance violation"""
    type: ViolationType
    severity: ViolationSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    related_rule: Optional[str] = None


@dataclass
class ComplianceReport:
    """Compliance validation report"""
    compliant: bool
    violations: List[ComplianceViolation]
    warnings: List[ComplianceViolation]
    blocking: bool  # Has critical violations in strict mode
    summary: str
    timestamp: datetime


class DopemuxEnforcer:
    """
    Dopemux Architecture Compliance Validator.

    Responsibilities:
    1. Validate two-plane boundary enforcement
    2. Check authority matrix compliance
    3. Enforce ADHD constraints (max 10 results, progressive disclosure)
    4. Validate tool preferences (Serena > bash)
    5. Complexity warnings (>0.7 needs break)
    6. Log violations to ConPort for tracking

    Example:
        enforcer = DopemuxEnforcer(
            workspace_id="/path/to/project",
            strict_mode=False  # Warn vs block
        )
        await enforcer.initialize()

        # Validate code changes
        report = await enforcer.validate_code_change(
            file_path="services/agents/new_agent.py",
            operation_type="create"
        )

        if not report.compliant:
            for violation in report.violations:
                print(f"{violation.severity}: {violation.message}")
    """

    def __init__(
        self,
        workspace_id: str,
        conport_client: Optional[Any] = None,
        serena_workspace: Optional[str] = None,
        strict_mode: bool = False
    ):
        """
        Initialize DopemuxEnforcer.

        Args:
            workspace_id: Absolute path to workspace
            conport_client: ConPort MCP client for logging violations
            serena_workspace: Workspace path for Serena (defaults to workspace_id)
            strict_mode: If True, BLOCK critical violations
        """
        self.workspace_id = workspace_id
        self.serena_workspace = serena_workspace or workspace_id
        self.conport_client = conport_client
        self.strict_mode = strict_mode

        # Validation rules
        self.rules = self._load_validation_rules()

        # Metrics
        self.metrics = {
            "validations_performed": 0,
            "violations_found": 0,
            "warnings_issued": 0,
            "critical_blocks": 0
        }

        logger.info(
            f"DopemuxEnforcer initialized (workspace: {workspace_id}, "
            f"strict: {strict_mode})"
        )

    async def initialize(self):
        """Initialize DopemuxEnforcer (no async setup needed currently)"""
        logger.info("✅ DopemuxEnforcer ready for compliance validation")

    def _load_validation_rules(self) -> Dict[str, Any]:
        """
        Load Dopemux validation rules.

        Rules based on Architecture 3.0 and ADHD principles.
        """
        return {
            "two_plane_boundary": {
                "description": "No direct cross-plane access (use TwoPlaneOrchestrator)",
                "patterns": [
                    "leantime.*import",  # Direct Leantime access
                    "pm_plane.*direct",  # Direct PM plane access
                ],
                "severity": ViolationSeverity.ERROR
            },
            "authority_matrix": {
                "description": "Use correct system for each data type",
                "rules": {
                    "tasks": "PM plane (Leantime)",
                    "decisions": "Cognitive plane (ConPort)",
                    "adhd_state": "Cognitive plane (ADHD Engine)",
                    "progress": "Cognitive plane (ConPort)",
                    "sprint_data": "PM plane (Leantime)"
                },
                "severity": ViolationSeverity.WARNING
            },
            "tool_preferences": {
                "description": "Use MCP tools instead of bash for code operations",
                "forbidden": [
                    ("bash.*cat.*\\.py", "Use Read tool or Serena MCP"),
                    ("bash.*grep.*code", "Use Grep tool or Serena find_symbol"),
                    ("bash.*find.*\\.py", "Use Glob tool or Serena list_dir"),
                ],
                "severity": ViolationSeverity.WARNING
            },
            "adhd_constraints": {
                "description": "ADHD-optimized result limits and progressive disclosure",
                "rules": {
                    "max_results": 10,  # Never return > 10 items without pagination
                    "progressive_disclosure": True,  # Essential first, details on request
                    "complexity_warnings": 0.7  # Warn at >0.7 complexity
                },
                "severity": ViolationSeverity.INFO
            },
            "complexity_breaks": {
                "description": "Mandatory breaks for high complexity tasks",
                "thresholds": {
                    "info": 0.5,  # Suggest break at 25 min
                    "warning": 0.7,  # Recommend break at 25 min
                    "critical": 0.9  # Mandatory break at 25 min
                },
                "severity": ViolationSeverity.WARNING
            }
        }

    async def validate_code_change(
        self,
        file_path: str,
        operation_type: str = "modify",  # create, modify, delete
        content: Optional[str] = None
    ) -> ComplianceReport:
        """
        Validate code change against Dopemux architecture rules.

        Args:
            file_path: Path to file being changed
            operation_type: Type of change (create, modify, delete)
            content: File content to validate (optional)

        Returns:
            ComplianceReport with violations and warnings
        """
        self.metrics["validations_performed"] += 1

        violations = []
        warnings = []

        logger.info(f"🔍 Validating {operation_type} operation on {file_path}")

        # Rule 1: Check complexity if modifying code
        if operation_type in ["create", "modify"] and content:
            complexity_violations = await self._check_complexity(file_path, content)
            violations.extend(complexity_violations)

        # Rule 2: Check tool preferences in content
        if content:
            tool_violations = self._check_tool_preferences(content, file_path)
            violations.extend(tool_violations)

        # Rule 3: Check two-plane boundaries
        boundary_violations = self._check_two_plane_boundaries(file_path, content)
        violations.extend(boundary_violations)

        # Rule 4: Check ADHD constraints
        adhd_violations = self._check_adhd_constraints(content)
        violations.extend(adhd_violations)

        # Separate violations by severity
        critical = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        errors = [v for v in violations if v.severity == ViolationSeverity.ERROR]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        info = [v for v in violations if v.severity == ViolationSeverity.INFO]

        # Update metrics
        self.metrics["violations_found"] += len(errors) + len(critical)
        self.metrics["warnings_issued"] += len(warnings)
        if critical:
            self.metrics["critical_blocks"] += 1

        # Determine compliance
        compliant = len(critical) == 0 and len(errors) == 0
        blocking = len(critical) > 0 and self.strict_mode

        # Create summary
        summary = self._generate_summary(critical, errors, warnings, info)

        # Log to ConPort if violations found
        if (critical or errors or warnings) and self.conport_client:
            try:
                await self._log_violations_to_conport(file_path, violations)
            except Exception as e:
                logger.warning(f"⚠️ Failed to log violations to ConPort: {e}")

        return ComplianceReport(
            compliant=compliant,
            violations=violations,
            warnings=warnings,
            blocking=blocking,
            summary=summary,
            timestamp=datetime.now(timezone.utc)
        )

    async def _check_complexity(
        self,
        file_path: str,
        content: str
    ) -> List[ComplianceViolation]:
        """
        Check code complexity using Serena MCP.

        Week 7: 70% code reuse from Serena complexity scoring
        """
        violations = []

        # TODO: Integrate with Serena MCP
        # For now, use simple heuristic
        line_count = len(content.split('\n'))
        estimated_complexity = min(1.0, line_count / 500)  # Rough estimate

        complexity_thresholds = self.rules["complexity_breaks"]["thresholds"]

        if estimated_complexity >= complexity_thresholds["critical"]:
            violations.append(ComplianceViolation(
                type=ViolationType.COMPLEXITY_WARNING,
                severity=ViolationSeverity.CRITICAL,
                message=f"Very high complexity ({estimated_complexity:.2f}) - Mandatory break after 25 min",
                file_path=file_path,
                suggestion="Break this into smaller functions or take break after 25 minutes"
            ))
        elif estimated_complexity >= complexity_thresholds["warning"]:
            violations.append(ComplianceViolation(
                type=ViolationType.COMPLEXITY_WARNING,
                severity=ViolationSeverity.WARNING,
                message=f"High complexity ({estimated_complexity:.2f}) - Break recommended after 25 min",
                file_path=file_path,
                suggestion="Consider breaking into smaller functions"
            ))
        elif estimated_complexity >= complexity_thresholds["info"]:
            violations.append(ComplianceViolation(
                type=ViolationType.COMPLEXITY_WARNING,
                severity=ViolationSeverity.INFO,
                message=f"Medium complexity ({estimated_complexity:.2f}) - Suggest break at 25 min",
                file_path=file_path,
                suggestion="Take break if working longer than 25 minutes"
            ))

        return violations

    def _check_tool_preferences(
        self,
        content: str,
        file_path: str
    ) -> List[ComplianceViolation]:
        """Check for tool preference violations (bash instead of MCP)"""
        violations = []

        forbidden_patterns = self.rules["tool_preferences"]["forbidden"]

        for pattern, suggestion in forbidden_patterns:
            if "bash" in content.lower() and ("cat" in content or "grep" in content or "find" in content):
                violations.append(ComplianceViolation(
                    type=ViolationType.TOOL_PREFERENCE,
                    severity=ViolationSeverity.WARNING,
                    message="Using bash for code operations (prefer MCP tools)",
                    file_path=file_path,
                    suggestion=suggestion
                ))
                break  # Only warn once per file

        return violations

    def _check_two_plane_boundaries(
        self,
        file_path: str,
        content: Optional[str]
    ) -> List[ComplianceViolation]:
        """Check for direct cross-plane access violations"""
        violations = []

        if not content:
            return violations

        # Check for direct Leantime access (should use TwoPlaneOrchestrator)
        if "import leantime" in content.lower() or "from leantime" in content.lower():
            violations.append(ComplianceViolation(
                type=ViolationType.TWO_PLANE_BOUNDARY,
                severity=ViolationSeverity.ERROR,
                message="Direct Leantime access detected (use TwoPlaneOrchestrator)",
                file_path=file_path,
                suggestion="Use TwoPlaneOrchestrator.pm_to_cognitive() or cognitive_to_pm()"
            ))

        return violations

    def _check_adhd_constraints(self, content: Optional[str]) -> List[ComplianceViolation]:
        """Check ADHD-specific constraints (max results, progressive disclosure)"""
        violations = []

        if not content:
            return violations

        # Check for large result sets without pagination
        # Look for patterns like: limit=50, limit(50), [:100]
        import re

        # Pattern 1: limit=50 or limit = 50
        limit_pattern = r"limit\s*=\s*(\d+)"
        matches = re.findall(limit_pattern, content)

        # Pattern 2: .limit(50) or .limit (50)
        limit_method_pattern = r"\.limit\s*\(\s*(\d+)\s*\)"
        matches.extend(re.findall(limit_method_pattern, content))

        # Pattern 3: [:50] or [0:100]
        slice_pattern = r"\[(?:\d+:)?(\d+)\]"
        slice_matches = re.findall(slice_pattern, content)
        matches.extend(slice_matches)

        for match in matches:
            limit = int(match)
            if limit > self.rules["adhd_constraints"]["rules"]["max_results"]:
                violations.append(ComplianceViolation(
                    type=ViolationType.ADHD_CONSTRAINT,
                    severity=ViolationSeverity.INFO,
                    message=f"Result limit {limit} exceeds ADHD-friendly max (10)",
                    suggestion=f"Consider reducing limit to 10 or add pagination"
                ))
                break  # Only warn once per file

        return violations

    def _generate_summary(
        self,
        critical: List[ComplianceViolation],
        errors: List[ComplianceViolation],
        warnings: List[ComplianceViolation],
        info: List[ComplianceViolation]
    ) -> str:
        """Generate human-readable compliance summary"""

        if not (critical or errors or warnings or info):
            return "✅ Fully compliant with Dopemux architecture"

        parts = []

        if critical:
            parts.append(f"🚫 {len(critical)} critical violation(s)")
        if errors:
            parts.append(f"❌ {len(errors)} error(s)")
        if warnings:
            parts.append(f"⚠️ {len(warnings)} warning(s)")
        if info:
            parts.append(f"💡 {len(info)} suggestion(s)")

        return ", ".join(parts)

    async def _log_violations_to_conport(
        self,
        file_path: str,
        violations: List[ComplianceViolation]
    ):
        """
        Log compliance violations to ConPort for tracking.

        Week 7: ConPort integration for compliance monitoring
        """
        if not self.conport_client:
            return

        # Log to custom_data category: "compliance_violations"
        violation_data = {
            "file_path": file_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "violation_count": len(violations),
            "violations": [
                {
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "message": v.message,
                    "suggestion": v.suggestion
                }
                for v in violations
            ]
        }

        await self.conport_client.log_custom_data(
            workspace_id=self.workspace_id,
            category="compliance_violations",
            key=f"{file_path}_{int(datetime.now().timestamp())}",
            value=violation_data
        )

        logger.info(f"📝 Compliance violations logged to ConPort for {file_path}")

    async def validate_operation(
        self,
        operation: str,
        data_type: str,
        source_plane: str
    ) -> ComplianceReport:
        """
        Validate operation against authority matrix.

        Checks if the operation is being performed by the correct plane.

        Args:
            operation: Operation name (e.g., "update_task")
            data_type: Data type (e.g., "tasks", "decisions")
            source_plane: Which plane is making the request ("pm" or "cognitive")

        Returns:
            ComplianceReport with authority violations
        """
        self.metrics["validations_performed"] += 1  # Track validation

        violations = []

        authority_rules = self.rules["authority_matrix"]["rules"]

        if data_type in authority_rules:
            authority = authority_rules[data_type]

            # Check write operations
            if operation.startswith("update_") or operation.startswith("set_") or operation.startswith("create_"):
                # Write operation
                if source_plane not in authority.lower():
                    self.metrics["violations_found"] += 1  # Track violation
                    violations.append(ComplianceViolation(
                        type=ViolationType.AUTHORITY_MATRIX,
                        severity=ViolationSeverity.ERROR,
                        message=f"{source_plane} cannot write {data_type} (authority: {authority})",
                        suggestion=f"Route through {authority} or use TwoPlaneOrchestrator"
                    ))

        compliant = len(violations) == 0
        blocking = any(v.severity == ViolationSeverity.CRITICAL for v in violations) and self.strict_mode

        return ComplianceReport(
            compliant=compliant,
            violations=violations,
            warnings=[],
            blocking=blocking,
            summary=self._generate_summary([], violations, [], []),
            timestamp=datetime.now(timezone.utc)
        )

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get enforcement metrics"""
        return {
            "validations_performed": self.metrics["validations_performed"],
            "violations_found": self.metrics["violations_found"],
            "warnings_issued": self.metrics["warnings_issued"],
            "critical_blocks": self.metrics["critical_blocks"],
            "strict_mode": self.strict_mode
        }

    async def close(self):
        """Shutdown enforcer"""
        logger.info("🛑 DopemuxEnforcer shutdown complete")


# ============================================================================
# Demo / Test
# ============================================================================

async def demo():
    """Demonstrate DopemuxEnforcer"""

    print("\n" + "="*70)
    print("DOPEMUX ENFORCER DEMO")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False  # Warn only
    )

    await enforcer.initialize()

    # Example 1: Validate code with bash usage
    print("\n" + "="*70)
    print("Example 1: Tool Preference Violation (bash cat)")
    print("="*70)

    code_with_bash = '''
async def read_file():
    result = subprocess.run(["bash", "cat", "auth.py"], capture_output=True)
    return result.stdout
'''

    report = await enforcer.validate_code_change(
        file_path="services/test/bad_example.py",
        operation_type="create",
        content=code_with_bash
    )

    print(f"\nCompliance: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")
        if v.suggestion:
            print(f"    Suggestion: {v.suggestion}")

    # Example 2: Validate authority matrix
    print("\n" + "="*70)
    print("Example 2: Authority Matrix Validation")
    print("="*70)

    report = await enforcer.validate_operation(
        operation="update_decision",
        data_type="decisions",
        source_plane="pm"  # PM trying to write decisions!
    )

    print(f"\nCompliance: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")
        if v.suggestion:
            print(f"    Suggestion: {v.suggestion}")

    # Metrics
    print("\n" + "="*70)
    print("Enforcement Metrics")
    print("="*70)

    metrics = await enforcer.get_metrics_summary()
    print(f"\nValidations Performed: {metrics['validations_performed']}")
    print(f"Violations Found: {metrics['violations_found']}")
    print(f"Warnings Issued: {metrics['warnings_issued']}")
    print(f"Strict Mode: {metrics['strict_mode']}")

    await enforcer.close()

    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
