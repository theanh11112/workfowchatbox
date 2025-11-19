# scripts/start_server.py
import subprocess
import time
import sys
import requests

def start_api_server():
    """Khởi chạy API server"""
    print("🚀 KHỞI CHẠY COMPANY CHATBOT API SERVER")
    print("=" * 50)
    
    try:
        # Kiểm tra xem server đã chạy chưa
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ API server đã chạy sẵn")
        print("📚 Truy cập: http://localhost:8000")
        return True
    except:
        print("🔄 Khởi chạy API server...")
        
        # Chạy server trong process mới
        process = subprocess.Popen([
            sys.executable, "scripts/fastapi_server.py"
        ])
        
        # Chờ server khởi động
        print("⏳ Đang khởi động server...")
        time.sleep(3)
        
        # Kiểm tra lại
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server khởi chạy thành công!")
                print("📚 Truy cập: http://localhost:8000")
                print("📖 Documentation: http://localhost:8000/docs")
                return True
        except:
            print("❌ Không thể khởi chạy API server")
            return False

def main():
    if start_api_server():
        print("\n🎯 CÁC BƯỚC TIẾP THEO:")
        print("1. 📝 Test API: python scripts/test_api_client.py")
        print("2. 🔍 Validation: python scripts/validate_step1_5.py") 
        print("3. 🚀 Integrate với n8n: Sử dụng webhook đến http://localhost:8000/search")
        print("\n💡 Giữ terminal này mở để server tiếp tục chạy")
        print("   Nhấn Ctrl+C để dừng server")
        
        try:
            # Giữ script chạy
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Dừng server...")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()