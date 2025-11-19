# scripts/fastapi_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import chromadb
from user_manager import UserManager
import uvicorn
from typing import List, Optional

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Company Chatbot API",
    description="API cho hệ thống chatbot nội bộ công ty với phân quyền",
    version="1.0.0"
)

# Khởi tạo components
user_mgr = UserManager()
vector_store = chromadb.PersistentClient(path="./chroma_db")
collection = vector_store.get_collection("company_documents")

# Models
class SearchRequest(BaseModel):
    user_id: str
    query: str
    top_k: Optional[int] = 5

class SearchResult(BaseModel):
    content: str
    metadata: dict
    distance: float
    document_id: str

class SearchResponse(BaseModel):
    user_info: dict
    query: str
    total_found: int
    total_after_filter: int
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
    """Tạo embedding đơn giản - sẽ thay bằng model thật sau"""
    import numpy as np
    return np.random.randn(384).tolist()

def filter_results_by_permission(results, allowed_categories):
    """Lọc kết quả theo categories được phép"""
    filtered_results = []
    
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        metadata = results['metadatas'][0][i]
        distance = results['distances'][0][i]
        doc_id = results['ids'][0][i]
        
        if metadata['category'] in allowed_categories:
            filtered_results.append({
                'content': doc,
                'metadata': metadata,
                'distance': distance,
                'document_id': doc_id
            })
    
    return filtered_results

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
            "users": "/users"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kiểm tra tình trạng hệ thống"""
    try:
        # Kiểm tra user database
        users = user_mgr.get_all_users()
        
        # Kiểm tra vector store
        vector_count = collection.count()
        
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
        
        # Tạo embedding cho query
        query_embedding = create_simple_embedding(request.query)
        
        # Tìm kiếm trong vector database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k * 3  # Lấy nhiều hơn để filter
        )
        
        # Lọc kết quả theo permissions
        filtered_results = filter_results_by_permission(
            results, user_permissions['allowed_categories']
        )
        
        # Giới hạn số kết quả
        final_results = filtered_results[:request.top_k]
        
        # Format results
        search_results = []
        for result in final_results:
            search_results.append(SearchResult(
                content=result['content'],
                metadata=result['metadata'],
                distance=result['distance'],
                document_id=result['document_id']
            ))
        
        return SearchResponse(
            user_info={
                "user_id": user_permissions['user_id'],
                "username": user_permissions['username'], 
                "role": user_permissions['role']
            },
            query=request.query,
            total_found=len(results['documents'][0]),
            total_after_filter=len(final_results),
            allowed_categories=user_permissions['allowed_categories'],
            results=search_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tìm kiếm: {str(e)}")

@app.get("/categories")
async def get_categories_info():
    """Lấy thông tin về các categories và phân quyền"""
    conn = user_mgr._get_connection()
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

if __name__ == "__main__":
    print("🚀 KHỞI CHẠY COMPANY CHATBOT API")
    print("=" * 50)
    print("📚 Endpoints:")
    print("   • GET  /          - Thông tin API")
    print("   • GET  /health    - Kiểm tra hệ thống") 
    print("   • GET  /user/{id} - Thông tin user")
    print("   • GET  /users     - Danh sách users")
    print("   • POST /search    - Tìm kiếm tài liệu")
    print("   • GET  /categories- Phân quyền theo role")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )