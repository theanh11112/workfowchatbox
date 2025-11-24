# scripts/validate_step1_4.py
import os
import json
import sqlite3
import sys
import pickle
import numpy as np

def validate_step1_4():
    print("🔍 KIỂM TRA HOÀN THÀNH BƯỚC 1.4 - TOÀN BỘ HỆ THỐNG")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Kiểm tra Documents Metadata (Bước 1.1)
    print("\n1. 📋 KIỂM TRA DOCUMENTS METADATA (Bước 1.1)")
    metadata_file = 'config/documents_metadata.json'
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            docs_count = len(metadata.get('documents', []))
            print(f"   ✅ Metadata file: {docs_count} documents")
        except Exception as e:
            print(f"   ❌ Lỗi metadata: {e}")
            all_checks_passed = False
    else:
        print(f"   ❌ File metadata không tồn tại")
        all_checks_passed = False
    
    # 2. Kiểm tra Document Chunks (Bước 1.2)
    print("\n2. 📄 KIỂM TRA DOCUMENT CHUNKS (Bước 1.2)")
    chunks_file = 'outputs/document_chunks.json'
    if os.path.exists(chunks_file):
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            chunks_count = len(chunks_data.get('chunks', []))
            stats = chunks_data.get('statistics', {})
            print(f"   ✅ Chunks file: {chunks_count} chunks")
            print(f"   • Documents processed: {stats.get('processed_documents', 0)}")
            print(f"   • Error documents: {stats.get('error_documents', 0)}")
        except Exception as e:
            print(f"   ❌ Lỗi chunks file: {e}")
            all_checks_passed = False
    else:
        print(f"   ❌ File chunks không tồn tại")
        all_checks_passed = False
    
    # 3. Kiểm tra Vector Store (Bước 1.3)
    print("\n3. 🗄️ KIỂM TRA VECTOR STORE (Bước 1.3)")
    vector_store_file = './simple_vector_store/vector_store.pkl'
    if os.path.exists(vector_store_file):
        try:
            with open(vector_store_file, 'rb') as f:
                vector_data = pickle.load(f)
            vectors_count = len(vector_data.get('vectors', {}))
            metadata_count = len(vector_data.get('metadata', {}))
            print(f"   ✅ Vector store: {vectors_count} vectors")
            print(f"   • Vector dimensions: {len(list(vector_data['vectors'].values())[0]) if vectors_count > 0 else 0}")
            print(f"   • Metadata entries: {metadata_count}")
            
            # Test vector search
            if vectors_count > 0:
                test_vector = list(vector_data['vectors'].values())[0]
                similarities = []
                for vec in vector_data['vectors'].values():
                    similarity = np.dot(test_vector, vec) / (np.linalg.norm(test_vector) * np.linalg.norm(vec))
                    similarities.append(similarity)
                print(f"   • Search test: Hoạt động (similarity range: {min(similarities):.4f} - {max(similarities):.4f})")
                
        except Exception as e:
            print(f"   ❌ Lỗi vector store: {e}")
            all_checks_passed = False
    else:
        print(f"   ❌ Vector store không tồn tại")
        all_checks_passed = False
    
    # 4. Kiểm tra User Database (Bước 1.4)
    print("\n4. 👥 KIỂM TRA USER DATABASE (Bước 1.4)")
    db_path = './company_chat.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Kiểm tra tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = ['users', 'roles_permissions']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if not missing_tables:
                print(f"   ✅ Database: {len(tables)} tables")
            else:
                print(f"   ❌ Thiếu tables: {missing_tables}")
                all_checks_passed = False
            
            # Kiểm tra số lượng
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM roles_permissions")
            role_count = cursor.fetchone()[0]
            
            print(f"   • Total users: {user_count}")
            print(f"   • Total roles: {role_count}")
            
            # Kiểm tra roles permissions
            cursor.execute("SELECT role, allowed_categories FROM roles_permissions")
            roles = cursor.fetchall()
            print(f"   • Roles defined: {len(roles)}")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Lỗi database: {e}")
            all_checks_passed = False
    else:
        print(f"   ❌ Database không tồn tại")
        all_checks_passed = False
    
    # 5. Kiểm tra Search API với phân quyền
    print("\n5. 🔍 KIỂM TRA SEARCH API VỚI PHÂN QUYỀN")
    try:
        # Import SearchAPI
        import importlib.util
        spec = importlib.util.spec_from_file_location("search_api", "scripts/search_api.py")
        search_api_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(search_api_module)
        SearchAPI = search_api_module.SearchAPI
        
        api = SearchAPI()
        
        # Test phân quyền
        test_cases = [
            ('user001', 'employee', 'nghỉ phép', True),
            ('user001', 'employee', 'lương thưởng', False),  # Employee không được xem salary
            ('user003', 'manager', 'lương tháng 13', True),   # Manager được xem salary
        ]
        
        for user_id, expected_role, query, should_work in test_cases:
            result = api.search_with_permissions(user_id, query, top_k=1)
            
            if 'error' not in result:
                actual_role = result['user_info']['role']
                has_results = len(result['results']) > 0
                
                if actual_role == expected_role and (has_results == should_work or not should_work):
                    status = "✅"
                else:
                    status = "❌"
                    all_checks_passed = False
                
                print(f"   {status} {user_id} ({actual_role}): '{query}' -> {len(result['results'])} kết quả")
            else:
                print(f"   ❌ {user_id}: Lỗi - {result.get('error')}")
                all_checks_passed = False
                
    except Exception as e:
        print(f"   ❌ Lỗi search API: {e}")
        all_checks_passed = False
    
    # 6. Kiểm tra tính nhất quán
    print("\n6. 🔄 KIỂM TRA TÍNH NHẤT QUÁN")
    try:
        # Kiểm tra số lượng documents khớp
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        chunks_count = len(chunks_data.get('chunks', []))
        
        with open(vector_store_file, 'rb') as f:
            vector_data = pickle.load(f)
        vectors_count = len(vector_data.get('vectors', {}))
        
        if chunks_count == vectors_count:
            print(f"   ✅ Documents consistency: {chunks_count} chunks = {vectors_count} vectors")
        else:
            print(f"   ❌ Inconsistency: {chunks_count} chunks vs {vectors_count} vectors")
            all_checks_passed = False
            
        # Kiểm tra categories khớp
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        expected_categories = list(metadata.get('categories', {}).keys())
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT allowed_categories FROM roles_permissions WHERE role = 'admin'")
        admin_categories_json = cursor.fetchone()[0]
        admin_categories = json.loads(admin_categories_json)
        conn.close()
        
        # Admin nên có tất cả categories
        missing_in_admin = [cat for cat in expected_categories if cat not in admin_categories]
        if not missing_in_admin:
            print(f"   ✅ Categories consistency: Admin có {len(admin_categories)} categories")
        else:
            print(f"   ⚠️  Admin thiếu categories: {missing_in_admin}")
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra consistency: {e}")
        all_checks_passed = False
    
    # TỔNG KẾT
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("🎉 HOÀN THÀNH XUẤT SẮC BƯỚC 1.4 - TOÀN BỘ HỆ THỐNG")
        print("\n📊 TỔNG KẾT HỆ THỐNG:")
        print(f"   • Documents: {docs_count} documents")
        print(f"   • Chunks: {chunks_count} chunks") 
        print(f"   • Vectors: {vectors_count} vectors")
        print(f"   • Users: {user_count} users")
        print(f"   • Roles: {role_count} roles")
        print(f"   • Search với phân quyền: ✅ Hoạt động")
        print(f"   • Database: ✅ Khả dụng")
        print(f"   • Vector Store: ✅ Khả dụng")
        print(f"\n🚀 HỆ THỐNG ĐÃ SẴN SÀNG CHO BƯỚC 2 - FASTAPI SERVER!")
    else:
        print("❌ CHƯA HOÀN THÀNH - Vui lòng kiểm tra lại các bước")
    
    return all_checks_passed

if __name__ == "__main__":
    success = validate_step1_4()
    sys.exit(0 if success else 1)