# run_app.py - Script khởi chạy ứng dụng với kiểm tra
import subprocess
import sys
import os

def install_requirements():
    """Cài đặt các package cần thiết"""
    print("📦 Đang cài đặt các package cần thiết...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Cài đặt thành công!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài đặt: {e}")
        return False

def create_directories():
    """Tạo các thư mục cần thiết"""
    directories = ['templates', 'static', 'static/css', 'static/js', 'uploads', 'covers']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Tạo thư mục: {directory}")

def check_mongodb():
    """Kiểm tra MongoDB"""
    print("🔍 Kiểm tra MongoDB...")
    try:
        from test_mongodb import test_mongodb_connection
        return test_mongodb_connection()
    except ImportError:
        print("❌ Không tìm thấy file test_mongodb.py")
        return False

def setup_sample_data():
    """Thiết lập dữ liệu mẫu"""
    print("\n🎯 Thiết lập dữ liệu mẫu...")
    response = input("Bạn có muốn tạo dữ liệu mẫu không? (y/n): ").lower().strip()
    
    if response in ['y', 'yes', 'có']:
        try:
            from create_sample_data import create_sample_data
            return create_sample_data()
        except ImportError:
            print("❌ Không tìm thấy file create_sample_data.py")
            return False
    else:
        print("⏭️  Bỏ qua tạo dữ liệu mẫu")
        return True

def main():
    print("🚀 KHỞI CHẠY ỨNG DỤNG THƯ VIỆN SỐ")
    print("=" * 50)
    
    # Tạo thư mục
    print("📁 Tạo các thư mục cần thiết...")
    create_directories()
    
    # Cài đặt requirements
    if not install_requirements():
        print("❌ Không thể cài đặt các package cần thiết")
        return
    
    # Kiểm tra MongoDB
    if not check_mongodb():
        print("❌ MongoDB chưa sẵn sàng. Vui lòng khắc phục trước khi tiếp tục.")
        return
    
    # Thiết lập dữ liệu mẫu
    if not setup_sample_data():
        print("⚠️  Có lỗi khi thiết lập dữ liệu mẫu, nhưng ứng dụng vẫn có thể chạy")
    
    # Chạy ứng dụng
    print("\n🎯 Khởi chạy ứng dụng...")
    print("🌐 Ứng dụng sẽ chạy tại: http://localhost:5000")
    print("🛑 Nhấn Ctrl+C để dừng ứng dụng")
    print("-" * 50)
    
    try:
        import app
        app.app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Lỗi import app.py: {e}")
        print("💡 Đảm bảo file app.py tồn tại trong cùng thư mục")
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt! Ứng dụng đã dừng")
    except Exception as e:
        print(f"❌ Lỗi khởi chạy: {e}")

if __name__ == "__main__":
    main()