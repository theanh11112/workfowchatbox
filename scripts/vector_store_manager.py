# scripts/vector_store_simple.py
import json
import os
import sys
import numpy as np

class SimpleVectorStore:
    def __init__(self, persist_directory="./simple_vector_store"):
        """Vector store đơn giản sử dụng numpy"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        self.vectors = {}
        self.metadata = {}
        print("✅ Đã khởi tạo Simple Vector Store")
    
    def create_simple_embedding(self, text):
        """Tạo embedding đơn giản từ text"""
        # Tạo vector giả định dựa trên độ dài text và các từ khóa
        words = text.lower().split()
        vector = np.zeros(100)  # Vector 100 dimensions
        
        # Đơn giản: mỗi từ đóng góp vào vector
        for i, word in enumerate(words[:100]):  # Giới hạn 100 từ đầu
            # Tạo hash đơn giản từ từ
            hash_val = hash(word) % 100
            vector[hash_val] += 1
        
        # Chuẩn hóa vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()
    
    def add_documents(self, chunks):
        """Thêm documents vào vector store"""
        print("📥 Đang thêm documents vào vector store...")
        
        for chunk in chunks:
            chunk_id = chunk['id']
            content = chunk['content']
            
            # Tạo embedding
            embedding = self.create_simple_embedding(content)
            
            # Lưu vector và metadata
            self.vectors[chunk_id] = embedding
            self.metadata[chunk_id] = {
                "document_id": chunk['document_id'],
                "category": chunk['category'],
                "allowed_roles": chunk['allowed_roles'],
                "title": chunk['title'],
                "content": content[:200] + "..." if len(content) > 200 else content,  # Lưu preview
                "word_count": chunk['word_count']
            }
        
        print(f"✅ Đã thêm {len(chunks)} documents")
        
        # Thống kê
        categories = {}
        for chunk in chunks:
            cat = chunk['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"📊 Phân bố theo category:")
        for cat, count in categories.items():
            print(f"   • {cat}: {count} chunks")
    
    def cosine_similarity(self, vec1, vec2):
        """Tính cosine similarity giữa 2 vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)
    
    def search(self, query, n_results=3):
        """Tìm kiếm documents tương tự"""
        print(f"\n🔍 TÌM KIẾM: '{query}'")
        
        # Tạo embedding cho query
        query_embedding = self.create_simple_embedding(query)
        
        # Tính similarity với tất cả documents
        similarities = []
        for chunk_id, vector in self.vectors.items():
            similarity = self.cosine_similarity(query_embedding, vector)
            similarities.append((chunk_id, similarity))
        
        # Sắp xếp theo similarity (cao nhất trước)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Lấy kết quả top n
        top_results = similarities[:n_results]
        
        print(f"✅ Tìm thấy {len(top_results)} kết quả phù hợp:")
        
        for i, (chunk_id, similarity) in enumerate(top_results):
            metadata = self.metadata[chunk_id]
            print(f"\n--- Kết quả {i+1} (similarity: {similarity:.4f}) ---")
            print(f"ID: {chunk_id}")
            print(f"Title: {metadata['title']}")
            print(f"Category: {metadata['category']}")
            print(f"Roles: {metadata['allowed_roles']}")
            print(f"Content: {metadata['content']}")
    
    def save(self):
        """Lưu vector store"""
        import pickle
        
        data = {
            'vectors': self.vectors,
            'metadata': self.metadata
        }
        
        with open(f'{self.persist_directory}/vector_store.pkl', 'wb') as f:
            pickle.dump(data, f)
        
        print(f"💾 Đã lưu vector store tại: {self.persist_directory}/vector_store.pkl")
    
    def load(self):
        """Tải vector store"""
        import pickle
        
        try:
            with open(f'{self.persist_directory}/vector_store.pkl', 'rb') as f:
                data = pickle.load(f)
            
            self.vectors = data['vectors']
            self.metadata = data['metadata']
            print(f"📂 Đã tải vector store với {len(self.vectors)} documents")
            return True
        except FileNotFoundError:
            print("ℹ️  Chưa có vector store được lưu")
            return False

def main():
    print("🚀 BẮT ĐẦU THIẾT LẬP VECTOR STORE")
    print("=" * 50)
    
    # Khởi tạo vector store
    vector_store = SimpleVectorStore()
    
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
            print("   Hãy chạy Bước 1.2 trước")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            sys.exit(1)
    
    # Test tìm kiếm
    print("\n" + "=" * 50)
    print("🧪 TEST TÌM KIẾM")
    print("=" * 50)
    
    vector_store.search("nghỉ phép", n_results=2)
    vector_store.search("lương thưởng", n_results=2)
    vector_store.search("giờ làm việc", n_results=2)
    vector_store.search("bảo hiểm xã hội", n_results=2)
    
    print(f"\n🎉 HOÀN THÀNH THIẾT LẬP VECTOR STORE")
    print(f"📁 Vector store location: ./simple_vector_store")

if __name__ == "__main__":
    main()