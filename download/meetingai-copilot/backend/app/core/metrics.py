"""
Application metrics collection for MeetingAI Copilot.

Tracks request counts, processing times, and business metrics.
Provides a thread-safe MetricsCollector with counters, gauges, and timers,
as well as a TimerContext context manager for timing code blocks.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional


@dataclass
class MetricPoint:
    """A single metric data point."""

    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe metrics collector for the application.

    Supports three metric types:
    - Counters: Monotonically increasing values (e.g., request counts).
    - Gauges: Point-in-time values that can go up or down (e.g., active connections).
    - Timers: Duration measurements with statistical summaries (avg, min, max, p95).
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._start_time = time.time()

    def increment(
        self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric.

        Args:
            name: The metric name.
            value: The amount to increment by (default 1.0).
            tags: Optional tags for dimensional metrics.
        """
        key = f"{name}:{tags}" if tags else name
        with self._lock:
            self._counters[key] += value

    def gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric to a specific value.

        Args:
            name: The metric name.
            value: The value to set.
            tags: Optional tags for dimensional metrics.
        """
        key = f"{name}:{tags}" if tags else name
        with self._lock:
            self._gauges[key] = value

    def timer(
        self, name: str, duration_seconds: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timing metric.

        Args:
            name: The metric name.
            duration_seconds: The measured duration in seconds.
            tags: Optional tags for dimensional metrics.
        """
        key = f"{name}:{tags}" if tags else name
        with self._lock:
            self._timers[key].append(duration_seconds)
            # Keep only last 1000 measurements to prevent unbounded memory growth
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]

    def get_metrics(self) -> dict:
        """Get all collected metrics as a dictionary.

        Returns:
            Dictionary containing uptime, counters, gauges, and timer summaries.
        """
        with self._lock:
            uptime = time.time() - self._start_time

            timers_summary: Dict[str, dict] = {}
            for key, values in self._timers.items():
                if values:
                    sorted_values = sorted(values)
                    timers_summary[key] = {
                        "count": len(values),
                        "avg": round(sum(values) / len(values), 6),
                        "min": round(min(values), 6),
                        "max": round(max(values), 6),
                        "p95": round(
                            sorted_values[int(len(sorted_values) * 0.95)]
                            if len(sorted_values) >= 20
                            else max(values),
                            6,
                        ),
                    }

            return {
                "uptime_seconds": round(uptime, 1),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timers": timers_summary,
            }

    def reset(self) -> None:
        """Reset all metrics. Useful for testing."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()


# Global metrics collector instance
metrics = MetricsCollector()


class TimerContext:
    """Context manager for timing code blocks.

    Usage::

        with TimerContext("api.request", tags={"endpoint": "/auth/login"}):
            # ... code to time ...
            pass

    The duration is automatically recorded in the global metrics collector
    when the context exits.
    """

    def __init__(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> None:
        self.name = name
        self.tags = tags
        self.start: Optional[float] = None

    def __enter__(self) -> "TimerContext":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        if self.start is not None:
            duration = time.perf_counter() - self.start
            metrics.timer(self.name, duration, self.tags)
