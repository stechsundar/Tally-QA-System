from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qa_system import TallyQASystem
import os
from dotenv import load_dotenv
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Tally AI API")

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Initialize variables
qa_system = None
qa_ready = False
initialization_error = None

# Check for required environment variables
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    logger.warning("⚠️ ANTHROPIC_API_KEY not found in environment variables")
else:
    logger.info("✅ ANTHROPIC_API_KEY found")

# ========================================
# THIS IS WHERE THE STARTUP EVENT GOES!
# Place it AFTER app = FastAPI() and BEFORE route definitions
# ========================================
@app.on_event("startup")
async def startup_event():
    """Initialize QA system when the server starts"""
    global qa_system, qa_ready, initialization_error
    
    logger.info("🚀 Starting Tally AI Backend...")
    
    try:
        logger.info("Initializing QA System...")
        qa_system = TallyQASystem()
        
        logger.info("Loading vector store...")
        qa_system.load_vectorstore()
        
        logger.info("Creating QA chain...")
        qa_system.create_qa_chain(api_key)
        
        qa_ready = True
        logger.info("✅ QA System initialized successfully")
    except Exception as e:
        initialization_error = str(e)
        logger.error(f"❌ QA System initialization failed: {e}")
        logger.exception("Full error traceback:")

# ========================================
# REQUEST/RESPONSE MODELS
# ========================================
class QuestionRequest(BaseModel):
    question: str

# ========================================
# API ENDPOINTS
# ========================================
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question to the Tally AI system"""
    logger.info(f"📝 Received question: {request.question[:100]}...")
    
    if not qa_ready or qa_system is None:
        error_msg = f"QA system not initialized. Error: {initialization_error}" if initialization_error else "QA system not initialized"
        logger.error(error_msg)
        raise HTTPException(
            status_code=503, 
            detail=error_msg
        )
    
    try:
        result = qa_system.ask(request.question)
        logger.info("✅ Question answered successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Error processing question: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    """Get subdomain configuration"""
    import json
    config_path = "subdomains.json"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading config: {e}")
            return {"error": str(e)}
    
    logger.warning("Config file not found")
    return {"error": "Config file not found"}

@app.get("/health")
async def health_check():
    """Detailed health check for debugging deployment issues"""
    health_status = {
        "status": "healthy" if qa_ready else "unhealthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {
            "qa_system": qa_ready,
            "api_key_configured": bool(api_key),
            "vector_db_exists": os.path.exists("./tally_chroma_db"),
            "docs_file_exists": os.path.exists("tally_docs.json"),
            "config_file_exists": os.path.exists("subdomains.json")
        },
        "environment": {
            "port": os.environ.get("PORT", "7860"),
            "host": os.environ.get("HOST", "0.0.0.0"),
            "space_id": os.environ.get("SPACE_ID", "N/A")
        }
    }
    
    if initialization_error:
        health_status["initialization_error"] = initialization_error
    
    if not qa_ready:
        health_status["error"] = "QA system not initialized"
    
    return health_status

@app.get("/status")
async def status():
    """Quick status check"""
    return {
        "status": "ready" if qa_ready else "starting",
        "engine": "Tally Expert AI v2",
        "qa_system_ready": qa_ready,
        "api_key_configured": bool(api_key),
        "environment": "production" if os.environ.get("PORT") else "development",
        "initialization_error": initialization_error if not qa_ready else None
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Tally AI Backend API",
        "status": "running",
        "engine": "Tally Expert AI v2",
        "qa_system_ready": qa_ready,
        "endpoints": {
            "root": "/",
            "status": "/status",
            "health": "/health",
            "config": "/config",
            "ask": "/ask (POST)",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "note": "Visit /docs for interactive API documentation"
    }

# ========================================
# SERVER STARTUP
# ========================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )