"""
Redis Caching Helper for Trekking Management Application.
Implements cache expiration and fallback to database if Redis is offline.
"""

import os
import json
import redis

# Redis connection URL (default to localhost:6379)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

_redis_client = None


def get_redis_client():
    """
    Get or create Redis client instance.
    Returns None gracefully if Redis server is not reachable.
    """
    global _redis_client
    if _redis_client is None:
        try:
            client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            client.ping()
            _redis_client = client
            print(" Connected to Redis cache.")
        except Exception:
            _redis_client = False  # Mark as unavailable so we don't spam reconnects
            print(" Redis server not detected. Caching is bypassed (falling back to database).")

    return _redis_client if _redis_client is not False else None


def get_cache(key):
    """
    Retrieve cached data by key. Returns parsed JSON or None.
    """
    client = get_redis_client()
    if not client:
        return None
    try:
        cached = client.get(key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"⚠️ Cache read error for key '{key}': {e}")
    return None


def set_cache(key, data, expire_seconds=300):
    """
    Store serialized JSON in Redis with expiration time (default: 5 minutes / 300s).
    """
    client = get_redis_client()
    if not client:
        return False
    try:
        client.setex(key, expire_seconds, json.dumps(data))
        return True
    except Exception as e:
        print(f"⚠️ Cache write error for key '{key}': {e}")
        return False


def clear_cache(pattern="treks:*"):
    """
    Invalidate cache entries matching a pattern (e.g. after trek creation/update/booking).
    """
    client = get_redis_client()
    if not client:
        return
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception as e:
        print(f"⚠️ Cache clear error: {e}")
