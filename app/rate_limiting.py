# app/rate_limiting.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import time
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter đơn giản dựa trên user_id
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Kiểm tra user có vượt quá rate limit không
        """
        now = time.time()
        
        # Khởi tạo nếu user chưa có trong dict
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Xóa các requests cũ (trong vòng 1 phút)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] 
            if now - req_time < 60  # 60 seconds
        ]
        
        # Kiểm tra số lượng requests
        if len(self.requests[user_id]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return False
        
        # Thêm request mới
        self.requests[user_id].append(now)
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """
        Lấy số requests còn lại trong phút hiện tại
        """
        if user_id not in self.requests:
            return self.requests_per_minute
        
        now = time.time()
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] 
            if now - req_time < 60
        ]
        
        return self.requests_per_minute - len(self.requests[user_id])

# Khởi tạo rate limiter
# 30 requests mỗi phút cho mỗi user
rate_limiter = RateLimiter(requests_per_minute=30)

async def rate_limit_middleware(user_id: str):
    """
    Middleware để kiểm tra rate limit
    """
    if not rate_limiter.is_allowed(user_id):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again in a minute.",
                "remaining_requests": 0,
                "limit": rate_limiter.requests_per_minute
            }
        )
    
    return True