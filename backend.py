from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from agents.master_agent import MasterAgent
from models.schemas import AgentRequest, AgentResponse
from services.database import db
from services.mock_apis import router as mock_apis_router
import uuid
from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager

load_dotenv()

# Lifespan handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Tata Capital Loan Assistant API...")
    db.seed_initial_data()
    print("✅ Database seeded with initial data")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="Tata Capital Loan Assistant API", 
    description="Agentic AI System for Loan Processing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include mock APIs
app.include_router(mock_apis_router, prefix="/api/mock", tags=["Mock APIs"])

# Initialize agents
master_agent = MasterAgent()

@app.get("/")
async def root():
    return {
        "message": "Tata Capital Agentic AI Loan Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat (POST)",
            "download_pdf": "/api/download-pdf/{filename}",
            "health": "/api/health",
            "mock_apis": "/api/mock/"
        }
    }

@app.post("/api/chat", response_model=AgentResponse)
async def chat_endpoint(request: AgentRequest):
    """
    Main chat endpoint that routes through Master Agent
    """
    try:
        # Ensure session ID
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
        
        print(f"\n{'='*60}")
        print(f"📨 Incoming Request:")
        print(f"   Session: {request.session_id[:8]}...")
        print(f"   Message: {request.message}")
        print(f"   Context Keys: {list(request.context.keys()) if request.context else []}")
        if request.loan_intent:
            print(f"   Loan Intent: Amount={request.loan_intent.amount}, Tenure={request.loan_intent.tenure}")
        print(f"{'='*60}\n")
        
        # Process through master agent
        response = master_agent.process(request)
        
        print(f"\n{'='*60}")
        print(f"📤 Outgoing Response:")
        print(f"   Agent: {response.context.get('agent', 'unknown')}")
        print(f"   Next Agent: {response.next_agent}")
        print(f"   Message Length: {len(response.message)} chars")
        print(f"   Context Keys: {list(response.context.keys())}")
        print(f"   Has customer_id: {'customer_id' in response.context}")
        print(f"   Has verification_result: {'verification_result' in response.context}")
        print(f"{'='*60}\n")
        
        return response
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")

@app.get("/api/download-pdf/{filename}")
async def download_pdf(filename: str):
    """Download generated sanction letter PDF"""
    os.makedirs("sanction_letters", exist_ok=True)
    file_path = f"sanction_letters/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        file_path, 
        media_type='application/pdf', 
        filename=f"TataCapital_Sanction_{filename}"
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "loan_assistant_api",
        "version": "1.0.0",
        "gemini_configured": os.getenv("GEMINI_API_KEY") is not None,
        "mongodb_connected": db.client is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)