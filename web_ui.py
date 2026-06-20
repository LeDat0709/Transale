import streamlit as st
import pandas as pd
import time
import os
from sheet_translator import load_dataframe, process_translation, push_to_google_sheet

st.set_page_config(page_title="Translation Tool", page_icon="🚀", layout="wide")

st.title("🚀 Google Sheet Translation Tool")
st.markdown("Công cụ tự động dịch Google Sheet và bắn dữ liệu trực tiếp lên Sheet đích.")

# Sidebar: Cấu hình
with st.sidebar:
    st.header("⚙️ Cấu Hình")
    engine_choice = st.radio(
        "Phương thức dịch:",
        (1, 2),
        format_func=lambda x: "LibreTranslate (VPS Local)" if x == 1 else "Google Translate (Cloud)",
        index=1
    )
    
    st.markdown("---")
    auto_push = st.checkbox("Bắn dữ liệu lên Sheet đích sau khi dịch?", value=True)

# Main UI
st.subheader("1. Nguồn Dữ Liệu")
source_input = st.text_input("🔗 Link Google Sheet GỐC (Hoặc đường dẫn file CSV cục bộ):", placeholder="https://docs.google.com/spreadsheets/d/...")

target_input = ""
if auto_push:
    target_input = st.text_input("🎯 Link Google Sheet ĐÍCH:", placeholder="https://docs.google.com/spreadsheets/d/...")

if 'df' not in st.session_state:
    st.session_state.df = None
if 'columns' not in st.session_state:
    st.session_state.columns = []

if st.button("📥 Tải Dữ Liệu / Load Columns"):
    if not source_input:
        st.warning("Vui lòng nhập link nguồn!")
    else:
        try:
            with st.spinner("Đang tải dữ liệu..."):
                df = load_dataframe(source_input)
                st.session_state.df = df
                st.session_state.columns = df.columns.tolist()
            st.success(f"Đã tải thành công {len(df)} dòng dữ liệu!")
        except Exception as e:
            st.error(f"Lỗi tải dữ liệu: {e}")

if st.session_state.columns:
    st.subheader("2. Chọn Cột Cần Dịch")
    selected_cols = st.multiselect("Chọn các cột muốn dịch:", options=st.session_state.columns)
    
    if selected_cols:
        st.subheader("3. Tiến Hành Dịch")
        
        col1, col2 = st.columns([1, 5])
        start_btn = col1.button("▶️ Bắt Đầu Dịch", type="primary")
        stop_btn = col2.button("⏹️ Dừng / Lưu Checkpoint")
        
        if 'is_running' not in st.session_state:
            st.session_state.is_running = False
            
        if stop_btn:
            st.session_state.is_running = False
            st.warning("Đã ghi nhận lệnh dừng. Đang lưu Checkpoint...")
            
        if start_btn:
            st.session_state.is_running = True
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(current, total, text):
                progress_bar.progress(current / total)
                status_text.text(text)
                
            def check_cancel():
                # Trong luồng đồng bộ của Streamlit, nút Dừng khó nhận ngay lập tức, 
                # nhưng ta để sẵn cơ chế nếu sau này dùng Threading.
                return not st.session_state.is_running

            with st.spinner("Đang chạy dịch thuật..."):
                try:
                    df_result, success = process_translation(
                        st.session_state.df, 
                        selected_cols, 
                        engine_choice=engine_choice,
                        progress_callback=progress_callback,
                        check_cancel=check_cancel
                    )
                    
                    if success:
                        st.success("🎉 Dịch hoàn tất!")
                        st.balloons()
                        
                        if auto_push and target_input:
                            with st.spinner("Đang bắn dữ liệu lên Sheet đích..."):
                                push_to_google_sheet(df_result, target_input)
                                st.success("✅ Đã bắn dữ liệu thành công!")
                    else:
                        st.warning("Đã dừng tiến trình và lưu checkpoint!")
                        
                except Exception as e:
                    st.error(f"Lỗi trong quá trình dịch: {e}")
            
            st.session_state.is_running = False
