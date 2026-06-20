import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import os
import time
import sys
import io

# Ép console dùng UTF-8 trên Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

TARGET_LANG = 'de' # Dịch sang tiếng Đức
LINKS_FILE = 'links.txt'
OUTPUT_DIR = 'Translated_Stories'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_text_from_url(url):
    try:
        # Giả lập Browser để không bị chặn
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Thường nội dung chính của WP nằm trong entry-content hoặc article
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        
        # Nếu không có entry-content, lấy toàn bộ thẻ <p>
        if content_div:
            paragraphs = content_div.find_all('p')
        else:
            paragraphs = soup.find_all('p')
            
        # Lọc ra text
        story_text = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Tìm tiêu đề
        title = soup.find('h1').get_text().strip() if soup.find('h1') else 'Untitled_Story'
        # Xoá các ký tự không hợp lệ trong tên file
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        
        return safe_title, story_text
    except Exception as e:
        print(f"❌ Lỗi khi đọc {url}: {e}")
        return None, None

def translate_story(text):
    translator = GoogleTranslator(source='auto', target=TARGET_LANG)
    
    # Chia nhỏ text ra để Google Translate không báo lỗi (Max 5000 ký tự)
    limit = 4500
    if len(text) <= limit:
        return translator.translate(text)
        
    print(f"   (Đoạn văn quá dài: {len(text):,} ký tự. Đang chia nhỏ ra dịch...)")
    chunks = []
    # Cắt theo cụm xuống dòng để tránh đứt câu
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < limit:
            current_chunk += p + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        try:
            res = translator.translate(chunk)
            translated_chunks.append(res)
            # Ngủ 1 giây giữa các chunk để tránh bị Google ban IP
            time.sleep(1)
        except Exception as e:
            print(f"❌ Lỗi khi dịch phần {i+1}: {e}")
            translated_chunks.append(f"[LỖI DỊCH PHẦN NÀY: {e}]")
            
    return "\n\n".join(translated_chunks)

def main():
    if not os.path.exists(LINKS_FILE):
        print(f"❌ Không tìm thấy file {LINKS_FILE}")
        return
        
    with open(LINKS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith('http')]
        
    if not urls:
        print(f"❌ File {LINKS_FILE} trống hoặc không chứa URL hợp lệ.")
        return
        
    print(f"🚀 BẮT ĐẦU CÀO VÀ DỊCH {len(urls)} TRUYỆN 🚀")
    print("-" * 50)
    
    for idx, url in enumerate(urls):
        print(f"[{idx+1}/{len(urls)}] Đang lấy dữ liệu từ: {url}")
        
        # 1. Cào nội dung
        title, story_text = get_text_from_url(url)
        
        if not story_text:
            print("   👉 Bỏ qua do không trích xuất được chữ.")
            continue
            
        print(f"   ✅ Lấy xong: '{title}' ({len(story_text):,} ký tự). Đang tiến hành dịch...")
        
        # 2. Dịch nội dung
        start_time = time.time()
        translated_text = translate_story(story_text)
        end_time = time.time()
        
        # 3. Lưu thành file txt
        output_file = os.path.join(OUTPUT_DIR, f"{title}_DE.txt")
        with open(output_file, 'w', encoding='utf-8') as out_f:
            out_f.write(f"Nguồn: {url}\n\n")
            out_f.write(translated_text)
            
        print(f"   🎉 Đã dịch xong trong {round(end_time - start_time, 1)}s. Đã lưu vào mục '{OUTPUT_DIR}'")
        
        # Ngủ 2s giữa các bài để bảo vệ IP
        time.sleep(2)

if __name__ == "__main__":
    main()
