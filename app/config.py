# app/config.py
import os
from typing import List

class Settings:
    """Cấu hình ứng dụng"""
    
    # API Settings
    API_TITLE = "Company Chatbot Backend API"
    API_DESCRIPTION = "Backend service for company chatbot with authentication and rate limiting"
    API_VERSION = "1.1.0"
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8001))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security
    API_KEYS: List[str] = [
        "company-chatbot-prod-2024",
        "company-chatbot-backup-2024",
        "dev-test-key-123"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT", "30"))
    
    # Search API
    SEARCH_API_URL = os.getenv("SEARCH_API_URL", "http://localhost:8000/search")
    SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "30"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/chatbot.log"

settings = Settings()