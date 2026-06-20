import pandas as pd
import sys

# Change default encoding to utf-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')

print("Reading DE file...")
df_de = pd.read_excel('Tạo Bài Viết + Post WP_DE.xlsx')
print(f"Target shape: {df_de.shape}")

print("Reading Source file...")
df_src = pd.read_excel('Tạo Bài Viết + Post WP.xlsx')

diff_count = 0
for col in df_src.columns:
    if df_src[col].dtype == object:
        # Check how many differ
        same_count = (df_src[col] == df_de[col]).sum()
        total_valid = df_src[col].notna().sum()
        print(f"Column '{col}': {same_count} rows are identical to source (out of {total_valid} valid rows)")
