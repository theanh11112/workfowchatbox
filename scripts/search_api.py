# scripts/search_api.py
import json
import chromadb
from user_manager import UserManager

class SearchAPI:
    def __init__(self):
        self.user_mgr = UserManager()
        self.vector_store = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.vector_store.get_collection("company_documents")
    
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
        
        # Tạo embedding đơn giản cho query (tạm thời)
        query_embedding = self._create_simple_embedding(query)
        
        # Tìm kiếm trong vector database
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2  # Lấy nhiều hơn để filter
            )
            
            # Lọc kết quả theo permissions
            filtered_results = self._filter_results_by_permission(
                results, user_permissions['allowed_categories']
            )
            
            # Giới hạn số kết quả
            final_results = filtered_results[:top_k]
            
            return {
                "user_info": {
                    "user_id": user_id,
                    "username": user_permissions['username'],
                    "role": user_permissions['role']
                },
                "query": query,
                "total_found": len(results['documents'][0]),
                "total_after_filter": len(final_results),
                "allowed_categories": user_permissions['allowed_categories'],
                "results": final_results
            }
            
        except Exception as e:
            return {
                "error": f"Lỗi tìm kiếm: {e}",
                "results": []
            }
    
    def _create_simple_embedding(self, text):
        """Tạo embedding đơn giản (sẽ thay bằng model thật sau)"""
        # Vector 384 dimensions ngẫu nhiên tạm thời
        import numpy as np
        return np.random.randn(384).tolist()
    
    def _filter_results_by_permission(self, results, allowed_categories):
        """Lọc kết quả theo categories được phép"""
        filtered_docs = []
        filtered_metadatas = []
        filtered_distances = []
        filtered_ids = []
        
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            doc_id = results['ids'][0][i]
            
            # Kiểm tra category có được phép không
            if metadata['category'] in allowed_categories:
                filtered_docs.append(doc)
                filtered_metadatas.append(metadata)
                filtered_distances.append(distance)
                filtered_ids.append(doc_id)
        
        return list(zip(filtered_docs, filtered_metadatas, filtered_distances, filtered_ids))

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
        ('user005', 'báo cáo tài chính', 'HR hỏi về confidential'),
        ('admin001', 'tất cả thông tin', 'Admin hỏi tổng quát')
    ]
    
    for user_id, query, description in test_cases:
        print(f"\n🎯 {description}")
        print("-" * 30)
        
        result = api.search_with_permissions(user_id, query, top_k=2)
        
        if 'error' in result:
            print(f"❌ Lỗi: {result['error']}")
            continue
        
        print(f"👤 User: {result['user_info']['username']} ({result['user_info']['role']})")
        print(f"🔍 Query: '{result['query']}'")
        print(f"📊 Kết quả: {result['total_after_filter']}/{result['total_found']} (sau/before filter)")
        print(f"✅ Categories được phép: {result['allowed_categories']}")
        
        if result['results']:
            for i, (doc, metadata, distance, doc_id) in enumerate(result['results']):
                print(f"\n   --- Kết quả {i+1} (distance: {distance:.4f}) ---")
                print(f"   📄 Title: {metadata['title']}")
                print(f"   🏷️ Category: {metadata['category']}")
                print(f"   👥 Roles: {json.loads(metadata['allowed_roles'])}")
                print(f"   📝 Content: {doc[:80]}...")
        else:
            print("   ❌ Không có kết quả phù hợp với quyền truy cập")

if __name__ == "__main__":
    test_search_api()