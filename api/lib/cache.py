import os
import json
from datetime import datetime, timezone

# Cache TTL in seconds (1 hour)
CACHE_TTL = 3600

def get_redis():
    """Initialize Upstash Redis client"""
    try:
        from upstash_redis import Redis
        url = os.environ.get("UPSTASH_REDIS_REST_URL")
        token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        
        if not url or not token:
            return None
            
        return Redis(url=url, token=token)
    except Exception as e:
        print(f"Redis connection error: {e}")
        return None

def get_cached_data(key):
    """Retrieve data from Redis cache"""
    redis = get_redis()
    if not redis:
        return None
        
    try:
        cached = redis.get(key)
        if cached:
            if isinstance(cached, str):
                return json.loads(cached)
            return cached
    except Exception as e:
        print(f"Redis read error for {key}: {e}")
    return None

def set_cached_data(key, data, ex=CACHE_TTL):
    """Store data in Redis cache"""
    redis = get_redis()
    if not redis:
        return False
        
    try:
        redis.set(key, json.dumps(data), ex=ex)
        return True
    except Exception as e:
        print(f"Redis write error for {key}: {e}")
        return False
