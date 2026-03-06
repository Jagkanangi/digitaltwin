from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from utils.LoggerInit import init as initialize_logger
from services.UIService import UIService
from utils.SystemConfig import config

# Initialize logger and project files
initialize_logger()
ui_service = UIService()
ui_service.process_startup_files()

# Get a logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatTwin REST Service",
    description="The chat service layer of the Digital Twin project, handling RAG and LLM orchestration.",
    version="1.0.0",
    # Industry Standard: Disable docs in production via Env Var
    docs_url="/docs" if config.system.env_name == "dev" else None,
    redoc_url=None
)

# Add CORS middleware
origins = config.system.allowed_origins.split(",") if config.system.allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message

    try:
        return_str = ui_service.chatToTwin(message, session_id)
        return ChatResponse(response=return_str, session_id=session_id)
    except Exception as e:
        logger.error(f"Error during chat in session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during chat processing.")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)