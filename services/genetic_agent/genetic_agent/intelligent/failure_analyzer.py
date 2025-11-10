"""Failure Analysis System for intelligent error signal extraction."""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FailureSeverity(Enum):
    """Severity levels for failure signals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FailureSignal:
    """Represents an extracted failure signal with metadata."""
    signal_type: str
    description: str
    severity: FailureSeverity
    confidence: float
    source_location: Optional[str] = None
    suggested_fix: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.severity, FailureSeverity):
            self.severity = FailureSeverity(self.severity)


class FailureAnalyzer:
    """Analyzes error messages and test outputs to extract actionable failure signals."""

    def __init__(self):
        self.signal_patterns = self._initialize_signal_patterns()

    def _initialize_signal_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the signal ontology with patterns for common failure types."""
        return {
            # Logic Errors
            "assertion_failure": {
                "patterns": [
                    r"AssertionError",
                    r"assert.*failed",
                    r"assertion.*failed"
                ],
                "severity": FailureSeverity.HIGH,
                "description": "Logic assertion failed - check conditional logic",
                "suggested_fix": "Review conditional statements and boolean logic"
            },

            "logic_error": {
                "patterns": [
                    r"incorrect logic",
                    r"wrong calculation",
                    r"logic.*error"
                ],
                "severity": FailureSeverity.HIGH,
                "description": "Logic error in algorithm implementation",
                "suggested_fix": "Review algorithm logic and mathematical operations"
            },

            # Runtime Errors
            "null_pointer": {
                "patterns": [
                    r"NoneType",
                    r"None",
                    r"null pointer",
                    r"'NoneType' object",
                    r"None.*attribute"
                ],
                "severity": FailureSeverity.HIGH,
                "description": "Null pointer exception - accessing attribute of None",
                "suggested_fix": "Add null checks before accessing object attributes"
            },

            "boundary_error": {
                "patterns": [
                    r"IndexError",
                    r"list index out of range",
                    r"index.*out of range",
                    r"KeyError",
                    r"key.*not found"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "Boundary or indexing error",
                "suggested_fix": "Check array/list boundaries and key existence"
            },

            "type_error": {
                "patterns": [
                    r"TypeError",
                    r"unhashable type",
                    r"type.*error",
                    r"unsupported operand"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "Type mismatch or unsupported operation",
                "suggested_fix": "Verify variable types and operation compatibility"
            },

            "attribute_error": {
                "patterns": [
                    r"AttributeError",
                    r"'object' has no attribute",
                    r"has no attribute"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "Attribute access on object without that attribute",
                "suggested_fix": "Check object attributes and method availability"
            },

            # Import and Module Errors
            "import_error": {
                "patterns": [
                    r"ImportError",
                    r"ModuleNotFoundError",
                    r"No module named"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "Import or module resolution error",
                "suggested_fix": "Check import statements and module availability"
            },

            # Code Quality Issues
            "unused_code": {
                "patterns": [
                    r"unused variable",
                    r"unused import",
                    r"dead code"
                ],
                "severity": FailureSeverity.LOW,
                "description": "Unused code detected",
                "suggested_fix": "Remove unused variables, imports, or code"
            },

            "complexity_issue": {
                "patterns": [
                    r"high complexity",
                    r"cognitive complexity",
                    r"too complex"
                ],
                "severity": FailureSeverity.LOW,
                "description": "Code complexity exceeds recommended limits",
                "suggested_fix": "Refactor complex functions into smaller, simpler functions"
            },

            # Test-Specific Errors
            "test_failure": {
                "patterns": [
                    r"FAILED",
                    r"test.*failed",
                    r"FAILED.*test"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "Test case failure",
                "suggested_fix": "Review test expectations and implementation"
            },

            # Syntax and Parse Errors
            "syntax_error": {
                "patterns": [
                    r"SyntaxError",
                    r"syntax.*error",
                    r"invalid syntax"
                ],
                "severity": FailureSeverity.CRITICAL,
                "description": "Syntax error preventing code execution",
                "suggested_fix": "Check Python syntax, indentation, and statement structure"
            },

            # Value and Data Errors
            "value_error": {
                "patterns": [
                    r"ValueError",
                    r"value.*error",
                    r"invalid.*value"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "Invalid value provided to function or operation",
                "suggested_fix": "Validate input values and add error handling"
            },

            # File and IO Errors
            "file_error": {
                "patterns": [
                    r"FileNotFoundError",
                    r"IOError",
                    r"file.*error"
                ],
                "severity": FailureSeverity.MEDIUM,
                "description": "File or I/O operation error",
                "suggested_fix": "Check file paths, permissions, and availability"
            },

            # Runtime Environment Errors
            "runtime_error": {
                "patterns": [
                    r"RuntimeError",
                    r"runtime.*error"
                ],
                "severity": FailureSeverity.HIGH,
                "description": "Runtime execution error",
                "suggested_fix": "Review runtime conditions and error handling"
            },

            # Memory and Resource Errors
            "memory_error": {
                "patterns": [
                    r"MemoryError",
                    r"memory.*error",
                    r"out of memory"
                ],
                "severity": FailureSeverity.CRITICAL,
                "description": "Memory allocation or usage error",
                "suggested_fix": "Optimize memory usage, check for memory leaks"
            }
        }

    def extract_signals(self, error_text: str, source_type: str = "unknown") -> List[FailureSignal]:
        """Extract failure signals from error text.

        Args:
            error_text: The error message or test output to analyze
            source_type: Source of the error ("pytest", "runtime", "lint", etc.)

        Returns:
            List of extracted failure signals with confidence scores
        """
        signals = []
        error_text_lower = error_text.lower()

        for signal_type, signal_config in self.signal_patterns.items():
            confidence = self._calculate_pattern_match(error_text_lower, signal_config["patterns"])

            if confidence > 0.0:
                signal = FailureSignal(
                    signal_type=signal_type,
                    description=signal_config["description"],
                    severity=signal_config["severity"],
                    confidence=confidence,
                    source_location=source_type,
                    suggested_fix=signal_config["suggested_fix"]
                )
                signals.append(signal)

        # Sort by confidence (highest first)
        signals.sort(key=lambda s: s.confidence, reverse=True)

        return signals

    def _calculate_pattern_match(self, text: str, patterns: List[str]) -> float:
        """Calculate confidence score for pattern matching."""
        max_confidence = 0.0

        for pattern in patterns:
            # Use regex matching with case-insensitive search
            if re.search(pattern, text, re.IGNORECASE):
                # Base confidence on pattern specificity
                confidence = self._assess_pattern_specificity(pattern)

                # Boost confidence for exact matches
                if re.search(r'\b' + re.escape(pattern.lower()) + r'\b', text):
                    confidence += 0.2

                max_confidence = max(max_confidence, min(confidence, 1.0))

        return max_confidence

    def _assess_pattern_specificity(self, pattern: str) -> float:
        """Assess how specific and reliable a pattern is."""
        # More specific patterns get higher base confidence
        if "AttributeError" in pattern or "TypeError" in pattern:
            return 0.9  # Very specific error types
        elif "AssertionError" in pattern:
            return 0.85
        elif "IndexError" in pattern or "KeyError" in pattern:
            return 0.8
        elif "ImportError" in pattern or "SyntaxError" in pattern:
            return 0.95  # Critical syntax/import issues
        elif "unused" in pattern.lower():
            return 0.6  # Code quality issues are less critical
        elif "complexity" in pattern.lower():
            return 0.5  # Subjective quality metric
        else:
            return 0.7  # Default confidence for other patterns

    def analyze_test_output(self, test_output: str) -> Dict[str, Any]:
        """Analyze pytest or test framework output for failure patterns."""
        signals = self.extract_signals(test_output, "pytest")

        # Extract specific test failure information
        failed_tests = []
        if "FAILED" in test_output:
            # Parse pytest output for failed test names
            lines = test_output.split('\n')
            for line in lines:
                if "FAILED" in line and "::" in line:
                    # Extract test name from pytest output format
                    test_name = line.split("::")[-1].strip()
                    failed_tests.append(test_name)

        return {
            "signals": signals,
            "failed_tests": failed_tests,
            "total_signals": len(signals),
            "high_severity_signals": len([s for s in signals if s.severity in [FailureSeverity.HIGH, FailureSeverity.CRITICAL]])
        }

    def analyze_runtime_error(self, error_message: str, traceback: str = "") -> Dict[str, Any]:
        """Analyze runtime error with optional traceback."""
        combined_text = f"{error_message}\n{traceback}"
        signals = self.extract_signals(combined_text, "runtime")

        return {
            "signals": signals,
            "primary_signal": signals[0] if signals else None,
            "error_type": self._extract_error_type(error_message),
            "has_traceback": bool(traceback.strip())
        }

    def _extract_error_type(self, error_message: str) -> str:
        """Extract the main error type from an error message."""
        # Look for common error type patterns
        error_patterns = [
            (r"(AttributeError|TypeError|ValueError|KeyError|IndexError|ImportError|SyntaxError)", "python_builtin"),
            (r"(AssertionError)", "assertion"),
            (r"(MemoryError|RecursionError)", "resource"),
            (r"(OSError|IOError)", "io"),
            (r"(ConnectionError|TimeoutError)", "network")
        ]

        for pattern, category in error_patterns:
            if re.search(pattern, error_message):
                return category

        return "unknown"

    def get_signal_statistics(self, signals: List[FailureSignal]) -> Dict[str, Any]:
        """Generate statistics about extracted signals."""
        if not signals:
            return {"total_signals": 0}

        severity_counts = {}
        for severity in FailureSeverity:
            severity_counts[severity.value] = 0

        for signal in signals:
            severity_counts[signal.severity.value] += 1

        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        high_confidence_signals = len([s for s in signals if s.confidence >= 0.8])

        return {
            "total_signals": len(signals),
            "severity_breakdown": severity_counts,
            "average_confidence": round(avg_confidence, 2),
            "high_confidence_signals": high_confidence_signals,
            "signal_types": list(set(s.signal_type for s in signals))
        }