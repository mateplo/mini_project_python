"""System metrics helper."""

import psutil


def get_system_metrics() -> dict:
    """Return CPU, memory and disk usage. cpu_percent is non-blocking."""
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / 1e9, 2),
        "memory_total_gb": round(mem.total / 1e9, 2),
        "disk_percent": psutil.disk_usage("/").percent,
    }
