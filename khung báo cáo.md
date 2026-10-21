# TÓM TẮT

Đề tài trình bày việc xây dựng hệ thống chuyển đổi văn bản thành âm thanh (Text-to-Speech — TTS) cho tiếng Việt ở mức từ (word-level), sử dụng phương pháp tổng hợp ghép nối (concatenative synthesis). Hệ thống nhận đầu vào là câu tiếng Việt, chuẩn hóa và mã hóa từng từ theo quy ước bộ gõ VNI, sau đó tra cứu cơ sở dữ liệu SQLite để tìm tệp âm thanh `.wav` tương ứng do các thành viên trong nhóm thu âm. Các tệp âm thanh được ghép nối bằng thư viện `pydub` với kỹ thuật chèn khoảng lặng 50 ms và làm mịn bờ ghép (cross-fade 10 ms) nhằm tạo ra tín hiệu đầu ra liền mạch. Toàn bộ hệ thống được triển khai trên nền tảng Web với FastAPI (backend), SQLite (CSDL) và HTML/CSS/JavaScript (frontend), cho phép người dùng nhập văn bản, chọn giọng đọc, nghe kết quả trực tiếp trên trình duyệt và tải xuống tệp `.wav`. Kết quả thực nghiệm cho thấy âm thanh tổng hợp rõ tiếng ở mức từ đơn, tuy nhiên ngữ điệu liên từ vẫn còn hạn chế so với cách phát âm liền mạch tự nhiên.

---

# 1. ĐẶT VẤN ĐỀ

## 1.1. Bối cảnh & Tầm quan trọng

Tổng hợp giọng nói từ văn bản (Text-to-Speech — TTS) là bài toán quan trọng trong lĩnh vực xử lý ngôn ngữ tự nhiên và đa phương tiện. Công nghệ TTS được ứng dụng rộng rãi trong nhiều lĩnh vực thực tế:

- **Hỗ trợ người khiếm thị**: đọc tài liệu, sách nói, tin tức tự động.
- **Trợ lý ảo & IoT**: tích hợp trong các thiết bị thông minh (Google Assistant, Siri, Alexa) để giao tiếp bằng giọng nói.
- **Giáo dục**: hỗ trợ học phát âm ngoại ngữ, đọc bài cho trẻ em.
- **Truyền thông đa phương tiện**: tự động tạo lời bình cho video, podcast, nội dung kỹ thuật số.

Đối với tiếng Việt — ngôn ngữ có hệ thống thanh điệu phức tạp với 6 thanh (ngang, sắc, huyền, hỏi, ngã, nặng) — bài toán TTS đặt ra thách thức đặc biệt trong việc biểu diễn và xử lý dấu thanh khi mã hóa văn bản thành tín hiệu âm thanh.

## 1.2. Mục tiêu đề tài

Xây dựng hệ thống TTS tiếng Việt ở **mức từ (word-level)** dựa trên bộ ngữ liệu thu âm do chính các thành viên trong nhóm thực hiện. Cụ thể, hệ thống cần đạt được:

1. Thu âm và tổ chức bộ ngữ liệu âm thanh đơn từ tiếng Việt theo giọng đọc từng thành viên.
2. Thiết kế cơ sở dữ liệu SQLite để quản lý quan hệ **từ — âm thanh — người đọc** cùng các đặc trưng trích xuất.
3. Xây dựng module mã hóa văn bản tiếng Việt sang hệ thống mã VNI phục vụ tra cứu.
4. Phát triển engine ghép nối âm thanh từ các file `.wav` đơn từ thành câu hoàn chỉnh.
5. Triển khai giao diện Web cho phép người dùng tương tác trực quan: nhập văn bản → nghe kết quả → tải xuống.

## 1.3. Phạm vi & Phương pháp tiếp cận

Hệ thống sử dụng phương pháp **tổng hợp ghép nối (concatenative synthesis)** — phương pháp cổ điển nhưng hiệu quả cho bài toán TTS mức từ. Ý tưởng cốt lõi: mỗi từ trong câu đầu vào được ánh xạ tới một tệp âm thanh `.wav` đã thu âm sẵn trong kho ngữ liệu, sau đó các tệp được ghép nối tuần tự có xử lý làm mịn biên.

**Phạm vi**:
- Ngữ liệu: tập hợp các từ đơn tiếng Việt thường dùng, thu âm bởi 2 thành viên nhóm.
- Đầu vào: câu tiếng Việt (các từ đã có trong kho ngữ liệu).
- Đầu ra: tệp âm thanh `.wav` tổng hợp.
- Hệ thống hoạt động trên nền Web (trình duyệt), không yêu cầu cài đặt phần mềm phía người dùng.

---

# 2. PHƯƠNG PHÁP NGHIÊN CỨU

## 2.1. Ngữ liệu song song & Quy ước mã hóa VNI

### 2.1.1. Mô tả tập dữ liệu

Tập dữ liệu âm thanh bao gồm các tệp `.wav` thu âm đơn từ tiếng Việt theo giọng đọc của từng thành viên trong nhóm:

| Speaker ID | Tên thành viên    | Vai trò           |
|:----------:|:------------------|:-------------------|
| 1          | Nguyễn Thành Phát | Thu âm giọng đọc 1 |
| 2          | Võ Trường Nguyên  | Thu âm giọng đọc 2 |

Các tệp âm thanh được lưu tại thư mục `static/audio_corpus/` với định dạng WAV (Waveform Audio File Format), đảm bảo chất lượng gốc không nén. Dữ liệu mẫu ban đầu gồm 8 từ cơ bản: *các, bạn, con, cá, bè, ba, đang, đi*.

### 2.1.2. Quy tắc mã hóa VNI

Để ánh xạ giữa từ tiếng Việt có dấu và tên tệp `.wav`, đề tài sử dụng hệ thống mã hóa dựa trên bộ gõ VNI với các quy tắc sau:

**Quy tắc dấu thanh** — thêm số biểu diễn thanh điệu vào cuối mã:

| Số | Thanh điệu | Ví dụ từ | Mã VNI |
|:--:|:-----------|:---------|:-------|
| 0  | Không dấu (ngang) | ba    | `ba0`   |
| 1  | Sắc        | bác      | `bac1`  |
| 2  | Huyền      | bè       | `be2`   |
| 3  | Hỏi        | cảng     | `cang3` |
| 4  | Ngã        | bãi      | `bai4`  |
| 5  | Nặng       | bạn      | `ban5`  |

**Quy tắc nguyên âm & phụ âm đặc biệt** — thay thế các ký tự không thuộc ASCII cơ bản:

| Ký tự gốc | Mã VNI | Ký tự gốc | Mã VNI |
|:----------:|:------:|:----------:|:------:|
| â          | `a+`   | ă          | `aa`   |
| ô          | `o+`   | ơ          | `oo`   |
| ê          | `e+`   | ư          | `uu`   |
| đ          | `d-`   |            |        |

**Ví dụ minh hoạ quá trình mã hóa**:

| Từ tiếng Việt | Phân tích              | Mã VNI   |
|:--------------|:-----------------------|:---------|
| đang          | đ → `d-`, ang, thanh 0 | `d-ang0` |
| đi            | đ → `d-`, i, thanh 0   | `d-i0`   |
| cá            | c, a, thanh 1 (sắc)    | `ca1`    |
| bạn           | b, a, n, thanh 5 (nặng)| `ban5`   |

Module `vni_encoder.py` cài đặt bảng tra `VNI_MAP` chứa đầy đủ ánh xạ cho 67 ký tự nguyên âm có dấu tiếng Việt (bao gồm 6 biến thể thanh điệu cho mỗi nguyên âm: a/á/à/ả/ã/ạ, â/ấ/ầ/ẩ/ẫ/ậ, …) và phụ âm `đ`.

## 2.2. Sơ đồ khối & Quy trình xử lý của hệ thống

### 2.2.1. Sơ đồ khối (Block Diagram)

```
┌──────────────────┐
│  Văn bản đầu vào │  (Ví dụ: "bác ba đang đi")
│  (Câu tiếng Việt)│
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  Chuẩn hóa văn bản       │  normalize_text()
│  • Chuyển chữ thường      │  - Bỏ dấu câu, ký tự đặc biệt
│  • Loại bỏ dấu câu       │  - Chuẩn hóa khoảng trắng
│  • Chuẩn hóa khoảng trắng│
└────────┬─────────────────┘
         │  "bác ba đang đi"
         ▼
┌──────────────────────────┐
│  Mã hóa VNI              │  word_to_vni() cho từng từ
│  • Tách câu thành từ đơn  │  encode_sentence()
│  • Chuyển đổi theo VNI_MAP│
└────────┬─────────────────┘
         │  ["bac1", "ba0", "d-ang0", "d-i0"]
         ▼
┌──────────────────────────┐
│  Tra cứu CSDL SQLite     │  get_audio_candidates()
│  • JOIN Words ↔ Audio_Corpus│
│  • Ưu tiên speaker được chọn│
│  • Fallback sang speaker khác│
└────────┬─────────────────┘
         │  [path1.wav, path2.wav, ...]
         ▼
┌──────────────────────────┐
│  Ghép nối âm thanh (pydub)│  concatenate_audio()
│  • Silence insertion 50ms │
│  • Cross-fade 10ms        │
│  • Export WAV              │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────┐
│  Tín hiệu âm thanh│  /static/temp_outputs/output.wav
│  đầu ra (.wav)    │  → Phát trên trình duyệt / Tải xuống
└──────────────────┘
```

### 2.2.2. Giải thích luồng xử lý

1. **Chuẩn hóa văn bản** (`vni_encoder.normalize_text`): Câu đầu vào được chuyển về chữ thường, loại bỏ tất cả dấu câu và ký tự đặc biệt bằng biểu thức chính quy `re.sub(r'[^\w\s]', '', text)`, chuẩn hóa nhiều khoảng trắng liên tiếp thành một.

2. **Mã hóa VNI** (`vni_encoder.encode_sentence`): Câu được tách thành danh sách từ đơn bằng `split()`. Mỗi từ được chuẩn hóa Unicode dạng NFC qua `unicodedata.normalize('NFC', ...)`, sau đó duyệt từng ký tự qua bảng tra `VNI_MAP` để thay thế nguyên âm có dấu và phụ âm `đ`, cuối cùng gắn mã thanh điệu vào cuối.

3. **Tra cứu CSDL** (`database.get_audio_candidates`): Với mỗi mã VNI, hệ thống thực hiện truy vấn JOIN giữa bảng `Words` và `Audio_Corpus` để tìm đường dẫn tệp `.wav`. Kết quả được sắp xếp ưu tiên: speaker được chọn trước (`CASE WHEN ac.speaker_id = ? THEN 0 ELSE 1 END`), nếu không có thì dùng dự phòng từ speaker khác. Nếu hoàn toàn không có audio, từ đó được ghi nhận vào bảng `Missing_Audio` và bỏ qua khi ghép.

4. **Ghép nối âm thanh** (`tts_engine.concatenate_audio`): Sử dụng thư viện `pydub.AudioSegment` để đọc và ghép các tệp `.wav` tuần tự. Giữa hai từ liên tiếp được chèn khoảng lặng 50 ms (`AudioSegment.silent(duration=50)`) và áp dụng cross-fade 10 ms tại điểm ghép (`append(..., crossfade=10)`) nhằm giảm tiếng "click" và tạo chuyển tiếp mượt mà. File kết quả được xuất ra `static/temp_outputs/output.wav`.

5. **Trả kết quả**: Backend trả về JSON chứa URL tệp âm thanh, danh sách mã VNI đã mã hóa, danh sách từ không tìm thấy (`not_found`) và thông tin các từ phải dùng speaker dự phòng (`fallback_used`). Frontend nhận kết quả, hiển thị trình phát audio và chip mã VNI (đánh dấu đỏ cho từ thiếu audio).

### 2.2.3. Thành phần phần mềm (Công nghệ sử dụng)

| Thành phần  | Công nghệ             | Vai trò                                                                                |
|:------------|:----------------------|:---------------------------------------------------------------------------------------|
| Backend API | **FastAPI** (Python)  | Xử lý yêu cầu HTTP, điều phối luồng TTS, cung cấp RESTful API (`/api/tts`, `/api/speakers`) |
| CSDL        | **SQLite**            | Lưu trữ và quản lý dữ liệu từ vựng, giọng đọc, kho âm thanh và theo dõi audio thiếu   |
| Frontend    | **HTML/CSS/JavaScript** | Giao diện Web tương tác: nhập liệu, chọn giọng đọc, trình phát audio tùy chỉnh         |
| Xử lý audio | **pydub**             | Đọc, ghép nối, chèn silence, cross-fade và xuất tệp `.wav`                              |
| Template    | **Jinja2**            | Render trang HTML động từ server với dữ liệu từ CSDL                                   |

## 2.3. Quản lý và Lưu trữ CSDL

### 2.3.1. Lược đồ quan hệ (ER Diagram)

```
┌─────────────┐       ┌───────────────────┐       ┌──────────────┐
│   Words     │       │   Audio_Corpus    │       │   Speakers   │
├─────────────┤       ├───────────────────┤       ├──────────────┤
│ PK word_id  │──1:N──│ FK word_id        │  N:1──│ PK speaker_id│
│ original_word│      │ FK speaker_id     │       │ speaker_name │
│ vni_code    │       │ PK audio_id       │       └──────────────┘
└─────────────┘       │ file_path         │
                      │ duration_ms       │
                      │ pitch_avg         │
                      │ energy_avg        │
                      └───────────────────┘

┌───────────────────┐
│   Missing_Audio   │
├───────────────────┤
│ PK missing_id     │
│ vni_code          │
│ original_word     │
│ speaker_id        │
│ request_count     │
│ status            │
│ first_seen        │
│ last_seen         │
└───────────────────┘
```

### 2.3.2. Bảng Words (Danh mục từ vựng)

Lưu trữ từ tiếng Việt gốc và mã VNI tương ứng. Cột `vni_code` có ràng buộc `UNIQUE` để đảm bảo mỗi từ chỉ có duy nhất một mã VNI.

```sql
CREATE TABLE IF NOT EXISTS Words (
    word_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    original_word TEXT    NOT NULL,
    vni_code      TEXT    UNIQUE NOT NULL
);
```

### 2.3.3. Bảng Speakers (Thành viên thu âm)

Lưu danh sách các thành viên đã thu âm, phục vụ cho tính năng chọn giọng đọc trên giao diện.

```sql
CREATE TABLE IF NOT EXISTS Speakers (
    speaker_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    speaker_name TEXT    NOT NULL
);
```

### 2.3.4. Bảng Audio_Corpus (Kho âm thanh & Đặc trưng)

Bảng trung tâm liên kết từ vựng với tệp âm thanh thông qua khóa ngoại `word_id` (tham chiếu `Words`) và `speaker_id` (tham chiếu `Speakers`). Ngoài đường dẫn tệp `.wav`, bảng còn lưu các đặc trưng âm thanh được trích xuất.

```sql
CREATE TABLE IF NOT EXISTS Audio_Corpus (
    audio_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id     INTEGER NOT NULL,
    speaker_id  INTEGER NOT NULL,
    file_path   TEXT    NOT NULL,
    duration_ms REAL,
    pitch_avg   REAL,
    energy_avg  REAL,
    FOREIGN KEY (word_id)    REFERENCES Words(word_id),
    FOREIGN KEY (speaker_id) REFERENCES Speakers(speaker_id)
);
```

### 2.3.5. Bảng Missing_Audio (Theo dõi audio còn thiếu)

Bảng tự động ghi nhận các cặp (mã VNI, giọng đọc) chưa có audio khi người dùng yêu cầu. Cơ chế `ON CONFLICT ... DO UPDATE` cho phép đếm số lần yêu cầu (`request_count`) để ưu tiên bổ sung các từ phổ biến nhất.

```sql
CREATE TABLE IF NOT EXISTS Missing_Audio (
    missing_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    vni_code      TEXT NOT NULL,
    original_word TEXT,
    speaker_id    INTEGER NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    status        TEXT NOT NULL DEFAULT 'pending',
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    UNIQUE (vni_code, speaker_id)
);
```

## 2.4. Trích rút đặc trưng & Thuật toán ghép nối âm thanh

### 2.4.1. Đặc trưng âm thanh

Mỗi tệp `.wav` trong kho ngữ liệu có thể được biểu diễn qua các chỉ số đặc trưng sau, lưu trong bảng `Audio_Corpus`:

| Đặc trưng | Trường CSDL | Đơn vị | Ý nghĩa |
|:-----------|:------------|:-------|:---------|
| **Thời lượng** (Duration) | `duration_ms` | ms | Độ dài thời gian phát của đoạn âm thanh |
| **Độ cao** (Pitch) | `pitch_avg` | Hz | Tần số dao động trung bình của dây thanh, phản ánh cao/thấp giọng |
| **Năng lượng** (Energy) | `energy_avg` | dB/RMS | Cường độ tín hiệu trung bình, phản ánh to/nhỏ giọng |

Ngoài ra, trong phân tích và trực quan hóa, có thể sử dụng thêm:
- **Dạng sóng (Waveform)**: biểu đồ biên độ tín hiệu theo thời gian — thể hiện cấu trúc thời gian của âm thanh.
- **Phổ tần (Spectrogram)**: biểu đồ 2D thể hiện phân bố năng lượng theo tần số và thời gian — cho phép nhận diện formant và đặc trưng ngữ âm.

### 2.4.2. Thuật toán ghép nối âm thanh

Quy trình ghép nối được cài đặt trong hàm `concatenate_audio()` của module `tts_engine.py`:

```python
final_audio = AudioSegment.empty()
silence = AudioSegment.silent(duration=50)  # Khoảng lặng 50ms

for vni in vni_codes:
    # Bước 1: Tra cứu tệp .wav qua CSDL (ưu tiên speaker → fallback)
    selected_path = ...  # get_audio_candidates(vni, speaker_id)
    
    # Bước 2: Đọc tệp .wav
    segment = AudioSegment.from_wav(selected_path)
    
    # Bước 3: Ghép nối
    if len(final_audio) == 0:
        final_audio = segment           # Từ đầu tiên
    else:
        # Chèn khoảng lặng 50ms + cross-fade 10ms
        final_audio = final_audio.append(silence, crossfade=10)
        final_audio = final_audio.append(segment, crossfade=10)

# Bước 4: Xuất kết quả
final_audio.export("static/temp_outputs/output.wav", format="wav")
```

**Giải thích các kỹ thuật xử lý**:

- **Chèn khoảng lặng (Silence Insertion — 50 ms)**: Mô phỏng khoảng nghỉ tự nhiên giữa các từ khi nói. Giá trị 50 ms được chọn vì đủ ngắn để không gây cảm giác ngắt quãng, nhưng đủ dài để phân biệt ranh giới từ.

- **Làm mịn bờ ghép (Cross-fading — 10 ms)**: Tại điểm nối giữa hai đoạn audio, kỹ thuật cross-fade tạo vùng chuyển tiếp mượt bằng cách giảm dần biên độ đoạn trước (fade-out) đồng thời tăng dần biên độ đoạn sau (fade-in). Điều này loại bỏ hiện tượng "click" hoặc tiếng giật do sự khác biệt biên độ đột ngột tại điểm ghép.

```
Đoạn trước      Silence 50ms      Đoạn sau
────────╲     ┌────────────┐     ╱────────
         ╲    │            │    ╱
          ╲───┤ cross-fade ├───╱
              │   10ms     │
              └────────────┘
```

**Cơ chế dự phòng (Fallback)**: Khi không tìm thấy audio của speaker được chọn, hệ thống tự động tìm audio từ speaker khác thông qua truy vấn sắp xếp ưu tiên. Thông tin dự phòng được ghi nhận vào `Missing_Audio` để quản trị viên bổ sung sau. Nếu hoàn toàn không có audio cho một từ ở bất kỳ speaker nào, từ đó bị bỏ qua và người dùng được thông báo.

---

# 3. KẾT QUẢ VÀ THẢO LUẬN

## 3.1. Giao diện và Đemo Chương trình

### 3.1.1. Trang chủ — Giao diện tổng hợp TTS

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 1: Trang chủ (trạng thái ban đầu)
    1. Chạy server: uvicorn app.main:app --reload
    2. Mở trình duyệt tại http://127.0.0.1:8000
    3. Chụp toàn bộ trang chủ khi chưa nhập gì (trạng thái mặc định)
    → Hiển thị: Panel "Văn Bản Đầu Vào" (bên trái) và Panel "Kết Quả Âm Thanh" (bên phải)
    → Lưu ảnh vào thư mục báo cáo, ví dụ: images/giao_dien_trang_chu.png
-->

*Hình 1: Giao diện trang chủ hệ thống TTS tiếng Việt*

Giao diện chính được thiết kế theo bố cục hai cột (two-column grid):

- **Panel trái — Văn bản đầu vào**: gồm ô textarea cho phép nhập câu tiếng Việt (tối đa 500 ký tự có đếm realtime), dropdown chọn giọng đọc (hiển thị tên thành viên từ CSDL), thanh trạng thái hiển thị kết quả xử lý, và nút "Chuyển Đổi Thành Âm Thanh".

- **Panel phải — Kết quả âm thanh**: hiển thị placeholder "Âm thanh sẽ xuất hiện ở đây sau khi bạn nhấn Chuyển Đổi" khi chưa có kết quả. Sau khi xử lý thành công, panel chuyển sang hiển thị thanh dạng sóng (waveform bars) có animation, trình phát audio tùy chỉnh với các nút Play/Pause, thanh tiến trình (seek-able), hiển thị thời gian, nút tải xuống, và dãy chip mã VNI.

### 3.1.2. Quá trình tổng hợp âm thanh

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 2: Kết quả tổng hợp thành công
    1. Nhập vào ô text: "các bạn con cá"
    2. Giữ giọng đọc mặc định (Nguyễn Thành Phát)
    3. Nhấn nút "Chuyển Đổi Thành Âm Thanh"
    4. Chờ xử lý xong, chụp hình khi hiện thanh trạng thái "✅ Chuyển đổi thành công!"
    → Cần thấy: trình phát audio, waveform bars, chip VNI (cac1, ban5, con0, ca1)
    → Lưu ảnh: images/ket_qua_thanh_cong.png
-->

*Hình 2: Kết quả tổng hợp thành công với câu "các bạn con cá"*

Khi người dùng nhập văn bản và nhấn nút chuyển đổi:
1. Nút chuyển sang trạng thái loading (hiện spinner, vô hiệu hóa click).
2. Frontend gửi yêu cầu POST đến `/api/tts` với JSON `{"text": "...", "speaker_id": 1}`.
3. Backend xử lý và trả về kết quả.
4. Thanh trạng thái hiển thị "✅ Chuyển đổi thành công!".
5. Panel kết quả hiện trình phát audio với waveform animation và dãy chip mã VNI.

### 3.1.3. Trình phát audio tùy chỉnh

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 3: Trình phát audio đang chơi nhạc
    1. Sau khi chuyển đổi thành công, nhấn nút Play ▶
    2. Chụp hình khi audio đang phát (waveform bars animate, nút đổi thành ⏸)
    → Lưu ảnh: images/trinh_phat_audio.png
-->

*Hình 3: Trình phát audio tùy chỉnh với waveform animation đang phát*

Trình phát audio được xây dựng tùy chỉnh (không dùng controls mặc định của trình duyệt) với các tính năng:
- Nút Play/Pause với chuyển đổi biểu tượng (▶ ↔ ⏸).
- Thanh tiến trình cho phép click để seek đến vị trí bất kỳ.
- Hiển thị thời gian hiện tại và tổng thời lượng (format m:ss).
- Nút tải xuống file `.wav` kết quả.
- Thanh waveform bars có animation khi đang phát.

### 3.1.4. Xử lý từ không có audio

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 4: Trường hợp có từ thiếu audio
    1. Nhập một câu có từ chưa thu âm, ví dụ: "các bạn đang học bài"
       (giả sử "học" và "bài" chưa có trong kho audio)
    2. Nhấn chuyển đổi
    3. Chụp hình khi hiện cảnh báo "⚠ Đã bỏ qua X từ chưa có audio"
    → Cần thấy: chip VNI có màu đỏ cho từ không tìm thấy
    → Lưu ảnh: images/tu_khong_co_audio.png
-->

*Hình 4: Cảnh báo khi có từ chưa có trong kho audio*

Khi gặp từ chưa có audio trong CSDL, hệ thống:
- Hiển thị cảnh báo vàng: "⚠ Đã bỏ qua N từ chưa có audio. Xem bảng Missing_Audio để bổ sung."
- Đánh dấu chip mã VNI tương ứng bằng màu đỏ (nền `#ffebee`, chữ `#d32f2f`).
- Tự động ghi nhận vào bảng `Missing_Audio` trong CSDL.
- Vẫn ghép và phát các từ còn lại (bỏ qua từ thiếu).

### 3.1.5. Trang Database Explorer

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 5: Trang Database Explorer — bảng Words
    1. Truy cập http://127.0.0.1:8000/database
    2. Nhấn chọn bảng "Words" ở sidebar trái
    3. Chụp toàn bộ trang
    → Cần thấy: header, stat cards (số bảng, số bản ghi, số cột), sidebar, bảng dữ liệu
    → Lưu ảnh: images/database_words.png
-->

*Hình 5: Trang Database Explorer — Bảng Words*

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 6: Trang Database Explorer — bảng Audio_Corpus
    1. Nhấn chọn bảng "Audio_Corpus" ở sidebar
    2. Chụp toàn bộ trang
    → Cần thấy: các cột audio_id, word_id, speaker_id, file_path, duration_ms, pitch_avg, energy_avg
    → Lưu ảnh: images/database_audio_corpus.png
-->

*Hình 6: Trang Database Explorer — Bảng Audio_Corpus*

Trang Database Explorer (`/database`) cung cấp giao diện quản trị CSDL trực quan:
- **Tổng quan thống kê**: 3 stat card hiển thị số bảng, số bản ghi trong bảng đang chọn, và số cột.
- **Sidebar chọn bảng**: Danh sách 4 bảng (Audio_Corpus, Missing_Audio, Speakers, Words) cho phép nhấn chuyển đổi.
- **Bảng dữ liệu**: Hiển thị tối đa 100 bản ghi với ô tìm kiếm realtime lọc theo nội dung.
- **Form nhập liệu**: Hai form cho phép thêm từ mới vào bảng `Words` và thêm audio vào `Audio_Corpus` trực tiếp trên giao diện.

<!-- 📸 HƯỚNG DẪN CHỤP HÌNH 7: Form thêm dữ liệu
    1. Cuộn xuống phần form thêm dữ liệu phía dưới trang Database Explorer
    2. Chụp hình cả hai form: "Thêm từ mới" và "Thêm audio corpus"
    → Lưu ảnh: images/database_forms.png
-->

*Hình 7: Form thêm từ mới và thêm audio corpus*

## 3.2. Đánh giá kết quả chất lượng âm thanh

### 3.2.1. Bảng đánh giá

| Tiêu chí           | Mức đánh giá | Ghi chú |
|:--------------------|:-------------|:--------|
| Độ rõ tiếng từng từ | Tốt          | Mỗi từ đơn phát rõ ràng, đúng thanh điệu vì sử dụng audio gốc thu âm |
| Độ tự nhiên liên từ | Trung bình   | Có thể nhận ra ranh giới ghép giữa các từ; ngữ điệu chưa liền mạch |
| Tốc độ xử lý       | Tốt          | Thời gian phản hồi < 1 giây cho câu 5–10 từ |
| Khả năng dự phòng   | Tốt          | Tự động tìm speaker khác khi thiếu audio, thông báo rõ ràng cho người dùng |
| Giao diện người dùng | Tốt         | Trực quan, responsive, có feedback trạng thái realtime |

### 3.2.2. Phân tích ưu/nhược điểm

**Ưu điểm**:
- Chất lượng từng từ đơn **cao và tự nhiên** vì sử dụng trực tiếp audio thu âm gốc, không qua mô hình sinh tổng hợp.
- Hệ thống **dễ mở rộng**: chỉ cần thu âm thêm từ mới, thêm vào CSDL là có thể sử dụng ngay.
- Cơ chế **fallback thông minh**: tự động chuyển sang giọng đọc khác khi thiếu audio, đồng thời ghi nhận để bổ sung sau.
- **Kiến trúc module rõ ràng**: tách biệt encoder, database, engine và API server — dễ bảo trì và phát triển.
- Bảng `Missing_Audio` giúp quản trị viên **ưu tiên thu âm** các từ được yêu cầu nhiều nhất (`request_count`).

**Nhược điểm**:
- **Ngữ điệu liên từ thiếu tự nhiên**: phương pháp ghép nối từ đơn không thể mô phỏng sự biến đổi pitch, cường độ và nhịp điệu giữa các từ trong câu hoàn chỉnh (coarticulation).
- **Phụ thuộc vào kho ngữ liệu**: hệ thống chỉ phát âm được những từ đã có trong CSDL; từ mới hoàn toàn sẽ bị bỏ qua.
- Cross-fade 10 ms giúp giảm hiện tượng "click" nhưng **chưa xử lý được sự chênh lệch pitch và energy** giữa hai từ liền kề từ các lượt thu âm khác nhau.
- Chưa xử lý được **từ ghép, từ đồng âm** và các trường hợp đặc biệt trong tiếng Việt.

---

# 4. KẾT LUẬN VÀ HÀM Ý QUẢN TRỊ

## 4.1. Tóm tắt kết quả

Đề tài đã hoàn thành việc xây dựng hệ thống TTS tiếng Việt mức từ sử dụng phương pháp tổng hợp ghép nối, đáp ứng đầy đủ các yêu cầu đặt ra: (1) Thu âm và tổ chức bộ ngữ liệu âm thanh đơn từ theo quy ước mã hóa VNI; (2) Thiết kế CSDL SQLite gồm 4 bảng quan hệ quản lý từ vựng, giọng đọc, kho âm thanh và theo dõi audio thiếu; (3) Xây dựng module mã hóa VNI hỗ trợ đầy đủ 6 thanh điệu và 7 ký tự đặc biệt tiếng Việt; (4) Cài đặt engine ghép nối với kỹ thuật silence insertion và cross-fade; (5) Triển khai giao diện Web hoàn chỉnh trên nền FastAPI với trình phát audio tùy chỉnh, trang quản trị CSDL và cơ chế dự phòng thông minh. Kết quả cho thấy âm thanh tổng hợp rõ ràng ở mức từ đơn, hệ thống phản hồi nhanh và giao diện trực quan.

## 4.2. Hạn chế & Hướng phát triển

- **Xử lý ngữ điệu liên từ**: Áp dụng kỹ thuật prosody modification (TD-PSOLA, WSOLA) để điều chỉnh pitch và duration giữa các từ, tạo ngữ điệu câu tự nhiên hơn.
- **Mở rộng ngữ liệu**: Tăng số lượng từ thu âm, bổ sung thêm giọng đọc đa dạng (nam/nữ, vùng miền).
- **TTS mức âm vị (phoneme-level)**: Chuyển từ ghép nối mức từ sang mức âm vị/biphone để xử lý được từ hoàn toàn mới chưa thu âm.
- **Tích hợp trích xuất đặc trưng tự động**: Sử dụng thư viện `librosa` để tự động tính duration, pitch, energy khi import audio mới.
- **Tối ưu cross-fade theo đặc trưng**: Điều chỉnh tham số cross-fade dựa trên pitch và energy hai đoạn liền kề để ghép mượt hơn.

---

# Tài liệu tham khảo

1. Taylor, P. (2009). *Text-to-Speech Synthesis*. Cambridge University Press.
2. Dutoit, T. (1997). *An Introduction to Text-to-Speech Synthesis*. Kluwer Academic Publishers.
3. FastAPI Documentation. https://fastapi.tiangolo.com/
4. pydub — Manipulate audio with a simple and easy high level interface. https://github.com/jiaaro/pydub
5. SQLite Documentation. https://www.sqlite.org/docs.html
6. Unicode Consortium. *The Unicode Standard — Vietnamese characters*. https://unicode.org/
7. Nguyễn Hữu Quỳnh. (2001). *Tiếng Việt hiện đại — Ngữ âm, Ngữ pháp, Phong cách*. NXB Giáo dục.

---

# Phụ lục

## A. Hàm mã hóa VNI (`vni_encoder.py`)

### Bảng tra VNI_MAP (trích)

```python
VNI_MAP = {
    # Nguyên âm a (6 thanh điệu)
    'a': ('a', '0'), 'á': ('a', '1'), 'à': ('a', '2'),
    'ả': ('a', '3'), 'ã': ('a', '4'), 'ạ': ('a', '5'),
    # Nguyên âm â (6 thanh điệu)
    'â': ('a+', '0'), 'ấ': ('a+', '1'), 'ầ': ('a+', '2'),
    'ẩ': ('a+', '3'), 'ẫ': ('a+', '4'), 'ậ': ('a+', '5'),
    # ... (tổng cộng 67 ánh xạ cho tất cả nguyên âm tiếng Việt)
    'đ': ('d-', '0')
}
```

### Hàm chuyển đổi từ đơn

```python
def word_to_vni(word: str) -> str:
    word = unicodedata.normalize('NFC', word.lower())
    tone = '0'
    vni_word = ""
    for char in word:
        if char in VNI_MAP:
            base, char_tone = VNI_MAP[char]
            vni_word += base
            if char_tone != '0':
                tone = char_tone
        else:
            vni_word += char
    return vni_word + tone
```

## B. Hàm ghép nối audio (`tts_engine.py`)

```python
def concatenate_audio(vni_codes, speaker_id):
    final_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=50)
    not_found = []
    fallback_used = []

    for vni in vni_codes:
        # Tra cứu CSDL: ưu tiên speaker → fallback speaker khác
        for candidate in database.get_audio_candidates(vni, speaker_id):
            full_path = os.path.join(BASE_DIR, candidate["file_path"])
            if os.path.exists(full_path):
                selected_path = full_path
                break

        if selected_path is None:
            database.record_missing_audio(vni, speaker_id)
            not_found.append(vni)
            continue

        segment = AudioSegment.from_wav(selected_path)

        if len(final_audio) == 0:
            final_audio = segment
        else:
            # Chèn silence 50ms + cross-fade 10ms
            final_audio = final_audio.append(silence, crossfade=10)
            final_audio = final_audio.append(segment, crossfade=10)

    if len(final_audio) > 0:
        final_audio.export(OUTPUT_FILE, format="wav")

    return "/static/temp_outputs/output.wav", not_found, fallback_used
```

## C. Cấu trúc API Endpoints

| Method | Endpoint          | Mô tả                           | Request Body / Params              | Response                                 |
|:-------|:------------------|:---------------------------------|:-----------------------------------|:-----------------------------------------|
| GET    | `/`               | Trang chủ giao diện TTS          | —                                  | HTML (index.html)                        |
| GET    | `/database`       | Trang quản trị CSDL              | `?table=Words`                     | HTML (database.html)                     |
| POST   | `/database/words` | Thêm từ mới vào bảng Words       | Form: `original_word`, `vni_code`  | Redirect → `/database?table=Words`       |
| POST   | `/database/audio` | Thêm audio vào Audio_Corpus      | Form: `word_id`, `speaker_id`, ... | Redirect → `/database?table=Audio_Corpus`|
| GET    | `/api/speakers`   | Danh sách giọng đọc              | —                                  | `{"speakers": [...]}`                    |
| POST   | `/api/tts`        | Tổng hợp âm thanh từ văn bản     | JSON: `{"text": "...", "speaker_id": 1}` | `{"audio_url": "...", "vni_codes": [...], "not_found": [...], "fallback_used": [...]}` |
