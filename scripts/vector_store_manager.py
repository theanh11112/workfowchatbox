# scripts/vector_store_manager.py
import json
import chromadb
from chromadb.config import Settings
import numpy as np
import os
import sys

class SimpleVectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        """Khởi tạo vector store đơn giản"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Khởi tạo ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        print("✅ Đã khởi tạo ChromaDB client")
    
    def create_simple_embeddings(self, texts):
        """Tạo embeddings đơn giản (placeholder - sẽ thay bằng model thật sau)"""
        print("🔧 Đang tạo embeddings...")
        embeddings = []
        
        for text in texts:
            # Tạo vector giả định có 384 dimensions (giống sentence-transformers)
            words = text.split()
            vector = np.random.randn(384).tolist()  # Vector ngẫu nhiên tạm thời
            embeddings.append(vector)
        
        return embeddings
    
    def create_collection(self, collection_name="company_documents"):
        """Tạo collection trong ChromaDB"""
        try:
            # Thử lấy collection nếu đã tồn tại
            collection = self.client.get_collection(collection_name)
            print(f"✅ Collection '{collection_name}' đã tồn tại")
            return collection
        except Exception as e:
            # Tạo collection mới
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Sử dụng cosine similarity
            )
            print(f"✅ Đã tạo collection mới: '{collection_name}'")
            return collection
    
    def add_documents_to_collection(self, collection, chunks):
        """Thêm documents vào vector database"""
        print("📥 Đang thêm documents vào vector database...")
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk['content'])
            metadatas.append({
                "document_id": chunk['document_id'],
                "category": chunk['category'],
                "allowed_roles": json.dumps(chunk['allowed_roles']),  # Lưu dạng JSON string
                "title": chunk['title'],
                "chunk_index": chunk['chunk_index'],
                "total_chunks": chunk['total_chunks'],
                "word_count": chunk['word_count']
            })
            ids.append(chunk['id'])
        
        # Tạo embeddings đơn giản
        embeddings = self.create_simple_embeddings(documents)
        
        # Thêm vào collection
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Đã thêm {len(documents)} documents vào collection")
        
        # Thống kê
        categories = {}
        for chunk in chunks:
            cat = chunk['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"📊 Phân bố theo category:")
        for cat, count in categories.items():
            print(f"   • {cat}: {count} chunks")
    
    def test_search(self, collection, query_text="nghỉ phép", n_results=3):
        """Test tìm kiếm trong vector database"""
        print(f"\n🔍 TEST TÌM KIẾM: '{query_text}'")
        
        # Tạo embedding cho query
        query_embedding = self.create_simple_embeddings([query_text])[0]
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        print(f"✅ Tìm thấy {len(results['documents'][0])} kết quả:")
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"\n--- Kết quả {i+1} (distance: {distance:.4f}) ---")
            print(f"Title: {metadata['title']}")
            print(f"Category: {metadata['category']}")
            print(f"Content: {doc[:100]}...")

def main():
    # Khởi tạo vector store
    print("🚀 BẮT ĐẦU THIẾT LẬP VECTOR DATABASE")
    print("=" * 50)
    
    vector_store = SimpleVectorStore()
    
    # Tạo collection
    collection = vector_store.create_collection()
    
    # Load chunks từ bước trước
    try:
        with open('outputs/document_chunks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data['chunks']
        print(f"📖 Đã load {len(chunks)} chunks từ file")
        
        # Thêm documents vào collection
        vector_store.add_documents_to_collection(collection, chunks)
        
        # Test search
        vector_store.test_search(collection, "nghỉ phép")
        vector_store.test_search(collection, "lương thưởng")
        vector_store.test_search(collection, "giờ làm việc")
        
        print(f"\n🎉 HOÀN THÀNH THIẾT LẬP VECTOR DATABASE")
        print(f"📁 Database location: ./chroma_db")
        
    except FileNotFoundError:
        print("❌ File outputs/document_chunks.json không tồn tại")
        print("   Hãy chạy Bước 1.2 trước")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()