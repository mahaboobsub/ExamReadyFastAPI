import redis
import hashlib
import json
from typing import Optional, Dict
from app.config.settings import settings

class RedisService:
    """Redis caching for Custom Exams"""

    def __init__(self):
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5
            )
            self.ttl = settings.REDIS_CACHE_TTL
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            self.client = None

    # ✅ FIX: Method names with underscores
    def generate_cache_key(self, request: Dict) -> str:
        # Normalize to ensure deterministic key
        normalized = {
            "template_id": request.get("template_id"),
            "chapters": sorted(request.get("chapters", [])),
            "chapter_weightage": request.get("chapter_weightage", {}),
            "difficulty": request.get("difficulty", "Mixed")
        }
        key_str = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_cached_exam(self, cache_key: str) -> Optional[Dict]:
        if not self.client: return None
        try:
            data = self.client.get(f"exam:cache:{cache_key}")
            return json.loads(data) if data else None
        except:
            return None

    def cache_exam(self, cache_key: str, exam_data: Dict):
        if not self.client: return
        try:
            self.client.set(
                f"exam:cache:{cache_key}",
                json.dumps(exam_data),
                ex=self.ttl
            )
        except Exception as e:
            print(f"⚠️ Failed to cache exam: {e}")

redis_service = RedisService()