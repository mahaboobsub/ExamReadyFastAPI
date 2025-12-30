# from pydantic_settings import BaseSettings
# import os

# class Settings(BaseSettings):
#     # --- API Security ---
#     X_INTERNAL_KEY: str
#     ENVIRONMENT: str = "development"

#     # --- Gemini API ---
#     GEMINI_API_KEY: str ="AIzaSyCeNFHsHaMBpUjOJ8SO8jEWaLpeWdMPaG8"
#     GEMINI_MODEL: str = "gemini-2.5-flash"
#     GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

#     # --- Redis ---
#     REDIS_URL: str ="rediss://default:AUcnAAIncDEzNGViNzZjM2VjMzQ0OTc0OGNhZmFiYmY3NDA3M2M1ZHAxMTgyMTU@faithful-treefrog-18215.upstash.io:6379"

#     # --- Database Paths ---
#     # CHROMA_PATH: str = "./data/chromadb"
#     # BM25_INDEX_PATH: str = "./data/bm25/index.pkl"
    
#     # NEW - Add these:
#     QDRANT_URL: str
#     QDRANT_API_KEY: str
#     QDRANT_COLLECTION_NAME: str = "cbse_textbooks"
#     TEXTBOOK_PATH: str = "./data/textbooks"
#     OUTPUT_PDF_PATH: str = "./data/pdfs"

#     # --- RAG Configuration ---
#     SEMANTIC_TOP_K: int = 50
#     BM25_TOP_K: int = 50
#     RERANK_TOP_K: int = 8
#     CACHE_TTL: int = 604800  # 7 days

#     # --- LLM Configuration ---
#     LLM_TEMPERATURE: float = 0.3
#     LLM_MAX_TOKENS: int = 800

#     class Config:
#         env_file = ".env"
#         extra = "ignore" # Ignore extra fields in .env if any

# settings = Settings()


from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # --- API Security ---
    X_INTERNAL_KEY: str = Field(..., env="X_INTERNAL_KEY")
    ENVIRONMENT: str = "development"

    # --- Gemini API (Required) ---
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

    # --- Redis ---
    REDIS_URL: str = Field(..., env="REDIS_URL")

    # --- Database Paths ---
    QDRANT_URL: str = Field(..., env="QDRANT_URL")
    QDRANT_API_KEY: str = Field(..., env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = "cbse_textbooks"
    
    TEXTBOOK_PATH: str = "./data/textbooks"
    OUTPUT_PDF_PATH: str = "./data/pdfs"

    # --- RAG Configuration ---
    SEMANTIC_TOP_K: int = 50
    BM25_TOP_K: int = 50
    RERANK_TOP_K: int = 8
    CACHE_TTL: int = 604800

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()