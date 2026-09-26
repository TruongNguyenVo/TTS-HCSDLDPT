"""
tts_engine.py - Engine ghép nối các tệp âm thanh .wav

Sử dụng thư viện pydub để xử lý và ghép nối audio.
"""

import os

# TODO: Bỏ comment khi có file âm thanh để test
# from pydub import AudioSegment

from app import database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "temp_outputs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "output.wav")


def concatenate_audio(vni_codes: list[str], speaker_id: int) -> str:
    """
    Ghép nối các file .wav tương ứng với danh sách mã VNI và xuất file kết quả.

    Quy trình:
        1. Gọi database để lấy đường dẫn từng file .wav theo mã VNI & giọng đọc
        2. Tạo AudioSegment rỗng
        3. Duyệt qua từng file: ghép âm thanh + chèn 50ms silence + cross-fade 5-10ms
        4. Xuất file kết quả ra static/temp_outputs/output.wav
        5. Trả về URL của file kết quả

    Args:
        vni_codes (list[str]): Danh sách mã VNI (VD: ["bac1", "ba0", "cang3"])
        speaker_id (int): ID giọng đọc được chọn

    Returns:
        str: URL tương đối của file âm thanh kết quả (VD: "/static/temp_outputs/output.wav")
    """
    # TODO: Implement logic ghép nối audio bằng pydub
    # Placeholder - trả về URL mặc định
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return "/static/temp_outputs/output.wav"
