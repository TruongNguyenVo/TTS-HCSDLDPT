"""
database.py - Kết nối & thao tác CSDL SQLite

Các hàm chính:
- init_db(): Tạo bảng và nạp dữ liệu ban đầu nếu chưa có
- get_audio_path(vni_code, speaker_id): Tra cứu đường dẫn file .wav
- get_all_speakers(): Lấy danh sách tất cả giọng đọc
"""

import sqlite3
import os

# Đường dẫn tuyệt đối đến file database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_connection() -> sqlite3.Connection:
    """Trả về một kết nối đến CSDL SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    return conn


def init_db():
    """
    Tự động tạo các bảng và nạp dữ liệu ban đầu nếu chưa có.
    Được gọi một lần khi khởi động ứng dụng.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # --- Tạo bảng Words ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Words (
            word_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            original_word TEXT    NOT NULL,
            vni_code      TEXT    UNIQUE NOT NULL
        )
    """)

    # --- Tạo bảng Speakers ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Speakers (
            speaker_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            speaker_name TEXT    NOT NULL
        )
    """)

    # --- Tạo bảng Audio_Corpus ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Audio_Corpus (
            audio_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id    INTEGER NOT NULL,
            speaker_id INTEGER NOT NULL,
            file_path  TEXT    NOT NULL,
            duration_ms REAL,
            pitch_avg   REAL,
            energy_avg  REAL,
            FOREIGN KEY (word_id)    REFERENCES Words(word_id),
            FOREIGN KEY (speaker_id) REFERENCES Speakers(speaker_id)
        )
    """)

    conn.commit()

    # --- Nạp dữ liệu mẫu nếu chưa có ---
    _seed_sample_data(conn)

    conn.close()
    print("[DB] Database initialized successfully!")


def _seed_sample_data(conn: sqlite3.Connection):
    """
    Nạp dữ liệu mẫu ban đầu vào CSDL nếu chưa có dữ liệu.
    Chỉ chạy một lần khi database còn trống.

    Dữ liệu mẫu:
        - 1 Speaker mặc định
        - 8 từ với mã VNI và đường dẫn file .mav tương ứng
    """
    cursor = conn.cursor()

    # Kiểm tra nếu đã có dữ liệu thì bỏ qua
    cursor.execute("SELECT COUNT(*) FROM Speakers")
    if cursor.fetchone()[0] > 0:
        return

    print("[DB] Seeding sample data...")

    # --- Thêm Speaker mặc định ---
    cursor.execute(
        "INSERT INTO Speakers (speaker_name) VALUES (?)",
        ("Giọng mẫu",)
    )
    speaker_id = cursor.lastrowid

    # --- Dữ liệu mẫu: (vni_code, original_word) ---
    sample_words = [
        ("cac1",   "các"),
        ("ban5",   "bạn"),
        ("con0",   "con"),
        ("ca1",    "cá"),
        ("be2",    "bè"),
        ("ba0",    "ba"),
        ("d-ang0", "đang"),
        ("d-i0",   "đi"),
    ]

    for vni_code, original_word in sample_words:
        # Thêm vào bảng Words
        cursor.execute(
            "INSERT OR IGNORE INTO Words (original_word, vni_code) VALUES (?, ?)",
            (original_word, vni_code)
        )
        cursor.execute(
            "SELECT word_id FROM Words WHERE vni_code = ?",
            (vni_code,)
        )
        word_id = cursor.fetchone()[0]

        # file_name = vni_code + ".wav"
        file_path = f"static/audio_corpus/{vni_code}.wav"

        # Thêm vào bảng Audio_Corpus
        cursor.execute(
            """INSERT OR IGNORE INTO Audio_Corpus
               (word_id, speaker_id, file_path, duration_ms, pitch_avg, energy_avg)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (word_id, speaker_id, file_path, None, None, None)
        )

    conn.commit()
    print(f"[DB] Seeded {len(sample_words)} sample words with speaker_id={speaker_id}.")


def get_audio_path(vni_code: str, speaker_id: int) -> str | None:
    """
    Tra cứu đường dẫn file .wav tương ứng với mã VNI và giọng đọc.

    Args:
        vni_code (str): Mã VNI của từ cần tra (VD: "bac1", "ba0")
        speaker_id (int): ID của người thu âm

    Returns:
        str | None: Đường dẫn file .wav hoặc None nếu không tìm thấy
    """
    # TODO: Implement logic truy vấn CSDL
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ac.file_path
        FROM Audio_Corpus ac
        JOIN Words w ON ac.word_id = w.word_id
        WHERE w.vni_code = ? AND ac.speaker_id = ?
        LIMIT 1
    """, (vni_code, speaker_id))

    row = cursor.fetchone()
    conn.close()

    return row["file_path"] if row else None


def get_all_speakers() -> list[dict]:
    """
    Lấy danh sách tất cả các giọng đọc để hiển thị trên giao diện.

    Returns:
        list[dict]: Danh sách dict với keys 'speaker_id' và 'speaker_name'
    """
    # TODO: Implement logic truy vấn CSDL
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT speaker_id, speaker_name FROM Speakers ORDER BY speaker_id")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
