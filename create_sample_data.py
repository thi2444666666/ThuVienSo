# create_sample_data.py - Tạo dữ liệu mẫu
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
from bson import ObjectId

def create_sample_data():
    """Tạo dữ liệu mẫu cho ứng dụng"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['digital_library']
        
        print("🎯 Tạo dữ liệu mẫu cho Thư viện Số...")
        
        # Xóa dữ liệu cũ nếu có
        print("🗑️  Xóa dữ liệu cũ...")
        db.users.delete_many({})
        db.books.delete_many({})
        db.downloads.delete_many({})
        db.favorites.delete_many({})
        db.reading_history.delete_many({})
        
        # Tạo users mẫu
        print("👥 Tạo người dùng mẫu...")
        users_data = [
            {
                "name": "Administrator",
                "email": "admin@library.com",
                "password_hash": generate_password_hash("admin123"),
                "role": "Admin",
                "status": "Active",
                "created_at": datetime.now()
            },
            {
                "name": "Nguyễn Văn An",
                "email": "user1@example.com",
                "password_hash": generate_password_hash("user123"),
                "role": "User",
                "status": "Active",
                "created_at": datetime.now() - timedelta(days=10)
            },
            {
                "name": "Trần Thị Bình",
                "email": "user2@example.com",
                "password_hash": generate_password_hash("user123"),
                "role": "User",
                "status": "Active",
                "created_at": datetime.now() - timedelta(days=5)
            },
            {
                "name": "Lê Hoàng Nam",
                "email": "user3@example.com",
                "password_hash": generate_password_hash("user123"),
                "role": "User",
                "status": "Blocked",
                "created_at": datetime.now() - timedelta(days=2)
            }
        ]
        
        user_result = db.users.insert_many(users_data)
        user_ids = user_result.inserted_ids
        print(f"✅ Đã tạo {len(user_ids)} người dùng")
        
        # Tạo books mẫu
        print("📚 Tạo sách mẫu...")
        books_data = [
            {
                "title": "Lập trình Python cơ bản",
                "author": "Nguyễn Văn A",
                "description": "Cuốn sách hướng dẫn lập trình Python từ cơ bản đến nâng cao, phù hợp cho người mới bắt đầu.",
                "published_year": 2023,
                "file_path": "uploads/python_basic.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=30)
            },
            {
                "title": "Khoa học dữ liệu với Python",
                "author": "Trần Thị B",
                "description": "Tìm hiểu về khoa học dữ liệu, machine learning và data analysis với Python.",
                "published_year": 2023,
                "file_path": "uploads/data_science_python.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=25)
            },
            {
                "title": "Web Development với Flask",
                "author": "Lê Văn C",
                "description": "Xây dựng ứng dụng web hiện đại với Flask framework.",
                "published_year": 2022,
                "file_path": "uploads/flask_web_dev.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=20)
            },
            {
                "title": "Cơ sở dữ liệu MongoDB",
                "author": "Phạm Thị D",
                "description": "Hướng dẫn sử dụng MongoDB cho các ứng dụng hiện đại.",
                "published_year": 2023,
                "file_path": "uploads/mongodb_guide.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=15)
            },
            {
                "title": "Trí tuệ nhân tạo và Machine Learning",
                "author": "Hoàng Văn E",
                "description": "Giới thiệu về AI và ML, các thuật toán cơ bản và ứng dụng thực tế.",
                "published_year": 2023,
                "file_path": "uploads/ai_ml_guide.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=10)
            },
            {
                "title": "Docker và Containerization",
                "author": "Vũ Thị F",
                "description": "Tìm hiểu về Docker, containerization và DevOps practices.",
                "published_year": 2022,
                "file_path": "uploads/docker_guide.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=8)
            },
            {
                "title": "JavaScript Modern và React",
                "author": "Đặng Văn G",
                "description": "Học JavaScript ES6+ và phát triển ứng dụng với React.",
                "published_year": 2023,
                "file_path": "uploads/js_react.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=5)
            },
            {
                "title": "Cybersecurity Fundamentals",
                "author": "Ngô Thị H",
                "description": "Các nguyên tắc cơ bản về bảo mật thông tin và an ninh mạng.",
                "published_year": 2023,
                "file_path": "uploads/cybersecurity.pdf",
                "cover_image": None,
                "created_at": datetime.now() - timedelta(days=3)
            }
        ]
        
        book_result = db.books.insert_many(books_data)
        book_ids = book_result.inserted_ids
        print(f"✅ Đã tạo {len(book_ids)} cuốn sách")
        
        # Tạo text search index
        try:
            db.books.create_index([("title", "text"), ("author", "text"), ("description", "text")])
            print("✅ Đã tạo text search index cho books")
        except Exception as e:
            print(f"⚠️  Cảnh báo tạo index: {e}")
        
        # Tạo downloads mẫu
        print("📥 Tạo lượt tải mẫu...")
        download_data = []
        for _ in range(20):
            download_data.append({
                "user_id": random.choice(user_ids[1:]),  # Không tính admin
                "book_id": random.choice(book_ids),
                "downloaded_at": datetime.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            })
        
        db.downloads.insert_many(download_data)
        print(f"✅ Đã tạo {len(download_data)} lượt tải")
        
        # Tạo favorites mẫu
        print("❤️  Tạo danh sách yêu thích mẫu...")
        favorite_data = []
        for user_id in user_ids[1:]:  # Không tính admin
            # Mỗi user yêu thích 2-4 cuốn sách ngẫu nhiên
            num_favorites = random.randint(2, 4)
            favorite_books = random.sample(book_ids, num_favorites)
            
            for book_id in favorite_books:
                favorite_data.append({
                    "user_id": user_id,
                    "book_id": book_id,
                    "created_at": datetime.now() - timedelta(
                        days=random.randint(0, 20),
                        hours=random.randint(0, 23)
                    )
                })
        
        db.favorites.insert_many(favorite_data)
        print(f"✅ Đã tạo {len(favorite_data)} mục yêu thích")
        
        # Tạo reading history mẫu
        print("📖 Tạo lịch sử đọc mẫu...")
        history_data = []
        for user_id in user_ids[1:]:  # Không tính admin
            # Mỗi user có lịch sử đọc 3-6 cuốn sách
            num_history = random.randint(3, 6)
            history_books = random.sample(book_ids, num_history)
            
            for book_id in history_books:
                history_data.append({
                    "user_id": user_id,
                    "book_id": book_id,
                    "last_page": random.randint(1, 50),
                    "updated_at": datetime.now() - timedelta(
                        days=random.randint(0, 15),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                })
        
        db.reading_history.insert_many(history_data)
        print(f"✅ Đã tạo {len(history_data)} mục lịch sử đọc")
        
        # Thống kê tổng quan
        print("\n📊 THỐNG KÊ DỮ LIỆU MẪU:")
        print(f"👥 Users: {db.users.count_documents({})}")
        print(f"📚 Books: {db.books.count_documents({})}")
        print(f"📥 Downloads: {db.downloads.count_documents({})}")
        print(f"❤️  Favorites: {db.favorites.count_documents({})}")
        print(f"📖 Reading History: {db.reading_history.count_documents({})}")
        
        print("\n🔑 THÔNG TIN ĐĂNG NHẬP:")
        print("Admin:")
        print("  Email: admin@library.com")
        print("  Password: admin123")
        print("\nUser mẫu:")
        print("  Email: user1@example.com")
        print("  Password: user123")
        
        print("\n✅ TẠO DỮ LIỆU MẪU HOÀN THÀNH!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tạo dữ liệu mẫu: {e}")
        return False

if __name__ == "__main__":
    create_sample_data()