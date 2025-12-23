import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 (Google Sheets 연동)")

# 2. 구글 시트 주소 설정 (에러 방지를 위해 직접 입력)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 데이터 불러오기 함수
def load_data():
    # 주소를 직접 전달하여 에러를 원천 차단합니다.
    return conn.read(spreadsheet=SHEET_URL, ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error(f"연결 오류가 발생했습니다: {e}")
    st.info("시트의 '공유' 설정에서 서비스 계정 이메일이 '편집자'로 추가되었는지 확인하세요.")
    st.stop()

# 5. 사이드바: 시험 추가
with st.sidebar:
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용 (예: 중간고사)")
        note = st.text_area("메모")
        submit = st.form_submit_button("구글 시트에 저장하기")

        if submit and subject:
            new_row = pd.DataFrame([{
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # 저장할 때도 주소를 직접 지정합니다.
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success(f"'{subject}' 저장 완료!")
            st.rerun()

# 6. 메인 화면: 일정 목록
st.subheader("📋 전체 시험 일정")

if df.empty or len(df) == 0:
    st.info("등록된 시험 일정이 없습니다.")
else:
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
