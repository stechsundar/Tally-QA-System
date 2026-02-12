import os
import datetime
import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from qa_system import TallyQASystem


# --------------------------------------------------
# Load environment
# --------------------------------------------------

load_dotenv()

# --------------------------------------------------
# Global State
# --------------------------------------------------

qa_system = None
qa_ready = False
initialization_error = None

semaphore = asyncio.Semaphore(5)  # max concurrent requests


# --------------------------------------------------
# Lifespan Startup (Modern FastAPI)
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_system, qa_ready, initialization_error

    try:
        print("🚀 Initializing QA system...")

        qa_system = TallyQASystem()
        qa_system.load_vectorstore()
        qa_system.create_qa_chain()

        qa_ready = True
        print("✅ QA system ready.")

    except Exception as e:
        initialization_error = str(e)
        print("❌ QA initialization failed:", initialization_error)

    yield

    print("🛑 Shutting down...")


# --------------------------------------------------
# Create App FIRST
# --------------------------------------------------

app = FastAPI(
    title="Tally AI Backend API",
    version="3.0.0",
    lifespan=lifespan
)

# --------------------------------------------------
# Middleware
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Rate Limiter (AFTER app creation)
# --------------------------------------------------

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
    )


# --------------------------------------------------
# Models
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str


# --------------------------------------------------
# Caching Layer (Cost Reduction)
# --------------------------------------------------

@lru_cache(maxsize=1000)
def cached_ask(question: str):
    return qa_system.ask(question.lower().strip())


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Tally AI Backend API",
        "engine": "Tally Expert AI v3",
        "qa_ready": qa_ready,
        "time": datetime.datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "ask": "/ask (POST)",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    try:
        count = qa_system.vectorstore._collection.count()
        return {
            "status": "healthy",
            "vector_documents": count,
            "model": "claude-3-haiku-20240307"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }


@app.get("/status")
async def status():
    api_key = os.getenv("ANTHROPIC_API_KEY")

    return {
        "status": "ready" if qa_ready else "starting" if not initialization_error else "error",
        "qa_ready": qa_ready,
        "api_key_present": bool(api_key),
        "vector_db_exists": os.path.exists("./tally_chroma_db"),
        "docs_file_exists": os.path.exists("tally_docs.json"),
        "initialization_error": initialization_error
    }


@app.post("/ask")
@limiter.limit("10/minute")
async def ask_question(request: Request, req: QuestionRequest):
    async with semaphore:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(cached_ask, req.question),
                timeout=20
            )
            return result

        except asyncio.TimeoutError:
            return {
                "short_answer": "Request timed out.",
                "long_answer": "The system took too long to respond.",
                "sources": []
            }

        except Exception as e:
            print("🔥 INTERNAL ERROR:", str(e))
            return {
                "short_answer": "An internal system error occurred.",
                "long_answer": "Please try again later.",
                "sources": []
            }


# --------------------------------------------------
# Entry point (HF / Docker / Local)
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 7860))

    print(f"🚀 Starting server on 0.0.0.0:{port}")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
