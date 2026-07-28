"""
Shared HTTP client for inter-service communication.

Features:
- Configurable timeouts
- Retry with exponential backoff
- Optional circuit breaker integration
- Consistent error shape
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 0.4

# Optional circuit breakers keyed by service name
_breakers: dict = {}


class ServiceError(Exception):
    def __init__(self, service: str, message: str, status_code: int = 503):
        self.service = service
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")


def register_breaker(name: str, breaker) -> None:
    _breakers[name] = breaker


def get_breaker(name: str):
    return _breakers.get(name)


def call_service(
    service_name: str,
    method: str,
    url: str,
    *,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> Any:
    breaker = _breakers.get(service_name)

    def _do_request():
        last_error: Optional[str] = None

        for attempt in range(retries + 1):
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers or {},
                    json=json,
                    params=params,
                    timeout=timeout,
                )

                if resp.status_code >= 500:
                    last_error = f"upstream returned {resp.status_code}"
                    logger.warning("%s %s failed (attempt %s): %s", method, url, attempt + 1, last_error)
                    if attempt < retries:
                        time.sleep(backoff * (2 ** attempt))
                        continue
                    raise ServiceError(service_name, last_error, status_code=503)

                if resp.status_code >= 400:
                    try:
                        body = resp.json()
                        msg = body.get("error") or resp.reason
                    except Exception:
                        msg = resp.reason or "request failed"
                    raise ServiceError(service_name, msg, status_code=resp.status_code)

                if resp.status_code == 204 or not resp.content:
                    return None
                return resp.json()

            except ServiceError:
                raise
            except requests.Timeout:
                last_error = "request timed out"
            except requests.ConnectionError as exc:
                last_error = f"connection error: {exc}"
            except requests.RequestException as exc:
                last_error = str(exc)

            logger.warning("%s %s error (attempt %s): %s", method, url, attempt + 1, last_error)
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))

        raise ServiceError(service_name, last_error or "unavailable", status_code=503)

    if breaker is not None:
        try:
            from circuit_breaker import CircuitOpenError
        except ImportError:
            from services.shared.circuit_breaker import CircuitOpenError  # type: ignore

        try:
            return breaker.call(_do_request)
        except CircuitOpenError as exc:
            raise ServiceError(service_name, f"circuit open: {exc}", status_code=503) from exc

    return _do_request()
