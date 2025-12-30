import google.generativeai as genai
from app.config.settings import settings
from typing import List
import time
import asyncio
import random
import os
import logging

logger = logging.getLogger("examready")

class GeminiService:
    """
    Gemini API Integration with:
    - Automatic Key Rotation (Round-Robin)
    - Rate Limit Handling (429 / Quota)
    - Server Error Handling (500)
    """
    
    def __init__(self):
        # 1. Load all available keys from Environment
        self.api_keys = [
            settings.GEMINI_API_KEY,
            os.getenv("GEMINI_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3"),
            os.getenv("GEMINI_API_KEY_4")
        ]
        # Filter out invalid keys (None or empty strings)
        self.api_keys = [k for k in self.api_keys if k and len(k) > 10]
        
        if not self.api_keys:
            raise ValueError("❌ No valid GEMINI_API_KEY found in environment variables")

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
        Generate text (Async) with automatic key rotation and retry logic.
        """
        keys_tried = 0
        total_keys = len(self.api_keys)
        
        # Allow retrying across keys
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
                    
                    # Handle Rate Limit / Quota
                    if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                        if self._rotate_key():
                            keys_tried += 1
                            break # Break retry loop to try new key immediately
                        else:
                            # No backup keys, must wait
                            wait_time = (2 ** attempt) * 2 + random.uniform(1, 3)
                            print(f"   ⏳ Rate Limited. Waiting {wait_time:.1f}s...")
                            await asyncio.sleep(wait_time)
                    
                    # Handle Server Errors (500)
                    elif "500" in error_str or "internal" in error_str:
                         wait_time = (2 ** attempt) * 2
                         print(f"   ⚠️ Gemini Internal Error. Retrying in {wait_time}s...")
                         await asyncio.sleep(wait_time)
                    
                    else:
                        print(f"   ❌ Gemini Generation Error: {e}")
                        raise e
            
            # If retries exhausted for this key, try rotating
            if not self._rotate_key():
                 break
            keys_tried += 1

        raise Exception("Max retries exceeded on all available Gemini API keys")

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector (Sync) with robust error handling for 500s.
        """
        max_retries = 4  # Increased retries for stability
        
        for attempt in range(max_retries):
            try:
                # Clean text to avoid whitespace issues
                text = text.replace("\n", " ").strip()
                if not text:
                    return []

                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                return result['embedding']
            
            except Exception as e:
                error_str = str(e).lower()
                
                # 1. Handle 500 Internal Server Error (Common with Embeddings)
                if "500" in error_str or "internal error" in error_str:
                    wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                    # Only log if it keeps failing
                    if attempt > 0:
                        print(f"   ⚠️ Gemini 500 Error (Attempt {attempt+1}). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                
                # 2. Handle Rate Limits
                if "429" in error_str or "quota" in error_str:
                    if self._rotate_key():
                        continue # Try new key immediately
                    else:
                        time.sleep(2)
                        continue
                
                print(f"   ❌ Critical Embedding Error: {str(e)}")
                return []
        
        print("   ❌ Failed to generate embedding after max retries")
        return []

    def embed_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        Batch size reduced to 20 to prevent 500 errors.
        """
        embeddings = []
        total = len(texts)
        print(f"   Generating embeddings for {total} chunks...")
        
        for i in range(0, total, batch_size):
            batch = texts[i:i+batch_size]
            for text in batch:
                emb = self.embed(text)
                if emb:
                    embeddings.append(emb)
                else:
                    # Fallback for failed embedding to keep list alignment
                    embeddings.append([0.0] * 768) 
                
                # Tiny delay to prevent flooding the API
                time.sleep(0.1) 
            
            # Progress update
            print(f"   Processed {min(i+batch_size, total)}/{total}")
            
        return embeddings