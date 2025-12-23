import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 (Google Sheets)")

# 2. 구글 시트 연결
# 에러 방지를 위해 connection만 먼저 선언합니다.
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 데이터 불러오기 함수
def load_data():
    # Secrets에 등록된 spreadsheet 주소를 사용하여 데이터를 읽어옵니다.
    # 에러 방지를 위해 ttl=0 설정을 유지합니다.
    return conn.read(ttl=0)

try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다. 구글 시트 공유 설정을 확인해주세요.")
    st.stop()

# 4. 사이드바: 시험 추가
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
            # 새로운 데이터를 기존 시트에 추가(Update) 합니다.
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success(f"'{subject}' 저장 완료!")
            st.rerun()

# 5. 메인 화면: 일정 목록
st.subheader("📋 전체 시험 일정")

if df.empty or len(df) == 0:
    st.info("등록된 시험 일정이 없습니다.")
else:
    # 날짜 정렬 및 표시
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
                df = df.drop(idx).drop(columns=['date_obj'])
                conn.update(data=df)
                st.rerun()
