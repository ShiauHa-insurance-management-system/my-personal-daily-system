import streamlit as st
import pandas as pd
import os
import io
import zipfile
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# --- 1. 系統設定與樣式 ---
st.set_page_config(page_title="個人雲端記事本", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; margin-bottom: 5px; }
    /* 全系統備份按鈕專屬樣式：深藍色背景，白字 */
    .stDownloadButton>button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: bold; 
        background-color: #0d47a1; 
        color: white; 
        border: 2px solid #0d47a1;
        padding: 10px;
    }
    .stDownloadButton>button:hover {
        background-color: #1565c0;
        color: white;
    }
    .anniversary-text { font-size: 1.1rem; color: #e91e63; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 定義資料庫檔案名稱
DB_FILES = {
    "notes_todo.csv": "待辦事項紀錄",
    "notes_anniversary.csv": "紀念日紀錄"
}

# 設定萬年曆極限範圍
MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2100, 12, 31)

# --- 2. 登入驗證 ---
if "auth_notes" not in st.session_state: st.session_state.auth_notes = False
if not st.session_state.auth_notes:
    st.title("🔐 個人記事隱私門禁")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("驗證登入"):
        if pwd == "085799": 
            st.session_state.auth_notes = True
            st.rerun()
        else: st.error("密碼錯誤")
    st.stop()

# --- 3. 核心功能邏輯 ---
def save_data(df, filename):
    df.to_csv(filename, index=False)

def load_data(filename, columns):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columns)

# 打包 ZIP 函數
def create_zip_backup():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for file in DB_FILES.keys():
            if os.path.exists(file):
                zf.write(file)
    return buf.getvalue()

# --- 4. 側邊欄：一鍵全系統備份中心 ---
with st.sidebar:
    st.title("🛠️ 系統控制台")
    
    st.subheader("📥 全系統備份中心")
    st.caption("一鍵打包所有個人紀錄")
    
    # 檢查是否有任何資料檔案存在
    existing_files = [f for f in DB_FILES.keys() if os.path.exists(f)]
    
    if existing_files:
        zip_data = create_zip_backup()
        st.download_button(
            label="🚀 一鍵下載全部資料 (ZIP)",
            data=zip_data,
            file_name=f"full_system_backup_{date.today()}.zip",
            mime="application/zip"
        )
    else:
        st.warning("目前尚無可備份的資料")

    st.divider()
    
    # 日子計算器
    st.subheader("📅 日子計算器")
    sd = st.date_input("開始日期", date.today(), min_value=MIN_DATE, max_value=MAX_DATE, key="calc_start")
    ed = st.date_input("結束日期", date.today(), min_value=MIN_DATE, max_value=MAX_DATE, key="calc_end")
    if sd and ed:
        diff_days = abs((ed - sd).days)
        st.info(f"相隔總天數：{diff_days} 天")
    
    st.divider()
    if st.button("🔓 安全登出"):
        st.session_state.auth_notes = False
        st.rerun()

# --- 5. 主畫面分頁 ---
tab1, tab2 = st.tabs(["📝 待辦事項", "💖 紀念日追蹤"])

with tab1:
    st.subheader("📌 新增待辦事項")
    with st.form("todo_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        task = col1.text_input("要做什麼事？")
        task_date = col2.date_input("選擇日期", date.today(), min_value=MIN_DATE, max_value=MAX_DATE)
        task_time = st.text_input("預定時間")
        if st.form_submit_button("加入清單"):
            if task:
                new_todo = pd.DataFrame([{"日期": task_date, "時間": task_time, "內容": task, "狀態": "未完成"}])
                todos = load_data("notes_todo.csv", ["日期", "時間", "內容", "狀態"])
                pd.concat([todos, new_todo], ignore_index=True).to_csv("notes_todo.csv", index=False)
                st.rerun()

    st.divider()
    todos = load_data("notes_todo.csv", ["日期", "時間", "內容", "狀態"])
    if not todos.empty:
        for idx, row in todos.iloc[::-1].iterrows():
            status_emoji = "✅" if row['狀態'] == "已完成" else "⏳"
            with st.expander(f"{status_emoji} {row['日期']} | {row['內容']}"):
                new_content = st.text_input("修改內容", row['內容'], key=f"edit_todo_{idx}")
                c1, c2, c3 = st.columns(3)
                if c1.button("🆗 完成", key=f"done_{idx}"):
                    todos.at[idx, '狀態'] = "已完成"
                    save_data(todos, "notes_todo.csv"); st.rerun()
                if c2.button("💾 儲存修改", key=f"save_{idx}"):
                    todos.at[idx, '內容'] = new_content
                    save_data(todos, "notes_todo.csv"); st.rerun()
                if c3.button("🗑️ 刪除事項", key=f"del_todo_{idx}"):
                    todos.drop(idx).to_csv("notes_todo.csv", index=False); st.rerun()

with tab2:
    st.subheader("🌹 紀錄重要紀念日")
    with st.form("anniv_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        a_name = col_a.text_input("紀念日名稱")
        a_date = col_b.date_input("起始日期", date.today(), min_value=MIN_DATE, max_value=MAX_DATE)
        if st.form_submit_button("新增紀念日"):
            if a_name:
                new_a = pd.DataFrame([{"名稱": a_name, "日期": a_date}])
                annivs = load_data("notes_anniversary.csv", ["名稱", "日期"])
                pd.concat([annivs, new_a], ignore_index=True).to_csv("notes_anniversary.csv", index=False)
                st.rerun()

    st.divider()
    annivs = load_data("notes_anniversary.csv", ["名稱", "日期"])
    if not annivs.empty:
        for idx, row in annivs.iterrows():
            start_d = datetime.strptime(str(row['日期']), "%Y-%m-%d").date()
            today = date.today()
            diff_days = (today - start_d).days
            rd = relativedelta(today, start_d)
            with st.container():
                st.markdown(f"### 🎊 {row['名稱']}")
                st.markdown(f"<p class='anniversary-text'>📅 起始日：{row['日期']}</p>", unsafe_allow_html=True)
                m1, m2, m3 = st.columns(3)
                m1.metric("已過年數", f"{rd.years} 年")
                m2.metric("已過月數", f"{(rd.years * 12) + rd.months} 個月")
                m3.metric("已過總天數", f"{diff_days:,} 天")
                if st.button(f"🗑️ 移除此紀念日", key=f"del_anniv_{idx}"):
                    annivs.drop(idx).to_csv("notes_anniversary.csv", index=False); st.rerun()
                st.divider()