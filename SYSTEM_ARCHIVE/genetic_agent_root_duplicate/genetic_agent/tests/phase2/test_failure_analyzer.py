"""Unit tests for the Failure Analysis System."""

import pytest
from genetic_agent.intelligent.failure_analyzer import (
    FailureAnalyzer,
    FailureSignal,
    FailureSeverity
)


@pytest.fixture
def analyzer():
    """Fixture for FailureAnalyzer instance."""
    return FailureAnalyzer()


class TestFailureAnalyzer:
    """Test suite for FailureAnalyzer."""

    def test_extract_signals_null_pointer(self, analyzer):
        """Test extraction of null pointer signals."""
        error_text = "AttributeError: 'NoneType' object has no attribute 'name'"
        signals = analyzer.extract_signals(error_text, "runtime")

        assert len(signals) > 0
        primary_signal = signals[0]
        assert primary_signal.signal_type == "null_pointer"
        assert primary_signal.severity == FailureSeverity.HIGH
        assert primary_signal.confidence > 0.8
        assert "null checks" in primary_signal.suggested_fix

    def test_extract_signals_boundary_error(self, analyzer):
        """Test extraction of boundary error signals."""
        error_text = "IndexError: list index out of range"
        signals = analyzer.extract_signals(error_text, "runtime")

        assert len(signals) > 0
        primary_signal = signals[0]
        assert primary_signal.signal_type == "boundary_error"
        assert primary_signal.severity == FailureSeverity.MEDIUM
        assert primary_signal.confidence > 0.7

    def test_extract_signals_assertion_failure(self, analyzer):
        """Test extraction of assertion failure signals."""
        error_text = "AssertionError: Expected True but got False"
        signals = analyzer.extract_signals(error_text, "pytest")

        assert len(signals) > 0
        primary_signal = signals[0]
        assert primary_signal.signal_type == "assertion_failure"
        assert primary_signal.severity == FailureSeverity.HIGH
        assert primary_signal.confidence > 0.8

    def test_extract_signals_type_error(self, analyzer):
        """Test extraction of type error signals."""
        error_text = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        signals = analyzer.extract_signals(error_text, "runtime")

        assert len(signals) > 0
        primary_signal = signals[0]
        assert primary_signal.signal_type == "type_error"
        assert primary_signal.severity == FailureSeverity.MEDIUM
        assert primary_signal.confidence > 0.7

    def test_extract_signals_syntax_error(self, analyzer):
        """Test extraction of syntax error signals."""
        error_text = "SyntaxError: invalid syntax"
        signals = analyzer.extract_signals(error_text, "runtime")

        assert len(signals) > 0
        primary_signal = signals[0]
        assert primary_signal.signal_type == "syntax_error"
        assert primary_signal.severity == FailureSeverity.CRITICAL
        assert primary_signal.confidence > 0.9

    def test_extract_signals_multiple_patterns(self, analyzer):
        """Test extraction when multiple patterns match."""
        error_text = "AttributeError: 'NoneType' object has no attribute 'name' and TypeError: unsupported operand"
        signals = analyzer.extract_signals(error_text, "runtime")

        # Should find both null_pointer and type_error signals
        signal_types = [s.signal_type for s in signals]
        assert "null_pointer" in signal_types
        assert "type_error" in signal_types

        # Should be sorted by confidence (highest first)
        assert signals[0].confidence >= signals[1].confidence

    def test_extract_signals_no_match(self, analyzer):
        """Test behavior when no patterns match."""
        error_text = "This is a custom error message with no standard patterns"
        signals = analyzer.extract_signals(error_text, "runtime")

        # Should return empty list or very low confidence signals
        high_conf_signals = [s for s in signals if s.confidence > 0.5]
        assert len(high_conf_signals) == 0

    def test_analyze_test_output(self, analyzer):
        """Test analysis of pytest output."""
        test_output = """
        ============================= test session starts ==============================
        test_example.py::test_function FAILED
        test_example.py::test_another FAILED
        ======================== 2 failed, 8 passed in 1.23s ========================
        """

        result = analyzer.analyze_test_output(test_output)

        assert result["total_signals"] > 0
        assert len(result["failed_tests"]) >= 2
        assert "test_function" in result["failed_tests"]
        assert "test_another" in result["failed_tests"]

    def test_analyze_runtime_error(self, analyzer):
        """Test analysis of runtime error."""
        error_message = "AttributeError: 'NoneType' object has no attribute 'name'"
        traceback = "File 'example.py', line 10, in function\n    obj.name"

        result = analyzer.analyze_runtime_error(error_message, traceback)

        assert result["total_signals"] > 0
        assert result["primary_signal"] is not None
        assert result["error_type"] == "python_builtin"
        assert result["has_traceback"] is True

    def test_get_signal_statistics(self, analyzer):
        """Test signal statistics generation."""
        signals = [
            FailureSignal("null_pointer", "test", FailureSeverity.HIGH, 0.9),
            FailureSignal("boundary_error", "test", FailureSeverity.MEDIUM, 0.7),
            FailureSignal("type_error", "test", FailureSeverity.MEDIUM, 0.8)
        ]

        stats = analyzer.get_signal_statistics(signals)

        assert stats["total_signals"] == 3
        assert stats["severity_breakdown"]["high"] == 1
        assert stats["severity_breakdown"]["medium"] == 2
        assert stats["average_confidence"] > 0.7
        assert stats["high_confidence_signals"] >= 2
        assert len(stats["signal_types"]) == 3

    def test_get_signal_statistics_empty(self, analyzer):
        """Test signal statistics with empty list."""
        stats = analyzer.get_signal_statistics([])

        assert stats["total_signals"] == 0

    def test_signal_confidence_ranking(self, analyzer):
        """Test that signals are ranked by confidence."""
        # Create test error with multiple potential matches
        error_text = "AttributeError: 'NoneType' object has no attribute 'name' and some other text"
        signals = analyzer.extract_signals(error_text, "runtime")

        # Verify signals are sorted by confidence descending
        confidences = [s.confidence for s in signals]
        assert confidences == sorted(confidences, reverse=True)

    def test_pattern_specificity_scoring(self, analyzer):
        """Test that more specific patterns get higher confidence."""
        # Test specific error type vs generic pattern
        specific_error = "AttributeError: specific attribute error"
        generic_error = "some error occurred"

        specific_signals = analyzer.extract_signals(specific_error, "runtime")
        generic_signals = analyzer.extract_signals(generic_error, "runtime")

        # Specific patterns should generally have higher confidence
        if specific_signals and generic_signals:
            assert max(s.confidence for s in specific_signals) >= max(s.confidence for s in generic_signals)

    def test_source_location_tracking(self, analyzer):
        """Test that source location is properly tracked."""
        error_text = "AttributeError: test error"
        signals = analyzer.extract_signals(error_text, "pytest")

        for signal in signals:
            assert signal.source_location == "pytest"

    def test_signal_data_integrity(self, analyzer):
        """Test that all signal data is properly populated."""
        error_text = "AttributeError: 'NoneType' object has no attribute 'name'"
        signals = analyzer.extract_signals(error_text, "runtime")

        for signal in signals:
            assert isinstance(signal.signal_type, str)
            assert isinstance(signal.description, str)
            assert isinstance(signal.severity, FailureSeverity)
            assert isinstance(signal.confidence, (int, float))
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.suggested_fix is not None