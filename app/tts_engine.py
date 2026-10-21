"""
tts_engine.py - Engine ghép nối các tệp âm thanh .wav

Sử dụng thư viện pydub để xử lý và ghép nối audio.
"""

import os

import os
from pydub import AudioSegment
from app import database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "temp_outputs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "output.wav")

def concatenate_audio(
    vni_codes: list[str], speaker_id: int
) -> tuple[str, list[str], list[dict]]:
    """
    Ghép nối các file .wav tương ứng với danh sách mã VNI và xuất file kết quả.

    Quy trình:
        1. Gọi database để lấy đường dẫn từng file .wav theo mã VNI & giọng đọc
           và dùng speaker khác làm dự phòng nếu cần
        2. Tạo AudioSegment rỗng
        3. Duyệt qua từng file: ghép âm thanh + chèn 50ms silence + cross-fade 5-10ms
        4. Xuất file kết quả ra static/temp_outputs/output.wav
        5. Trả về URL của file kết quả và danh sách mã VNI không tìm thấy

    Args:
        vni_codes (list[str]): Danh sách mã VNI (VD: ["bac1", "ba0", "cang3"])
        speaker_id (int): ID giọng đọc được chọn

    Returns:
        tuple[str, list[str], list[dict]]: URL, mã VNI không tìm thấy và
            thông tin các audio phải dùng speaker dự phòng
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    final_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=50)
    not_found = []
    fallback_used = []
    
    for vni in vni_codes:
        selected_path = None
        selected_speaker_id = None
        for candidate in database.get_audio_candidates(vni, speaker_id):
            audio_path = candidate["file_path"]
            full_path = (
                os.path.join(BASE_DIR, audio_path)
                if not os.path.isabs(audio_path)
                else audio_path
            )
            if os.path.exists(full_path):
                selected_path = full_path
                selected_speaker_id = candidate["speaker_id"]
                break

        if selected_path is None:
            database.record_missing_audio(vni, speaker_id)
            not_found.append(vni)
            continue

        if selected_speaker_id != speaker_id:
            database.record_missing_audio(vni, speaker_id)
            fallback_used.append({
                "vni_code": vni,
                "requested_speaker_id": speaker_id,
                "actual_speaker_id": selected_speaker_id,
            })

        segment = AudioSegment.from_wav(selected_path)
        
        if len(final_audio) == 0:
            final_audio = segment
        else:
            # Thêm khoảng lặng 50ms và dùng crossfade 10ms để ghép mượt hơn
            final_audio = final_audio.append(silence, crossfade=10)
            final_audio = final_audio.append(segment, crossfade=10)
            
    # Xuất ra file
    if len(final_audio) > 0:
        final_audio.export(OUTPUT_FILE, format="wav")
        
    return "/static/temp_outputs/output.wav", not_found, fallback_used
