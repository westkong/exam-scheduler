import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리 프로", page_icon="📅", layout="wide")
st.title("📅 시험 일정표 프로 (캘린더 고정 모드)")

# 2. 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 사용자 식별
with st.sidebar:
    st.header("👤 로그인")
    user_id = st.text_input("이름", key="user_id", help="본인의 이름을 입력하면 개인 일정이 로드됩니다.")
    if not user_id:
        st.info("이름을 입력해 주세요.")
        st.stop()

# 5. 데이터 불러오기
@st.cache_data(ttl=5)
def load_data():
    try:
        data = conn.read(spreadsheet=SHEET_URL, ttl=0)
        return data if data is not None else pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])
    except:
        return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

all_df = load_data()
my_df = all_df[all_df["owner"] == user_id].copy() if not all_df.empty and "owner" in all_df.columns else pd.DataFrame()

# 6. 사이드바: 일정 추가
with st.sidebar:
    st.markdown("---")
    st.header("➕ 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목명")
        exam_date = st.date_input("날짜", min_value=date.today())
        desc = st.text_input("시험 종류 (예: 중간고사)")
        note = st.text_area("메모")
        if st.form_submit_button("저장하기") and subject:
            new_row = pd.DataFrame([{"owner": user_id, "subject": subject, "date": exam_date.strftime("%Y-%m-%d"), "desc": desc, "note": note}])
            conn.update(spreadsheet=SHEET_URL, data=pd.concat([all_df, new_row], ignore_index=True))
            st.cache_data.clear()
            st.rerun()

# 7. 메인 화면: 탭 메뉴
# 세션 상태(session_state)를 사용하여 사용자가 선택한 탭을 유지하려고 시도하지만, 
# 기본적으로 탭은 클릭 시 해당 위치를 유지합니다.
tab1, tab2 = st.tabs(["📊 리스트 보기", "🗓️ 월간 캘린더"])

with tab1:
    if my_df.empty:
        st.info("등록된 일정이 없습니다.")
    else:
        my_df['date_obj'] = pd.to_datetime(my_df['date']).dt.date
        for idx, row in my_df.sort_values('date_obj').iterrows():
            diff = (row['date_obj'] - date.today()).days
            d_text = f"D-{diff}" if diff > 0 else (":red[D-day]" if diff == 0 else f"D+{abs(diff)}")
            with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
                st.write(f"내용: {row['desc']}")
                st.write(f"메모: {row['note']}")
                if st.button("삭제", key=f"del_{idx}"):
                    conn.update(spreadsheet=SHEET_URL, data=all_df.drop(idx))
                    st.cache_data.clear()
                    st.rerun()

with tab2:
    # --- 캘린더 컨트롤러 ---
    # selectbox의 key를 지정하면 값이 바뀌어도 페이지가 리스트 탭으로 튕기지 않습니다.
    col1, col2 = st.columns([1, 4])
    with col1:
        selected_year = st.selectbox("연도 선택", range(date.today().year - 1, date.today().year + 3), index=1, key="year_select")
    with col2:
        selected_month = st.selectbox("월 선택", range(1, 13), index=date.today().month - 1, key="month_select")
    
    st.markdown(f"### 🗓️ {selected_year}년 {selected_month}월")
    
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    # 요일 헤더
    cols = st.columns(7)
    days = ["월", "화", "수", "목", "금", "토", "일"]
    for i, day in enumerate(days):
        cols[i].markdown(f"<p style='text-align:center; background-color:#f0f2f6; border-radius:5px;'><b>{day}</b></p>", unsafe_allow_html=True)
        
    if not my_df.empty:
        my_df['dt'] = pd.to_datetime(my_df['date'])
        month_events = my_df[(my_df['dt'].dt.year == selected_year) & (my_df['dt'].dt.month == selected_month)]
    else:
        month_events = pd.DataFrame()

    # 달력 그리기
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                # 오늘 날짜 이모티콘 변경 (📍 대신 ✨ 또는 🔥)
                is_today = (day == date.today().day and selected_month == date.today().month and selected_year == date.today().year)
                
                # 오늘이면 배경색과 이모티콘을 다르게 표시
                bg_color = "#fff4f4" if is_today else "#ffffff"
                day_label = f"✨ **오늘 {day}**" if is_today else f"**{day}**"
                
                # 날짜 박스 시작
                cols[i].markdown(f"""
                    <div style='border:1px solid #eee; padding:5px; height:110px; border-radius:8px; background-color:{bg_color}; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);'>
                    <span style='color: {"#ff4b4b" if is_today else "#31333F"}; font-size: 14px;'>{day_label}</span>
                """, unsafe_allow_html=True)
                
                # 해당 날짜 시험 표시
                if not month_events.empty:
                    day_data = month_events[month_events['dt'].dt.day == day]
                    for _, event in day_data.iterrows():
                        cols[i].markdown(f"<div style='font-size:11px; color:white; background-color:#ff4b4b; padding:2px 5px; border-radius:4px; margin-top:2px;'>📕 {event['subject']}</div>", unsafe_allow_html=True)
                
                cols[i].markdown("</div>", unsafe_allow_html=True)
