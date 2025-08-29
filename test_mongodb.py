# test_mongodb.py - File kiểm tra kết nối MongoDB độc lập
from pymongo import MongoClient
import pymongo
from datetime import datetime

def test_mongodb_connection():
    """
    Script kiểm tra kết nối MongoDB chi tiết
    Chạy file này trước khi chạy ứng dụng chính
    """
    print("🔍 KIỂM TRA KẾT NỐI MONGODB")
    print("=" * 50)
    
    # Danh sách các port phổ biến để thử
    possible_connections = [
        'mongodb://localhost:27017/',
        'mongodb://127.0.0.1:27017/',
        'mongodb://localhost:27018/',
        'mongodb://localhost:27019/',
    ]
    
    successful_connection = None
    
    for conn_str in possible_connections:
        try:
            print(f"🔗 Đang thử kết nối: {conn_str}")
            
            client = MongoClient(conn_str, 
                               serverSelectionTimeoutMS=3000,
                               connectTimeoutMS=3000)
            
            # Thử ping
            client.admin.command('ping')
            print(f"✅ Kết nối thành công!")
            
            # Lấy thông tin server
            server_info = client.server_info()
            print(f"📊 MongoDB version: {server_info.get('version', 'Unknown')}")
            
            # Kiểm tra databases
            db_names = client.list_database_names()
            print(f"📁 Databases có sẵn: {db_names}")
            
            successful_connection = conn_str
            break
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            continue
    
    if successful_connection:
        print(f"\n🎉 THÀNH CÔNG! Sử dụng connection string: {successful_connection}")
        
        # Thử tạo test database
        try:
            client = MongoClient(successful_connection)
            test_db = client['test_digital_library']
            
            # Tạo test collection
            test_collection = test_db['test_users']
            
            # Insert test document
            test_doc = {
                "name": "Test User",
                "email": "test@example.com",
                "created_at": datetime.now()
            }
            
            result = test_collection.insert_one(test_doc)
            print(f"✅ Test insert thành công, ID: {result.inserted_id}")
            
            # Đọc test document
            found_doc = test_collection.find_one({"_id": result.inserted_id})
            print(f"✅ Test read thành công: {found_doc['name']}")
            
            # Xóa test document
            test_collection.delete_one({"_id": result.inserted_id})
            print(f"✅ Test delete thành công")
            
            # Xóa test database
            client.drop_database('test_digital_library')
            print(f"✅ Dọn dẹp test data thành công")
            
        except Exception as e:
            print(f"⚠️  Cảnh báo khi test database operations: {e}")
        
        return True
    else:
        print("\n❌ THẤT BẠI! Không thể kết nối MongoDB")
        print("\n🛠️  HƯỚNG DẪN KHẮC PHỤC:")
        print("1. Kiểm tra MongoDB đã được cài đặt:")
        print("   mongod --version")
        print("\n2. Khởi động MongoDB service:")
        print("   Windows: net start MongoDB")
        print("   macOS: brew services start mongodb-community")
        print("   Ubuntu: sudo systemctl start mongod")
        print("\n3. Kiểm tra MongoDB đang chạy:")
        print("   Windows: tasklist /FI \"IMAGENAME eq mongod.exe\"")
        print("   macOS/Linux: ps aux | grep mongod")
        print("\n4. Kiểm tra port MongoDB:")
        print("   netstat -an | grep 27017")
        print("\n5. Thử khởi động MongoDB thủ công:")
        print("   mongod --dbpath C:\\data\\db  (Windows)")
        print("   mongod --dbpath /usr/local/var/mongodb  (macOS)")
        print("   mongod --dbpath /var/lib/mongodb  (Linux)")
        print("\n6. Kiểm tra MongoDB shell:")
        print("   mongosh  (hoặc mongo với phiên bản cũ)")
        
        return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    if success:
        print(f"\n🚀 MongoDB sẵn sàng! Bạn có thể chạy ứng dụng chính với: python app.py")
    else:
        print(f"\n🛑 Vui lòng khắc phục vấn đề MongoDB trước khi chạy ứng dụng")

# ===============================

