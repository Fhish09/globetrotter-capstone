"""
Observability helpers for GlobeTrotter microservices.

- Structured logging with request context
- Prometheus-style /metrics endpoint
- Request tracing via X-Request-ID propagation
"""
from __future__ import annotations

import logging
import time
import uuid
from functools import wraps
from typing import Callable, Optional

from flask import Flask, g, request, Response, jsonify

# ---------------------------------------------------------------------------
# In-memory metrics (Prometheus text format, no extra dependency required)
# ---------------------------------------------------------------------------

_counters: dict[str, float] = {}
_histograms: dict[str, list[float]] = {}


def _inc(name: str, labels: str = "", value: float = 1.0) -> None:
    key = f"{name}|{labels}"
    _counters[key] = _counters.get(key, 0.0) + value


def _observe(name: str, labels: str, value: float) -> None:
    key = f"{name}|{labels}"
    _histograms.setdefault(key, []).append(value)
    # Keep last 500 samples per series to bound memory
    if len(_histograms[key]) > 500:
        _histograms[key] = _histograms[key][-500:]


def render_metrics() -> str:
    lines = [
        "# HELP http_requests_total Total HTTP requests",
        "# TYPE http_requests_total counter",
    ]
    for key, val in sorted(_counters.items()):
        name, labels = key.split("|", 1)
        if labels:
            lines.append(f'{name}{{{labels}}} {val}')
        else:
            lines.append(f"{name} {val}")

    lines.append("# HELP http_request_duration_seconds Request latency")
    lines.append("# TYPE http_request_duration_seconds summary")
    for key, samples in sorted(_histograms.items()):
        name, labels = key.split("|", 1)
        if not samples:
            continue
        count = len(samples)
        total = sum(samples)
        label_str = f"{{{labels}}}" if labels else ""
        lines.append(f"{name}_count{label_str} {count}")
        lines.append(f"{name}_sum{label_str} {total:.6f}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s level=%(levelname)s service=%(name)s request_id=%(request_id)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(g, "request_id", "-") if has_request_context() else "-"
        return True


def has_request_context() -> bool:
    try:
        from flask import has_request_context as _hrc
        return _hrc()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Flask integration
# ---------------------------------------------------------------------------

def init_observability(app: Flask, service_name: str) -> logging.Logger:
    """Attach logging, request tracing, and /metrics to a Flask app."""
    logger = setup_logging(service_name)
    for h in logger.handlers:
        h.addFilter(RequestIdFilter())

    @app.before_request
    def _start_request():
        incoming = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        g.request_id = incoming or str(uuid.uuid4())
        g.start_time = time.perf_counter()
        logger.info(
            "method=%s path=%s", request.method, request.path,
        )

    @app.after_request
    def _end_request(response: Response):
        duration = time.perf_counter() - getattr(g, "start_time", time.perf_counter())
        status = response.status_code
        path = request.path
        method = request.method

        # Don't metric-spam the metrics endpoint itself heavily
        labels = f'service="{service_name}",method="{method}",status="{status}",path="{path}"'
        _inc("http_requests_total", labels)
        _observe("http_request_duration_seconds", labels, duration)

        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.1f",
            method, path, status, duration * 1000,
        )
        return response

    @app.get("/metrics")
    def metrics():
        return Response(render_metrics(), mimetype="text/plain; version=0.0.4")

    return logger


def trace_headers() -> dict:
    """Headers to forward on inter-service calls for distributed tracing."""
    rid = getattr(g, "request_id", None) if has_request_context() else None
    if rid:
        return {"X-Request-ID": rid}
    return {}
