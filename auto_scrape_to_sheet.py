import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import os
import sys
import io
import time
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Ép console dùng UTF-8 trên Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# ----- CẤU HÌNH -----
TARGET_LANG = 'de' # Dịch sang tiếng Đức
LINKS_FILE = 'links.txt'
TOKEN_FILE = 'token.json'
# Điền sẵn ID Sheet cũ từ translator.py (bạn có thể đổi lại nếu muốn)
SHEET_ID = '1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc'
SHEET_TAB = 'Đạt _ Đức'  # Tên Tab sẽ bắn dữ liệu vào
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def load_google_sheets():
    """Xác thực và kết nối với Google Sheets."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        creds = Credentials(
            token=d.get('token'),
            refresh_token=d.get('refresh_token'),
            token_uri=d.get('token_uri'),
            client_id=d.get('client_id'),
            client_secret=d.get('client_secret'),
            scopes=d.get('scopes') or SCOPES,
        )
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
        else:
            print(f"❌ Lỗi: File {TOKEN_FILE} không hợp lệ hoặc đã hết hạn!")
            sys.exit(1)
            
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def get_text_from_url(url):
    """Cào text từ link."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        if content_div:
            paragraphs = content_div.find_all('p')
        else:
            paragraphs = soup.find_all('p')
            
        story_text = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        title = soup.find('h1').get_text().strip() if soup.find('h1') else 'Untitled_Story'
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        
        return safe_title, story_text
    except Exception as e:
        print(f"   ❌ Lỗi khi đọc {url}: {e}")
        return None, None

def translate_story(text):
    """Dịch text sang tiếng Đức bằng chia nhỏ đoạn."""
    if not text: return ""
    translator = GoogleTranslator(source='auto', target=TARGET_LANG)
    limit = 4500
    if len(text) <= limit:
        try: return translator.translate(text)
        except: return text
        
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
        except:
            translated_chunks.append(chunk)
            
    return "\n\n".join(translated_chunks)

def push_to_sheet(sheets_api, row_data):
    """Thêm một dòng mới vào Sheet."""
    range_name = f"'{SHEET_TAB}'!A:I"
    body = {'values': [row_data]}
    
    try:
        result = sheets_api.values().append(
            spreadsheetId=SHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"   ❌ Lỗi khi đẩy lên Sheet: {e}")
        return False

def main():
    if not os.path.exists(LINKS_FILE):
        print(f"❌ Không tìm thấy file {LINKS_FILE}")
        return
        
    with open(LINKS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith('http')]
        
    if not urls:
        print(f"❌ File {LINKS_FILE} trống!")
        return
        
    print(f"🚀 TÌM THẤY {len(urls)} LINK. ĐANG KẾT NỐI GOOGLE SHEETS...")
    sheets_api = load_google_sheets()
    print("✅ Đã kết nối Sheet thành công!\n")
    
    # Chia thành các nhóm, mỗi nhóm 4 links
    chunked_urls = [urls[i:i + 4] for i in range(0, len(urls), 4)]
    
    for group_idx, url_group in enumerate(chunked_urls):
        print(f"[{group_idx+1}/{len(chunked_urls)}] ĐANG XỬ LÝ NHÓM {len(url_group)} CHAPTERS...")
        
        chapters_translated = ["", "", "", ""]
        brief_text = ""
        
        for i, url in enumerate(url_group):
            print(f"   👉 Cào & Dịch Chapter {i+1}...")
            title, text = get_text_from_url(url)
            if not text: continue
            
            translated = translate_story(text)
            chapters_translated[i] = translated
            
            # Lấy 200 ký tự đầu tiên của Chapter 1 làm Brief
            if i == 0:
                brief_text = (translated[:200] + "...") if len(translated) > 200 else translated
                
        # Dữ liệu 1 hàng: A=Trống, B=Date, C=Brief, D=Status, E=IsProcess, F,G,H,I=Chapters
        date_str = datetime.now().strftime("%H:%M:%S-%d/%m/%Y")
        row_data = [
            "", # Cột 1
            date_str, # DATE
            brief_text, # Brief
            "Hoàn tất content", # Status
            "Done", # Is Processing?
            chapters_translated[0], # Chapter 1 (F)
            chapters_translated[1], # Chapter 2 (G)
            chapters_translated[2], # Chapter 3 (H)
            chapters_translated[3], # Chapter 4 (I)
        ]
        
        print("   ☁️ Đang bắn dữ liệu lên Google Sheet...")
        if push_to_sheet(sheets_api, row_data):
            print("   🎉 Bắn thành công!\n")
        else:
            print("   ❌ Bắn thất bại.\n")
            
if __name__ == "__main__":
    main()
