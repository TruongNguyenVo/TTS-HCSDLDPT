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
            original_word TEXT    UNIQUE NOT NULL,
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
    conn.close()
    print("[DB] Database initialized successfully!")


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
