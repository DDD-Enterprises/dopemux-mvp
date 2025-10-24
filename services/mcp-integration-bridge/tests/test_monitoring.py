"""
Tests for Prometheus Monitoring & Metrics
Validates metric recording and export
"""

import pytest
import time

try:
    from prometheus_client import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from monitoring import IntegrationBridgeMetrics


@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus client not installed")
class TestIntegrationBridgeMetrics:
    """Test IntegrationBridgeMetrics"""

    @pytest.fixture
    def metrics(self):
        """Create metrics instance with dedicated registry"""
        registry = CollectorRegistry()
        return IntegrationBridgeMetrics(registry=registry)

    def test_records_event_published(self, metrics):
        """Test event publishing metrics"""
        metrics.record_event_published("serena", "code.complexity.high", 0.003)

        # Export and verify
        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_event_publish_latency_seconds" in output
        assert "integration_bridge_events_published_total" in output
        assert 'source_agent="serena"' in output

    def test_records_dedup_check(self, metrics):
        """Test deduplication metrics"""
        metrics.record_dedup_check(is_duplicate=False)
        metrics.record_dedup_check(is_duplicate=True)
        metrics.record_dedup_check(is_duplicate=True)

        metrics.update_dedup_hit_rate(66.67)  # 2 of 3 were duplicates

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_dedup_checks_total" in output
        assert "integration_bridge_dedup_hits_total" in output
        assert "integration_bridge_dedup_hit_rate_percent" in output

    def test_records_aggregation(self, metrics):
        """Test aggregation metrics"""
        metrics.record_aggregation(events_in=100, events_out=20)

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_aggregation_events_in_total" in output
        assert "integration_bridge_aggregation_events_out_total" in output
        assert "integration_bridge_aggregation_reduction_percent" in output

    def test_records_pattern_insight(self, metrics):
        """Test pattern detection metrics"""
        metrics.record_pattern_insight("high_complexity_cluster", "high")
        metrics.record_pattern_insight("knowledge_gaps", "medium")

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_pattern_insights_total" in output
        assert 'pattern_name="high_complexity_cluster"' in output
        assert 'severity="high"' in output

    def test_records_pattern_detection_cycle(self, metrics):
        """Test pattern detection cycle metrics"""
        metrics.record_pattern_detection_cycle(latency_seconds=2.5)

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_pattern_detection_latency_seconds" in output
        assert "integration_bridge_pattern_detection_runs_total" in output

    def test_updates_circuit_breaker_state(self, metrics):
        """Test circuit breaker state metrics"""
        metrics.update_circuit_breaker_state("conport-mcp", "closed")
        metrics.update_circuit_breaker_state("adhd-engine", "open")

        metrics.record_circuit_breaker_failure("conport-mcp")
        metrics.record_circuit_breaker_fallback("conport-mcp")

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_circuit_breaker_state" in output
        assert 'breaker_name="conport-mcp"' in output
        assert "integration_bridge_circuit_breaker_failures_total" in output
        assert "integration_bridge_circuit_breaker_fallback_calls_total" in output

    def test_records_agent_events(self, metrics):
        """Test agent event metrics"""
        metrics.record_agent_event("serena", "code.complexity.high")
        metrics.record_agent_event("serena", "code.complexity.high")
        metrics.record_agent_event("zen", "decision.consensus.reached")

        metrics.record_agent_emission_error("dope-context")

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_agent_events_total" in output
        assert 'agent_name="serena"' in output
        assert 'event_type="code.complexity.high"' in output
        assert "integration_bridge_agent_emission_errors_total" in output

    def test_records_cache_access(self, metrics):
        """Test cache metrics"""
        metrics.record_cache_access("memory", hit=True)
        metrics.record_cache_access("memory", hit=False)
        metrics.record_cache_access("redis", hit=True)

        metrics.update_cache_hit_rate("memory", 50.0)
        metrics.update_cache_hit_rate("redis", 85.0)

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_cache_hits_total" in output
        assert "integration_bridge_cache_misses_total" in output
        assert "integration_bridge_cache_hit_rate_percent" in output
        assert 'tier="memory"' in output

    def test_updates_system_metrics(self, metrics):
        """Test system-level metrics"""
        metrics.update_active_agents(6)
        metrics.update_event_stream_length(1234)

        output = metrics.export_metrics().decode('utf-8')

        assert "integration_bridge_active_agents" in output
        assert "integration_bridge_event_stream_length" in output

    def test_export_metrics_format(self, metrics):
        """Test metrics export format"""
        metrics.record_event_published("test-agent", "test.event", 0.001)

        output = metrics.export_metrics()

        assert isinstance(output, bytes)
        assert len(output) > 0

        # Should be valid Prometheus format
        text = output.decode('utf-8')
        assert "# HELP" in text
        assert "# TYPE" in text

    def test_content_type_correct(self, metrics):
        """Test Prometheus content type"""
        content_type = metrics.get_content_type()

        # Should be Prometheus format
        assert "text/plain" in content_type or "openmetrics" in content_type


class TestMetricsWithoutPrometheus:
    """Test metrics when Prometheus not available"""

    def test_metrics_disabled_gracefully(self):
        """Test that metrics work even without Prometheus"""
        # This would create metrics with PROMETHEUS_AVAILABLE = False
        # Should not crash, just no-op

        # If Prometheus is installed, skip this test
        if PROMETHEUS_AVAILABLE:
            pytest.skip("Prometheus is available")

        metrics = IntegrationBridgeMetrics()

        assert metrics.enabled is False

        # Should not crash
        metrics.record_event_published("agent", "event", 0.001)
        metrics.record_dedup_check(True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
