
"""Tests for Policy Shield privacy redaction system."""
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from chatx.redaction.policy_shield import (
    PolicyShield, PrivacyPolicy, RedactionReport
)
from chatx.privacy.differential_privacy import NoiseDistribution, PrivacyBudget, StatisticalQuery, DPResult
from chatx.redaction.patterns import PIIMatch


@pytest.fixture
def sample_policy():
    """Sample privacy policy for testing."""
    return PrivacyPolicy(
        threshold=0.995,
        strict_mode=False,
        block_hard_fail=True,
        pseudonymize=True,
        detect_names=True,
        opaque_tokens=True,
        enable_differential_privacy=True,
        dp_epsilon=1.0,
        dp_delta=1e-6
    )


@pytest.fixture
def policy_shield(sample_policy, tmp_path):
    """Policy Shield instance with test policy."""
    salt_file = tmp_path / "salt.txt"
    return PolicyShield(policy=sample_policy, salt_file=salt_file)


class TestPrivacyPolicy:
    """Test PrivacyPolicy configuration."""
    
    def test_default_initialization(self):
        """Test default policy initialization."""
        policy = PrivacyPolicy()
        assert policy.threshold == 0.995
        assert policy.strict_mode is False
        assert policy.block_hard_fail is True
        assert policy.pseudonymize is True
        assert policy.detect_names is True
        assert policy.enable_differential_privacy is True
        assert policy.dp_epsilon == 1.0
        assert policy.dp_delta == 1e-6
    
    def test_strict_mode_policy(self):
        """Test strict mode policy initialization."""
        policy = PrivacyPolicy(strict_mode=True)
        assert policy.get_effective_threshold() == 0.999
    
    def test_get_effective_threshold(self):
        """Test effective threshold calculation."""
        # Default mode
        policy = PrivacyPolicy()
        assert policy.get_effective_threshold() == 0.995
        
        # Strict mode
        policy.strict_mode = True
        assert policy.get_effective_threshold() == 0.999


class TestPolicyShield:
    """Test PolicyShield functionality."""
    
    def test_initialization_default(self):
        """Test Policy Shield initialization with defaults."""
        shield = PolicyShield()
        assert shield.policy.threshold == 0.995
        assert shield.dp_engine is not None
    
    def test_initialization_with_policy(self, sample_policy):
        """Test initialization with custom policy."""
        shield = PolicyShield(policy=sample_policy)
        assert shield.policy is sample_policy
        assert shield.dp_engine is not None
    
    def test_initialization_without_dp(self):
        """Test initialization without differential privacy."""
        policy = PrivacyPolicy(enable_differential_privacy=False)
        shield = PolicyShield(policy=policy)
        assert shield.dp_engine is None
    
    def test_initialization_with_existing_salt_file(self, tmp_path):
        """Test initialization with existing salt file."""
        salt_file = tmp_path / "existing_salt.txt"
        salt_file.write_text("test_salt_content")
        
        shield = PolicyShield(salt_file=salt_file)
        assert salt_file.exists()
        assert salt_file.read_text() == "test_salt_content"
    
    def test_redact_text_no_pii(self, policy_shield):
        """Test text redaction with no PII."""
        text = "Hello, this is a test message with no PII."
        result_text, matches, tokens = policy_shield._redact_text(text)
        
        assert result_text == text
        assert len(matches) == 0
        assert tokens == 0
    
    def test_calculate_coverage_with_pii(self, policy_shield):
        """Test coverage calculation with PII present."""
        pii_matches = [PIIMatch("John", "PERSON", 10, 14, 0.9)]
        coverage = policy_shield._calculate_coverage("Hello my name is John", pii_matches)
        assert coverage > 0.0
        assert coverage < 1.0
    
    def test_calculate_coverage_no_pii(self, policy_shield):
        """Test coverage calculation with no PII."""
        coverage = policy_shield._calculate_coverage("No PII here", [])
        assert coverage == 1.0
    
    def test_calculate_coverage_empty_text(self, policy_shield):
        """Test coverage calculation with empty text."""
        coverage = policy_shield._calculate_coverage("", [])
        assert coverage == 1.0
    
    def test_redact_chunk_text_success(self, policy_shield):
        """Test successful chunk text redaction."""
        text = "This is a test message"
        redacted, metadata = policy_shield.redact_chunk_text(text)
        
        assert isinstance(redacted, str)
        assert isinstance(metadata, dict)
        assert 'coverage' in metadata
        assert 'tokens_redacted' in metadata
        assert 'threshold_met' in metadata
        assert 'pii_types' in metadata
        assert 'hard_fail_classes' in metadata
    
    def test_redact_chunks_success(self, policy_shield):
        """Test chunk list redaction success."""
        chunks = [
            {'text': 'Hello John Doe', 'id': '1'},
            {'text': 'Contact me', 'id': '2'}
        ]
        
        redacted_chunks, report = policy_shield.redact_chunks(chunks)
        
        assert len(redacted_chunks) == 2
        assert isinstance(report, RedactionReport)
        assert report.messages_total == 2
        assert 'coverage' in report.__dict__
        assert report.tokens_redacted >= 0
    
    def test_redact_chunks_with_empty_chunks(self, policy_shield):
        """Test chunk redaction with empty text chunks."""
        chunks = [
            {'text': '', 'id': '1'},
            {'text': 'Valid text', 'id': '2'}
        ]
        
        redacted_chunks, report = policy_shield.redact_chunks(chunks)
        
        assert len(redacted_chunks) == 2
        assert report.messages_total == 2
    
    def test_save_redaction_report(self, policy_shield, tmp_path):
        """Test redaction report saving."""
        report_file = tmp_path / "test_report.json"
        
        report = RedactionReport(
            coverage=0.98,
            strict=False,
            hardfail_triggered=False,
            messages_total=10,
            tokens_redacted=25,
            placeholders={'PERSON': 3, 'EMAIL': 1},
            coarse_label_counts={},
            visibility_leaks=[],
            notes=[]
        )
        
        policy_shield.save_redaction_report(report, report_file)
        
        assert report_file.exists()
        
        # Verify JSON content
        with open(report_file) as f:
            saved_data = json.load(f)
        
        assert saved_data['coverage'] == 0.98
        assert saved_data['messages_total'] == 10
    
    def test_preflight_cloud_check_success(self, policy_shield):
        """Test successful cloud preflight check."""
        report = RedactionReport(
            coverage=0.999,
            strict=False,
            hardfail_triggered=False,
            messages_total=10,
            tokens_redacted=5,
            placeholders={},
            coarse_label_counts={},
            visibility_leaks=[],
            notes=[]
        )
        
        chunks = [{'text': 'redacted text', 'meta': {}}]
        
        passed, issues = policy_shield.preflight_cloud_check(chunks, report)
        assert passed is True
        assert len(issues) == 0
    
    def test_preflight_cloud_check_coverage_failure(self, policy_shield):
        """Test cloud preflight check with coverage failure."""
        report = RedactionReport(
            coverage=0.95,
            strict=False,
            hardfail_triggered=False,
            messages_total=10,
            tokens_redacted=5,
            placeholders={},
            coarse_label_counts={},
            visibility_leaks=[],
            notes=[]
        )
        
        chunks = [{'text': 'redacted text', 'meta': {}}]
        
        passed, issues = policy_shield.preflight_cloud_check(chunks, report)
        
        assert passed is False
        assert any('coverage' in issue.lower() for issue in issues)
    
    def test_preflight_cloud_check_hard_fail_failure(self, policy_shield):
        """Test cloud preflight check with hard-fail trigger."""
        report = RedactionReport(
            coverage=0.999,
            strict=False,
            hardfail_triggered=True,
            messages_total=10,
            tokens_redacted=5,
            placeholders={},
            coarse_label_counts={},
            visibility_leaks=[],
            notes=[]
        )
        
        chunks = [{'text': 'redacted text', 'meta': {}}]
        
        passed, issues = policy_shield.preflight_cloud_check(chunks, report)
        
        assert passed is False
        assert any('hard-fail' in issue.lower() for issue in issues)
    
    def test_preflight_cloud_check_leaks_failure(self, policy_shield):
        """Test cloud preflight check with visibility leaks."""
        report = RedactionReport(
            coverage=0.999,
            strict=False,
            hardfail_triggered=False,
            messages_total=10,
            tokens_redacted=5,
            placeholders={},
            coarse_label_counts={},
            visibility_leaks=['chunk_1'],
            notes=[]
        )
        
        chunks = [{'text': 'redacted text', 'meta': {}}]
        
        passed, issues = policy_shield.preflight_cloud_check(chunks, report)
        
        assert passed is False
        assert any('visibility' in issue.lower() for issue in issues)
    
    def test_preflight_cloud_check_fine_labels_failure(self, policy_shield):
        """Test cloud preflight check with fine-grained labels."""
        report = RedactionReport(
            coverage=0.999,
            strict=False,
            hardfail_triggered=False,
            messages_total=10,
            tokens_redacted=5,
            placeholders={},
            coarse_label_counts={},
            visibility_leaks=[],
            notes=[]
        )
        
        chunks = [{'text': 'redacted text', 'meta': {'labels_fine_local': ['PII']}}]
        
        passed, issues = policy_shield.preflight_cloud_check(chunks, report)
        
        assert passed is False
        assert any('fine-grained' in issue.lower() for issue in issues)
    
    def test_aggregate_statistics_with_dp(self, policy_shield):
        """Test DP statistical aggregation."""
        data = [
            {'value': 10, 'category': 'A'},
            {'value': 20, 'category': 'B'},
            {'value': 30, 'category': 'A'}
        ]
        
        queries = [
            StatisticalQuery(query_type="count", field_name="value"),
            StatisticalQuery(query_type="sum", field_name="value")
        ]
        
        results = policy_shield.aggregate_statistics_with_dp(data, queries)
        
        assert len(results) == 2
        for query_name, result in results.items():
            assert isinstance(result, DPResult)
            assert 'privacy_cost' in result.__dict__
    
    def test_aggregate_statistics_no_dp_enabled(self):
        """Test DP statistical aggregation when DP is disabled."""
        policy = PrivacyPolicy(enable_differential_privacy=False)
        shield = PolicyShield(policy=policy)
        
        data = [{'value': 10}]
        queries = [StatisticalQuery(query_type="count", field_name="value")]
        
        with pytest.raises(ValueError, match="Differential privacy is not enabled"):
            shield.aggregate_statistics_with_dp(data, queries)
    
    def test_generate_privacy_safe_summary_basic(self):
        """Test basic privacy-safe summary generation."""
        policy = PrivacyPolicy(enable_differential_privacy=False)
        shield = PolicyShield(policy=policy)
        
        chunks = [
            {'text': 'Test message 1', 'meta': {}},
            {'text': 'Test message 2', 'meta': {}}
        ]
        
        summary = shield.generate_privacy_safe_summary(chunks)
        
        assert summary['total_chunks'] == 2
        assert summary['privacy_method'] == 'none'
    
    def test_generate_privacy_safe_summary_with_dp(self, policy_shield):
        """Test privacy-safe summary with differential privacy."""
        chunks = [
            {'text': 'Test message 1', 'meta': {'labels_coarse': ['test']}},
            {'text': 'Test message 2', 'meta': {'labels_coarse': ['test']}}
        ]
        
        summary = policy_shield.generate_privacy_safe_summary(chunks, include_label_distribution=True)
        
        assert 'total_chunks' in summary
        assert summary['privacy_method'] == 'differential_privacy'
        assert 'privacy_parameters' in summary
    
    def test_generate_privacy_safe_summary_no_chunks(self, policy_shield):
        """Test privacy-safe summary with empty chunk list."""
        summary = policy_shield.generate_privacy_safe_summary([])
        
        assert summary['total_chunks'] == 0
        assert 'avg_chunk_length' in summary
    
    def test_get_tokenizer_stats(self, policy_shield):
        """Test tokenizer statistics retrieval."""
        stats = policy_shield.get_tokenizer_stats()
        assert isinstance(stats, dict)
    
    def test_get_differential_privacy_budget_summary(self, policy_shield):
        """Test DP budget summary retrieval."""
        summary = policy_shield.get_differential_privacy_budget_summary()
        assert isinstance(summary, dict)
    
    def test_redaction_report_serialization(self):
        """Test redaction report to_dict serialization."""
        report = RedactionReport(
            coverage=0.95,
            strict=False,
            hardfail_triggered=False,
            messages_total=5,
            tokens_redacted=10,
            placeholders={'PERSON': 2},
            coarse_label_counts={'emotion': 3},
            visibility_leaks=[],
            notes=['Test note']
        )
        
        data = report.to_dict()
        
        assert data['coverage'] == 0.95
        assert data['messages_total'] == 5
        assert data['placeholders'] == {'PERSON': 2}
        assert data['notes'] == ['Test note']


if __name__ == "__main__":
    pytest.main([__file__])
