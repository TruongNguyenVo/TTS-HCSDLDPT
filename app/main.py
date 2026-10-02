"""
main.py - FastAPI Server & định nghĩa các API Endpoints

Endpoints:
    GET  /               -> Trả về trang chủ index.html
    GET  /api/speakers   -> Lấy danh sách giọng đọc
    POST /api/tts        -> Tổng hợp âm thanh từ văn bản
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app import database
from app import vni_encoder
from app import tts_engine

# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(
    title="Hệ Thống TTS Tiếng Việt",
    description="Text-To-Speech sử dụng phương pháp ghép nối (Concatenative Synthesis)",
    version="1.0.0"
)

# --- Mount thư mục static và templates ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Pydantic Model cho request body ---
class TTSRequest(BaseModel):
    text: str
    speaker_id: int = 1


# --- Sự kiện khởi động: khởi tạo CSDL ---
@app.on_event("startup")
async def startup_event():
    database.init_db()
    print("[SERVER] FastAPI TTS Server started successfully!")


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/", response_class=HTMLResponse, summary="Trang chủ")
async def index(request: Request):
    """Trả về trang giao diện chính index.html."""
    speakers = database.get_all_speakers()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"speakers": speakers}
    )


@app.get("/api/speakers", summary="Danh sách giọng đọc")
async def get_speakers():
    """
    Lấy danh sách tất cả người thu âm từ CSDL.

    Returns:
        list[dict]: Danh sách speakers với speaker_id và speaker_name
    """
    speakers = database.get_all_speakers()
    return {"speakers": speakers}


@app.post("/api/tts", summary="Tổng hợp âm thanh")
async def text_to_speech(body: TTSRequest):
    """
    Nhận văn bản, tổng hợp âm thanh và trả về URL file kết quả.

    Request body:
        text (str): Câu tiếng Việt cần chuyển đổi (VD: "bác ba cảng")
        speaker_id (int): ID giọng đọc được chọn (mặc định: 1)

    Returns:
        dict: { "audio_url": "/static/temp_outputs/output.wav" }
    """
    vni_codes = vni_encoder.encode_sentence(body.text)
    audio_url, not_found = tts_engine.concatenate_audio(vni_codes, body.speaker_id)
    return {"audio_url": audio_url, "vni_codes": vni_codes, "not_found": not_found}
