import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리 마스터", page_icon="🚀", layout="wide")
st.title("🚀 시험 일정 관리 마스터")

# 2. 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 사용자 식별
with st.sidebar:
    st.header("👤 로그인")
    user_id = st.text_input("이름을 입력하세요", key="user_id")
    if not user_id:
        st.warning("이름을 입력해야 서비스를 이용할 수 있습니다.")
        st.stop()

# 5. 데이터 불러오기
@st.cache_data(ttl=5)
def load_data():
    try:
        data = conn.read(spreadsheet=SHEET_URL, ttl=0)
        # 필요한 컬럼이 없을 경우 대비
        cols = ["owner", "subject", "date", "desc", "note", "color", "status"]
        if data is None or data.empty:
            return pd.DataFrame(columns=cols)
        for col in cols:
            if col not in data.columns:
                data[col] = "🔴" if col == "color" else ("미시작" if col == "status" else "")
        return data
    except:
        return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note", "color", "status"])

all_df = load_data()
my_df = all_df[all_df["owner"] == user_id].copy() if not all_df.empty else pd.DataFrame()

# 6. 사이드바: 일정 추가 (색상 및 상태 추가)
with st.sidebar:
    st.markdown("---")
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목명")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        color = st.selectbox("색상 태그", ["🔴 빨강", "🟠 주황", "🟡 노랑", "🟢 초록", "🔵 파랑", "🟣 보라"])
        status = st.selectbox("공부 상태", ["⏳ 미시작", "📖 공부 중", "✅ 완료"])
        desc = st.text_input("상세 내용")
        note = st.text_area("메모")
        
        if st.form_submit_button("저장하기") and subject:
            new_row = pd.DataFrame([{
                "owner": user_id, "subject": subject, 
                "date": exam_date.strftime("%Y-%m-%d"), 
                "color": color.split()[0], "status": status.split()[1],
                "desc": desc, "note": note
            }])
            conn.update(spreadsheet=SHEET_URL, data=pd.concat([all_df, new_row], ignore_index=True))
            st.cache_data.clear()
            st.rerun()

# 7. [신규] D-Day 배너 (상단 대시보드)
if not my_df.empty:
    my_df['dt'] = pd.to_datetime(my_df['date'])
    future_exams = my_df[my_df['dt'].dt.date >= date.today()].sort_values('dt').head(3)
    
    if not future_exams.empty:
        st.subheader("🚨 임박한 시험 TOP 3")
        cols = st.columns(len(future_exams))
        for i, (idx, row) in enumerate(future_exams.iterrows()):
            d_day = (row['dt'].date() - date.today()).days
            with cols[i]:
                st.info(f"**{row['subject']}**\n\n**D-{d_day}** ({row['date']})")

# 8. 메인 화면: 탭 메뉴
tab1, tab2 = st.tabs(["📊 상세 리스트", "🗓️ 스마트 캘린더"])

with tab1:
    if my_df.empty:
        st.info("등록된 일정이 없습니다.")
    else:
        for idx, row in my_df.sort_values('dt').iterrows():
            d_day = (row['dt'].date() - date.today()).days
            d_text = f"D-{d_day}" if d_day > 0 else (":red[D-day]" if d_day == 0 else f"D+{abs(d_day)}")
            with st.expander(f"{row['color']} {d_text} | {row['subject']} [{row['status']}]"):
                st.write(f"**내용:** {row['desc']}")
                st.write(f"**메모:** {row['note']}")
                if st.button("삭제", key=f"del_{idx}"):
                    conn.update(spreadsheet=SHEET_URL, data=all_df.drop(idx))
                    st.cache_data.clear()
                    st.rerun()

with tab2:
    c1, c2 = st.columns([1, 4])
    selected_year = c1.selectbox("연도", range(date.today().year-1, date.today().year+3), index=1, key="y")
    selected_month = c2.selectbox("월", range(1, 13), index=date.today().month-1, key="m")
    
    cal = calendar.monthcalendar(selected_year, selected_month)
    cols = st.columns(7)
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        cols[i].markdown(f"<p style='text-align:center; background-color:#f0f2f6; border-radius:5px;'><b>{d}</b></p>", unsafe_allow_html=True)
    
    month_events = my_df[(my_df['dt'].dt.year == selected_year) & (my_df['dt'].dt.month == selected_month)] if not my_df.empty else pd.DataFrame()

    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: cols[i].write("")
            else:
                is_today = (day == date.today().day and selected_month == date.today().month and selected_year == date.today().year)
                bg = "#FFF9E6" if is_today else "#ffffff"
                txt = f"{day} 📍" if is_today else f"{day}"
                
                cols[i].markdown(f"<div style='border:1px solid #eee; padding:5px; min-height:110px; border-radius:8px; background-color:{bg};'>", unsafe_allow_html=True)
                cols[i].markdown(f"<div style='text-align:center; font-size:14px; color:{'#FF8C00' if is_today else '#31333F'};'>{txt}</div>", unsafe_allow_html=True)
                
                if not month_events.empty:
                    day_data = month_events[month_events['dt'].dt.day == day]
                    for _, ev in day_data.iterrows():
                        # 색상 태그에 따른 배경색 매핑
                        c_map = {"🔴":"#ff4b4b", "🟠":"#ffa500", "🟡":"#f9d71c", "🟢":"#28a745", "🔵":"#007bff", "🟣":"#6f42c1"}
                        bg_c = c_map.get(ev['color'], "#ff4b4b")
                        cols[i].markdown(f"<div style='font-size:9px; color:white; background-color:{bg_c}; padding:2px; border-radius:3px; margin-top:2px;'>{ev['status'][0]} {ev['subject']}</div>", unsafe_allow_html=True)
                cols[i].markdown("</div>", unsafe_allow_html=True)
