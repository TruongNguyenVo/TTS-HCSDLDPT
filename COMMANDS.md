# COMMANDS.md - Lệnh Thường Dùng Trong Dự Án TTS

> Chạy tất cả lệnh từ thư mục gốc dự án: `TTS-HCSDLDPT/`

---

## 1. Khởi Động Server

```bash
# Chạy server với hot-reload (dùng khi dev)
python -m uvicorn app.main:app --reload

# Chạy trên cổng cụ thể (mặc định là 8000)
python -m uvicorn app.main:app --reload --port 8000

# Truy cập ứng dụng tại:
# http://127.0.0.1:8000

# Xem tài liệu API tự động (Swagger UI):
# http://127.0.0.1:8000/docs

# Xem tài liệu API dạng ReDoc:
# http://127.0.0.1:8000/redoc
```

---

## 2. Cài Đặt Thư Viện

```bash
# Cài toàn bộ thư viện từ requirements.txt
pip install -r requirements.txt

# Cài thủ công từng thư viện
pip install fastapi uvicorn[standard] pydub python-multipart jinja2 aiofiles

# Kiểm tra thư viện đã cài
pip list
pip show fastapi
```

---

## 3. Quản Lý Database SQLite

### 3.1. Mở SQLite shell (CLI)

```bash
# Mở file database.db bằng sqlite3 CLI
sqlite3 database.db

# Thoát sqlite3 shell
.quit
```

### 3.2. Xem dữ liệu trong DB

```bash
# Liệt kê tất cả các bảng
sqlite3 database.db ".tables"

# Xem cấu trúc (schema) của từng bảng
sqlite3 database.db ".schema Words"
sqlite3 database.db ".schema Speakers"
sqlite3 database.db ".schema Audio_Corpus"

# Xem toàn bộ dữ liệu từng bảng
sqlite3 database.db "SELECT * FROM Words;"
sqlite3 database.db "SELECT * FROM Speakers;"
sqlite3 database.db "SELECT * FROM Audio_Corpus;"

# Xem dữ liệu theo dạng bảng đẹp hơn
sqlite3 database.db -column -header "SELECT * FROM Words;"
sqlite3 database.db -column -header "SELECT * FROM Speakers;"
sqlite3 database.db -column -header "SELECT * FROM Audio_Corpus;"

# Đếm số bản ghi
sqlite3 database.db "SELECT COUNT(*) FROM Words;"
sqlite3 database.db "SELECT COUNT(*) FROM Audio_Corpus;"
```

### 3.3. Thay đổi cấu trúc DB (Migration thủ công)

```bash
# Thêm cột mới vào bảng (ALTER TABLE)
sqlite3 database.db "ALTER TABLE Audio_Corpus ADD COLUMN sample_rate INTEGER DEFAULT 44100;"

# Xóa và tạo lại DB từ đầu (khi thay đổi lớn)
# CẢNH BÁO: Mất toàn bộ dữ liệu!
del database.db
python -c "from app.database import init_db; init_db()"

# Hoặc dùng Python shell để chạy lại init_db
python -c "from app.database import init_db; init_db()"
```

### 3.4. Nạp dữ liệu mẫu (seed)

```bash
# Chạy script seed dữ liệu (tạo file này khi cần)
python -c "
import sqlite3
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Thêm speakers mẫu
c.execute(\"INSERT OR IGNORE INTO Speakers (speaker_name) VALUES ('Speaker 1')\")
c.execute(\"INSERT OR IGNORE INTO Speakers (speaker_name) VALUES ('Speaker 2')\")

# Thêm từ mẫu
c.execute(\"INSERT OR IGNORE INTO Words (original_word, vni_code) VALUES ('ba', 'ba0')\")
c.execute(\"INSERT OR IGNORE INTO Words (original_word, vni_code) VALUES ('bác', 'bac1')\")

conn.commit()
conn.close()
print('Seed done!')
"
```

---

## 4. Kiểm Tra Nhanh API (bằng curl)

```bash
# Lấy danh sách giọng đọc
curl http://127.0.0.1:8000/api/speakers

# Gọi API tổng hợp âm thanh
curl -X POST http://127.0.0.1:8000/api/tts ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"bac ba cang\", \"speaker_id\": 1}"
```

---

## 5. Git

```bash
# Xem trạng thái
git status

# Commit nhanh
git add .
git commit -m "feat: ..."

# Xem lịch sử commit
git log --oneline -10
```

---

## 6. Tiện Ích Python

```bash
# Kiểm tra phiên bản Python
python --version

# Mở Python shell để test nhanh module
python -c "from app.vni_encoder import encode_sentence; print(encode_sentence('ba bac'))"
python -c "from app.database import get_all_speakers; print(get_all_speakers())"
```
