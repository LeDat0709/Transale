import os
import sys
import io
import time
import json
from deep_translator import GoogleTranslator
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Ép console dùng UTF-8 trên Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# ----- CẤU HÌNH -----
TARGET_LANG = 'de' 
TOKEN_FILE = 'token.json'
SHEET_ID = '1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc'
SOURCE_TAB = 'Đạt _ Đức'
TARGET_TAB = 'Đạt_Mỹ'
START_ROW = 1099
END_ROW = 1196

# Mapping index (0-based) sang ký tự cột trên Google Sheets
COLUMNS_TO_TRANSLATE = {
    2: 'C', # Brief
    5: 'F', # Chapter 1
    6: 'G', # Chapter 2
    7: 'H', # Chapter 3
    8: 'I', # Chapter 4
    9: 'J'  # Prompt Video
}
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def load_google_sheets():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        creds = Credentials(
            token=d.get('token'), refresh_token=d.get('refresh_token'),
            token_uri=d.get('token_uri'), client_id=d.get('client_id'),
            client_secret=d.get('client_secret'), scopes=d.get('scopes') or SCOPES,
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
        else:
            # Không sys.exit() ở đây: ném lỗi rõ ràng để caller bắt được và
            # đẩy lên web console thay vì thoát âm thầm.
            raise RuntimeError(
                f"File {TOKEN_FILE} không hợp lệ hoặc đã hết hạn "
                f"(thiếu token/refresh_token). Hãy tạo lại token.json hợp lệ."
            )
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def translate_long_text(text):
    if not text or not str(text).strip():
        return text
        
    translator = GoogleTranslator(source='auto', target=TARGET_LANG)
    limit = 4500
    if len(text) <= limit:
        try:
            return translator.translate(text)
        except:
            return text
            
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < limit:
            current_chunk += p + "\n\n"
        else:
            if current_chunk.strip(): chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    if current_chunk.strip(): chunks.append(current_chunk.strip())
        
    translated_chunks = []
    for chunk in chunks:
        try:
            translated_chunks.append(translator.translate(chunk))
            time.sleep(1) # Chống ban IP
        except Exception as e:
            translated_chunks.append(chunk)
            
    return "\n\n".join(translated_chunks)

def main(start_row=START_ROW, end_row=END_ROW, source_tab=SOURCE_TAB, target_tab=TARGET_TAB, sheet_id=SHEET_ID, log_callback=None, auto_mode=False, stop_event=None):
    def log(msg, end="\n"):
        print(msg, end=end, flush=True)
        if log_callback: log_callback(msg + end)

    log("🚀 KẾT NỐI GOOGLE SHEETS...")
    sheets_api = load_google_sheets()
    
    current_row = start_row
    
    while True:
        if stop_event and stop_event.is_set():
            log("\n🛑 ĐÃ DỪNG TIẾN TRÌNH.")
            break
            
        # Xác định range cần đọc
        if auto_mode:
            read_range = f"'{source_tab}'!A{current_row}:J{current_row}"
        else:
            if current_row > end_row:
                log(f"\n🎉 HOÀN TẤT DỊCH ĐẾN DÒNG {end_row}!")
                break
            read_range = f"'{source_tab}'!A{current_row}:J{end_row}"
            
        try:
            result = sheets_api.values().get(spreadsheetId=sheet_id, range=read_range).execute()
            rows = result.get('values', [])
        except Exception as e:
            log(f"❌ Lỗi khi đọc dữ liệu: {e}")
            if auto_mode:
                time.sleep(10)
                continue
            else:
                break
                
        if not rows:
            if auto_mode:
                # Không in ra quá nhiều để tránh rác log, cứ ngầm chờ 10s
                time.sleep(10)
                continue
            else:
                log("⚠️ Không có dữ liệu ở khoảng này!")
                break
                
        # Xử lý các dòng tải về
        for idx, row in enumerate(rows):
            if stop_event and stop_event.is_set():
                break
                
            sheet_row_number = current_row + idx
            log(f"\n👉 Đang xử lý Dòng {sheet_row_number} ...")
            
            updates = []
            for col_idx, col_letter in COLUMNS_TO_TRANSLATE.items():
                if col_idx < len(row):
                    original_text = row[col_idx]
                    if original_text and len(original_text.strip()) > 10:
                        log(f"   + Dịch Cột {col_letter} ({len(original_text):,} chars)... ", end="")
                        t0 = time.time()
                        translated = translate_long_text(original_text)
                        t1 = time.time()
                        log(f"Xong ({round(t1-t0, 1)}s)")
                        
                        updates.append({
                            'range': f"'{target_tab}'!{col_letter}{sheet_row_number}",
                            'values': [[translated]]
                        })
                        
            if updates:
                log(f"   ☁️ Đang ghi đè lên Google Sheet ({target_tab})...")
                try:
                    sheets_api.values().batchUpdate(
                        spreadsheetId=sheet_id,
                        body={
                            'valueInputOption': 'RAW',
                            'data': updates
                        }
                    ).execute()
                    log("   ✅ Lưu thành công!")
                except Exception as e:
                    log(f"   ❌ Lỗi lưu dữ liệu: {e}")
            else:
                log("   ⚠️ Không có text để dịch ở dòng này.")
                
            time.sleep(1) # Nghỉ nhẹ để Google không chặn
            
        if stop_event and stop_event.is_set():
            log("\n🛑 ĐÃ DỪNG TIẾN TRÌNH.")
            break
            
        current_row += len(rows)
        
        if not auto_mode:
            log(f"\n🎉 HOÀN TẤT DỊCH TỪ DÒNG {start_row} ĐẾN {end_row}!")
            break

if __name__ == "__main__":
    main()
