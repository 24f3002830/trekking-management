"""
Redis Caching Helper for Trekking Management Application.
Handles cache storage, expiration, and automatic fallback if Redis is offline.
"""

import os
import json
import redis

# Redis connection URL (default to localhost:6379/0)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

_redis_client = None


def get_redis_client():
    """
    Get or create the Redis client connection.
    Returns None if Redis server is unreachable.
    """
    global _redis_client

    if _redis_client is None:
        try:
            client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            client.ping()
            _redis_client = client
            print("Connected to Redis cache.")
        except Exception:
            _redis_client = False
            print("Redis server not detected. Caching is bypassed (falling back to database).")

    if _redis_client is False:
        return None

    return _redis_client


def get_cache(key):
    """
    Retrieve cached data by key. Returns parsed Python dict/list, or None.
    """
    client = get_redis_client()
    if client is None:
        return None

    try:
        cached_string = client.get(key)
        if cached_string:
            return json.loads(cached_string)
    except Exception as error:
        print(f"Cache read error for key '{key}': {error}")

    return None


def set_cache(key, data, expire_seconds=300):
    """
    Store data in Redis as JSON with a time-to-live expiration (default: 5 minutes).
    """
    client = get_redis_client()
    if client is None:
        return False

    try:
        json_data = json.dumps(data)
        client.setex(key, expire_seconds, json_data)
        return True
    except Exception as error:
        print(f"Cache write error for key '{key}': {error}")
        return False


def clear_cache(pattern="treks:*"):
    """
    Clear all cache entries matching a pattern when data is updated.
    """
    client = get_redis_client()
    if client is None:
        return

    try:
        keys_to_delete = client.keys(pattern)
        if keys_to_delete:
            client.delete(*keys_to_delete)
    except Exception as error:
        print(f"Cache clear error: {error}")
