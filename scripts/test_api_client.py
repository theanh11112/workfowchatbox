# scripts/test_api_client.py
import requests
import json
import sys

class APIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 10
    
    def health_check(self):
        """Kiểm tra tình trạng API"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_user_info(self, user_id):
        """Lấy thông tin user"""
        try:
            response = requests.get(f"{self.base_url}/user/{user_id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def search_documents(self, user_id, query, top_k=3):
        """Tìm kiếm tài liệu"""
        try:
            payload = {
                "user_id": user_id,
                "query": query,
                "top_k": top_k
            }
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_all_users(self):
        """Lấy danh sách users"""
        try:
            response = requests.get(f"{self.base_url}/users", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_categories_info(self):
        """Lấy thông tin phân quyền"""
        try:
            response = requests.get(f"{self.base_url}/categories", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

def safe_get(data, key, default="N/A"):
    """Lấy giá trị an toàn từ dict"""
    return data.get(key, default) if isinstance(data, dict) else default

def run_comprehensive_test():
    """Chạy test toàn diện API"""
    print("🚀 TEST TOÀN DIỆN COMPANY CHATBOT API")
    print("=" * 60)
    
    client = APIClient()
    
    # Test 1: Health check
    print("1. 🔧 HEALTH CHECK")
    health = client.health_check()
    if 'error' in health:
        print(f"   ❌ API unhealthy: {health['error']}")
        return False
    
    if 'status' in health and health['status'] == 'healthy':
        print(f"   ✅ API healthy - Users: {safe_get(health, 'total_users')}, Documents: {safe_get(health, 'total_documents')}")
    else:
        print(f"   ❌ API unhealthy: {health}")
        return False
    
    # Test 2: Categories info
    print("\n2. 🏷️ CATEGORIES & PERMISSIONS")
    categories = client.get_categories_info()
    if 'error' in categories:
        print(f"   ❌ Lỗi lấy categories: {categories['error']}")
        return False
    
    roles = safe_get(categories, 'roles', {})
    for role, info in roles.items():
        if isinstance(info, dict):
            print(f"   • {role}: {safe_get(info, 'category_count')} categories - {safe_get(info, 'description')}")
        else:
            print(f"   • {role}: {info}")
    
    # Test 3: User info
    print("\n3. 👥 USER INFORMATION")
    test_users = ['user001', 'user003', 'user005', 'admin001']
    
    for user_id in test_users:
        user_info = client.get_user_info(user_id)
        if 'error' not in user_info:
            print(f"   ✅ {user_id}: {safe_get(user_info, 'username')} - {safe_get(user_info, 'role')}")
            print(f"      Categories: {safe_get(user_info, 'allowed_categories', [])}")
        else:
            print(f"   ❌ {user_id}: {user_info['error']}")
    
    # Test 4: Search với phân quyền
    print("\n4. 🔍 SEARCH WITH PERMISSIONS")
    test_cases = [
        ('user001', 'nghỉ phép bao nhiêu ngày', 'Employee hỏi policy'),
        ('user001', 'lương tháng 13 thế nào', 'Employee hỏi salary (bị chặn)'),
        ('user003', 'lương và thưởng', 'Manager hỏi salary'),
        ('user005', 'thông tin bảo mật', 'HR hỏi confidential'),
        ('admin001', 'tất cả các chính sách', 'Admin hỏi tổng quát')
    ]
    
    for user_id, query, description in test_cases:
        print(f"\n   🎯 {description}")
        print(f"   Query: '{query}'")
        
        result = client.search_documents(user_id, query, top_k=2)
        
        if 'error' in result:
            print(f"   ❌ Lỗi: {result['error']}")
            continue
        
        # Sử dụng safe_get để tránh KeyError
        user_info = safe_get(result, 'user_info', {})
        results_list = safe_get(result, 'results', [])
        
        print(f"   👤 User: {safe_get(user_info, 'username', 'Unknown')} ({safe_get(user_info, 'role', 'Unknown')})")
        print(f"   📊 Kết quả: {safe_get(result, 'total_after_filter', safe_get(result, 'total_found', 0))}/{safe_get(result, 'total_found', 0)}")
        print(f"   ✅ Categories được phép: {safe_get(result, 'allowed_categories', [])}")
        
        if results_list:
            for i, item in enumerate(results_list):
                if isinstance(item, dict):
                    metadata = safe_get(item, 'metadata', {})
                    print(f"      {i+1}. [{safe_get(metadata, 'category', 'Unknown')}] {safe_get(metadata, 'title', 'No title')}")
                    print(f"         Distance: {safe_get(item, 'distance', 0):.4f}")
                    content = safe_get(item, 'content', '')
                    print(f"         Content: {content[:60]}{'...' if len(content) > 60 else ''}")
                else:
                    print(f"      {i+1}. Invalid result format: {item}")
        else:
            print("      ❌ Không có kết quả phù hợp")
    
    # Test 5: All users
    print("\n5. 📋 ALL USERS")
    users_data = client.get_all_users()
    if 'error' in users_data:
        print(f"   ❌ Lỗi lấy users: {users_data['error']}")
    else:
        print(f"   Tổng số users: {safe_get(users_data, 'total_users', 0)}")
        users_list = safe_get(users_data, 'users', [])
        for user in users_list[:3]:  # Hiển thị 3 user đầu
            if isinstance(user, dict):
                print(f"   • {safe_get(user, 'id', 'Unknown')}: {safe_get(user, 'username', 'Unknown')} - {safe_get(user, 'role', 'Unknown')}")
    
    return True

def test_specific_scenario():
    """Test scenario cụ thể"""
    print("\n" + "=" * 60)
    print("🎯 TEST SCENARIO CỤ THỂ: PHÂN QUYỀN SALARY")
    print("=" * 60)
    
    client = APIClient()
    
    # Scenario: So sánh kết quả search về salary giữa các roles
    query = "lương thưởng"
    
    print(f"Query: '{query}'")
    print("-" * 40)
    
    roles_to_test = [
        ('user001', 'employee'),
        ('user003', 'manager'), 
        ('user005', 'hr'),
        ('admin001', 'admin')
    ]
    
    for user_id, role_name in roles_to_test:
        result = client.search_documents(user_id, query, top_k=2)
        
        if 'error' in result:
            print(f"❌ {role_name}: {result['error']}")
            continue
        
        allowed_categories = safe_get(result, 'allowed_categories', [])
        results_list = safe_get(result, 'results', [])
        
        salary_access = 'salary' in allowed_categories
        salary_results = len([r for r in results_list if isinstance(r, dict) and safe_get(r.get('metadata', {}), 'category') == 'salary'])
        
        status = "✅ CÓ QUYỀN" if salary_access else "❌ KHÔNG CÓ QUYỀN"
        print(f"👤 {role_name.upper()}: {status}")
        print(f"   • Kết quả salary: {salary_results}")
        print(f"   • Tổng kết quả: {safe_get(result, 'total_after_filter', len(results_list))}")
        print(f"   • Categories: {allowed_categories}")

def debug_api_response():
    """Debug chi tiết response từ API"""
    print("\n" + "=" * 60)
    print("🐛 DEBUG API RESPONSE")
    print("=" * 60)
    
    client = APIClient()
    
    # Test search với user001
    print("Testing search with user001...")
    result = client.search_documents('user001', 'nghỉ phép')
    
    print("Full response structure:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if 'error' not in result:
        print("\nAvailable keys in response:")
        for key in result.keys():
            print(f"  - {key}")

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        
        if success:
            test_specific_scenario()
        else:
            print("\n❌ Comprehensive test failed, skipping specific scenario test")
        
        # Chạy debug nếu có lỗi
        debug_api_response()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST HOÀN TẤT!")
            print("📚 API đã sẵn sàng cho integration với n8n")
        else:
            print("⚠️ TEST CÓ LỖI! Vui lòng kiểm tra API")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {str(e)}")
        print("Stack trace:")
        import traceback
        traceback.print_exc()
        sys.exit(1)