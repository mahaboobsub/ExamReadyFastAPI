from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import chromadb
import redis
from app.config.settings import settings
from fastapi.middleware.gzip import GZipMiddleware

# Import Routers
from app.routers import exam
from app.routers import quiz 
from app.routers import flashcards, tutor
from app.middleware.logging import PerformanceLogger


# Configure Gemini once on startup
genai.configure(api_key=settings.GEMINI_API_KEY)

app = FastAPI(
    title="ExamReady AI Service",
    version="1.0.0",
    description="AI Backend for Exam Generation, RAG, and Tutoring"
)

# --- MIDDLEWARE ---

# 1. CORS (Allow requests from Node.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change to your Node.js server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# 2. Security (Check X-Internal-Key)
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

# --- REGISTER ROUTERS ---
app.add_middleware(PerformanceLogger)
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
        "system": "CPU-Optimized + Upstash"
    }

@app.get("/health")
def health_check():
    """Verify connections to Critical Infrastructure"""
    health_status = {
        "redis": "unknown",
        "gemini": "unknown",
        "chroma": "unknown"
    }

    # 1. Test Redis (Upstash)
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        if r.ping():
            health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"

    # 2. Test Gemini API
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        # Generate a tiny response to prove auth works
        response = model.generate_content("Say OK", generation_config={"max_output_tokens": 5})
        if response.text:
            health_status["gemini"] = "connected"
    except Exception as e:
        health_status["gemini"] = f"error: {str(e)}"

    # 3. Test ChromaDB (Local)
    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        client.heartbeat()
        health_status["chroma"] = "ready"
    except Exception as e:
        health_status["chroma"] = f"error: {str(e)}"

    return health_status