# scripts/fastapi_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import pickle
import numpy as np
import uvicorn
from typing import List, Optional
import sys
import os

# Thêm path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.user_manager import UserManager
except ImportError:
    # Fallback import
    import importlib.util
    spec = importlib.util.spec_from_file_location("user_manager", "scripts/user_manager.py")
    user_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_manager)
    UserManager = user_manager.UserManager

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Company Chatbot API",
    description="API cho hệ thống chatbot nội bộ công ty với phân quyền",
    version="1.0.0"
)

# Khởi tạo components
user_mgr = UserManager()

# Load Simple Vector Store
def load_vector_store():
    """Tải Simple Vector Store"""
    try:
        with open('./simple_vector_store/vector_store.pkl', 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"❌ Lỗi tải vector store: {e}")
        return {'vectors': {}, 'metadata': {}}

vector_store = load_vector_store()

# Models
class SearchRequest(BaseModel):
    user_id: str
    query: str
    top_k: Optional[int] = 5

class SearchResult(BaseModel):
    id: str
    content: str
    metadata: dict
    similarity: float

class SearchResponse(BaseModel):
    user_info: dict
    query: str
    total_found: int
    allowed_categories: List[str]
    results: List[SearchResult]

class UserInfoResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    department: str
    allowed_categories: List[str]

class HealthResponse(BaseModel):
    status: str
    database: str
    vector_store: str
    total_users: int
    total_documents: int

# Utility functions
def create_simple_embedding(text):
    """Tạo embedding đơn giản từ text"""
    words = text.lower().split()
    vector = np.zeros(100)
    
    for i, word in enumerate(words[:100]):
        hash_val = hash(word) % 100
        vector[hash_val] += 1
    
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
        
    return vector

def cosine_similarity(vec1, vec2):
    """Tính cosine similarity giữa 2 vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)

def search_with_permissions(query, allowed_categories, top_k=5):
    """Tìm kiếm với phân quyền"""
    query_embedding = create_simple_embedding(query)
    
    similarities = []
    for chunk_id, vector in vector_store['vectors'].items():
        similarity = cosine_similarity(query_embedding, vector)
        metadata = vector_store['metadata'][chunk_id]
        
        # Chỉ thêm nếu category được phép
        if metadata['category'] in allowed_categories:
            similarities.append((chunk_id, similarity, metadata))
    
    # Sắp xếp theo similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    final_results = similarities[:top_k]
    
    # Format kết quả
    formatted_results = []
    for chunk_id, similarity, metadata in final_results:
        formatted_results.append({
            'id': chunk_id,
            'content': metadata.get('content', ''),
            'metadata': metadata,
            'similarity': similarity
        })
    
    return len(similarities), formatted_results

# Routes
@app.get("/")
async def root():
    return {
        "message": "Company Chatbot API đang hoạt động",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search (POST)",
            "user_info": "/user/{user_id}",
            "health": "/health",
            "users": "/users",
            "categories": "/categories",
            "docs": "/docs (Swagger UI)"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kiểm tra tình trạng hệ thống"""
    try:
        # Kiểm tra user database
        users = user_mgr.get_all_users()
        
        # Kiểm tra vector store
        vector_count = len(vector_store['vectors'])
        
        return HealthResponse(
            status="healthy",
            database="connected",
            vector_store="connected", 
            total_users=len(users),
            total_documents=vector_count
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database="error",
            vector_store="error",
            total_users=0,
            total_documents=0
        )

@app.get("/user/{user_id}", response_model=UserInfoResponse)
async def get_user_info(user_id: str):
    """Lấy thông tin user và permissions"""
    user_permissions = user_mgr.get_user_permissions(user_id)
    user_info = user_mgr.get_user_info(user_id)
    
    if not user_permissions or not user_info:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    
    return UserInfoResponse(
        user_id=user_info['id'],
        username=user_info['username'],
        email=user_info['email'],
        role=user_info['role'],
        department=user_info['department'],
        allowed_categories=user_permissions['allowed_categories']
    )

@app.get("/users")
async def get_all_users():
    """Lấy danh sách tất cả users (cho admin)"""
    users = user_mgr.get_all_users()
    return {
        "total_users": len(users),
        "users": users
    }

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Tìm kiếm tài liệu với phân quyền"""
    try:
        # Kiểm tra user permissions
        user_permissions = user_mgr.get_user_permissions(request.user_id)
        if not user_permissions:
            raise HTTPException(status_code=404, detail="User không tồn tại")
        
        # Tìm kiếm với phân quyền
        total_found, results = search_with_permissions(
            request.query, 
            user_permissions['allowed_categories'], 
            request.top_k
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                id=result['id'],
                content=result['content'],
                metadata=result['metadata'],
                similarity=result['similarity']
            ))
        
        return SearchResponse(
            user_info={
                "user_id": user_permissions['user_id'],
                "username": user_permissions['username'], 
                "role": user_permissions['role']
            },
            query=request.query,
            total_found=total_found,
            allowed_categories=user_permissions['allowed_categories'],
            results=search_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tìm kiếm: {str(e)}")

@app.get("/categories")
async def get_categories_info():
    """Lấy thông tin về các categories và phân quyền"""
    import sqlite3
    
    conn = sqlite3.connect('./company_chat.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, allowed_categories, description 
        FROM roles_permissions 
        ORDER BY role
    ''')
    
    roles_data = cursor.fetchall()
    conn.close()
    
    categories_info = {}
    for role, allowed_categories_json, description in roles_data:
        allowed_categories = json.loads(allowed_categories_json)
        categories_info[role] = {
            'description': description,
            'allowed_categories': allowed_categories,
            'category_count': len(allowed_categories)
        }
    
    return {
        "roles": categories_info
    }

@app.get("/test-search")
async def test_search():
    """Endpoint test tìm kiếm (cho development)"""
    test_cases = [
        {"user_id": "user001", "query": "nghỉ phép"},
        {"user_id": "user003", "query": "lương thưởng"},
        {"user_id": "user005", "query": "bảo hiểm"}
    ]
    
    results = []
    for test in test_cases:
        try:
            user_permissions = user_mgr.get_user_permissions(test["user_id"])
            if user_permissions:
                total_found, search_results = search_with_permissions(
                    test["query"], user_permissions['allowed_categories'], 2
                )
                results.append({
                    "user": test["user_id"],
                    "role": user_permissions['role'],
                    "query": test["query"],
                    "found": total_found,
                    "results_count": len(search_results)
                })
        except Exception as e:
            results.append({
                "user": test["user_id"],
                "error": str(e)
            })
    
    return {"test_results": results}

if __name__ == "__main__":
    print("🚀 KHỞI CHẠY COMPANY CHATBOT API")
    print("=" * 50)
    print("📚 Endpoints:")
    print("   • GET  /           - Thông tin API")
    print("   • GET  /health     - Kiểm tra hệ thống") 
    print("   • GET  /user/{id}  - Thông tin user")
    print("   • GET  /users      - Danh sách users")
    print("   • POST /search     - Tìm kiếm tài liệu")
    print("   • GET  /categories - Phân quyền theo role")
    print("   • GET  /test-search- Test tìm kiếm")
    print("   • GET  /docs       - Swagger UI Documentation")
    print("=" * 50)
    print("🌐 Server sẽ chạy tại: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )