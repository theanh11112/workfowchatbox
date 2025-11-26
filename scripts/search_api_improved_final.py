# scripts/search_api_improved_final.py
import json
import pickle
import numpy as np
import sys
import os
import re
from collections import Counter

# Thêm current directory vào Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.user_manager import UserManager
except ImportError:
    # Fallback import
    import importlib.util
    spec = importlib.util.spec_from_file_location("user_manager", "user_manager.py")
    user_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(user_manager)
    UserManager = user_manager.UserManager

class ImprovedFinalSearchAPI:
    def __init__(self):
        self.user_mgr = UserManager()
        self.vector_store = self._load_improved_vector_store()
        print("🚀 Đã khởi tạo Improved Final Search API")
    
    def _load_improved_vector_store(self):
        """Tải Improved Vector Store - tốt hơn Fixed"""
        try:
            with open('./improved_vector_store/vector_store.pkl', 'rb') as f:
                data = pickle.load(f)
            print("✅ Đã tải Improved Vector Store")
            print(f"   • Documents: {len(data['vectors'])}")
            print(f"   • Vector dimension: {data.get('vector_dim', 300)}")
            print(f"   • Vocabulary size: {len(data.get('vocab', {}))}")
            return data
        except Exception as e:
            print(f"❌ Lỗi tải improved vector store: {e}")
            return {'vectors': {}, 'metadata': {}, 'vocab': {}}
    
    def improved_preprocess(self, text):
        """Tiền xử lý GIỐNG ImprovedVectorStore"""
        # Chuyển thành chữ thường
        text = text.lower().strip()
        
        # Loại bỏ các ký tự đặc biệt, giữ lại chữ cái, số và khoảng trắng
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Thay thế nhiều khoảng trắng bằng một khoảng trắng
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_improved_embedding(self, text):
        """Tạo embedding GIỐNG ImprovedVectorStore"""
        processed_text = self.improved_preprocess(text)
        words = processed_text.split()
        
        vector_dim = self.vector_store.get('vector_dim', 300)
        vocab = self.vector_store.get('vocab', {})
        
        vector = np.zeros(vector_dim)
        
        if not words:
            return vector
        
        # Tính TF
        word_count = len(words)
        word_freq = Counter(words)
        
        # TF-IDF embedding GIỐNG ImprovedVectorStore
        for word, count in word_freq.items():
            if word in vocab:
                word_info = vocab[word]
                tf = count / word_count
                tf_idf = tf * word_info.get('idf', 1.0)
                
                # Sử dụng multiple hash functions GIỐNG ImprovedVectorStore
                for seed in range(3):
                    hash_val = (hash(word + str(seed)) % (vector_dim // 3)) + (seed * (vector_dim // 3))
                    if hash_val < vector_dim:
                        vector[hash_val] += tf_idf
        
        # Thêm semantic boost cho các từ khóa quan trọng
        important_keywords = {
            'nghỉ phép': [0.8, 0.6, 0.4],
            'lương thưởng': [0.7, 0.5, 0.3], 
            'bảo hiểm': [0.6, 0.4, 0.2],
            'giờ làm việc': [0.5, 0.3, 0.1],
            'hợp đồng': [0.4, 0.2, 0.1],
            'cơ cấu': [0.3, 0.2, 0.1],
            'hệ thống': [0.3, 0.2, 0.1]
        }
        
        for phrase, weights in important_keywords.items():
            if phrase in processed_text:
                for i, weight in enumerate(weights):
                    if i * 3 < vector_dim:
                        vector[i * 3] += weight
        
        # Chuẩn hóa vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def cosine_similarity(self, vec1, vec2):
        """Cosine similarity"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, similarity)
    
    def search(self, user_id, query, top_k=5, similarity_threshold=0.1):
        """Tìm kiếm với Improved Vector Store"""
        print(f"🔍 User {user_id} tìm kiếm: '{query}'")
        
        # Kiểm tra user permissions
        user_permissions = self.user_mgr.get_user_permissions(user_id)
        if not user_permissions:
            return {"error": "User không tồn tại", "results": []}
        
        print(f"   Role: {user_permissions['role']}")
        print(f"   Allowed categories: {user_permissions['allowed_categories']}")
        
        # Tạo embedding cho query
        query_embedding = self.create_improved_embedding(query)
        
        # Tìm kiếm
        similarities = []
        for chunk_id, vector in self.vector_store['vectors'].items():
            # Chuyển đổi vector sang numpy array nếu cần
            if isinstance(vector, list):
                vector = np.array(vector)
            
            similarity = self.cosine_similarity(query_embedding, vector)
            metadata = self.vector_store['metadata'][chunk_id]
            
            # Kiểm tra phân quyền
            if metadata['category'] in user_permissions['allowed_categories']:
                if similarity >= similarity_threshold:
                    similarities.append((chunk_id, similarity, metadata))
        
        # Sắp xếp và lấy kết quả
        similarities.sort(key=lambda x: x[1], reverse=True)
        final_results = similarities[:top_k]
        
        print(f"   ✅ Tìm thấy {len(similarities)} kết quả, trả về {len(final_results)}")
        print(f"   📊 Similarity range: {[f'{s[1]:.4f}' for s in final_results]}")
        
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
    
    def smart_search(self, user_id, query, top_k=5):
        """Smart search với threshold thấp hơn"""
        return self.search(user_id, query, top_k, similarity_threshold=0.05)

def test_improved_search():
    """Test improved search API"""
    print("🚀 TEST IMPROVED FINAL SEARCH API")
    print("=" * 60)
    
    api = ImprovedFinalSearchAPI()
    
    test_cases = [
        ('user001', 'nghỉ phép', 'Employee hỏi nghỉ phép'),
        ('user001', 'lương thưởng', 'Employee hỏi lương'),
        ('user003', 'lương tháng 13', 'Manager hỏi thưởng'),
        ('user005', 'bảo hiểm', 'HR hỏi bảo hiểm'),
        ('user001', 'giờ làm việc', 'Employee hỏi giờ làm'),
        ('user003', 'chính sách công ty', 'Manager hỏi policy'),
        ('user005', 'cơ cấu lương', 'HR hỏi lương')
    ]
    
    for user_id, query, description in test_cases:
        print(f"\n🎯 {description}")
        print("-" * 40)
        
        result = api.smart_search(user_id, query, top_k=3)
        
        if 'error' in result:
            print(f"❌ Lỗi: {result['error']}")
            continue
        
        print(f"👤 User: {result['user_info']['username']} ({result['user_info']['role']})")
        print(f"🔍 Query: '{result['query']}'")
        print(f"📊 Found: {result['total_found']} results")
        
        if result['results']:
            for i, item in enumerate(result['results']):
                print(f"   {i+1}. {item['metadata']['title']} (similarity: {item['similarity']:.4f})")
                print(f"      Category: {item['metadata']['category']}")
                print(f"      Content: {item['content'][:80]}...")
        else:
            print("   ❌ Không có kết quả phù hợp")
    
    print(f"\n🎉 HOÀN THÀNH TEST IMPROVED FINAL SEARCH API")

if __name__ == "__main__":
    test_improved_search()