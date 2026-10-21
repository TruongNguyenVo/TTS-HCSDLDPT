"""
database.py - Kết nối & thao tác CSDL SQLite

Các hàm chính:
- init_db(): Tạo bảng và nạp dữ liệu ban đầu nếu chưa có
- get_audio_path(vni_code, speaker_id): Tra cứu đường dẫn file .wav
- get_all_speakers(): Lấy danh sách tất cả giọng đọc
"""

import sqlite3
import os
from datetime import datetime, timezone

# Đường dẫn tuyệt đối đến file database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_connection() -> sqlite3.Connection:
    """Trả về một kết nối đến CSDL SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    conn.execute("PRAGMA foreign_keys = ON")
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

    cursor.execute("""
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
        )
    """)

    # Dọn các bản ghi mẫu bị nhân đôi từ các phiên bản trước.
    cursor.execute("""
        DELETE FROM Audio_Corpus
        WHERE audio_id NOT IN (
            SELECT MIN(audio_id)
            FROM Audio_Corpus
            GROUP BY word_id, speaker_id, file_path
        )
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_audio_corpus_word_speaker_file
        ON Audio_Corpus (word_id, speaker_id, file_path)
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
        - 2 Speaker mặc định
        - 8 từ với mã VNI và đường dẫn file .mav tương ứng
    """
    cursor = conn.cursor()

    # --- Đảm bảo có hai speaker mẫu ---
    cursor.execute(
        "INSERT OR IGNORE INTO Speakers (speaker_id, speaker_name) VALUES (?, ?)",
        (1, "Nguyễn Thành Phát")
    )
    cursor.execute(
        "UPDATE Speakers SET speaker_name = ? WHERE speaker_id = 1",
        ("Nguyễn Thành Phát",)
    )
    cursor.execute(
        "INSERT OR IGNORE INTO Speakers (speaker_id, speaker_name) VALUES (?, ?)",
        (2, "Võ Trường Nguyên")
    )
    speaker_id = 1

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

    inserted_count = 0
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
        inserted_count += cursor.rowcount

    conn.commit()
    print(
        f"[DB] Seed checked {len(sample_words)} sample words; "
        f"inserted {inserted_count} new audio records."
    )


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


def get_audio_candidates(vni_code: str, speaker_id: int) -> list[dict]:
    """Lấy audio của speaker được chọn trước, rồi đến các speaker khác."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT ac.file_path, ac.speaker_id
            FROM Audio_Corpus ac
            JOIN Words w ON ac.word_id = w.word_id
            WHERE w.vni_code = ?
            ORDER BY CASE WHEN ac.speaker_id = ? THEN 0 ELSE 1 END,
                     ac.speaker_id
            """,
            (vni_code, speaker_id),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def record_missing_audio(vni_code: str, speaker_id: int) -> None:
    """Ghi nhận một cặp từ-speaker chưa có audio để bổ sung sau."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        word = conn.execute(
            "SELECT original_word FROM Words WHERE vni_code = ?",
            (vni_code,),
        ).fetchone()
        original_word = word["original_word"] if word else None
        conn.execute(
            """
            INSERT INTO Missing_Audio
                (vni_code, original_word, speaker_id, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(vni_code, speaker_id) DO UPDATE SET
                request_count = request_count + 1,
                last_seen = excluded.last_seen,
                original_word = COALESCE(excluded.original_word, Missing_Audio.original_word),
                status = CASE
                    WHEN Missing_Audio.status = 'completed' THEN 'pending'
                    ELSE Missing_Audio.status
                END
            """,
            (vni_code, original_word, speaker_id, now, now),
        )
        conn.commit()
    finally:
        conn.close()


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


def get_database_snapshot(selected_table: str | None = None) -> dict:
    """Lấy schema và một trang dữ liệu để hiển thị trên trang quản trị CSDL."""
    conn = get_connection()
    try:
        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        table_names = [row["name"] for row in table_rows]

        if not table_names:
            return {"tables": [], "selected_table": None, "columns": [], "rows": [], "total": 0}

        if selected_table not in table_names:
            selected_table = table_names[0]

        quoted_table = '"' + selected_table.replace('"', '""') + '"'
        columns = [
            row["name"]
            for row in conn.execute(
                f"PRAGMA table_info({quoted_table})"
            ).fetchall()
        ]
        total = conn.execute(
            f"SELECT COUNT(*) AS total FROM {quoted_table}"
        ).fetchone()["total"]
        rows = [
            dict(row)
            for row in conn.execute(
                f"SELECT * FROM {quoted_table} LIMIT 100"
            ).fetchall()
        ]

        return {
            "tables": table_names,
            "selected_table": selected_table,
            "columns": columns,
            "rows": rows,
            "total": total,
            "words": [
                dict(row)
                for row in conn.execute(
                    "SELECT word_id, original_word, vni_code FROM Words ORDER BY original_word"
                ).fetchall()
            ],
            "speakers": [
                dict(row)
                for row in conn.execute(
                    "SELECT speaker_id, speaker_name FROM Speakers ORDER BY speaker_name"
                ).fetchall()
            ],
        }
    finally:
        conn.close()


def insert_word(original_word: str, vni_code: str) -> int:
    """Thêm một từ mới và trả về word_id."""
    original_word = original_word.strip()
    vni_code = vni_code.strip()
    if not original_word or not vni_code:
        raise ValueError("Từ gốc và mã VNI không được để trống.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO Words (original_word, vni_code) VALUES (?, ?)",
            (original_word, vni_code),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def insert_audio(
    word_id: int,
    speaker_id: int,
    file_path: str,
    duration_ms: float | None = None,
    pitch_avg: float | None = None,
    energy_avg: float | None = None,
) -> int:
    """Thêm một bản ghi audio vào Audio_Corpus."""
    file_path = file_path.strip()
    if not file_path:
        raise ValueError("Đường dẫn file audio không được để trống.")

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO Audio_Corpus
                (word_id, speaker_id, file_path, duration_ms, pitch_avg, energy_avg)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (word_id, speaker_id, file_path, duration_ms, pitch_avg, energy_avg),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
