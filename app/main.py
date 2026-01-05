from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import redis
import os
from app.config.settings import settings
from app.middleware.logging import PerformanceLogger

# Import Routers
from app.routers import exam
from app.routers import exam_v2  # ✅ V2 Router
from app.routers import quiz 
from app.routers import flashcards, tutor

# Import Services
from app.services.qdrant_service import qdrant_service

app = FastAPI(
    title="ExamReady AI Service",
    version="2.0.0",
    description="AI Backend for Exam Generation (v2), RAG, and Tutoring"
)

# --- MIDDLEWARE ---
app.add_middleware(PerformanceLogger)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# --- SECURITY ---
@app.middleware("http")
async def verify_internal_key(request: Request, call_next):
    public_paths = ["/", "/health", "/docs", "/openapi.json"]
    
    # Allow access to static PDFs
    if request.url.path in public_paths or request.url.path.startswith("/static"):
        return await call_next(request)
    
    client_key = request.headers.get("X-Internal-Key")
    if client_key != settings.X_INTERNAL_KEY:
        return JSONResponse(
            status_code=403, 
            content={"detail": "Forbidden: Invalid or missing X-Internal-Key"}
        )
        
    return await call_next(request)

# --- STATIC FILES ---
os.makedirs("data/pdfs", exist_ok=True)
app.mount("/static/pdfs", StaticFiles(directory="data/pdfs"), name="pdfs")

# --- STARTUP EVENTS ---
@app.on_event("startup")
async def startup_event():
    """Verify Qdrant connection and initialize async client"""
    try:
        # Initialize Async Client
        await qdrant_service.initialize()
        
        # Check Collections
        textbook_exists = await qdrant_service.client.collection_exists(
            settings.QDRANT_COLLECTION_NAME
        )
        questions_exists = await qdrant_service.client.collection_exists(
            settings.QDRANT_COLLECTION_QUESTIONS
        )
        
        status_msg = "✅ Connected to Qdrant Cloud."
        if not textbook_exists:
            status_msg += f" ⚠️ Missing Textbooks ({settings.QDRANT_COLLECTION_NAME})."
        if not questions_exists:
            status_msg += f" ⚠️ Missing Questions ({settings.QDRANT_COLLECTION_QUESTIONS})."
            
        print(status_msg)
        
    except Exception as e:
        print(f"❌ Qdrant Startup Error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup async connections"""
    await qdrant_service.close()
    print("🔌 Async connections closed")

# --- REGISTER ROUTERS ---
app.include_router(exam.router) 
app.include_router(exam_v2.router)
app.include_router(quiz.router)
app.include_router(flashcards.router)
app.include_router(tutor.router)

# --- HEALTH CHECK ---
@app.get("/health")
async def health_check():
    """Enhanced health check: Redis + Qdrant Collections"""
    health = {
        "status": "healthy",
        "services": {
            "redis": "unknown",
            "qdrant": "unknown",
            "collections": {}
        }
    }

    # 1. Test Redis (Upstash)
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        if r.ping():
            health["services"]["redis"] = "connected"
    except Exception as e:
        health["services"]["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # 2. Test Qdrant Cloud & Collections
    try:
        if qdrant_service.client:
            # Check Collections
            textbooks = await qdrant_service.client.collection_exists(settings.QDRANT_COLLECTION_NAME)
            questions = await qdrant_service.client.collection_exists(settings.QDRANT_COLLECTION_QUESTIONS)
            
            health["services"]["qdrant"] = "connected"
            health["services"]["collections"] = {
                "textbooks": "ready" if textbooks else "missing",
                "questions": "ready" if questions else "missing"
            }
            
            if not (textbooks and questions):
                health["status"] = "degraded"
        else:
             health["services"]["qdrant"] = "disconnected (client None)"
             health["status"] = "degraded"

    except Exception as e:
        health["services"]["qdrant"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health

@app.get("/")
def read_root():
    return {
        "status": "active",
        "service": "ExamReady AI",
        "version": "v2.0",
        "system": "Qdrant Cloud + Gemini"
    }