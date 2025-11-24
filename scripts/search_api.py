# scripts/search_api.py
import json
import pickle
import numpy as np
import sys
import os

# Thêm current directory vào Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import UserManager
try:
    from scripts.user_manager import UserManager
except ImportError:
    # Fallback: import trực tiếp nếu chạy từ thư mục scripts
    import importlib.util
    spec = importlib.util.spec_from_file_location("user_manager", "user_manager.py")
    user_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_manager)
    UserManager = user_manager.UserManager

class SearchAPI:
    def __init__(self):
        self.user_mgr = UserManager()
        self.vector_store = self._load_vector_store()
    
    def _load_vector_store(self):
        """Tải Simple Vector Store"""
        try:
            with open('./simple_vector_store/vector_store.pkl', 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"❌ Lỗi tải vector store: {e}")
            return {'vectors': {}, 'metadata': {}}
    
    def search_with_permissions(self, user_id, query, top_k=5):
        """Tìm kiếm với kiểm tra phân quyền"""
        print(f"🔍 User {user_id} tìm kiếm: '{query}'")
        
        # Kiểm tra user permissions
        user_permissions = self.user_mgr.get_user_permissions(user_id)
        if not user_permissions:
            return {
                "error": "User không tồn tại",
                "results": []
            }
        
        print(f"   Role: {user_permissions['role']}")
        print(f"   Categories được phép: {user_permissions['allowed_categories']}")
        
        # Tạo embedding cho query
        query_embedding = self._create_simple_embedding(query)
        
        # Tìm kiếm trong vector store
        try:
            # Tính similarity với tất cả documents
            similarities = []
            for chunk_id, vector in self.vector_store['vectors'].items():
                similarity = self.cosine_similarity(query_embedding, vector)
                metadata = self.vector_store['metadata'][chunk_id]
                
                # Chỉ thêm nếu category được phép
                if metadata['category'] in user_permissions['allowed_categories']:
                    similarities.append((chunk_id, similarity, metadata))
            
            # Sắp xếp theo similarity (cao nhất trước)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Giới hạn số kết quả
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
            
            return {
                "user_info": {
                    "user_id": user_id,
                    "username": user_permissions['username'],
                    "role": user_permissions['role']
                },
                "query": query,
                "total_found": len(similarities),
                "allowed_categories": user_permissions['allowed_categories'],
                "results": formatted_results
            }
            
        except Exception as e:
            return {
                "error": f"Lỗi tìm kiếm: {e}",
                "results": []
            }
    
    def _create_simple_embedding(self, text):
        """Tạo embedding đơn giản từ text"""
        words = text.lower().split()
        vector = np.zeros(100)  # Vector 100 dimensions
        
        for i, word in enumerate(words[:100]):
            hash_val = hash(word) % 100
            vector[hash_val] += 1
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def cosine_similarity(self, vec1, vec2):
        """Tính cosine similarity giữa 2 vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)

def test_search_api():
    """Test Search API với các scenario khác nhau"""
    print("🚀 TEST SEARCH API VỚI PHÂN QUYỀN")
    print("=" * 50)
    
    api = SearchAPI()
    
    # Test scenarios
    test_cases = [
        # (user_id, query, description)
        ('user001', 'nghỉ phép', 'Employee hỏi về policy'),
        ('user001', 'lương thưởng', 'Employee hỏi về salary'),
        ('user003', 'lương tháng 13', 'Manager hỏi về salary'),
        ('user005', 'bảo hiểm xã hội', 'HR hỏi về salary'),
        ('admin001', 'thông tin', 'Admin hỏi tổng quát')
    ]
    
    for user_id, query, description in test_cases:
        print(f"\n🎯 {description}")
        print("-" * 40)
        
        result = api.search_with_permissions(user_id, query, top_k=2)
        
        if 'error' in result:
            print(f"❌ Lỗi: {result['error']}")
            continue
        
        print(f"👤 User: {result['user_info']['username']} ({result['user_info']['role']})")
        print(f"🔍 Query: '{result['query']}'")
        print(f"📊 Tìm thấy: {result['total_found']} kết quả")
        print(f"✅ Categories được phép: {result['allowed_categories']}")
        
        if result['results']:
            for i, item in enumerate(result['results']):
                print(f"\n   --- Kết quả {i+1} (similarity: {item['similarity']:.4f}) ---")
                print(f"   📄 ID: {item['id']}")
                print(f"   🏷️ Title: {item['metadata']['title']}")
                print(f"   📂 Category: {item['metadata']['category']}")
                print(f"   👥 Roles: {item['metadata']['allowed_roles']}")
                print(f"   📝 Content: {item['content'][:80]}...")
        else:
            print("   ❌ Không có kết quả phù hợp với quyền truy cập")
    
    print(f"\n🎉 HOÀN THÀNH TEST SEARCH API")

if __name__ == "__main__":
    test_search_api()