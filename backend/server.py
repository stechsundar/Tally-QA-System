import os
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Your QA system
from qa_system import TallyQASystem

load_dotenv()  # Load environment variables from .env file

api_key = os.getenv("ANTHROPIC_API_KEY")

# Global state
qa_system = None
qa_ready = False
initialization_error = None

# --------------------------------------------------
# App setup
# --------------------------------------------------

app = FastAPI(
    title="Tally AI Backend API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace with Netlify URL later
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Global state (lazy-loaded)
# --------------------------------------------------

qa_system: TallyQASystem | None = None
qa_ready: bool = False
qa_error: str | None = None

@app.on_event("startup")
async def startup_event():
    global qa_system, qa_ready, initialization_error

    try:
        print("🚀 Initializing QA system...")

        qa_system = TallyQASystem()
        qa_system.load_vectorstore()
        qa_system.create_qa_chain(api_key)

        qa_ready = True
        initialization_error = None

        print("✅ QA system READY")

    except Exception as e:
        qa_ready = False
        initialization_error = str(e)
        print("❌ QA system failed:", e)


# --------------------------------------------------
# Models
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def init_qa_system():
    """
    Initialize QA system lazily.
    This MUST NOT run at import time on HF.
    """
    global qa_system, qa_ready, qa_error

    if qa_ready:
        return

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        qa_error = "ANTHROPIC_API_KEY not set in Hugging Face Variables"
        raise RuntimeError(qa_error)

    try:
        qa_system = TallyQASystem()
        qa_system.load_vectorstore()
        qa_system.create_qa_chain(api_key)
        qa_ready = True
        print("✅ QA system initialized")
    except Exception as e:
        qa_error = str(e)
        print("❌ QA init failed:", qa_error)
        raise

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "Tally AI Backend API",
        "engine": "Tally Expert AI v2",
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
async def health():
    return {
        "ok": True,
        "qa_ready": qa_ready,
        "error": qa_error,
        "time": datetime.datetime.utcnow().isoformat()
    }

@app.get("/status")
async def status():
    api_key = os.getenv("ANTHROPIC_API_KEY")

    return {
        "status": "ready" if qa_ready else "starting" if not qa_error else "error",
        "engine": "Tally Expert AI v2",
        "qa_ready": qa_ready,
        "api_key_present": bool(api_key),
        "vector_db_exists": os.path.exists("./tally_chroma_db"),
        "docs_file_exists": os.path.exists("tally_docs.json"),
        "initialization_error": initialization_error
    }
    

@app.post("/ask")
async def ask_question(req: QuestionRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not qa_ready:
        try:
            init_qa_system()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"QA system not ready: {e}"
            )

    try:
        return qa_system.ask(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------------------------------
# Entry point (HF / Docker)
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
