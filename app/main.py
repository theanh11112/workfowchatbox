# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "user001"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    source: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    total_results: int = 0

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: dict

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Company Chatbot Backend API")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Company Chatbot Backend API")

app = FastAPI(
    title="Company Chatbot Backend API",
    description="Backend service for company chatbot - Replaces n8n workflow",
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

# Configuration
SEARCH_API_URL = "http://localhost:8000/search"
SEARCH_TIMEOUT = 30

@app.get("/")
async def root():
    return {
        "message": "Company Chatbot Backend API - Replaces n8n",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/v1/chat (POST)",
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check với dependency verification"""
    health_info = {
        "status": "healthy",
        "service": "Company Chatbot Backend API",
        "version": "1.0.0",
        "dependencies": {}
    }
    
    # Check search API health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5)
            search_health = response.json()
            health_info["dependencies"]["search_api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response": search_health
            }
            
            if response.status_code != 200:
                health_info["status"] = "degraded"
                
    except Exception as e:
        health_info["dependencies"]["search_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_info["status"] = "degraded"
    
    return health_info

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chatbot endpoint - Replaces n8n workflow
    """
    try:
        logger.info(f"Chat request - User: {request.user_id}, Message: {request.message}")
        
        # Call existing search API
        search_result = await call_search_api(request.user_id, request.message)
        
        # Process and format response (replaces n8n code node)
        response = process_search_result(search_result)
        
        logger.info(f"Chat response - Success: {response.success}, Results: {response.total_results}")
        return response
        
    except httpx.RequestError as e:
        logger.error(f"Search API connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Search service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

async def call_search_api(user_id: str, query: str):
    """Call the existing search API (port 8000)"""
    async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
        payload = {
            "user_id": user_id,
            "query": query,
            "top_k": 3
        }
        
        response = await client.post(
            SEARCH_API_URL,
            json=payload
        )
        response.raise_for_status()
        return response.json()

def process_search_result(search_result: dict) -> ChatResponse:
    """Process search result and format chatbot response - Replaces n8n processing"""
    
    # Check for errors
    if "error" in search_result:
        return ChatResponse(
            success=False,
            response="Xin lỗi, tôi gặp sự cố khi tìm thông tin. Vui lòng thử lại sau.",
            total_results=0
        )
    
    results = search_result.get("results", [])
    total_found = search_result.get("total_found", 0)
    
    if not results:
        return ChatResponse(
            success=True,
            response="Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn trong tài liệu công ty.",
            total_results=0
        )
    
    # Get best result
    best_result = results[0]
    metadata = best_result.get("metadata", {})
    
    # Format response (replaces n8n formatting logic)
    response_text = format_chat_response(best_result, metadata)
    
    return ChatResponse(
        success=True,
        response=response_text,
        source=metadata.get("title"),
        category=metadata.get("category"),
        confidence=1 - best_result.get("similarity", 0),
        total_results=total_found
    )

def format_chat_response(result: dict, metadata: dict) -> str:
    """Format the chatbot response text - Replaces n8n template"""
    title = metadata.get("title", "Tài liệu")
    content = result.get("content", "")
    category = metadata.get("category", "general")
    
    # Truncate content for readability
    truncated_content = content[:250] + "..." if len(content) > 250 else content
    
    return f"""🤖 **Company Chatbot Response**

Dựa trên tài liệu công ty, tôi tìm thấy thông tin sau:

**📄 {title}**

{truncated_content}

*🏷️ Nguồn: {category}*"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )