"""Unit tests for api.metrics.get_system_metrics."""

from api.metrics import get_system_metrics


def test_contains_expected_keys():
    metrics = get_system_metrics()
    for key in ("cpu_percent", "memory_percent", "disk_percent"):
        assert key in metrics


def test_values_in_range():
    metrics = get_system_metrics()
    for key in ("cpu_percent", "memory_percent", "disk_percent"):
        assert 0 <= metrics[key] <= 100
