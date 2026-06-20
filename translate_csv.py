import pandas as pd
from deep_translator import GoogleTranslator
import sys
import concurrent.futures
import os
import time
import io

# Force UTF-8 for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

file_path = r"c:\Users\Admin\Downloads\Dịch truyện\Tool_Dich_Sheet\Tạo Bài Viết + Post WP - Đạt _ Đức (2).csv"
out_path = r"c:\Users\Admin\Downloads\Dịch truyện\Tool_Dich_Sheet\Tạo Bài Viết + Post WP - Đạt _ Đức_DE.csv"

print(f"Reading file: {file_path}...")
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error reading CSV: {e}")
    sys.exit(1)

def translate_text(text):
    if pd.isna(text) or not str(text).strip():
        return text
    text_str = str(text)
    translator = GoogleTranslator(source='auto', target='de')
    try:
        if len(text_str) > 4900:
            chunks = [text_str[i:i+4900] for i in range(0, len(text_str), 4900)]
            translated_chunks = [translator.translate(chunk) for chunk in chunks]
            return "".join(translated_chunks)
        else:
            return translator.translate(text_str)
    except Exception as e:
        return text_str

columns_to_translate = ['Brief', '(Chapter I)', 'Chapter 2', 'Chapter 3', 'Chaper 4', 'Prompt Video', 'Promt Tạo Ảnh']
cols_to_process = [col for col in columns_to_translate if col in df.columns]

print(f"Start translating {len(df)} rows. Columns: {cols_to_process}")

for col in cols_to_process:
    print(f"Translating column: {col}...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        df[col] = list(executor.map(translate_text, df[col]))

try:
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"DONE! File saved at: {out_path}")
except Exception as e:
    print(f"Error saving file: {e}")
    sys.exit(1)
