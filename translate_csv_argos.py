import os
import sys
import io
import pandas as pd
import argostranslate.package
import argostranslate.translate
import time

# Ép kiểu output thành UTF-8 trên Windows Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

file_path = r"c:\Users\Admin\Downloads\Dịch truyện\Tool_Dich_Sheet\Tạo Bài Viết + Post WP - Đạt _ Đức (2).csv"
out_path = r"c:\Users\Admin\Downloads\Dịch truyện\Tool_Dich_Sheet\Tạo Bài Viết + Post WP - Đạt _ Đức_DE.csv"

from_code = "en"
to_code = "de"

print("=======================================")
print("🚀 KHỞI ĐỘNG ARGOS TRANSLATE (OFFLINE)")
print("=======================================")
print("Đang kiểm tra và tải model dịch (English -> German) nếu chưa có...")

# Tải danh sách các gói ngôn ngữ hiện có
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
installed_packages = argostranslate.package.get_installed_packages()

is_installed = any(pkg.from_code == from_code and pkg.to_code == to_code for pkg in installed_packages)

if not is_installed:
    print("⏳ Chưa có model EN -> DE. Đang tiến hành tải xuống (khoảng ~100MB)... Xin vui lòng chờ.")
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
        )
    )
    argostranslate.package.install_from_path(package_to_install.download())
    print("✅ Tải và cài đặt model hoàn tất!")
else:
    print("✅ Model đã có sẵn trên máy!")

print(f"\n📂 Đang đọc file dữ liệu: {file_path}...")
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"❌ Lỗi khi đọc CSV: {e}")
    sys.exit(1)

def translate_text(text):
    if pd.isna(text) or not str(text).strip():
        return text
    text_str = str(text)
    try:
        if len(text_str) > 4000:
            # Chia nhỏ nếu đoạn văn quá dài
            chunks = [text_str[i:i+4000] for i in range(0, len(text_str), 4000)]
            translated_chunks = [argostranslate.translate.translate(chunk, from_code, to_code) for chunk in chunks]
            return "".join(translated_chunks)
        else:
            return argostranslate.translate.translate(text_str, from_code, to_code)
    except Exception as e:
        print(f"Lỗi dịch: {e}")
        return text_str

columns_to_translate = ['Brief', '(Chapter I)', 'Chapter 2', 'Chapter 3', 'Chaper 4', 'Prompt Video', 'Promt Tạo Ảnh']
cols_to_process = [col for col in columns_to_translate if col in df.columns]

print(f"\n⚡ Bắt đầu dịch {len(df)} dòng.")
print(f"Các cột sẽ dịch: {cols_to_process}")
start_time = time.time()

total_rows = len(df)
for col in cols_to_process:
    print(f"\n👉 Đang dịch cột: {col}...")
    for i in range(total_rows):
        original = df.at[i, col]
        df.at[i, col] = translate_text(original)
        
        # Log tiến độ mỗi 50 dòng
        if (i + 1) % 50 == 0 or (i + 1) == total_rows:
            print(f"   Đã xong {i+1}/{total_rows} dòng.")

end_time = time.time()
print(f"\n⏱️ Tổng thời gian dịch: {round((end_time - start_time) / 60, 2)} phút")

try:
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"🎉 HOÀN TẤT! File đã dịch được lưu tại:\n👉 {out_path}")
except Exception as e:
    print(f"❌ Lỗi khi lưu file: {e}")
    sys.exit(1)
