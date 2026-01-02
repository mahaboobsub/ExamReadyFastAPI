from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # --- API Security ---
    X_INTERNAL_KEY: str = Field(..., env="X_INTERNAL_KEY")
    ENVIRONMENT: str = "development"

    # --- Gemini API (Required) ---
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    GEMINI_TIMEOUT_SECONDS: int = 60           # Gemini generation timeout

    # --- Redis ---
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_CACHE_TTL: int = 604800  # 7 days in seconds

    # --- Qdrant ---
    QDRANT_URL: str = Field(..., env="QDRANT_URL")
    QDRANT_API_KEY: str = Field(..., env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = "cbse_textbooks"      # For RAG context
    QDRANT_COLLECTION_QUESTIONS: str = "board_questions" # ✅ NEW: For validated Question Bank
    QDRANT_TIMEOUT_SECONDS: int = 30           # Qdrant query timeout
    
    # --- Paths ---
    TEXTBOOK_PATH: str = "./data/textbooks"
    OUTPUT_PDF_PATH: str = "./data/pdfs"
    PDF_OUTPUT_DIR: str = "data/pdfs"
    PDF_UPLOAD_TO_S3: bool = False  # ⚠️ Enable in Phase 2

    # --- RAG Configuration ---
    SEMANTIC_TOP_K: int = 50
    BM25_TOP_K: int = 50
    RERANK_TOP_K: int = 8
    CACHE_TTL: int = 604800  # 7 days

    # --- LLM Configuration ---
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 8192

    # --- ✅ NEW: v5.0 PRD Configurations ---
    ALLOW_LLM_RUNTIME: bool = False      # Security: Prevent LLM usage for student/board modes
    ENABLE_CACHING: bool = True          # Enable Redis for Custom modes
    
    # Quality Thresholds
    BOARD_QUALITY_THRESHOLD: float = 0.85
    CUSTOM_QUALITY_THRESHOLD: float = 0.70
    
    # Generation Settings
    OVER_FETCH_RATIO: float = 1.5        # Fetch 50% extra for deduplication
    QDRANT_FALLBACK_THRESHOLD: float = 0.5 # Use LLM if < 50% questions found
    
    # Monitoring
    TOTAL_REQUEST_TIMEOUT_SECONDS: int = 120   # FastAPI request timeout (2 min)
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()