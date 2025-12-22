import redis
import json
import hashlib
from app.config.settings import settings
from typing import Any, Optional

# Global connection pool
# This is critical for high-concurrency performance
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

class CacheService:
    """Redis caching for RAG responses with Connection Pooling"""

    def __init__(self):
        # Use the global pool instead of creating a new connection every time
        self.redis_client = redis.Redis(connection_pool=redis_pool)

    def generate_cache_key(self, prefix: str, params: dict) -> str:
        """Generate deterministic cache key"""
        # Sort keys to ensure consistency
        key_str = json.dumps(params, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get_cached_response(self, key: str) -> Optional[dict]:
        """Retrieve from cache"""
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"⚠️ Cache Read Error: {e}")
            return None

    def set_cached_response(self, key: str, data: dict, ttl: int = 3600):
        """Save to cache with TTL"""
        try:
            self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            print(f"⚠️ Cache Write Error: {e}")
            
    def delete_pattern(self, pattern: str):
        """Clear cache by pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                print(f"🗑️ Cleared {len(keys)} keys matching '{pattern}'")
        except Exception as e:
            print(f"⚠️ Cache Delete Error: {e}")