"""
main.py - FastAPI Server & định nghĩa các API Endpoints

Endpoints:
    GET  /               -> Trả về trang chủ index.html
    GET  /api/speakers   -> Lấy danh sách giọng đọc
    POST /api/tts        -> Tổng hợp âm thanh từ văn bản
"""

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
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


@app.get("/database", response_class=HTMLResponse, summary="Xem dữ liệu CSDL")
async def database_view(request: Request, table: str | None = None):
    """Hiển thị schema và dữ liệu của các bảng trong CSDL SQLite."""
    snapshot = database.get_database_snapshot(table)
    return templates.TemplateResponse(
        request,
        "database.html",
        snapshot,
    )


@app.post("/database/words", summary="Thêm từ vào Words")
async def create_word(
    original_word: str = Form(...),
    vni_code: str = Form(...),
):
    try:
        database.insert_word(original_word, vni_code)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except database.sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Mã VNI đã tồn tại.") from error
    return RedirectResponse("/database?table=Words", status_code=303)


@app.post("/database/audio", summary="Thêm audio vào Audio_Corpus")
async def create_audio(
    word_id: int = Form(...),
    speaker_id: int = Form(...),
    file_path: str = Form(...),
    duration_ms: float | None = Form(None),
    pitch_avg: float | None = Form(None),
    energy_avg: float | None = Form(None),
):
    try:
        database.insert_audio(
            word_id, speaker_id, file_path, duration_ms, pitch_avg, energy_avg
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except database.sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=400,
            detail="word_id hoặc speaker_id không tồn tại.",
        ) from error
    return RedirectResponse("/database?table=Audio_Corpus", status_code=303)


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
    audio_url, not_found, fallback_used = tts_engine.concatenate_audio(
        vni_codes, body.speaker_id
    )
    return {
        "audio_url": audio_url,
        "vni_codes": vni_codes,
        "not_found": not_found,
        "fallback_used": fallback_used,
    }
