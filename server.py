from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qa_system import TallyQASystem
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Tally AI API")

# Allow React app to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your netlify URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the logic
qa_system = TallyQASystem()
try:
    qa_system.load_vectorstore()
    qa_system.create_qa_chain(os.getenv("ANTHROPIC_API_KEY"))
except Exception as e:
    print(f"Warning: System initialization delayed: {e}")

class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    try:
        result = qa_system.ask(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    import json
    config_path = "subdomains.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

@app.get("/status")
async def status():
    return {"status": "ready", "engine": "Tally Expert AI v2"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
