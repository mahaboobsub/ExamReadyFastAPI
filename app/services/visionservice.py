import google.generativeai as genai
from app.config.settings import settings
import time
import random
import threading

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class VisionService:
    """Gemini Vision integration with Global Rate Limiting"""

    # Shared lock and timer across all instances
    _last_request_time = 0
    _lock = threading.Lock()
    
    # HARD LIMIT: 1 request every 15 seconds (4 RPM safety margin)
    MIN_INTERVAL = 15.0 

    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def _wait_for_rate_limit(self):
        """Block execution to enforce 5 RPM limit"""
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self._last_request_time
            
            if elapsed < self.MIN_INTERVAL:
                sleep_time = self.MIN_INTERVAL - elapsed
                print(f"   ⏳ Throttling: Sleeping {sleep_time:.1f}s to respect free tier...")
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()

    def _bytes_to_blob(self, image_bytes: bytes, mime_type: str = "image/png"):
        return {"mime_type": mime_type, "data": image_bytes}

    def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        max_retries = 2 # Reduced retries to fail fast
        
        for attempt in range(max_retries):
            try:
                # 1. Enforce global rate limit BEFORE request
                self._wait_for_rate_limit()
                
                # 2. Call API
                image_blob = self._bytes_to_blob(image_bytes)
                response = self.model.generate_content([prompt, image_blob])
                return response.text.strip()

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    # If we STILL hit a limit, wait a long time
                    print(f"   ⚠️ Rate Limit Hit! Cooling down for 60s...")
                    time.sleep(60)
                    continue 
                
                print(f"   ❌ Vision Error: {error_str}")
                return "" # Skip this image on error
        
        return ""

    def describe_diagram(self, image_bytes: bytes) -> str:
        prompt = "Analyze this diagram from a science textbook. Describe labels, components, and the concept shown in 2-3 sentences."
        return self.analyze_image(image_bytes, prompt)

    def extract_formula(self, image_bytes: bytes) -> str:
        prompt = "Convert this formula image to LaTeX. Return ONLY the LaTeX code."
        return self.analyze_image(image_bytes, prompt)