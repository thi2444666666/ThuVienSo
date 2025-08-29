# app.py - Flask app (FULL) – MongoDB + GridFS, giữ cấu trúc & chức năng cũ,
# tương thích dữ liệu legacy (file_path, cover_image path) và bổ sung API/serve ảnh cần cho templates.

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, session, send_file, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from functools import wraps
from bson import ObjectId
from pymongo import MongoClient
import pymongo
import gridfs
import io
import PyPDF2
import docx

# ==================== APP CONFIG ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'

# Thư mục cũ vẫn giữ để tương thích nếu có dữ liệu legacy
app.config['UPLOAD_FOLDER'] = 'uploads'     # không dùng cho sách mới
app.config['COVER_FOLDER'] = 'covers'       # vẫn có thể dùng cho ảnh bìa cũ
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'epub', 'txt', 'doc', 'docx'}
app.config['ALLOWED_IMAGES'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COVER_FOLDER'], exist_ok=True)


# ==================== MONGODB + GRIDFS ====================
def connect_mongodb():
    try:
        # Tùy máy bạn, chỉnh connection string cho phù hợp
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['digital_library']

        # Indexes
        db.users.create_index("email", unique=True)
        try:
            # Text index cho tìm kiếm
            db.books.create_index([("title", "text"),
                                   ("author", "text"),
                                   ("description", "text")])
        except pymongo.errors.OperationFailure:
            pass

        # GridFS buckets
        fs = gridfs.GridFS(db)  # files: fs.files, fs.chunks
        fs_images = gridfs.GridFS(db, collection="images")  # ảnh bìa: images.files, images.chunks

        print("✅ MongoDB + GridFS sẵn sàng")
        return db, fs, fs_images
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        print("💡 Kiểm tra mongod đã chạy và cổng 27017.")
        raise

db, fs, fs_images = connect_mongodb()


# ==================== HELPERS ====================
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_text_preview(file_bytes, filename, max_chars=800):
    """Trích văn bản để hiển thị preview ngắn (safe)."""
    try:
        ext = filename.lower().split('.')[-1]
        if ext == "pdf":
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages[:3]:
                # .extract_text có thể trả None
                text += (page.extract_text() or "")
            text = text.strip()
            return (text[:max_chars] + "...") if len(text) > max_chars else text
        elif ext in ["doc", "docx"]:
            # python-docx chỉ đọc .docx tốt; .doc có thể không đọc được => fallback
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                text = "\n".join(p.text for p in doc.paragraphs[:30])
            except Exception:
                text = ""
            text = text.strip()
            if not text and ext == "doc":
                return "Không thể tạo xem trước cho file .doc (định dạng cũ)."
            return (text[:max_chars] + "...") if len(text) > max_chars else text
        elif ext == "txt":
            try:
                text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text = file_bytes.decode("latin-1", errors="ignore")
            text = text.strip()
            return (text[:max_chars] + "...") if len(text) > max_chars else text
        else:
            return "Không thể tạo xem trước cho định dạng file này."
    except Exception:
        return "Không thể tạo xem trước."
    

# ==================== AUTH DECORATORS ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        if not user or user.get('role') != 'Admin':
            flash('Bạn không có quyền truy cập trang này', 'error')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ROUTES ====================

@app.route('/')
def index():
    return redirect(url_for('login'))


# ---------- Auth ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        remember = request.form.get('remember', False)

        user = db.users.find_one({"email": email})
        if user and check_password_hash(user['password_hash'], password):
            if user.get('status') == 'Blocked':
                flash('Tài khoản của bạn đã bị khóa', 'error')
                return render_template('login.html')

            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            session['user_role'] = user['role']

            if remember:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)

            return redirect(url_for('admin_dashboard' if user['role'] == 'Admin' else 'user_dashboard'))
        else:
            flash('Email hoặc mật khẩu không đúng', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('register.html')

        if db.users.find_one({"email": email}):
            flash('Email đã được sử dụng', 'error')
            return render_template('register.html')

        user_data = {
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "User",
            "status": "Active",
            "created_at": datetime.now()
        }
        db.users.insert_one(user_data)
        flash('Đăng ký thành công! Vui lòng đăng nhập', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất thành công', 'success')
    return redirect(url_for('login'))


# ---------- Admin ----------
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_books = db.books.count_documents({})
    total_users = db.users.count_documents({})
    today = datetime.now().date()
    downloads_today = db.downloads.count_documents({
        "downloaded_at": {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today, datetime.max.time())
        }
    })
    new_books_today = db.books.count_documents({
        "created_at": {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today, datetime.max.time())
        }
    })
    stats = {
        'total_books': total_books,
        'total_users': total_users,
        'downloads_today': downloads_today,
        'new_books_today': new_books_today
    }
    return render_template('admin_dashboard.html', stats=stats)


@app.route('/admin/books')
@admin_required
def admin_books():
    books = list(db.books.find().sort("created_at", -1))
    return render_template('admin_books.html', books=books)


@app.route('/admin/books/add', methods=['GET', 'POST'])
@admin_required
def admin_add_book():
    """
    Sách mới:
      - Lưu file vào GridFS (field: file_id)
      - Ảnh bìa: ưu tiên GridFS (field: cover_id). Nếu muốn, vẫn cho phép lưu path legacy (cover_image).
      - Lưu preview text để hiển thị nhanh ở trang xem trước (nếu dùng).
    """
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()
        description = request.form['description'].strip()
        published_year = int(request.form['published_year'])

        # File sách -> GridFS
        file = request.files.get('file')
        if not file or not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            flash('File sách không hợp lệ', 'error')
            return render_template('admin_add_book.html')

        file_bytes = file.read()
        file_id = fs.put(
            file_bytes,
            filename=secure_filename(file.filename),
            content_type=getattr(file, "content_type", None)
        )
        preview = extract_text_preview(file_bytes, file.filename)

        # Ảnh bìa -> GridFS (khuyến nghị)
        cover_image = request.files.get('cover_image')
        cover_id = None
        cover_path = None  # legacy path nếu bạn vẫn muốn lưu ra thư mục
        if cover_image and allowed_file(cover_image.filename, app.config['ALLOWED_IMAGES']):
            try:
                # Lưu vào GridFS ảnh
                cover_id = fs_images.put(
                    cover_image.read(),
                    filename=secure_filename(cover_image.filename),
                    content_type=getattr(cover_image, "content_type", None)
                )
            except Exception:
                cover_id = None
            # Nếu muốn đồng thời lưu file ảnh ra thư mục (tùy chọn, giữ tương thích)
            try:
                cover_image.stream.seek(0)
                cover_filename = secure_filename(cover_image.filename)
                cover_path = os.path.join(app.config['COVER_FOLDER'], cover_filename)
                cover_image.save(cover_path)
            except Exception:
                cover_path = None

        book_data = {
            "title": title,
            "author": author,
            "description": description,
            "published_year": published_year,
            "file_id": file_id,              # GridFS file
            "cover_id": cover_id,            # GridFS image id (khuyến nghị dùng)
            "cover_image": cover_path,       # legacy path (nếu có)
            "preview": preview,              # text xem trước
            "created_at": datetime.now()
        }

        db.books.insert_one(book_data)
        flash('Thêm sách thành công', 'success')
        return redirect(url_for('admin_books'))

    return render_template('admin_add_book.html')


@app.route('/admin/books/edit/<book_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_book(book_id):
    book = db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        flash('Không tìm thấy sách', 'error')
        return redirect(url_for('admin_books'))

    if request.method == 'POST':
        update_data = {
            "title": request.form['title'].strip(),
            "author": request.form['author'].strip(),
            "description": request.form['description'].strip(),
            "published_year": int(request.form['published_year'])
        }

        # Ảnh bìa mới (GridFS)
        cover_image = request.files.get('cover_image')
        if cover_image and allowed_file(cover_image.filename, app.config['ALLOWED_IMAGES']):
            # lưu ảnh mới vào GridFS
            try:
                new_cover_id = fs_images.put(
                    cover_image.read(),
                    filename=secure_filename(cover_image.filename),
                    content_type=getattr(cover_image, "content_type", None)
                )
                update_data["cover_id"] = new_cover_id
            except Exception:
                pass

            # xóa cover GridFS cũ nếu có
            if book.get("cover_id"):
                try:
                    fs_images.delete(ObjectId(book["cover_id"]))
                except Exception:
                    pass

            # tùy chọn: lưu ra thư mục legacy
            try:
                cover_image.stream.seek(0)
                cover_filename = secure_filename(cover_image.filename)
                cover_path = os.path.join(app.config['COVER_FOLDER'], cover_filename)
                cover_image.save(cover_path)
                update_data["cover_image"] = cover_path
            except Exception:
                pass

        db.books.update_one({"_id": ObjectId(book_id)}, {"$set": update_data})
        flash('Cập nhật sách thành công', 'success')
        return redirect(url_for('admin_books'))

    return render_template('admin_edit_book.html', book=book)


@app.route('/admin/books/delete/<book_id>')
@admin_required
def admin_delete_book(book_id):
    book = db.books.find_one({"_id": ObjectId(book_id)})
    if book:
        # Xóa file sách từ GridFS
        try:
            if book.get('file_id'):
                fs.delete(ObjectId(book['file_id']))
        except Exception as e:
            print(f"Lỗi xóa file GridFS: {e}")

        # Xóa ảnh bìa GridFS
        try:
            if book.get('cover_id'):
                fs_images.delete(ObjectId(book['cover_id']))
        except Exception:
            pass

        # Xóa file cũ theo đường dẫn (nếu legacy)
        if book.get('file_path') and os.path.exists(book['file_path']):
            try:
                os.remove(book['file_path'])
            except Exception:
                pass

        # Xóa ảnh bìa legacy
        if book.get('cover_image') and os.path.exists(book['cover_image']):
            try:
                os.remove(book['cover_image'])
            except Exception:
                pass

        # Xóa DB + liên quan
        db.books.delete_one({"_id": ObjectId(book_id)})
        db.downloads.delete_many({"book_id": ObjectId(book_id)})
        db.favorites.delete_many({"book_id": ObjectId(book_id)})
        db.reading_history.delete_many({"book_id": ObjectId(book_id)})

        flash('Xóa sách thành công', 'success')
    else:
        flash('Không tìm thấy sách', 'error')

    return redirect(url_for('admin_books'))


@app.route('/admin/users')
@admin_required
def admin_users():
    users = list(db.users.find().sort("created_at", -1))
    return render_template('admin_users.html', users=users)


@app.route('/admin/users/toggle/<user_id>')
@admin_required
def admin_toggle_user(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        new_status = "Blocked" if user.get('status') == "Active" else "Active"
        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": new_status}})
        flash(f'Đã {"khóa" if new_status == "Blocked" else "mở khóa"} tài khoản', 'success')
    return redirect(url_for('admin_users'))


# ---------- User ----------
@app.route('/dashboard')
@login_required
def user_dashboard():
    recent_books = list(db.books.find().sort("created_at", -1).limit(6))

    user_id = ObjectId(session['user_id'])
    favorites = list(db.favorites.find({"user_id": user_id}).limit(5))
    favorite_books = []
    for fav in favorites:
        book = db.books.find_one({"_id": fav['book_id']})
        if book:
            favorite_books.append(book)

    return render_template('user_dashboard.html',
                           recent_books=recent_books,
                           favorite_books=favorite_books)


@app.route('/search')
@login_required
def search_books():
    query = request.args.get('q', '')
    year_filter = request.args.get('year', '')

    search_filter = {}
    if query:
        search_filter["$text"] = {"$search": query}
    if year_filter:
        try:
            search_filter["published_year"] = int(year_filter)
        except ValueError:
            pass

    books = list(db.books.find(search_filter))
    return render_template('search_books.html', books=books, query=query)


@app.route('/book/<book_id>')
@login_required
def book_detail(book_id):
    book = db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        flash('Không tìm thấy sách', 'error')
        return redirect(url_for('user_dashboard'))

    # Cập nhật lịch sử đọc
    user_id = ObjectId(session['user_id'])
    db.reading_history.update_one(
        {"user_id": user_id, "book_id": ObjectId(book_id)},
        {"$set": {"updated_at": datetime.now(), "last_page": 1}},
        upsert=True
    )

    is_favorite = db.favorites.find_one({"user_id": user_id, "book_id": ObjectId(book_id)}) is not None

    # Nếu sách có preview đã lưu thì dùng, nếu không thử tạo nhanh (cho dữ liệu cũ)
    preview_text = book.get("preview")
    if not preview_text and book.get("file_id"):
        try:
            file_obj = fs.get(ObjectId(book["file_id"]))
            file_bytes = file_obj.read()
            preview_text = extract_text_preview(file_bytes, file_obj.filename)
        except Exception:
            preview_text = None

    return render_template('book_detail.html', book=book, is_favorite=is_favorite, preview_text=preview_text)

# ---------- Preview (GridFS + fallback legacy) ----------
@app.route('/preview/<book_id>')
@login_required
def preview_book(book_id):
    book = db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        flash('Không tìm thấy sách', 'error')
        return redirect(url_for('user_dashboard'))

    # Ưu tiên GridFS
    if book.get('file_id'):
        try:
            file_obj = fs.get(ObjectId(book['file_id']))
            return send_file(
                io.BytesIO(file_obj.read()),
                download_name=file_obj.filename,
                as_attachment=False   # ✅ preview: không ép tải về
            )
        except gridfs.NoFile:
            flash('File trong GridFS không tồn tại', 'error')
            return redirect(url_for('book_detail', book_id=book_id))

    # Fallback: dữ liệu cũ lưu theo đường dẫn
    file_path = book.get('file_path')
    if file_path and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=False)

    flash('Không tìm thấy file sách', 'error')
    return redirect(url_for('book_detail', book_id=book_id))


# ---------- Ảnh bìa / hình ảnh từ GridFS ----------
@app.route('/cover/<cover_id>')
def get_cover(cover_id):
    """Serve ảnh bìa từ GridFS (images bucket)."""
    try:
        grid_out = fs_images.get(ObjectId(cover_id))
        ct = getattr(grid_out, "content_type", None) or "image/jpeg"
        return send_file(io.BytesIO(grid_out.read()), mimetype=ct)
    except Exception:
        return "Không tìm thấy ảnh bìa", 404


@app.route('/image/<image_id>')
def serve_image(image_id):
    """Alias để tương thích với template dùng /image/<id>."""
    return get_cover(image_id)

# ---------- Download (GridFS + fallback legacy) ----------
@app.route('/download/<book_id>')
@login_required
def download_book(book_id):
    book = db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        flash('Không tìm thấy sách', 'error')
        return redirect(url_for('user_dashboard'))

    # Log download
    user_id = ObjectId(session['user_id'])
    db.downloads.insert_one({
        "user_id": user_id,
        "book_id": ObjectId(book_id),
        "downloaded_at": datetime.now()
    })

    # Ưu tiên GridFS
    if book.get('file_id'):
        try:
            file_obj = fs.get(ObjectId(book['file_id']))
            return send_file(
                io.BytesIO(file_obj.read()),
                download_name=file_obj.filename,
                as_attachment=True
            )
        except gridfs.NoFile:
            flash('File trong GridFS không tồn tại', 'error')
            return redirect(url_for('book_detail', book_id=book_id))

    # Fallback: dữ liệu cũ lưu theo đường dẫn
    file_path = book.get('file_path')
    if file_path and os.path.isfile(file_path):   # ✅ dùng isfile để chắc chắn
        return send_file(file_path, as_attachment=True)

    flash('Không tìm thấy file sách', 'error')
    return redirect(url_for('book_detail', book_id=book_id))
@app.route('/favorite/<book_id>')
@login_required
def toggle_favorite(book_id):
    user_id = ObjectId(session['user_id'])
    existing = db.favorites.find_one({"user_id": user_id, "book_id": ObjectId(book_id)})

    if existing:
        db.favorites.delete_one({"_id": existing['_id']})
        message = 'Đã bỏ yêu thích'
    else:
        db.favorites.insert_one({
            "user_id": user_id,
            "book_id": ObjectId(book_id),
            "created_at": datetime.now()
        })
        message = 'Đã thêm vào yêu thích'

    flash(message, 'success')
    return redirect(url_for('book_detail', book_id=book_id))


@app.route('/my-library')
@login_required
def my_library():
    user_id = ObjectId(session['user_id'])

    downloads = list(db.downloads.find({"user_id": user_id}).sort("downloaded_at", -1))
    downloaded_books = []
    for d in downloads:
        book = db.books.find_one({"_id": d['book_id']})
        if book:
            downloaded_books.append(book)

    favorites = list(db.favorites.find({"user_id": user_id}).sort("created_at", -1))
    favorite_books = []
    for fav in favorites:
        book = db.books.find_one({"_id": fav['book_id']})
        if book:
            favorite_books.append(book)

    history = list(db.reading_history.find({"user_id": user_id}).sort("updated_at", -1).limit(10))
    history_books = []
    for h in history:
        book = db.books.find_one({"_id": h['book_id']})
        if book:
            history_books.append(book)

    return render_template('my_library.html',
                           downloaded_books=downloaded_books,
                           favorite_books=favorite_books,
                           history_books=history_books)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db.users.find_one({"_id": ObjectId(session['user_id'])})

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_info':
            name = request.form['name'].strip()
            db.users.update_one(
                {"_id": ObjectId(session['user_id'])},
                {"$set": {"name": name}}
            )
            session['user_name'] = name
            flash('Cập nhật thông tin thành công', 'success')

        elif action == 'change_password':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            if not check_password_hash(user['password_hash'], current_password):
                flash('Mật khẩu hiện tại không đúng', 'error')
            elif new_password != confirm_password:
                flash('Mật khẩu xác nhận không khớp', 'error')
            else:
                new_hash = generate_password_hash(new_password)
                db.users.update_one(
                    {"_id": ObjectId(session['user_id'])},
                    {"$set": {"password_hash": new_hash}}
                )
                flash('Đổi mật khẩu thành công', 'success')

        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


# ==================== APIs PHỤ TRỢ ====================

@app.route('/api/books/related/<book_id>')
@login_required
def api_related_books(book_id):
    """Trả về sách cùng tác giả để template load qua fetch (AJAX)."""
    book = db.books.find_one({"_id": ObjectId(book_id)})
    if not book:
        return jsonify([])

    author = book.get("author", "").strip()
    if not author:
        return jsonify([])

    related = list(db.books.find({
        "author": author,
        "_id": {"$ne": ObjectId(book_id)}
    }).sort("created_at", -1).limit(12))

    # Chuẩn hóa field theo template: dùng thumbnail_id (map từ cover_id)
    result = []
    for b in related:
        result.append({
            "id": str(b["_id"]),
            "title": b.get("title", ""),
            "author": b.get("author", ""),
            "thumbnail_id": str(b["cover_id"]) if b.get("cover_id") else None
        })
    return jsonify(result)


@app.route('/api/test-connection')
def test_connection():
    """API kiểm tra MongoDB + thống kê collections + GridFS."""
    try:
        db.command('ping')
        collections = db.list_collection_names()
        stats = {}
        for c in ['users', 'books', 'downloads', 'favorites', 'reading_history']:
            stats[c] = db[c].count_documents({}) if c in collections else 0

        # GridFS stats
        files_count = db.fs.files.count_documents({})
        total_size_cursor = db.fs.files.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$length"}}}
        ])
        total_size_value = 0
        for g in total_size_cursor:
            total_size_value = g.get("total", 0)

        images_count = db.images.files.count_documents({})
        images_size_cursor = db.images.files.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$length"}}}
        ])
        images_total_size = 0
        for g in images_size_cursor:
            images_total_size = g.get("total", 0)

        return jsonify({
            'status': 'success',
            'message': 'Kết nối MongoDB thành công',
            'database': 'digital_library',
            'collections': stats,
            'gridfs': {
                'files_count': files_count,
                'files_total_bytes': total_size_value,
                'images_count': images_count,
                'images_total_bytes': images_total_size
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


# ==================== MAIN ====================
if __name__ == '__main__':
    # Tạo admin mặc định nếu chưa có
    admin_exists = db.users.find_one({"role": "Admin"})
    if not admin_exists:
        admin_data = {
            "name": "Administrator",
            "email": "admin@library.com",
            "password_hash": generate_password_hash("admin123"),
            "role": "Admin",
            "status": "Active",
            "created_at": datetime.now()
        }
        db.users.insert_one(admin_data)
        print("✅ Đã tạo tài khoản admin mặc định:")
        print("   Email: admin@library.com")
        print("   Password: admin123")

    print("🚀 Ứng dụng Thư viện Số (GridFS) đang khởi động...")
    print("📍 Truy cập: http://localhost:5000")
    print("🔧 Test MongoDB: http://localhost:5000/api/test-connection")
    app.run(debug=True, host='0.0.0.0', port=5000)
