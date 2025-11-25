# app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
import time
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional

# Import modules mới
from auth import verify_api_key
from rate_limiting import rate_limit_middleware, rate_limiter
from custom_logging import setup_logging, log_chat_interaction, log_api_request, log_error
from config import settings

# Thiết lập logging
setup_logging()
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

class RateLimitResponse(BaseModel):
    remaining: int
    limit: int
    reset_time: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Company Chatbot Backend API with Authentication")
    logger.info(f"📊 Rate limit: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} requests/minute")
    yield
    # Shutdown
    logger.info("🛑 Shutting down Company Chatbot Backend API")

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
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

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware để tính thời gian xử lý và log request"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log API request
    user_id = "unknown"
    try:
        # Cố gắng lấy user_id từ body nếu là POST request
        if request.method == "POST" and "chat" in request.url.path:
            body = await request.body()
            import json
            body_data = json.loads(body)
            user_id = body_data.get("user_id", "unknown")
    except:
        pass
    
    log_api_request(
        user_id=user_id,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        processing_time=process_time
    )
    
    # Thêm headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/")
async def root():
    return {
        "message": "Company Chatbot Backend API - Secure Version",
        "version": settings.API_VERSION,
        "features": ["Authentication", "Rate Limiting", "Enhanced Logging"],
        "endpoints": {
            "chat": "/api/v1/chat (POST)",
            "health": "/api/v1/health",
            "rate_limit": "/api/v1/rate-limit/{user_id}",
            "docs": "/docs"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Kiểm tra search API
        async with httpx.AsyncClient() as client:
            search_health = await client.get("http://localhost:8000/health", timeout=5)
        
        return {
            "status": "healthy",
            "service": "Chatbot Backend API",
            "version": settings.API_VERSION,
            "search_api": "healthy" if search_health.status_code == 200 else "unhealthy",
            "timestamp": time.time()
        }
    except Exception as e:
        log_error("system", "health_check_failed", str(e))
        return {
            "status": "degraded",
            "service": "Chatbot Backend API", 
            "error": "Search API unavailable",
            "timestamp": time.time()
        }

@app.get("/api/v1/rate-limit/{user_id}", response_model=RateLimitResponse)
async def get_rate_limit_info(user_id: str, api_key: str = Depends(verify_api_key)):
    """Lấy thông tin rate limit cho user"""
    remaining = rate_limiter.get_remaining_requests(user_id)
    
    return RateLimitResponse(
        remaining=remaining,
        limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        reset_time=60  # Reset sau 60 giây
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    api_key: str = Depends(verify_api_key),
    response: Response = None
):
    """
    Main chatbot endpoint với authentication và rate limiting
    """
    start_time = time.time()
    
    try:
        # Kiểm tra rate limiting
        await rate_limit_middleware(request.user_id)
        
        logger.info(f"📨 Chat request - User: {request.user_id}, Message: {request.message}")
        
        # Gọi search API
        search_result = await call_search_api(request.user_id, request.message)
        
        # Xử lý và format response
        chat_response = process_search_result(search_result)
        
        # Tính thời gian xử lý
        response_time = time.time() - start_time
        
        # Ghi log
        log_chat_interaction(
            user_id=request.user_id,
            message=request.message,
            response=chat_response.dict(),
            response_time=response_time
        )
        
        logger.info(f"✅ Chat response - User: {request.user_id}, Success: {chat_response.success}, Time: {response_time:.2f}s")
        
        # Thêm rate limit info vào header (sửa lỗi ở đây)
        if response:
            remaining = rate_limiter.get_remaining_requests(request.user_id)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
        
        return chat_response
        
    except HTTPException:
        # Re-raise HTTP exceptions (rate limit, auth errors)
        raise
    except httpx.RequestError as e:
        logger.error(f"🔌 Search API connection error: {e}")
        log_error(request.user_id, "search_api_error", str(e))
        raise HTTPException(
            status_code=503,
            detail="Search service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        log_error(request.user_id, "unexpected_error", str(e), {"message": request.message})
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

async def call_search_api(user_id: str, query: str):
    """Gọi search API hiện có"""
    async with httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT) as client:
        payload = {
            "user_id": user_id,
            "query": query,
            "top_k": 3
        }
        
        response = await client.post(
            settings.SEARCH_API_URL,
            json=payload
        )
        response.raise_for_status()
        return response.json()

def process_search_result(search_result: dict) -> ChatResponse:
    """Xử lý search result và format chatbot response"""
    
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
    
    # Lấy kết quả tốt nhất
    best_result = results[0]
    metadata = best_result.get("metadata", {})
    
    # Format response
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
    """Format chatbot response text"""
    title = metadata.get("title", "Tài liệu")
    content = result.get("content", "")
    category = metadata.get("category", "general")
    
    # Giới hạn độ dài content
    truncated_content = content[:250] + "..." if len(content) > 250 else content
    
    return f"""🤖 **Company Chatbot Response**

Dựa trên tài liệu công ty, tôi tìm thấy thông tin sau:

**📄 {title}**

{truncated_content}

*🏷️ Nguồn: {category}*"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )