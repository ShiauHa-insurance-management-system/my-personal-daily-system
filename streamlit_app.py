import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# --- 1. 系統設定與樣式 ---
st.set_page_config(page_title="個人雲端記事本", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; font-weight: bold; background-color: #f0f2f6; }
    .memo-card { padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; background-color: #fff; }
    .anniversary-text { font-size: 1.1rem; color: #e91e63; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

DB_TODO = "notes_todo.csv"
DB_ANNIV = "notes_anniversary.csv"

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

# --- 4. 側邊欄：管理與日子計算器 ---
with st.sidebar:
    st.title("🛠️ 系統控制台")
    if st.button("🔓 安全登出"):
        st.session_state.auth_notes = False
        st.rerun()
    
    st.divider()
    st.subheader("📅 日子計算器")
    d1 = st.date_input("開始日期", date.today())
    d2 = st.date_input("結束日期", date.today())
    if d1 and d2:
        diff = abs((d2 - d1).days)
        st.info(f"相隔總天數：{diff} 天")
    
    st.divider()
    st.subheader("📥 數據備份")
    for db in [DB_TODO, DB_ANNIV]:
        if os.path.exists(db):
            with open(db, "rb") as f:
                st.download_button(f"下載 {db}", f, db, "text/csv")

# --- 5. 主畫面分頁 ---
tab1, tab2 = st.tabs(["📝 待辦事項", "💖 紀念日追蹤"])

# --- 待辦事項分頁 ---
with tab1:
    st.subheader("📌 新增待辦事項")
    with st.form("todo_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        task = col1.text_input("要做什麼事？")
        task_date = col2.date_input("日期", date.today())
        task_time = st.text_input("預定時間 (如：14:30 或 晚上)")
        if st.form_submit_button("加入清單"):
            if task:
                new_todo = pd.DataFrame([{"日期": task_date, "時間": task_time, "內容": task, "狀態": "未完成"}])
                todos = load_data(DB_TODO, ["日期", "時間", "內容", "狀態"])
                pd.concat([todos, new_todo], ignore_index=True).to_csv(DB_TODO, index=False)
                st.rerun()

    st.divider()
    todos = load_data(DB_TODO, ["日期", "時間", "內容", "狀態"])
    if not todos.empty:
        for idx, row in todos.iloc[::-1].iterrows():
            status_color = "🟢" if row['狀態'] == "已完成" else "🔴"
            with st.expander(f"{status_color} {row['日期']} | {row['時間']} | {row['內容']}"):
                new_content = st.text_input("修改內容", row['內容'], key=f"edit_{idx}")
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ 標記完成", key=f"done_{idx}"):
                    todos.at[idx, '狀態'] = "已完成"
                    save_data(todos, DB_TODO); st.rerun()
                if c2.button("💾 儲存修改", key=f"save_{idx}"):
                    todos.at[idx, '內容'] = new_content
                    save_data(todos, DB_TODO); st.rerun()
                if c3.button("🗑️ 刪除事項", key=f"del_t_{idx}"):
                    todos.drop(idx).to_csv(DB_TODO, index=False); st.rerun()

# --- 紀念日分頁 ---
with tab2:
    st.subheader("🌹 紀錄重要紀念日")
    with st.form("anniv_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        a_name = col_a.text_input("紀念日名稱")
        a_date = col_b.date_input("開始日期", date.today())
        if st.form_submit_button("新增紀念日"):
            if a_name:
                new_a = pd.DataFrame([{"名稱": a_name, "日期": a_date}])
                annivs = load_data(DB_ANNIV, ["名稱", "日期"])
                pd.concat([annivs, new_a], ignore_index=True).to_csv(DB_ANNIV, index=False)
                st.rerun()

    st.divider()
    annivs = load_data(DB_ANNIV, ["名稱", "日期"])
    if not annivs.empty:
        for idx, row in annivs.iterrows():
            start_d = datetime.strptime(str(row['日期']), "%Y-%m-%d").date()
            today = date.today()
            
            # 計算時間差
            diff_days = (today - start_d).days
            rd = relativedelta(today, start_d)
            
            with st.container():
                st.markdown(f"### 🎊 {row['名稱']}")
                st.markdown(f"<p class='anniversary-text'>起始日：{row['日期']}</p>", unsafe_allow_html=True)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("已過年數", f"{rd.years} 年")
                m2.metric("已過月數", f"{rd.years * 12 + rd.months} 個月")
                m3.metric("已過總天數", f"{diff_days} 天")
                
                if st.button(f"🗑️ 移除 {row['名稱']}", key=f"del_a_{idx}"):
                    annivs.drop(idx).to_csv(DB_ANNIV, index=False); st.rerun()
                st.divider()