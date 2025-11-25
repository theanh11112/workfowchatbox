# app/auth.py
from fastapi import HTTPException, Depends, status
from fastapi.security import APIKeyHeader
import os

# API Key configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Valid API keys (trong production nên lưu trong environment variables)
VALID_API_KEYS = [
    "company-chatbot-prod-2024",
    "company-chatbot-backup-2024", 
    "dev-test-key-123"
]

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    Xác thực API key từ header
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Please provide X-API-Key header."
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Please check your API key."
        )
    
    return api_key

# Optional: User authentication (nếu cần xác thực user cụ thể)
async def verify_user_access(user_id: str, api_key: str):
    """
    Kiểm tra user có quyền truy cập không
    """
    # Có thể thêm logic kiểm tra user permissions ở đây
    if not user_id or user_id == "unknown":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user ID"
        )
    return True