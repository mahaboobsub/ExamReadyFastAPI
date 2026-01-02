# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.gzip import GZipMiddleware
# from fastapi.staticfiles import StaticFiles  # ✅ NEW: For serving PDFs
# import redis
# import os  # ✅ NEW: For directory creation
# from app.config.settings import settings
# from app.middleware.logging import PerformanceLogger

# # Import Routers
# from app.routers import exam
# from app.routers import exam_v2  # ✅ NEW: Import v2 router
# from app.routers import quiz 
# from app.routers import flashcards, tutor

# # Import Services
# from app.services.qdrant_service import qdrant_service

# # NOTE: We DO NOT configure genai here anymore. 
# # GeminiService handles its own configuration and rotation internally.

# app = FastAPI(
#     title="ExamReady AI Service",
#     version="2.0.0", # Updated version
#     description="AI Backend for Exam Generation (v2), RAG, and Tutoring"
# )

# # --- MIDDLEWARE ---

# # 1. Logging (First to capture everything)
# app.add_middleware(PerformanceLogger)

# # 2. CORS (Allow requests from Node.js)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, change to your Node.js server URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 3. Compression
# app.add_middleware(GZipMiddleware, minimum_size=1000)

# # 4. Security (Check X-Internal-Key)
# @app.middleware("http")
# async def verify_internal_key(request: Request, call_next):
#     # Allow health checks, documentation, and static files without key
#     public_paths = ["/", "/health", "/docs", "/openapi.json"]
    
#     # Allow access to static PDFs (publicly accessible if URL is known)
#     # In strict mode, you might want to protect this too, but usually signed URLs are better.
#     if request.url.path in public_paths or request.url.path.startswith("/static"):
#         return await call_next(request)
    
#     # Check for the secret key defined in .env
#     client_key = request.headers.get("X-Internal-Key")
#     if client_key != settings.X_INTERNAL_KEY:
#         return JSONResponse(
#             status_code=403, 
#             content={"detail": "Forbidden: Invalid or missing X-Internal-Key"}
#         )
        
#     return await call_next(request)

# # --- STATIC FILES (PDF Serving) ---
# # Ensure the directory exists to prevent startup errors
# os.makedirs("data/pdfs", exist_ok=True)
# # Mount the directory to serve files at /static/pdfs
# app.mount("/static/pdfs", StaticFiles(directory="data/pdfs"), name="pdfs")


# # --- STARTUP EVENTS ---
# @app.on_event("startup")
# async def startup_event():
#     """Verify Qdrant connection on startup"""
#     try:
#         # Check if collection exists
#         qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
#         print(f"✅ Connected to Qdrant Cloud: Collection '{settings.QDRANT_COLLECTION_NAME}' exists")
#     except Exception as e:
#         print(f"⚠️ Qdrant Warning: Collection '{settings.QDRANT_COLLECTION_NAME}' not found or connection failed.")
#         print(f"   Error details: {e}")
#         print("   Run 'python scripts/migrate_to_qdrant.py' to initialize data.")

# # --- REGISTER ROUTERS ---
# app.include_router(exam.router) 
# app.include_router(exam_v2.router) # ✅ NEW: Register v2 endpoints
# app.include_router(quiz.router)
# app.include_router(flashcards.router)
# app.include_router(tutor.router)

# # --- CORE ENDPOINTS ---

# @app.get("/")
# def read_root():
#     return {
#         "status": "active",
#         "service": "ExamReady AI",
#         "environment": settings.ENVIRONMENT,
#         "system": "Qdrant Cloud + Gemini (Rotation Enabled)"
#     }

# @app.get("/health")
# def health_check():
#     """Verify connections to Critical Infrastructure"""
#     health_status = {
#         "status": "healthy",
#         "services": {
#             "redis": "unknown",
#             "qdrant": "unknown"
#             # Gemini is not checked here to avoid burning tokens/rate limits on frequent health pings
#         }
#     }

#     # 1. Test Redis (Upstash)
#     try:
#         r = redis.from_url(settings.REDIS_URL, decode_responses=True)
#         if r.ping():
#             health_status["services"]["redis"] = "connected"
#     except Exception as e:
#         health_status["services"]["redis"] = f"error: {str(e)}"
#         health_status["status"] = "degraded"

#     # 2. Test Qdrant Cloud
#     try:
#         info = qdrant_service.client.get_collection(settings.QDRANT_COLLECTION_NAME)
#         health_status["services"]["qdrant"] = {
#             "status": "connected",
#             "vectors_count": info.points_count,
#             "status": str(info.status)
#         }
#     except Exception as e:
#         health_status["services"]["qdrant"] = {"status": "error", "detail": str(e)}
#         health_status["status"] = "degraded"

#     return health_status

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