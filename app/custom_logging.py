# app/logging.py
import logging
import json
from datetime import datetime
import os
from pathlib import Path

def setup_logging():
    """
    Thiết lập hệ thống logging
    """
    # Tạo thư mục logs nếu chưa tồn tại
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Định dạng log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    # Cấu hình logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            # Ghi vào file
            logging.FileHandler('logs/chatbot.log', encoding='utf-8'),
            # Hiển thị trên console
            logging.StreamHandler()
        ]
    )
    
    # Giảm log level cho một số thư viện
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

def log_chat_interaction(user_id: str, message: str, response: dict, response_time: float):
    """
    Ghi log chi tiết cho mỗi lần tương tác chat
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "message": message[:500],  # Giới hạn độ dài message
        "response_success": response.get("success", False),
        "response_preview": response.get("response", "")[:200] + "..." if len(response.get("response", "")) > 200 else response.get("response", ""),
        "response_time": round(response_time, 3),
        "total_results": response.get("total_results", 0),
        "type": "chat_interaction"
    }
    
    logger = logging.getLogger("chatbot")
    logger.info(f"CHAT_INTERACTION: {json.dumps(log_entry, ensure_ascii=False)}")

def log_api_request(user_id: str, endpoint: str, method: str, status_code: int, processing_time: float):
    """
    Ghi log cho API requests
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "processing_time": round(processing_time, 3),
        "type": "api_request"
    }
    
    logger = logging.getLogger("api")
    logger.info(f"API_REQUEST: {json.dumps(log_entry)}")

def log_error(user_id: str, error_type: str, error_message: str, context: dict = None):
    """
    Ghi log lỗi
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {},
        "type": "error"
    }
    
    logger = logging.getLogger("error")
    logger.error(f"ERROR: {json.dumps(log_entry)}")