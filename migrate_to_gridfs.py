#!/usr/bin/env python3
"""
Script chuyển đổi dữ liệu từ file system sang MongoDB GridFS
Chạy script này khi muốn migrate từ hệ thống cũ sang hệ thống mới
"""

import os
import sys
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
import gridfs
from PIL import Image
from io import BytesIO
import PyPDF2
import docx

UPLOADS_DIR = "uploads"   # thư mục chứa sách cũ
COVERS_DIR = "covers"     # thư mục chứa bìa cũ


def connect_mongodb():
    """Kết nối MongoDB"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        client.admin.command('ping')
        print("✅ Kết nối MongoDB thành công")

        db = client['digital_library']
        fs = gridfs.GridFS(db)
        fs_images = gridfs.GridFS(db, collection="images")

        return db, fs, fs_images
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        return None, None, None


def extract_text_preview(file_path, max_chars=500):
    """Trích xuất text preview từ file"""
    try:
        file_ext = file_path.lower().split('.')[-1]

        if file_ext == 'pdf':
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num in range(min(3, len(reader.pages))):
                    text += reader.pages[page_num].extract_text() or ""
                return text[:max_chars] + "..." if len(text) > max_chars else text

        elif file_ext in ['doc', 'docx']:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs[:10]:
                text += paragraph.text + "\n"
            return text[:max_chars] + "..." if len(text) > max_chars else text

        elif file_ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                return content[:max_chars] + "..." if len(content) > max_chars else content

        return "Không thể tạo preview cho định dạng này."

    except Exception as e:
        print(f"Lỗi trích xuất text từ {file_path}: {e}")
        return "Lỗi trích xuất nội dung."


def generate_thumbnail(image_path):
    """Tạo thumbnail từ ảnh"""
    try:
        img = Image.open(image_path)
        img.thumbnail((300, 400), Image.Resampling.LANCZOS)

        thumb_io = BytesIO()
        img.save(thumb_io, format='JPEG', quality=85)
        thumb_io.seek(0)
        return thumb_io
    except Exception as e:
        print(f"Lỗi tạo thumbnail từ {image_path}: {e}")
        return None


# --- Các hàm migrate/cleanup/verify ---


def migrate_books_to_gridfs(db, fs, fs_images):
    """Di chuyển dữ liệu sách và bìa từ filesystem sang GridFS"""
    books = list(db.books.find({"$or": [{"file_path": {"$exists": True}}, {"cover_image": {"$exists": True}}]}))
    print(f"📚 Tìm thấy {len(books)} sách cần migrate")

    for book in books:
        updates = {}

        # --- migrate file chính ---
        if "file_path" in book and os.path.exists(book["file_path"]):
            file_path = book["file_path"]
            try:
                with open(file_path, "rb") as f:
                    file_id = fs.put(f, filename=os.path.basename(file_path))
                updates["file_id"] = file_id
                updates["preview_text"] = extract_text_preview(file_path)
                print(f"   ✅ Đã migrate file cho sách '{book.get('title')}'")

            except Exception as e:
                print(f"   ❌ Lỗi migrate file {file_path}: {e}")

        # --- migrate ảnh bìa ---
        if "cover_image" in book and os.path.exists(book["cover_image"]):
            image_path = book["cover_image"]
            try:
                with open(image_path, "rb") as f:
                    cover_id = fs_images.put(f, filename=os.path.basename(image_path))
                updates["cover_id"] = cover_id
                print(f"   🎨 Đã migrate bìa cho sách '{book.get('title')}'")
            except Exception as e:
                print(f"   ❌ Lỗi migrate bìa {image_path}: {e}")

        # --- cập nhật document ---
        if updates:
            db.books.update_one({"_id": book["_id"]}, {"$set": updates})


def verify_migration(db, fs, fs_images):
    """Xác minh dữ liệu đã migrate thành công"""
    migrated_books = list(db.books.find({"file_id": {"$exists": True}}))
    print(f"🔍 Có {len(migrated_books)} sách đã có file_id trong GridFS")

    # Kiểm tra GridFS thực sự chứa file
    for book in migrated_books[:5]:  # kiểm tra mẫu 5 sách
        try:
            file_id = book["file_id"]
            fs.get(file_id)  # thử lấy file
            print(f"   ✅ File GridFS tồn tại cho sách '{book.get('title')}'")
        except Exception as e:
            print(f"   ❌ Lỗi khi kiểm tra file GridFS cho sách {book.get('_id')}: {e}")


def cleanup_old_files(db):
    """Dọn dẹp đường dẫn file_path và cover_image cũ"""
    result = db.books.update_many({}, {"$unset": {"file_path": "", "cover_image": ""}})
    print(f"🧹 Đã dọn {result.modified_count} record, xóa field file_path và cover_image")


# --- main ---


def main():
    print("🚀 MongoDB GridFS Migration Tool")
    print("=" * 50)

    # Kết nối database
    db, fs, fs_images = connect_mongodb()
    if db is None:
        sys.exit(1)

    try:
        # Thực hiện migration
        migrate_books_to_gridfs(db, fs, fs_images)

        # Kiểm tra tính toàn vẹn
        verify_migration(db, fs, fs_images)

        # Tùy chọn dọn dẹp
        cleanup_old_files(db)

        print("\n🎉 Hoàn thành migration!")
        print("💡 Ứng dụng bây giờ đã tương thích với GridFS (app.py)")

    except KeyboardInterrupt:
        print("\n⏹️  Migration bị hủy bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")


if __name__ == "__main__":
    main()
