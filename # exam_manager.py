import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 (구글 시트 연동)")

# 2. 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 데이터 불러오기 (에러 방지를 위해 가장 보수적인 방식으로 호출)
def load_data():
    try:
        # spreadsheet 인자를 명시적으로 전달하되, 쿼리를 붙여서 문자열임을 확실히 합니다.
        return conn.read(spreadsheet=SHEET_URL, ttl=0)
    except Exception:
        # 시트가 아예 비어있거나 읽지 못할 경우를 대비한 기본값
        return pd.DataFrame(columns=["subject", "date", "desc", "note"])

df = load_data()

# 5. 사이드바: 시험 추가
with st.sidebar:
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용")
        note = st.text_area("메모")
        submit = st.form_submit_button("구글 시트에 저장")

        if submit and subject:
            new_row = pd.DataFrame([{
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # 업데이트 시 주소를 명시적으로 지정하여 에러 방지
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success("저장되었습니다!")
            st.rerun()

# 6. 메인 화면: 일정 목록
st.subheader("📋 전체 시험 일정")

if df is None or df.empty:
    st.info("등록된 시험 일정이 없습니다.")
else:
    # 날짜 정렬 처리
    df['date_obj'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values(by='date_obj')

    for idx, row in df.iterrows():
        today = date.today()
        diff = (row['date_obj'] - today).days
        d_text = f"D-{diff}" if diff > 0 else (":red[D-day]" if diff == 0 else f"D+{abs(diff)}")

        with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
            st.write(f"**내용:** {row['desc']}")
            st.write(f"**메모:** {row['note']}")
            if st.button("삭제", key=f"del_{idx}"):
                df = df.drop(idx)
                if 'date_obj' in df.columns:
                    df = df.drop(columns=['date_obj'])
                conn.update(spreadsheet=SHEET_URL, data=df)
                st.rerun()
