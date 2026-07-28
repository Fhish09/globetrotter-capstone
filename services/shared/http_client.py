"""
Shared HTTP client for inter-service communication.

Features:
- Configurable timeouts
- Simple retry with exponential backoff
- Consistent error shape for callers
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5          # seconds
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 0.4        # seconds


class ServiceError(Exception):
    """Raised when an upstream service call fails."""

    def __init__(self, service: str, message: str, status_code: int = 503):
        self.service = service
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")


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
    """Perform an HTTP call to another microservice.

    Retries on network errors and 5xx responses.
    Raises ServiceError on permanent failure.
    Returns parsed JSON on success.
    """
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
                logger.warning(
                    "%s %s failed (attempt %s): %s",
                    method, url, attempt + 1, last_error,
                )
                if attempt < retries:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise ServiceError(service_name, last_error, status_code=503)

            if resp.status_code >= 400:
                # Client errors (4xx) – don't retry
                try:
                    body = resp.json()
                    msg = body.get("error") or resp.reason
                except Exception:
                    msg = resp.reason or "request failed"
                raise ServiceError(service_name, msg, status_code=resp.status_code)

            if resp.status_code == 204 or not resp.content:
                return None

            return resp.json()

        except requests.Timeout:
            last_error = "request timed out"
            logger.warning("%s %s timeout (attempt %s)", method, url, attempt + 1)
        except requests.ConnectionError as exc:
            last_error = f"connection error: {exc}"
            logger.warning("%s %s connection error (attempt %s)", method, url, attempt + 1)
        except ServiceError:
            raise
        except requests.RequestException as exc:
            last_error = str(exc)
            logger.warning("%s %s error (attempt %s): %s", method, url, attempt + 1, exc)

        if attempt < retries:
            time.sleep(backoff * (2 ** attempt))

    raise ServiceError(service_name, last_error or "unavailable", status_code=503)
