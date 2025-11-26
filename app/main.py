# app/main.py - COMPLETE VERSION WITH USER_INFO SUPPORT - FIXED
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
import time
import asyncio
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import modules
from auth import verify_api_key
from rate_limiting import rate_limit_middleware, rate_limiter
from custom_logging import setup_logging, log_chat_interaction, log_api_request, log_error
from config import settings

# Thiết lập logging
setup_logging()
logger = logging.getLogger(__name__)

# Models - UPDATED: THÊM USER_INFO
class ChatRequest(BaseModel):
    message: str
    user_id: str = "user001"
    user_info: Optional[Dict[str, Any]] = None  # 🆕 THÊM USER_INFO
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*", "X-API-Key"],
)

# Biến toàn cục để theo dõi request
request_counter = 0

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware để tính thời gian xử lý và log request"""
    global request_counter
    start_time = time.time()
    request_id = request_counter
    request_counter += 1
    
    logger.debug(f"🔸 Request #{request_id}: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"❌ Request #{request_id} error: {e}")
        response = JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    
    process_time = time.time() - start_time
    
    user_id = "unknown"
    if request.method == "POST" and "chat" in request.url.path:
        user_id = "chat_user"
    
    log_api_request(
        user_id=user_id,
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        processing_time=process_time
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = str(request_id)
    
    logger.debug(f"🔹 Request #{request_id} completed in {process_time:.3f}s")
    
    return response

@app.get("/")
async def root():
    return {
        "message": "Company Chatbot Backend API - With User Info Support",
        "version": settings.API_VERSION,
        "features": ["Authentication", "Rate Limiting", "User Info Support"],
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
        timeout = httpx.Timeout(3.0, connect=1.0)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                search_health = await client.get("http://localhost:8000/health")
                search_status = "healthy" if search_health.status_code == 200 else "unhealthy"
            except (httpx.TimeoutException, httpx.ConnectError):
                search_status = "unreachable"
            except Exception as e:
                search_status = f"error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "service": "Chatbot Backend API",
            "version": settings.API_VERSION,
            "search_api": search_status,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "service": "Chatbot Backend API", 
            "error": "Health check failed",
            "timestamp": time.time()
        }

@app.get("/api/v1/rate-limit/{user_id}", response_model=RateLimitResponse)
async def get_rate_limit_info(user_id: str, api_key: str = Depends(verify_api_key)):
    """Lấy thông tin rate limit cho user"""
    remaining = rate_limiter.get_remaining_requests(user_id)
    
    return RateLimitResponse(
        remaining=remaining,
        limit=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        reset_time=60
    )

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    api_key: str = Depends(verify_api_key)
):
    """
    Main chatbot endpoint - FIXED: DÙNG USER_ID TỪ USER_INFO
    """
    start_time = time.time()
    
    try:
        # 🆕 SỬA QUAN TRỌNG: DÙNG USER_ID TỪ USER_INFO NẾU CÓ
        effective_user_id = request.user_id  # Mặc định
        
        if request.user_info and 'user_id' in request.user_info:
            effective_user_id = request.user_info['user_id']
            logger.info(f"🆔 Using user_id from user_info: {effective_user_id}")
        else:
            logger.info(f"🆔 Using user_id from request: {effective_user_id}")
        
        # Kiểm tra rate limiting với user_id thực tế
        await rate_limit_middleware(effective_user_id)
        
        logger.info(f"📨 Chat from {effective_user_id} - '{request.message[:50]}...'")
        
        # 🆕 LOG USER_INFO NẾU CÓ
        if request.user_info:
            logger.info(f"👤 User info: {request.user_info}")
            logger.info(f"🎯 User role from info: {request.user_info.get('role')}")
        else:
            logger.info(f"👤 No user_info provided")
        
        # Gọi search API với user_info và user_id ĐÚNG
        try:
            search_result = await asyncio.wait_for(
                call_search_api_with_user_info(effective_user_id, request.message, request.user_info),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning("⏰ Request timeout after 15s")
            return ChatResponse(
                success=False,
                response="Xin lỗi, yêu cầu đang mất nhiều thời gian xử lý. Vui lòng thử lại sau.",
                total_results=0
            )
        
        # Xử lý kết quả
        chat_response = process_search_result_safe(search_result)
        
        # Tính thời gian xử lý
        response_time = time.time() - start_time
        
        # Ghi log với user_id thực tế
        log_chat_interaction(
            user_id=effective_user_id,
            message=request.message,
            response=chat_response.dict(),
            response_time=response_time
        )
        
        logger.info(f"✅ Response sent in {response_time:.2f}s - Results: {chat_response.total_results}")
        
        return chat_response
        
    except HTTPException as he:
        logger.warning(f"🔐 HTTPException {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        log_error(effective_user_id, "unexpected_error", str(e), {"message": request.message})
        
        return ChatResponse(
            success=False,
            response="Xin lỗi, có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau.",
            total_results=0
        )

async def call_search_api_with_user_info(user_id: str, query: str, user_info: dict = None):
    """Gọi search API với user_info - THÊM LOG CHI TIẾT"""
    timeout = httpx.Timeout(10.0, connect=3.0)
    
    try:
        # 🆕 TẠO PAYLOAD VỚI USER_INFO VÀ USER_ID ĐÚNG
        payload = {
            "user_id": user_id,  # ✅ DÙNG USER_ID THỰC TẾ
            "query": query,
            "top_k": 3
        }
        
        # 🆕 THÊM USER_INFO VÀO PAYLOAD NẾU CÓ
        if user_info:
            payload["user_info"] = user_info
            logger.info(f"🔍 [CHATBOT_API] Sending to Search API - user_id: {user_id}, role: {user_info.get('role')}")
        else:
            logger.info(f"🔍 [CHATBOT_API] Sending to Search API - user_id: {user_id} (no user_info)")
        
        logger.debug(f"🔍 [CHATBOT_API] Full payload: {payload}")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "http://localhost:8000/search",
                json=payload
            )
            
            logger.info(f"✅ [CHATBOT_API] Search API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # 🆕 LOG CHI TIẾT RESPONSE TỪ SEARCH API
                user_info_from_search = data.get('user_info', {})
                user_role_from_search = user_info_from_search.get('role', 'unknown')
                logger.info(f"🎯 [CHATBOT_API] Search completed - User role from Search API: {user_role_from_search}")
                
                # 🆕 KIỂM TRA ROLE CÓ ĐÚNG KHÔNG
                expected_role = user_info.get('role') if user_info else 'unknown'
                if user_role_from_search != expected_role:
                    logger.warning(f"⚠️ [CHATBOT_API] Role mismatch! Expected: {expected_role}, Got: {user_role_from_search}")
                
                return data
            else:
                logger.warning(f"⚠️ [CHATBOT_API] Search API returned {response.status_code}")
                logger.warning(f"⚠️ [CHATBOT_API] Response text: {response.text}")
                return {"error": f"HTTP {response.status_code}", "results": []}
                
    except httpx.TimeoutException:
        logger.warning("⏰ [CHATBOT_API] Search API timeout")
        return {"error": "Search API timeout", "results": []}
    except httpx.ConnectError:
        logger.warning("🔌 [CHATBOT_API] Search API connection error")
        return {"error": "Search API connection failed", "results": []}
    except Exception as e:
        logger.error(f"💥 [CHATBOT_API] Search API error: {e}")
        return {"error": f"Search API error: {str(e)}", "results": []}

def process_search_result_safe(search_result: dict) -> ChatResponse:
    """Xử lý search result - SAFE & RELIABLE"""
    
    if "error" in search_result:
        error_msg = search_result["error"]
        logger.warning(f"⚠️ Search API error: {error_msg}")
        
        friendly_msg = "tạm thời không khả dụng"
        if "timeout" in error_msg.lower():
            friendly_msg = "phản hồi chậm"
        elif "connection" in error_msg.lower():
            friendly_msg = "mất kết nối"
            
        return ChatResponse(
            success=False,
            response=f"Xin lỗi, hệ thống tìm kiếm {friendly_msg}. Vui lòng thử lại sau.",
            total_results=0
        )
    
    results = search_result.get("results", [])
    total_found = search_result.get("total_found", 0)
    
    if not results or total_found == 0:
        return ChatResponse(
            success=True,
            response="Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn trong tài liệu công ty.",
            total_results=0
        )
    
    # Lấy kết quả tốt nhất
    best_result = results[0]
    metadata = best_result.get("metadata", {})
    
    try:
        response_text = format_chat_response_simple(best_result, metadata, total_found)
    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        response_text = f"Đã tìm thấy {total_found} kết quả phù hợp với câu hỏi của bạn."
    
    try:
        similarity = best_result.get("similarity", 0)
        confidence = max(0.0, min(1.0, float(1 - similarity))) if similarity else 0.8
    except:
        confidence = 0.8
    
    return ChatResponse(
        success=True,
        response=response_text,
        source=metadata.get("title"),
        category=metadata.get("category"),
        confidence=confidence,
        total_results=total_found
    )

def format_chat_response_simple(result: dict, metadata: dict, total_found: int) -> str:
    """Format chatbot response text - SIMPLE & SAFE"""
    title = metadata.get("title", "Tài liệu") or "Tài liệu"
    content = result.get("content", "") or ""
    category = metadata.get("category", "general") or "general"
    
    if len(content) > 200:
        truncated_content = content[:200] + "..."
    else:
        truncated_content = content
    
    response_text = f"""Tôi tìm thấy thông tin phù hợp:

{title}

{truncated_content}

Phân loại: {category}
Tổng cộng: {total_found} kết quả phù hợp"""
    
    return response_text

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Xử lý HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Xử lý mọi exceptions chưa được xử lý"""
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "Đã xảy ra lỗi không xác định"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
        loop="asyncio",
        limit_max_requests=1000,
        timeout_keep_alive=5,
        access_log=True
    )