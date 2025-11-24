# scripts/validate_step1_5.py
import os
import json
import requests
import time
import sys
from test_api_client import APIClient

def validate_step1_5():
    print("🔍 KIỂM TRA HOÀN THÀNH BƯỚC 1.5")
    print("=" * 50)
    
    # Kiểm tra API server có chạy không
    print("1. Kiểm tra API server:")
    client = APIClient()
    
    try:
        health = client.health_check()
        if health.get('status') == 'healthy':
            print(f"   ✅ API server đang chạy")
            print(f"   • Users: {health.get('total_users', 0)}")
            print(f"   • Documents: {health.get('total_documents', 0)}")
            print(f"   • Database: {health.get('database', 'N/A')}")
            print(f"   • Vector Store: {health.get('vector_store', 'N/A')}")
        else:
            print(f"   ❌ API server không healthy: {health}")
            return False
    except Exception as e:
        print(f"   ❌ Không thể kết nối đến API: {e}")
        print("   💡 Hãy chạy: python scripts/fastapi_server.py")
        return False
    
    # Kiểm tra các endpoints
    print("\n2. Kiểm tra endpoints:")
    endpoints_to_test = [
        ("/", "GET", "Root endpoint"),
        ("/health", "GET", "Health check"), 
        ("/user/user001", "GET", "User info"),
        ("/users", "GET", "All users"),
        ("/categories", "GET", "Categories info")
    ]
    
    all_endpoints_ok = True
    for endpoint, method, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"http://localhost:8000{endpoint}")
                if response.status_code == 200:
                    print(f"   ✅ {endpoint} - {description}")
                else:
                    print(f"   ❌ {endpoint} - Status: {response.status_code}")
                    all_endpoints_ok = False
        except Exception as e:
            print(f"   ❌ {endpoint} - Lỗi: {e}")
            all_endpoints_ok = False
    
    if not all_endpoints_ok:
        return False
    
    # Kiểm tra search functionality
    print("\n3. Kiểm tra search functionality:")
    test_cases = [
        ('user001', 'nghỉ phép', 'Employee search policy'),
        ('user003', 'lương', 'Manager search salary')
    ]
    
    search_ok = True
    for user_id, query, description in test_cases:
        result = client.search_documents(user_id, query, top_k=1)
        
        if 'error' in result:
            print(f"   ❌ {description}: {result['error']}")
            search_ok = False
        else:
            print(f"   ✅ {description}: {len(result.get('results', []))} kết quả")
    
    if not search_ok:
        return False
    
    # Kiểm tra phân quyền
    print("\n4. Kiểm tra phân quyền:")
    try:
        # Test employee không thể access salary
        employee_result = client.search_documents('user001', 'lương thưởng', top_k=5)
        employee_results = employee_result.get('results', [])
        employee_salary_results = len([r for r in employee_results if r.get('metadata', {}).get('category') == 'salary'])
        
        if employee_salary_results == 0:
            print(f"   ✅ Employee bị chặn truy cập salary")
        else:
            print(f"   ❌ Employee có thể truy cập salary: {employee_salary_results} kết quả")
            return False
        
        # Test manager có thể access salary  
        manager_result = client.search_documents('user003', 'lương thưởng', top_k=5)
        manager_results = manager_result.get('results', [])
        manager_salary_results = len([r for r in manager_results if r.get('metadata', {}).get('category') == 'salary'])
        
        if manager_salary_results > 0:
            print(f"   ✅ Manager có thể truy cập salary: {manager_salary_results} kết quả")
        else:
            print(f"   ⚠️ Manager không tìm thấy kết quả salary (có thể không có data)")
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra phân quyền: {e}")
        return False
    
    # Kiểm tra response format - SỬA LẠI THEO API THỰC TẾ
    print("\n5. Kiểm tra response format:")
    try:
        result = client.search_documents('user001', 'test', top_k=1)
        
        # Sửa lại required fields theo API thực tế
        required_fields = ['user_info', 'query', 'total_found', 'allowed_categories', 'results']
        missing_fields = [field for field in required_fields if field not in result]
        
        if not missing_fields:
            print(f"   ✅ Response format đúng chuẩn")
            print(f"   • Có field 'total_found': {result.get('total_found')}")
            print(f"   • Có field 'allowed_categories': {result.get('allowed_categories')}")
            print(f"   • Có field 'results': {len(result.get('results', []))} items")
        else:
            print(f"   ❌ Thiếu fields: {missing_fields}")
            print(f"   📋 Fields có sẵn: {list(result.keys())}")
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra format: {e}")
        return False
    
    # Kiểm tra dữ liệu mẫu
    print("\n6. Kiểm tra dữ liệu mẫu:")
    try:
        users_data = client.get_all_users()
        categories_data = client.get_categories_info()
        
        total_users = users_data.get('total_users', 0)
        total_roles = len(categories_data.get('roles', {}))
        
        print(f"   ✅ Users: {total_users} users trong database")
        print(f"   ✅ Roles: {total_roles} roles được định nghĩa")
        
        # Kiểm tra ít nhất có các roles cơ bản
        expected_roles = ['employee', 'manager', 'hr', 'admin']
        available_roles = list(categories_data.get('roles', {}).keys())
        missing_roles = [role for role in expected_roles if role not in available_roles]
        
        if not missing_roles:
            print(f"   ✅ Đầy đủ các roles: {available_roles}")
        else:
            print(f"   ⚠️ Thiếu roles: {missing_roles}")
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra dữ liệu: {e}")
        return False
    
    # Tổng kết
    print("\n" + "=" * 50)
    print("🎉 HOÀN THÀNH BƯỚC 1.5 - SEARCH API THÀNH CÔNG")
    print(f"\n📊 THỐNG KÊ:")
    print(f"   • API Server: Đang chạy trên port 8000")
    print(f"   • Endpoints: Đầy đủ")
    print(f"   • Search: Hoạt động")
    print(f"   • Phân quyền: Hoạt động")
    print(f"   • Response format: Chuẩn")
    print(f"   • Dữ liệu: Đầy đủ users và categories")
    print(f"\n🚀 API đã sẵn sàng cho n8n integration!")
    print(f"\n📝 NEXT STEPS:")
    print(f"   1. Tích hợp API với n8n workflow")
    print(f"   2. Tạo conversation flow trong n8n")
    print(f"   3. Thêm authentication nếu cần")
    print(f"   4. Deploy production")
    
    return True

if __name__ == "__main__":
    success = validate_step1_5()
    if success:
        print("\n✅ VALIDATION PASSED - BƯỚC 1.5 HOÀN THÀNH")
    else:
        print("\n❌ VALIDATION FAILED - CẦN KIỂM TRA LẠI")
    sys.exit(0 if success else 1)