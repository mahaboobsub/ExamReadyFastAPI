from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import redis
from app.config.settings import settings
from app.middleware.logging import PerformanceLogger

# Import Routers
from app.routers import exam
from app.routers import quiz 
from app.routers import flashcards, tutor

# Import Services
from app.services.qdrant_service import qdrant_service

# NOTE: We DO NOT configure genai here anymore. 
# GeminiService handles its own configuration and rotation internally.

app = FastAPI(
    title="ExamReady AI Service",
    version="1.0.0",
    description="AI Backend for Exam Generation, RAG, and Tutoring (Qdrant Cloud)"
)

# --- MIDDLEWARE ---

# 1. Logging (First to capture everything)
app.add_middleware(PerformanceLogger)

# 2. CORS (Allow requests from Node.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change to your Node.js server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. Security (Check X-Internal-Key)
@app.middleware("http")
async def verify_internal_key(request: Request, call_next):
    # Allow health checks and documentation without key
    public_paths = ["/", "/health", "/docs", "/openapi.json"]
    if request.url.path in public_paths:
        return await call_next(request)
    
    # Check for the secret key defined in .env
    client_key = request.headers.get("X-Internal-Key")
    if client_key != settings.X_INTERNAL_KEY:
        return JSONResponse(
            status_code=403, 
            content={"detail": "Forbidden: Invalid or missing X-Internal-Key"}
        )
        
    return await call_next(request)

# --- STARTUP EVENTS ---
@app.on_event("startup")
async def startup_event():
    """Verify Qdrant connection on startup"""
    try:
        # Check if collection exists
        qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
        print(f"✅ Connected to Qdrant Cloud: Collection '{settings.QDRANT_COLLECTION_NAME}' exists")
    except Exception as e:
        print(f"⚠️ Qdrant Warning: Collection '{settings.QDRANT_COLLECTION_NAME}' not found or connection failed.")
        print(f"   Error details: {e}")
        print("   Run 'python scripts/migrate_to_qdrant.py' to initialize data.")

# --- REGISTER ROUTERS ---
app.include_router(exam.router) 
app.include_router(quiz.router)
app.include_router(flashcards.router)
app.include_router(tutor.router)

# --- CORE ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "status": "active",
        "service": "ExamReady AI",
        "environment": settings.ENVIRONMENT,
        "system": "Qdrant Cloud + Gemini (Rotation Enabled)"
    }

@app.get("/health")
def health_check():
    """Verify connections to Critical Infrastructure"""
    health_status = {
        "status": "healthy",
        "services": {
            "redis": "unknown",
            "qdrant": "unknown"
            # Gemini is not checked here to avoid burning tokens/rate limits on frequent health pings
        }
    }

    # 1. Test Redis (Upstash)
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        if r.ping():
            health_status["services"]["redis"] = "connected"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # 2. Test Qdrant Cloud
    try:
        info = qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
        health_status["services"]["qdrant"] = {
            "status": "connected",
            "vectors_count": info.points_count,
            "status": str(info.status)
        }
    except Exception as e:
        health_status["services"]["qdrant"] = {"status": "error", "detail": str(e)}
        health_status["status"] = "degraded"

    return health_status