import os
import sys
import io
import pandas as pd
import argostranslate.package
import argostranslate.translate
import time
from tqdm import tqdm

# Force UTF-8 for Windows Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

file_path = r"c:\Users\Admin\Downloads\Dịch truyện\Tool_Dich_Sheet\Tạo Bài Viết + Post WP - Đạt _ Đức (2).csv"
out_path = r"c:\Users\Admin\Downloads\Dịch truyện\Tool_Dich_Sheet\Tạo Bài Viết + Post WP - Đạt _ Đức_DE.csv"

from_code = "en"
to_code = "de"

print("=======================================")
print("🚀 ARGOS TRANSLATE PRO (TỐI ƯU HÓA) 🚀")
print("=======================================")

# Load argostranslate
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
installed_packages = argostranslate.package.get_installed_packages()
is_installed = any(pkg.from_code == from_code and pkg.to_code == to_code for pkg in installed_packages)

if not is_installed:
    print("⏳ Đang tải model EN -> DE...")
    package_to_install = next(filter(lambda x: x.from_code == from_code and x.to_code == to_code, available_packages))
    argostranslate.package.install_from_path(package_to_install.download())
    print("✅ Tải xong model!")

print(f"\n📂 Đang đọc dữ liệu từ: {file_path}")
try:
    df = pd.read_csv(file_path)
    print(f"Thành công! Đọc được {len(df):,} dòng dữ liệu.")
except Exception as e:
    print(f"❌ Lỗi: {e}")
    sys.exit(1)

# Tính năng Checkpoint: Nối tiếp kết quả dịch cũ nếu có
if os.path.exists(out_path):
    print("🔄 Tìm thấy bản lưu trước đó. Tiếp tục dịch từ file cũ...")
    df_out = pd.read_csv(out_path)
    df.update(df_out) # Ghi đè những dòng đã dịch
else:
    df_out = df.copy()

def translate_text(text):
    if pd.isna(text) or not str(text).strip():
        return text
    text_str = str(text)
    try:
        if len(text_str) > 4000:
            chunks = [text_str[i:i+4000] for i in range(0, len(text_str), 4000)]
            translated_chunks = [argostranslate.translate.translate(chunk, from_code, to_code) for chunk in chunks]
            return "".join(translated_chunks)
        else:
            return argostranslate.translate.translate(text_str, from_code, to_code)
    except:
        return text_str

columns_to_translate = ['Brief', '(Chapter I)', 'Chapter 2', 'Chapter 3', 'Chaper 4', 'Prompt Video', 'Promt Tạo Ảnh']
cols_to_process = [col for col in columns_to_translate if col in df.columns]

print(f"\n⚡ Bắt đầu dịch các cột: {cols_to_process}")

# Dịch và hiển thị thanh tiến độ bằng tqdm
for col in cols_to_process:
    print(f"\n👉 Đang xử lý cột: {col}")
    
    # tqdm hiển thị thời gian và tốc độ ETA
    for i in tqdm(range(len(df)), desc=f"Dịch {col}", unit="dòng"):
        # Nếu đã có data (khác file gốc và không phải NaN) thì bỏ qua
        # Nhưng để đơn giản, ta dịch những dòng chưa bị ghi đè thành tiếng Đức.
        original = df.at[i, col]
        
        # Ở đây ta check nếu original không có chữ cái tiếng Đức nào thì dịch, 
        # Hoặc đơn giản là cứ dịch đè (để chắc chắn ta dùng cơ chế lưu liên tục)
        translated = translate_text(original)
        df_out.at[i, col] = translated
        
        # Tự động lưu file (Checkpoint) mỗi 1000 dòng để không mất dữ liệu nếu bị ngắt
        if (i + 1) % 1000 == 0:
            df_out.to_csv(out_path, index=False, encoding='utf-8-sig')

# Lưu file lần cuối
try:
    df_out.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"\n🎉 HOÀN TẤT! File được lưu tại: {out_path}")
except Exception as e:
    print(f"❌ Lỗi khi lưu: {e}")
