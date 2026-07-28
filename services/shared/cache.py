"""
Redis cache helper with graceful degradation.

If Redis is unavailable, operations no-op so the app keeps working.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis = None
_tried = False


def _client():
    global _redis, _tried
    if _tried:
        return _redis
    _tried = True
    url = os.environ.get("REDIS_URL", "")
    if not url:
        logger.info("REDIS_URL not set – caching disabled")
        return None
    try:
        import redis
        client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis = client
        logger.info("Connected to Redis at %s", url)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) – caching disabled", exc)
        _redis = None
    return _redis


def cache_get(key: str) -> Optional[Any]:
    client = _client()
    if not client:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get failed: %s", exc)
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    client = _client()
    if not client:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value))
    except Exception as exc:
        logger.warning("cache_set failed: %s", exc)


def cache_delete(key: str) -> None:
    client = _client()
    if not client:
        return
    try:
        client.delete(key)
    except Exception as exc:
        logger.warning("cache_delete failed: %s", exc)
