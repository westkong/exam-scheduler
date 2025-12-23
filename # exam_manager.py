import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 (Google Sheets)")

# 2. 구글 시트 주소 (반드시 본인의 주소인지 확인)
url = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 구글 시트 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 데이터 불러오기 함수 (에러 방지를 위해 방식을 변경함)
@st.cache_data(ttl=10) # 10초마다 데이터 갱신
def get_data(_conn, url):
    # 가장 안전한 호출 방식입니다.
    return _conn.read(spreadsheet=url)

try:
    df = get_data(conn, url)
    if df is None:
        df = pd.DataFrame(columns=["subject", "date", "desc", "note"])
except Exception as e:
    st.error(f"연결 오류가 발생했습니다.")
    st.info("구글 시트의 [공유] 설정에서 서비스 계정 이메일이 추가되었는지 확인하세요.")
    st.stop()

# 5. 사이드바: 시험 추가
with st.sidebar:
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용")
        note = st.text_area("메모")
        submit = st.form_submit_button("저장하기")

        if submit and subject:
            new_row = pd.DataFrame([{
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # 업데이트 시에도 주소를 명시적으로 전달
            conn.update(spreadsheet=url, data=updated_df)
            st.success("저장되었습니다!")
            st.cache_data.clear() # 캐시 삭제하여 즉시 반영
            st.rerun()

# 6. 메인 화면 목록
st.subheader("📋 전체 일정")
if df.empty:
    st.info("등록된 일정이 없습니다.")
else:
    df['date_obj'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values(by='date_obj')
    for idx, row in df.iterrows():
        today = date.today()
        diff = (row['date_obj'] - today).days
        d_text = f"D-{diff}" if diff > 0 else (":red[D-day]" if diff == 0 else f"D+{abs(diff)}")
        with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
            st.write(f"내용: {row['desc']}")
            st.write(f"메모: {row['note']}")
            if st.button("삭제", key=f"del_{idx}"):
                df = df.drop(idx).drop(columns=['date_obj'])
                conn.update(spreadsheet=url, data=df)
                st.cache_data.clear()
                st.rerun()
