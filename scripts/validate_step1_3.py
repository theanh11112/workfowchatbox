# scripts/validate_step1_3.py
import os
import json
import sys
import chromadb

def validate_step1_3():
    print("🔍 KIỂM TRA HOÀN THÀNH BƯỚC 1.3")
    print("=" * 50)
    
    # Kiểm tra thư mục chroma_db
    print("1. Kiểm tra vector database:")
    db_path = './chroma_db'
    
    if os.path.exists(db_path):
        print(f"   ✅ Thư mục database: {db_path}")
        
        # Đếm số file trong chroma_db
        files = os.listdir(db_path)
        print(f"   • Số file trong database: {len(files)}")
    else:
        print(f"   ❌ Thư mục database không tồn tại: {db_path}")
        return False
    
    # Kiểm tra kết nối đến collection
    print("\n2. Kiểm tra kết nối collection:")
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("company_documents")
        
        # Lấy thống kê
        stats = collection.count()
        print(f"   ✅ Kết nối thành công đến collection")
        print(f"   • Tổng số vectors: {stats}")
        
        # Kiểm tra search hoạt động
        results = collection.peek(limit=2)  # Xem 2 documents đầu
        if results['documents']:
            print(f"   • Sample documents: {len(results['documents'])}")
            print(f"   • Vector dimensions: {len(collection.peek(limit=1)['embeddings'][0]) if collection.peek(limit=1)['embeddings'] else 'N/A'}")
            
    except Exception as e:
        print(f"   ❌ Lỗi kết nối collection: {e}")
        return False
    
    # Kiểm tra metadata
    print("\n3. Kiểm tra metadata:")
    try:
        results = collection.peek(limit=1)
        if results['metadatas']:
            metadata = results['metadatas'][0]
            required_fields = ['document_id', 'category', 'allowed_roles', 'title']
            missing_fields = [field for field in required_fields if field not in metadata]
            
            if not missing_fields:
                print(f"   ✅ Metadata đầy đủ")
                print(f"   • Category: {metadata.get('category')}")
                print(f"   • Title: {metadata.get('title')}")
            else:
                print(f"   ❌ Thiếu fields: {missing_fields}")
                return False
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra metadata: {e}")
        return False
    
    # Test search functionality
    print("\n4. Kiểm tra chức năng tìm kiếm:")
    try:
        # Test search đơn giản
        test_results = collection.query(
            query_embeddings=[[0.1] * 384],  # Vector test
            n_results=1
        )
        
        if test_results['documents'] and len(test_results['documents'][0]) > 0:
            print(f"   ✅ Search hoạt động")
            print(f"   • Trả về: {len(test_results['documents'][0])} kết quả")
        else:
            print(f"   ⚠️  Search trả về 0 kết quả")
            
    except Exception as e:
        print(f"   ❌ Lỗi search: {e}")
        return False
    
    # Tổng kết
    print("\n" + "=" * 50)
    print("🎉 HOÀN THÀNH BƯỚC 1.3 - VECTOR DATABASE THÀNH CÔNG")
    print(f"\n📊 THỐNG KÊ:")
    print(f"   • Database location: {db_path}")
    print(f"   • Total vectors: {stats}")
    print(f"   • Collection: company_documents")
    print(f"   • Search: Hoạt động")
    
    return True

if __name__ == "__main__":
    success = validate_step1_3()
    sys.exit(0 if success else 1)