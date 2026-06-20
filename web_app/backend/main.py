import os
import sys
import queue
import threading
import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Thêm thư mục gốc vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import translate_sheet_range

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả nguồn gọi tới
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hàng đợi chứa các dòng log để gửi qua SSE
log_queue = queue.Queue()

def log_callback(msg: str):
    log_queue.put(msg)

class TranslateRequest(BaseModel):
    start_row: int
    end_row: int
    source_tab: str
    target_tab: str
    sheet_id: str
    auto_mode: bool = False

# Trạng thái để chặn việc chạy nhiều tiến trình cùng lúc
is_running = False
stop_event = threading.Event()

def run_translation_task(req: TranslateRequest):
    global is_running
    is_running = True
    stop_event.clear()
    try:
        translate_sheet_range.main(
            start_row=req.start_row,
            end_row=req.end_row,
            source_tab=req.source_tab,
            target_tab=req.target_tab,
            sheet_id=req.sheet_id,
            log_callback=log_callback,
            auto_mode=req.auto_mode,
            stop_event=stop_event
        )
    except Exception as e:
        log_callback(f"❌ Lỗi hệ thống: {e}")
    finally:
        is_running = False
        log_callback("[DONE]")

@app.post("/api/translate-range")
def start_translation(req: TranslateRequest, background_tasks: BackgroundTasks):
    global is_running
    if is_running:
        return {"status": "error", "message": "Tiến trình dịch đang chạy, vui lòng chờ."}
    
    # Xóa log cũ
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break
            
    background_tasks.add_task(run_translation_task, req)
    return {"status": "ok", "message": "Đã bắt đầu tiến trình dịch."}

@app.post("/api/stop")
def stop_translation():
    if not is_running:
        return {"status": "error", "message": "Không có tiến trình nào đang chạy."}
    stop_event.set()
    return {"status": "ok", "message": "Đang gửi lệnh dừng tiến trình..."}

@app.get("/api/status")
def get_status():
    return {"is_running": is_running}

@app.get("/api/logs")
async def stream_logs():
    async def event_generator():
        while True:
            try:
                # Dùng asyncio.to_thread để tránh block luồng asyncio
                msg = await asyncio.to_thread(log_queue.get, True, 1.0)
                yield {"data": msg}
                if msg == "[DONE]":
                    break
            except queue.Empty:
                # Nếu hàng đợi rỗng trong 1s, ta cứ yield một event rỗng hoặc comment để giữ kết nối
                yield {"event": "ping", "data": "ping"}
                
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
