import pandas as pd
from deep_translator import GoogleTranslator
import sys
import concurrent.futures

file_path = "Tạo Bài Viết + Post WP.xlsx"
out_path = "Tạo Bài Viết + Post WP_DE.xlsx"

try:
    df = pd.read_excel(file_path)
except Exception as e:
    print(f"Error reading excel: {e}")
    sys.exit(1)

def translate_text(text):
    if pd.isna(text) or not str(text).strip():
        return text
    text_str = str(text)
    # Instantiate translator inside thread for thread-safety
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

print(f"Start translating {df.shape[0]} rows and {df.shape[1]} columns...")

for col in df.columns:
    if df[col].dtype == object:
        print(f"Translating column: {col} using Multithreading (20 workers)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            df[col] = list(executor.map(translate_text, df[col]))

try:
    df.to_excel(out_path, index=False)
    print(f"Done! Saved to: {out_path}")
except Exception as e:
    print(f"Error saving excel: {e}")
    sys.exit(1)
