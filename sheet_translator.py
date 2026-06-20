import os
import re
import sys
import time
import requests
import pandas as pd
import gspread
from tqdm import tqdm

# Cấu hình API LibreTranslate chạy trên VPS
LIBRE_TRANSLATE_URL = "http://localhost:5000/translate"
SOURCE_LANG = "en"
TARGET_LANG = "de"
CHECKPOINT_FILE = "checkpoint.csv"
OUTPUT_FILE = "Translated_Output.csv"
CREDENTIALS_FILE = "credentials.json"

# Global engine choice
TRANSLATION_ENGINE = 1

def convert_google_sheet_url(url):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        raise ValueError("Link Google Sheet không hợp lệ.")
    sheet_id = match.group(1)
    gid_match = re.search(r'gid=([0-9]+)', url)
    gid_param = f"&gid={gid_match.group(1)}" if gid_match else ""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv{gid_param}"

def get_sheet_id(url):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def translate_text(text):
    if pd.isna(text) or not str(text).strip():
        return text 
    
    text_str = str(text)
    
    # Google Translate
    if TRANSLATION_ENGINE == 2:
        from deep_translator import GoogleTranslator
        try:
            translator = GoogleTranslator(source=SOURCE_LANG, target=TARGET_LANG)
            if len(text_str) > 4900:
                chunks = [text_str[i:i+4900] for i in range(0, len(text_str), 4900)]
                translated_chunks = [translator.translate(chunk) for chunk in chunks]
                return "".join(translated_chunks)
            else:
                return translator.translate(text_str)
        except Exception as e:
            return text_str
            
    # LibreTranslate
    payload = {"q": text_str, "source": SOURCE_LANG, "target": TARGET_LANG, "format": "text", "api_key": ""}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):
        try:
            response = requests.post(LIBRE_TRANSLATE_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json().get("translatedText", text_str)
        except:
            time.sleep(2)
    return text_str

def load_token():
    """Tải token OAuth 2.0 từ token.json giống như tool cũ của bạn."""
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    
    TOKEN_FILE = 'token.json'
    if not os.path.exists(TOKEN_FILE):
        return None
        
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        creds = Credentials(
            token=d.get('token'),
            refresh_token=d.get('refresh_token'),
            token_uri=d.get('token_uri'),
            client_id=d.get('client_id'),
            client_secret=d.get('client_secret'),
            scopes=d.get('scopes'),
        )
    except Exception as e:
        print(f"Lỗi đọc token: {e}")
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
        except Exception:
            pass
            
    return creds

def push_to_google_sheet(df, target_url):
    """Bắn dữ liệu từ DataFrame lên Google Sheet Đích"""
    print(f"\n[GOOGLE SHEETS API] Đang kết nối bằng tài khoản Google của bạn (token.json)...")
    try:
        creds = load_token()
        if not creds or not creds.valid:
            print("❌ Token không hợp lệ hoặc đã hết hạn. Vui lòng cấp quyền lại.")
            return
            
        gc = gspread.authorize(creds)
    except Exception as e:
        print(f"❌ Lỗi xác thực tài khoản Google: {e}")
        return

    try:
        sheet_id = get_sheet_id(target_url)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        
        print(f"✅ Đã kết nối tới Sheet: {sh.title}")
        print("⏳ Đang làm sạch sheet cũ và đẩy dữ liệu mới lên...")
        
        worksheet.clear()
        
        # Batch update toàn bộ bảng để không bị limit
        df_to_push = df.fillna('')
        data_to_push = [df_to_push.columns.values.tolist()] + df_to_push.values.tolist()
        
        worksheet.update(values=data_to_push, range_name=None)
        
        print("🎉 ĐÃ BẮN DỮ LIỆU LÊN GOOGLE SHEET THÀNH CÔNG!")
    except Exception as e:
        print(f"❌ Lỗi khi ghi lên Google Sheet đích: {e}")
        print("LƯU Ý: Vui lòng đảm bảo tài khoản Google của bạn có quyền sửa file Sheet này.")

def load_dataframe(sheet_input):
    if sheet_input.startswith('http'):
        csv_export_url = convert_google_sheet_url(sheet_input)
        return pd.read_csv(csv_export_url)
    else:
        return pd.read_csv(sheet_input)

def process_translation(df, selected_columns, engine_choice=2, progress_callback=None, check_cancel=None):
    """
    Hàm dịch chuyên dụng để gọi từ UI.
    - progress_callback(current, total, current_text)
    - check_cancel() -> bool (return True nếu user bấm Stop)
    """
    global TRANSLATION_ENGINE
    TRANSLATION_ENGINE = engine_choice
    
    start_index = 0
    if os.path.exists(CHECKPOINT_FILE):
        try:
            df = pd.read_csv(CHECKPOINT_FILE)
        except:
            pass

    total_rows = len(df)
    
    for index, row in df.iterrows():
        # Kiểm tra Hủy
        if check_cancel and check_cancel():
            df.to_csv(CHECKPOINT_FILE, index=False, encoding='utf-8')
            return df, False # Canceled
            
        for col in selected_columns:
            original_text = row[col]
            if pd.notna(original_text) and str(original_text).strip() != "":
                df.at[index, col] = translate_text(original_text)
        
        # Gọi callback cập nhật UI
        if progress_callback:
            progress_callback(index + 1, total_rows, f"Đang dịch dòng {index + 1}/{total_rows}...")
            
        if (index + 1) % 50 == 0:
            df.to_csv(CHECKPOINT_FILE, index=False, encoding='utf-8')
            
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        
    return df, True # Success

def main():
    print("Vui lòng chạy file web_ui.py bằng lệnh: streamlit run web_ui.py")

if __name__ == "__main__":
    main()
