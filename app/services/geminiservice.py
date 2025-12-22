# import google.generativeai as genai
# from app.config.settings import settings
# from typing import List
# import time
# import asyncio
# import random

# # Configure on module load
# genai.configure(api_key=settings.GEMINI_API_KEY)

# class GeminiService:
#     """Gemini API for LLM generation and embeddings"""

#     def __init__(self):
#         self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
#         self.embedding_model = settings.GEMINI_EMBEDDING_MODEL

#     async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500, max_retries: int = 5) -> str:
#         """
#         Generate text with Async Retry Logic + Exponential Backoff
#         """
#         for attempt in range(max_retries):
#             try:
#                 response = await self.model.generate_content_async(
#                     prompt,
#                     generation_config=genai.types.GenerationConfig(
#                         temperature=temperature,
#                         max_output_tokens=max_tokens,
#                         top_p=0.95,
#                         top_k=40
#                     )
#                 )
#                 return response.text.strip()
#             except Exception as e:
#                 error_str = str(e).lower()
#                 if "429" in error_str or "quota" in error_str:
#                     # Exponential Backoff: 5s, 10s, 20s, 40s, 80s
#                     wait_time = (2 ** attempt) * 5 + random.uniform(1, 3)
#                     print(f"   ⏳ Rate limit hit. Retry {attempt+1}/{max_retries} in {wait_time:.1f}s...")
#                     await asyncio.sleep(wait_time)
#                 else:
#                     print(f"❌ Gemini generation error: {str(e)}")
#                     raise e
        
#         raise Exception("Max retries exceeded for Gemini API")

#     def embed(self, text: str) -> List[float]:
#         """Generate embedding vector (Sync is fine for search)"""
#         try:
#             text = text.replace("\n", " ").strip()
#             result = genai.embed_content(
#                 model=self.embedding_model,
#                 content=text,
#                 task_type="retrieval_document"
#             )
#             return result['embedding']
#         except Exception as e:
#             print(f"❌ Gemini embedding error: {str(e)}")
#             return []

#     def embed_batch(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
#         """Generate embeddings for multiple texts"""
#         embeddings = []
#         total = len(texts)
#         print(f"   Generating embeddings for {total} chunks...")
#         for i in range(0, total, batch_size):
#             batch = texts[i:i+batch_size]
#             for text in batch:
#                 embeddings.append(self.embed(text))
#                 time.sleep(1.0) # Slow down batch embeddings for safety
#             print(f"   Processed {min(i+batch_size, total)}/{total}")
#         return embeddings



import google.generativeai as genai
from app.config.settings import settings
from typing import List
import time
import asyncio
import random
import os

class GeminiService:
    """Gemini API with Automatic Key Rotation & Rate Limit Handling"""
    
    def __init__(self):
        # 1. Load all available keys from Environment/Settings
        self.api_keys = [
            settings.GEMINI_API_KEY,
            os.getenv("GEMINI_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3"),
            os.getenv("GEMINI_API_KEY_4")
        ]
        
        # Filter out None or empty strings
        self.api_keys = [k for k in self.api_keys if k and len(k) > 10]
        
        if not self.api_keys:
            raise ValueError("No valid GEMINI_API_KEY found in environment variables")

        print(f"   🔑 Loaded {len(self.api_keys)} Gemini API keys for rotation")
        
        self.current_key_index = 0
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        
        # Configure with the first key
        self._configure_current_key()
    
    def _configure_current_key(self):
        """Switch the active GenAI client to the current key"""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        # print(f"   🔄 Switched to Key #{self.current_key_index + 1}")
    
    def _rotate_key(self) -> bool:
        """
        Switch to next available key.
        Returns: True if rotated, False if only 1 key exists.
        """
        if len(self.api_keys) <= 1:
            return False  # Can't rotate if we only have one key
        
        # Move to next index (Round Robin)
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_current_key()
        print(f"   ♻️  Rate Limit Hit -> Rotating to Key #{self.current_key_index + 1}")
        return True
    
    async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500, max_retries: int = 3) -> str:
        """
        Generate text with automatic key rotation on 429/Quota errors.
        """
        # Track how many keys we've tried to avoid infinite loops
        keys_tried = 0
        total_keys = len(self.api_keys)
        
        # We allow retrying across ALL keys
        # If we have 3 keys, and max_retries is 3, we essentially have 9 attempts distributed
        
        while keys_tried <= total_keys:
            for attempt in range(max_retries):
                try:
                    response = await self.model.generate_content_async(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                            top_p=0.95,
                            top_k=40
                        )
                    )
                    return response.text.strip()
                
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Check for Rate Limit / Quota errors
                    if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                        
                        # Strategy: Try to rotate key immediately
                        if self._rotate_key():
                            keys_tried += 1
                            # Break the inner retry loop to try the new key immediately
                            break 
                        else:
                            # If we can't rotate (only 1 key), we MUST wait
                            wait_time = (2 ** attempt) * 5 + random.uniform(1, 3)
                            print(f"   ⏳ No backup keys. Waiting {wait_time:.1f}s...")
                            await asyncio.sleep(wait_time)
                    
                    else:
                        # Non-rate-limit error (e.g., Safety filter, Bad Request)
                        print(f"   ❌ Gemini Error: {e}")
                        raise e
            
            # If we exhausted retries for the current key and didn't break,
            # we try to rotate one last time before giving up
            if not self._rotate_key():
                 # If we can't rotate, we are done
                 break
            keys_tried += 1

        raise Exception("Max retries exceeded on all available API keys")

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector (Synchronous) with rotation
        """
        # Try current key, if fail, rotate once
        for _ in range(len(self.api_keys) + 1):
            try:
                text = text.replace("\n", " ").strip()
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str:
                    if self._rotate_key():
                        continue # Try new key
                    else:
                        # No other keys, wait briefly and retry once
                        time.sleep(2)
                        continue
                print(f"❌ Gemini embedding error: {str(e)}")
                return []
        return []

    def embed_batch(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        total = len(texts)
        print(f"   Generating embeddings for {total} chunks...")
        
        for i in range(0, total, batch_size):
            batch = texts[i:i+batch_size]
            for text in batch:
                embeddings.append(self.embed(text))
                # Slight delay is still good practice even with rotation
                time.sleep(0.2) 
            print(f"   Processed {min(i+batch_size, total)}/{total}")
            
        return embeddings