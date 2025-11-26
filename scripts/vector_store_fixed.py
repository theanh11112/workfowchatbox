# scripts/vector_store_fixed.py
import json
import os
import sys
import numpy as np
from collections import Counter
import re
import math

class FixedVectorStore:
    def __init__(self, persist_directory="./fixed_vector_store"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        self.vectors = {}
        self.metadata = {}
        self.vector_dim = 100  # Giảm dimension để tăng mật độ
        print("✅ Đã khởi tạo Fixed Vector Store")
    
    def fixed_preprocess(self, text):
        """Tiền xử lý đơn giản nhưng hiệu quả"""
        text = text.lower().strip()
        # Giữ lại các ký tự quan trọng
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def create_better_embedding(self, text):
        """Tạo embedding tốt hơn với phân phối đều"""
        processed_text = self.fixed_preprocess(text)
        words = processed_text.split()
        
        vector = np.zeros(self.vector_dim)
        
        if not words:
            return vector.tolist()
        
        # Sử dụng multiple hash functions để phân phối tốt hơn
        for word in words:
            if len(word) < 2:  # Bỏ qua từ quá ngắn
                continue
                
            # Sử dụng 3 hash functions khác nhau
            for seed in range(3):
                hash_val = (hash(word + str(seed)) % (self.vector_dim // 3)) + (seed * (self.vector_dim // 3))
                vector[hash_val] += 1.0
        
        # Thêm semantic boost cho từ khóa quan trọng
        important_words = {
            'nghỉ': 2.0, 'phép': 2.0, 'nghỉ phép': 3.0,
            'lương': 2.0, 'thưởng': 2.0, 'lương thưởng': 3.0,
            'bảo hiểm': 2.5, 'xã hội': 1.5,
            'giờ': 2.0, 'làm việc': 2.5, 'giờ làm': 3.0,
            'chính sách': 2.0, 'nội quy': 2.0, 'quy định': 2.0,
            'công ty': 1.5, 'nhân viên': 1.5, 'hợp đồng': 2.0
        }
        
        for word, boost in important_words.items():
            if word in processed_text:
                # Boost các dimensions liên quan
                for i in range(2):
                    boost_idx = (hash(word + f"boost_{i}") % self.vector_dim)
                    vector[boost_idx] += boost
        
        # Chuẩn hóa vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        else:
            # Đảm bảo vector không bằng 0
            vector = np.ones(self.vector_dim) / self.vector_dim
            
        return vector.tolist()
    
    def add_documents(self, chunks):
        """Thêm documents với embedding được cải thiện"""
        print("📥 Đang thêm documents với fixed embedding...")
        
        for chunk in chunks:
            chunk_id = chunk['id']
            content = chunk['content']
            
            # Tạo embedding tốt hơn
            embedding = self.create_better_embedding(content)
            
            # Lưu thông tin
            self.vectors[chunk_id] = embedding
            self.metadata[chunk_id] = {
                "document_id": chunk['document_id'],
                "category": chunk['category'],
                "allowed_roles": chunk['allowed_roles'],
                "title": chunk['title'],
                "content": content[:200] + "..." if len(content) > 200 else content,
                "word_count": chunk['word_count']
            }
        
        print(f"✅ Đã thêm {len(chunks)} documents")
        
        # Hiển thị thống kê
        categories = {}
        for chunk in chunks:
            cat = chunk['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"📊 Phân bố theo category:")
        for cat, count in categories.items():
            print(f"   • {cat}: {count} chunks")
    
    def cosine_similarity(self, vec1, vec2):
        """Cosine similarity với xử lý edge cases"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Đảm bảo similarity không âm
        return max(0.0, similarity)
    
    def search(self, query, n_results=5, similarity_threshold=0.1):
        """Tìm kiếm với threshold thấp hơn"""
        print(f"\n🔍 TÌM KIẾM: '{query}'")
        
        # Tạo embedding cho query
        query_embedding = self.create_better_embedding(query)
        
        # Tính similarity với tất cả documents
        similarities = []
        for chunk_id, vector in self.vectors.items():
            similarity = self.cosine_similarity(query_embedding, vector)
            if similarity >= similarity_threshold:
                similarities.append((chunk_id, similarity))
        
        # Sắp xếp theo similarity (cao nhất trước)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Lấy kết quả top n
        top_results = similarities[:n_results]
        
        print(f"✅ Tìm thấy {len(top_results)} kết quả (threshold: {similarity_threshold}):")
        
        for i, (chunk_id, similarity) in enumerate(top_results):
            metadata = self.metadata[chunk_id]
            print(f"\n--- Kết quả {i+1} (similarity: {similarity:.4f}) ---")
            print(f"Title: {metadata['title']}")
            print(f"Category: {metadata['category']}")
            print(f"Content: {metadata['content']}")
    
    def save(self):
        """Lưu vector store"""
        import pickle
        
        data = {
            'vectors': self.vectors,
            'metadata': self.metadata,
            'vector_dim': self.vector_dim
        }
        
        with open(f'{self.persist_directory}/vector_store.pkl', 'wb') as f:
            pickle.dump(data, f)
        
        print(f"💾 Đã lưu fixed vector store tại: {self.persist_directory}")
    
    def load(self):
        """Tải vector store"""
        import pickle
        
        try:
            with open(f'{self.persist_directory}/vector_store.pkl', 'rb') as f:
                data = pickle.load(f)
            
            self.vectors = data['vectors']
            self.metadata = data['metadata']
            self.vector_dim = data.get('vector_dim', 100)
            
            print(f"📂 Đã tải fixed vector store với {len(self.vectors)} documents")
            return True
        except FileNotFoundError:
            print("ℹ️  Chưa có fixed vector store được lưu")
            return False

def main():
    print("🚀 TẠO FIXED VECTOR STORE VỚI EMBEDDING TỐT HƠN")
    print("=" * 50)
    
    # Khởi tạo vector store
    vector_store = FixedVectorStore()
    
    # Thử tải vector store đã lưu
    if not vector_store.load():
        # Nếu chưa có, tạo mới từ chunks
        try:
            with open('outputs/document_chunks.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data['chunks']
            print(f"📖 Đã load {len(chunks)} chunks từ file")
            
            # Thêm documents vào vector store
            vector_store.add_documents(chunks)
            
            # Lưu vector store
            vector_store.save()
            
        except FileNotFoundError:
            print("❌ File outputs/document_chunks.json không tồn tại")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            sys.exit(1)
    
    # Test tìm kiếm với threshold thấp
    print("\n" + "=" * 50)
    print("🧪 TEST TÌM KIẾM VỚI FIXED EMBEDDING")
    print("=" * 50)
    
    # Test với threshold thấp hơn
    test_queries = [
        "nghỉ phép",
        "lương thưởng", 
        "bảo hiểm xã hội",
        "giờ làm việc",
        "nội quy công ty"
    ]
    
    for query in test_queries:
        vector_store.search(query, n_results=3, similarity_threshold=0.05)
    
    print(f"\n🎉 HOÀN THÀNH FIXED VECTOR STORE")
    print(f"📁 Vector store location: ./fixed_vector_store")
    print(f"📊 Vector dimension: {vector_store.vector_dim}")

if __name__ == "__main__":
    main()