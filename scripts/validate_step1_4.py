# scripts/validate_step1_4.py
import os
import json
import sqlite3
import sys
from user_manager import UserManager

def validate_step1_4():
    print("🔍 KIỂM TRA HOÀN THÀNH BƯỚC 1.4")
    print("=" * 50)
    
    # Kiểm tra database file
    print("1. Kiểm tra user database:")
    db_path = './company_chat.db'
    
    if os.path.exists(db_path):
        print(f"   ✅ Database file: {db_path}")
        
        # Kiểm tra kích thước file
        file_size = os.path.getsize(db_path)
        print(f"   • Kích thước: {file_size} bytes")
    else:
        print(f"   ❌ Database file không tồn tại: {db_path}")
        return False
    
    # Kiểm tra tables
    print("\n2. Kiểm tra database structure:")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Kiểm tra tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'roles_permissions']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if not missing_tables:
            print(f"   ✅ Tables: {', '.join(tables)}")
        else:
            print(f"   ❌ Thiếu tables: {missing_tables}")
            return False
        
        # Kiểm tra số lượng users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   • Tổng users: {user_count}")
        
        # Kiểm tra số lượng roles
        cursor.execute("SELECT COUNT(*) FROM roles_permissions")
        role_count = cursor.fetchone()[0]
        print(f"   • Tổng roles: {role_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra database: {e}")
        return False
    
    # Kiểm tra user manager functionality
    print("\n3. Kiểm tra user manager:")
    try:
        user_mgr = UserManager()
        
        # Test get user permissions
        test_users = ['user001', 'user005', 'admin001']
        all_ok = True
        
        for user_id in test_users:
            permissions = user_mgr.get_user_permissions(user_id)
            if permissions:
                print(f"   ✅ {user_id}: {permissions['role']} - {len(permissions['allowed_categories'])} categories")
            else:
                print(f"   ❌ {user_id}: Không tìm thấy")
                all_ok = False
        
        if not all_ok:
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi user manager: {e}")
        return False
    
    # Kiểm tra search API với phân quyền
    print("\n4. Kiểm tra search với phân quyền:")
    try:
        from search_api import SearchAPI
        
        api = SearchAPI()
        
        # Test phân quyền cơ bản
        result = api.search_with_permissions('user001', 'nghỉ phép', top_k=1)
        
        if 'error' not in result and 'user_info' in result:
            print(f"   ✅ Search API hoạt động")
            print(f"   • User: {result['user_info']['username']}")
            print(f"   • Role: {result['user_info']['role']}")
            print(f"   • Categories: {result['allowed_categories']}")
        else:
            print(f"   ❌ Lỗi search API: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra search API: {e}")
        return False
    
    # Tổng kết
    print("\n" + "=" * 50)
    print("🎉 HOÀN THÀNH BƯỚC 1.4 - USER DATABASE THÀNH CÔNG")
    print(f"\n📊 THỐNG KÊ:")
    print(f"   • Database: {db_path}")
    print(f"   • Total users: {user_count}")
    print(f"   • Total roles: {role_count}")
    print(f"   • Search với phân quyền: Hoạt động")
    
    return True

if __name__ == "__main__":
    success = validate_step1_4()
    sys.exit(0 if success else 1)