# Hệ Thống Chuyển Đổi Văn Bản Thành Âm Thanh (Text-To-Speech - TTS)

Dự án Đề tài 1 môn **Hệ Cơ Sở Dữ Liệu Đa Phương Tiện**: Xây dựng hệ thống chuyển đổi văn bản thành âm thanh ở mức từ (word-level) dựa trên phương pháp tổng hợp ghép nối (Concatenative Synthesis) từ bộ ngữ liệu thu âm song song.

---

## 1. Cấu Trúc Thư Mục Dự Án

```text
tts-project/
├── app/
│   ├── __init__.py
│   ├── database.py         # Kết nối & thao tác CSDL SQLite
│   ├── vni_encoder.py      # Module chuẩn hóa & chuyển đổi văn bản sang mã VNI
│   ├── tts_engine.py       # Engine ghép nối các tệp âm thanh .wav
│   └── main.py             # FastAPI Server & định nghĩa các API Endpoints
├── static/
│   ├── audio_corpus/       # Kho chứa các tệp .wav thu âm gốc (ba0.wav, bac1.wav...)
│   ├── temp_outputs/       # Thư mục lưu tệp .wav kết quả sau khi ghép nối
│   ├── css/
│   │   └── style.css       # Giao diện ứng dụng
│   └── js/
│       └── main.js         # Gửi dữ liệu từ Web UI lên Backend
├── templates/
│   └── index.html          # Giao diện chính (ô nhập liệu & trình phát audio)
├── database.db             # Tệp CSDL SQLite
├── requirements.txt        # Danh sách thư viện Python
└── README.md               # Tài liệu hướng dẫn dự án
```

---

## 2. Thiết Kế Cơ Sở Dữ Liệu (SQLite)

CSDL được thiết kế gồm 3 bảng quan hệ để quản lý ngữ liệu văn bản - âm thanh theo từ, theo người thu âm và các thuộc tính đặc trưng âm thanh:

### Bảng `Words` (Danh mục từ vựng)
| Thuộc tính | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `word_id` | `INTEGER PRIMARY KEY` | Mã từ (Tự tăng) |
| `original_word` | `TEXT UNIQUE` | Từ tiếng Việt gốc (VD: `"bác"`, `"đê"`) |
| `vni_code` | `TEXT UNIQUE` | Mã VNI theo quy ước đề bài (VD: `"bac1"`, `"d-e+"`) |

### Bảng `Speakers` (Thành viên thu âm)
| Thuộc tính | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `speaker_id` | `INTEGER PRIMARY KEY` | Mã người đọc |
| `speaker_name` | `TEXT` | Tên thành viên thu âm trong nhóm |

### Bảng `Audio_Corpus` (Kho âm thanh & Đặc trưng)
| Thuộc tính | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `audio_id` | `INTEGER PRIMARY KEY` | Mã tệp âm thanh |
| `word_id` | `INTEGER FK` | Khóa ngoại liên kết `Words(word_id)` |
| `speaker_id` | `INTEGER FK` | Khóa ngoại liên kết `Speakers(speaker_id)` |
| `file_path` | `TEXT` | Đường dẫn tương đối tệp `.wav` gốc |
| `duration_ms` | `REAL` | Thời lượng tệp âm thanh (ms) |
| `pitch_avg` | `REAL` | Độ cao trung bình (Hz) |
| `energy_avg` | `REAL` | Năng lượng trung bình tín hiệu |

### Bảng `Missing_Audio` (Theo dõi audio còn thiếu)
| Thuộc tính | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `missing_id` | `INTEGER PRIMARY KEY` | Mã yêu cầu thiếu audio |
| `vni_code` | `TEXT` | Mã VNI cần bổ sung |
| `original_word` | `TEXT` | Từ tiếng Việt tương ứng, nếu đã có trong `Words` |
| `speaker_id` | `INTEGER` | Giọng đọc đang được yêu cầu |
| `request_count` | `INTEGER` | Số lần từ này được yêu cầu nhưng chưa có audio |
| `status` | `TEXT` | Trạng thái, mặc định là `pending` |
| `first_seen` | `TEXT` | Thời điểm phát hiện lần đầu |
| `last_seen` | `TEXT` | Thời điểm phát hiện gần nhất |

Khi không có audio của speaker được chọn, hệ thống sẽ tìm audio của speaker khác
làm dự phòng. Cặp `vni_code` và `speaker_id` vẫn được ghi vào `Missing_Audio`
để quản trị viên bổ sung audio đúng giọng đọc sau này. Nếu không có audio ở bất
kỳ speaker nào, từ đó được đưa vào `not_found` và bị bỏ qua khi ghép câu.

---

## 3. Các Module & Hàm Cần Thiết

### 3.1. Module `vni_encoder.py` (Mã hóa VNI)
Thực hiện chuyển đổi chuỗi văn bản tiếng Việt sang chuỗi mã VNI chuẩn quy ước đề bài.

* **`normalize_text(text: str) -> str`**: Làm sạch văn bản, bỏ dấu câu, chuyển về chữ thường.
* **`word_to_vni(word: str) -> str`**: Chuyển đổi 1 từ đơn tiếng Việt sang mã VNI.
  * Quy tắc dấu thanh: `1` (sắc), `2` (huyền), `3` (hỏi), `4` (ngã), `5` (nặng), `0` (không dấu).
  * Quy tắc nguyên âm/phụ âm đặc biệt: `â` -> `a+`, `ô` -> `o+`, `ê` -> `e+`, `ă` -> `aa`, `ơ` -> `oo`, `ư` -> `uu`, `đ` -> `d-`.
* **`encode_sentence(sentence: str) -> list[str]`**: Tách câu thành các từ đơn và trả về danh sách mã VNI.

### 3.2. Module `database.py` (Thao tác CSDL)
Quản lý kết nối và truy vấn CSDL SQLite.

* **`init_db()`**: Tự động tạo bảng và nạp dữ liệu ban đầu nếu chưa có.
* **`get_audio_path(vni_code: str, speaker_id: int) -> str`**: Tra cứu đường dẫn file `.wav` tương ứng với mã VNI và giọng đọc đã chọn.
* **`get_audio_candidates(vni_code: str, speaker_id: int) -> list[dict]`**: Lấy audio của speaker được chọn trước, sau đó đến các speaker khác để dùng dự phòng.
* **`record_missing_audio(vni_code: str, speaker_id: int) -> None`**: Ghi nhận hoặc tăng số lần yêu cầu một audio chưa có.
* **`get_all_speakers() -> list[dict]`**: Lấy danh sách tất cả các giọng đọc để hiển thị trên giao diện.

### 3.3. Module `tts_engine.py` (Xử lý ghép nối âm thanh)
Thực hiện ghép nối các file âm thanh `.wav` bằng thư viện `pydub`.

* **`concatenate_audio(vni_codes: list[str], speaker_id: int) -> str`**:
  1. Gọi `database.py` để lấy danh sách các file `.wav`.
  2. Tạo đoạn âm thanh trống (`AudioSegment.empty()`).
  3. Duyệt tuần tự qua các file `.wav`: ghép âm thanh, chèn khoảng lặng ngắn (50ms silence) giữa các từ và áp dụng kỹ thuật làm mịn (cross-fade 5-10ms).
  4. Xuất file kết quả ra thư mục `static/temp_outputs/output.wav`.
  5. Trả về đường dẫn URL của file âm thanh mới tổng hợp.

### 3.4. Module `main.py` (FastAPI Web Server)
Cung cấp các API RESTful cho Frontend.

* **`GET /`**: Trả về trang chủ `index.html`.
* **`GET /api/speakers`**: Lấy danh sách thành viên thu âm.
* **`POST /api/tts`**: Endpoint nhận JSON `{ "text": "bác ba cảng", "speaker_id": 1 }`, gọi `tts_engine` xử lý và trả về URL file kết quả `{ "audio_url": "/static/temp_outputs/output.wav" }`.

---

## 4. Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install fastapi uvicorn pydub
   ```
2. Khởi chạy server FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Truy cập giao diện tại `http://127.0.0.1:8000` trên trình duyệt.
