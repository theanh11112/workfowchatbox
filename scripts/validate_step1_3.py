# scripts/validate_step1_3.py
import os
import json
import sys
import pickle
# import numpy as np

def validate_step1_3():
    print("🔍 KIỂM TRA HOÀN THÀNH BƯỚC 1.3")
    print("=" * 50)
    
    # Kiểm tra thư mục simple_vector_store
    print("1. Kiểm tra vector database:")
    db_path = './simple_vector_store'
    db_file = f'{db_path}/vector_store.pkl'
    
    if os.path.exists(db_file):
        print(f"   ✅ File database: {db_file}")
        
        # Kiểm tra kích thước file
        file_size = os.path.getsize(db_file)
        print(f"   • Kích thước file: {file_size} bytes")
    else:
        print(f"   ❌ File database không tồn tại: {db_file}")
        return False
    
    # Kiểm tra nội dung vector store
    print("\n2. Kiểm tra nội dung vector store:")
    try:
        with open(db_file, 'rb') as f:
            data = pickle.load(f)
        
        vectors = data.get('vectors', {})
        metadata = data.get('metadata', {})
        
        print(f"   ✅ Đọc file thành công")
        print(f"   • Số vectors: {len(vectors)}")
        print(f"   • Số metadata: {len(metadata)}")
        
        # Kiểm tra vector dimensions
        if vectors:
            sample_vector = list(vectors.values())[0]
            print(f"   • Vector dimensions: {len(sample_vector)}")
        
    except Exception as e:
        print(f"   ❌ Lỗi đọc file: {e}")
        return False
    
    # Kiểm tra metadata
    print("\n3. Kiểm tra metadata:")
    try:
        if metadata:
            sample_metadata = list(metadata.values())[0]
            required_fields = ['document_id', 'category', 'allowed_roles', 'title']
            missing_fields = [field for field in required_fields if field not in sample_metadata]
            
            if not missing_fields:
                print(f"   ✅ Metadata đầy đủ")
                print(f"   • Category: {sample_metadata.get('category')}")
                print(f"   • Title: {sample_metadata.get('title')}")
                print(f"   • Roles: {sample_metadata.get('allowed_roles')}")
            else:
                print(f"   ❌ Thiếu fields: {missing_fields}")
                return False
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra metadata: {e}")
        return False
    
    # Test search functionality
    print("\n4. Kiểm tra chức năng tìm kiếm:")
    try:
        # Tạo class test đơn giản
        class TestVectorStore:
            def __init__(self, vectors, metadata):
                self.vectors = vectors
                self.metadata = metadata
            
            def cosine_similarity(self, vec1, vec2):
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    return 0
                return dot_product / (norm1 * norm2)
            
            def test_search(self, query_vector):
                similarities = []
                for chunk_id, vector in self.vectors.items():
                    similarity = self.cosine_similarity(query_vector, vector)
                    similarities.append((chunk_id, similarity))
                
                similarities.sort(key=lambda x: x[1], reverse=True)
                return similarities[:2]  # Trả về 2 kết quả
        
        # Test search
        test_store = TestVectorStore(vectors, metadata)
        if vectors:
            test_vector = list(vectors.values())[0]  # Dùng vector đầu tiên để test
            results = test_store.test_search(test_vector)
            
            if results:
                print(f"   ✅ Search hoạt động")
                print(f"   • Trả về: {len(results)} kết quả")
                print(f"   • Similarity range: {results[0][1]:.4f} - {results[-1][1]:.4f}")
            else:
                print(f"   ⚠️  Search trả về 0 kết quả")
                
    except Exception as e:
        print(f"   ❌ Lỗi search test: {e}")
        return False
    
    # Kiểm tra file chunks gốc
    print("\n5. Kiểm tra file chunks gốc:")
    chunks_file = "outputs/document_chunks.json"
    if os.path.exists(chunks_file):
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        chunks_count = len(chunks_data['chunks'])
        print(f"   ✅ File chunks gốc: {chunks_count} chunks")
        
        # So sánh số lượng
        if chunks_count == len(vectors):
            print(f"   ✅ Số lượng khớp: {chunks_count} chunks = {len(vectors)} vectors")
        else:
            print(f"   ⚠️  Số lượng không khớp: {chunks_count} chunks vs {len(vectors)} vectors")
    else:
        print(f"   ❌ File chunks không tồn tại")
        return False
    
    # Tổng kết
    print("\n" + "=" * 50)
    print("🎉 HOÀN THÀNH BƯỚC 1.3 - VECTOR STORE THÀNH CÔNG")
    print(f"\n📊 THỐNG KÊ:")
    print(f"   • Database location: {db_path}")
    print(f"   • Total vectors: {len(vectors)}")
    print(f"   • Vector dimensions: {len(list(vectors.values())[0]) if vectors else 0}")
    print(f"   • Search: Hoạt động")
    print(f"   • File chunks: {chunks_count} chunks")
    
    return True

if __name__ == "__main__":
    success = validate_step1_3()
    sys.exit(0 if success else 1)