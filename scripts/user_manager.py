# scripts/user_manager.py
import json
import sqlite3
import os
from datetime import datetime

class UserManager:
    def __init__(self, db_path="./company_chat.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và dữ liệu mẫu"""
        print("🗄️ Khởi tạo user database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tạo table users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(150),
                role VARCHAR(50) NOT NULL,
                department VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tạo table roles_permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles_permissions (
                role VARCHAR(50) PRIMARY KEY,
                allowed_categories JSON NOT NULL,
                description TEXT
            )
        ''')
        
        # Insert default roles
        default_roles = [
            ('employee', '["policy", "rules", "basic_info"]', 'Nhân viên cơ bản'),
            ('manager', '["policy", "rules", "basic_info", "salary", "team_info"]', 'Quản lý'),
            ('hr', '["policy", "rules", "basic_info", "salary", "team_info", "confidential"]', 'Nhân sự'),
            ('admin', '["policy", "rules", "basic_info", "salary", "team_info", "confidential", "system"]', 'Quản trị hệ thống')
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO roles_permissions (role, allowed_categories, description)
            VALUES (?, ?, ?)
        ''', default_roles)
        
        # Insert sample users
        sample_users = [
            ('user001', 'Nguyễn Văn A', 'a.nguyen@company.com', 'employee', 'IT'),
            ('user002', 'Trần Thị B', 'b.tran@company.com', 'employee', 'Marketing'),
            ('user003', 'Lê Văn C', 'c.le@company.com', 'manager', 'IT'),
            ('user004', 'Phạm Thị D', 'd.pham@company.com', 'manager', 'Sales'),
            ('user005', 'Hoàng Văn E', 'e.hoang@company.com', 'hr', 'HR'),
            ('admin001', 'System Admin', 'admin@company.com', 'admin', 'IT')
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO users (id, username, email, role, department)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_users)
        
        conn.commit()
        conn.close()
        print("✅ Đã khởi tạo database thành công")
    
    def get_user_info(self, user_id):
        """Lấy thông tin user bằng ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, department 
            FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'department': result[4]
            }
        return None
    
    def get_user_permissions(self, user_id):
        """Lấy permissions của user dựa trên role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.role, r.allowed_categories, r.description
            FROM users u
            JOIN roles_permissions r ON u.role = r.role
            WHERE u.id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id, username, role, allowed_categories_json, description = result
            allowed_categories = json.loads(allowed_categories_json)
            
            return {
                'user_id': user_id,
                'username': username,
                'role': role,
                'allowed_categories': allowed_categories,
                'role_description': description
            }
        return None
    
    def get_all_users(self):
        """Lấy danh sách tất cả users (cho admin)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.role, u.department, r.description
            FROM users u
            JOIN roles_permissions r ON u.role = r.role
            ORDER BY u.role, u.username
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        users = []
        for result in results:
            users.append({
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'role': result[3],
                'department': result[4],
                'role_description': result[5]
            })
        
        return users
    
    def add_user(self, user_id, username, email, role, department):
        """Thêm user mới"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (id, username, email, role, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, role, department))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print(f"❌ User ID {user_id} đã tồn tại")
            conn.close()
            return False
    
    def update_user_role(self, user_id, new_role):
        """Cập nhật role cho user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Kiểm tra role có hợp lệ không
        cursor.execute('SELECT role FROM roles_permissions WHERE role = ?', (new_role,))
        if not cursor.fetchone():
            print(f"❌ Role {new_role} không hợp lệ")
            conn.close()
            return False
        
        cursor.execute('''
            UPDATE users SET role = ? WHERE id = ?
        ''', (new_role, user_id))
        
        conn.commit()
        conn.close()
        return True

def main():
    # Khởi tạo user manager
    print("🚀 KHỞI TẠO USER DATABASE VÀ ROLE SYSTEM")
    print("=" * 50)
    
    user_mgr = UserManager()
    
    # Hiển thị thông tin sample users
    print("\n👥 DANH SÁCH USER MẪU:")
    users = user_mgr.get_all_users()
    
    for user in users:
        print(f"   • {user['id']}: {user['username']} - {user['role']} ({user['department']})")
    
    # Test permissions cho từng user
    print("\n🔐 TEST PERMISSIONS:")
    test_users = ['user001', 'user003', 'user005', 'admin001']
    
    for user_id in test_users:
        permissions = user_mgr.get_user_permissions(user_id)
        if permissions:
            print(f"\n--- {permissions['username']} ({permissions['role']}) ---")
            print(f"   Categories được phép: {', '.join(permissions['allowed_categories'])}")
            print(f"   Mô tả: {permissions['role_description']}")
    
    # Test phân quyền với các query khác nhau
    print("\n🔍 TEST PHÂN QUYền THEO CATEGORY:")
    test_scenarios = [
        ('user001', 'policy', 'employee hỏi về policy'),
        ('user001', 'salary', 'employee hỏi về salary'),
        ('user005', 'salary', 'hr hỏi về salary'),
        ('admin001', 'confidential', 'admin hỏi confidential')
    ]
    
    for user_id, category, scenario in test_scenarios:
        permissions = user_mgr.get_user_permissions(user_id)
        if permissions:
            has_access = category in permissions['allowed_categories']
            status = "✅ ĐƯỢC PHÉP" if has_access else "❌ KHÔNG ĐƯỢC PHÉP"
            print(f"   {scenario}: {status}")
    
    print(f"\n🎉 HOÀN THÀNH USER DATABASE")
    print(f"📁 Database: ./company_chat.db")

if __name__ == "__main__":
    main()