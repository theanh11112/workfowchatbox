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
            print(f"   ✅ {description}: {len(result['results'])} kết quả")
    
    if not search_ok:
        return False
    
    # Kiểm tra phân quyền
    print("\n4. Kiểm tra phân quyền:")
    try:
        # Test employee không thể access salary
        employee_result = client.search_documents('user001', 'lương thưởng', top_k=5)
        employee_salary_results = len([r for r in employee_result['results'] if r['metadata']['category'] == 'salary'])
        
        if employee_salary_results == 0:
            print(f"   ✅ Employee bị chặn truy cập salary")
        else:
            print(f"   ❌ Employee có thể truy cập salary: {employee_salary_results} kết quả")
            return False
        
        # Test manager có thể access salary  
        manager_result = client.search_documents('user003', 'lương thưởng', top_k=5)
        manager_salary_results = len([r for r in manager_result['results'] if r['metadata']['category'] == 'salary'])
        
        if manager_salary_results > 0:
            print(f"   ✅ Manager có thể truy cập salary: {manager_salary_results} kết quả")
        else:
            print(f"   ⚠️ Manager không tìm thấy kết quả salary (có thể không có data)")
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra phân quyền: {e}")
        return False
    
    # Kiểm tra response format
    print("\n5. Kiểm tra response format:")
    try:
        result = client.search_documents('user001', 'test', top_k=1)
        
        required_fields = ['user_info', 'query', 'total_found', 'total_after_filter', 'allowed_categories', 'results']
        missing_fields = [field for field in required_fields if field not in result]
        
        if not missing_fields:
            print(f"   ✅ Response format đúng chuẩn")
        else:
            print(f"   ❌ Thiếu fields: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra format: {e}")
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
    print(f"\n🚀 API đã sẵn sàng cho n8n integration!")
    
    return True

if __name__ == "__main__":
    success = validate_step1_5()
    sys.exit(0 if success else 1)