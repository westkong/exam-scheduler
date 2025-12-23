import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리 프로", page_icon="📅", layout="wide")
st.title("📅 시험 일정표 프로 (캘린더 모드)")

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
        if data is None:
            return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])
        return data
    except:
        return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

all_df = load_data()
my_df = all_df[all_df["owner"] == user_id].copy() if not all_df.empty and "owner" in all_df.columns else pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

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
tab1, tab2 = st.tabs(["📊 리스트 보기", "🗓️ 월간 캘린더"])

with tab1:
    if my_df.empty:
        st.info("등록된 일정이 없습니다.")
    else:
        # 날짜 데이터 변환 및 정렬
        my_df['date_obj'] = pd.to_datetime(my_df['date']).dt.date
        for idx, row in my_df.sort_values('date_obj').iterrows():
            diff = (row['date_obj'] - date.today()).days
            d_text = f"D-{diff}" if diff > 0 else (":red[D-day]" if diff == 0 else f"D+{abs(diff)}")
            with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
                st.write(f"내용: {row['desc']}")
                st.write(f"**메모:** {row['note']}")
                if st.button("삭제", key=f"del_{idx}"):
                    conn.update(spreadsheet=SHEET_URL, data=all_df.drop(idx))
                    st.cache_data.clear()
                    st.rerun()

with tab2:
    # 연도와 월 선택 시 탭이 바뀌지 않도록 세션 유지
    col1, col2 = st.columns([1, 4])
    with col1:
        y_now = date.today().year
        selected_year = st.
