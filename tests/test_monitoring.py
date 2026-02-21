import pytest
from datetime import datetime
from src.core.monitoring import MetricsCollector, MetricRecord

def test_metrics_collector_initialization():
    """Verify MetricsCollector initializes with an empty records list."""
    collector = MetricsCollector()
    assert collector.records == []

def test_record_api_call_basic():
    """Verify record_api_call correctly appends a MetricRecord."""
    collector = MetricsCollector()
    collector.record_api_call("test-service", "GET", "success")

    assert len(collector.records) == 1
    record = collector.records[0]
    assert isinstance(record, MetricRecord)
    assert record.service == "test-service"
    assert record.method == "GET"
    assert record.status == "success"
    assert isinstance(record.timestamp, datetime)
    assert record.duration is None
    assert record.metadata == {}

def test_record_api_call_with_optional_args():
    """Verify record_api_call handles optional duration and metadata."""
    collector = MetricsCollector()
    collector.record_api_call(
        "test-service",
        "POST",
        "error",
        duration=0.5,
        error_code=500,
        user_id="user123"
    )

    assert len(collector.records) == 1
    record = collector.records[0]
    assert record.duration == 0.5
    assert record.metadata == {"error_code": 500, "user_id": "user123"}

def test_get_metrics_no_filter():
    """Verify get_metrics returns all records when no filters are applied."""
    collector = MetricsCollector()
    collector.record_api_call("service1", "GET", "success")
    collector.record_api_call("service2", "POST", "success")

    metrics = collector.get_metrics()
    assert len(metrics) == 2
    assert metrics[0].service == "service1"
    assert metrics[1].service == "service2"

def test_get_metrics_filter_service():
    """Verify get_metrics correctly filters by service."""
    collector = MetricsCollector()
    collector.record_api_call("service1", "GET", "success")
    collector.record_api_call("service2", "POST", "success")
    collector.record_api_call("service1", "PUT", "success")

    metrics = collector.get_metrics(service="service1")
    assert len(metrics) == 2
    assert all(m.service == "service1" for m in metrics)

def test_get_metrics_filter_last_n():
    """Verify get_metrics correctly filters by last_n."""
    collector = MetricsCollector()
    for i in range(5):
        collector.record_api_call(f"service{i}", "GET", "success")

    metrics = collector.get_metrics(last_n=2)
    assert len(metrics) == 2
    assert metrics[0].service == "service3"
    assert metrics[1].service == "service4"

def test_get_metrics_combined_filter():
    """Verify get_metrics correctly filters by both service and last_n."""
    collector = MetricsCollector()
    collector.record_api_call("service1", "GET", "success") # 1
    collector.record_api_call("service2", "GET", "success")
    collector.record_api_call("service1", "POST", "success") # 2
    collector.record_api_call("service1", "PUT", "success") # 3

    metrics = collector.get_metrics(service="service1", last_n=2)
    assert len(metrics) == 2
    assert metrics[0].method == "POST"
    assert metrics[1].method == "PUT"

def test_clear_metrics():
    """Verify clear_metrics properly clears the records list."""
    collector = MetricsCollector()
    collector.record_api_call("service1", "GET", "success")
    assert len(collector.records) == 1

    collector.clear_metrics()
    assert len(collector.records) == 0

def test_get_summary_empty():
    """Verify get_summary handles empty records correctly."""
    collector = MetricsCollector()
    summary = collector.get_summary()
    assert summary == {"total_calls": 0}

def test_get_summary_mixed():
    """Verify get_summary provides accurate statistics for mixed statuses."""
    collector = MetricsCollector()
    # service1: 2 success, 1 error
    collector.record_api_call("service1", "GET", "success")
    collector.record_api_call("service1", "POST", "success")
    collector.record_api_call("service1", "PUT", "error")

    # service2: 1 success, 1 error
    collector.record_api_call("service2", "GET", "success")
    collector.record_api_call("service2", "DELETE", "error")

    summary = collector.get_summary()

    assert summary["total_calls"] == 5
    assert summary["success_calls"] == 3
    assert summary["error_calls"] == 2
    assert summary["success_rate"] == 0.6

    services = summary["services"]
    assert "service1" in services
    assert services["service1"]["total"] == 3
    assert services["service1"]["success"] == 2
    assert services["service1"]["error"] == 1

    assert "service2" in services
    assert services["service2"]["total"] == 2
    assert services["service2"]["success"] == 1
    assert services["service2"]["error"] == 1
