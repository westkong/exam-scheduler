import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 (Google Sheets)")

# 2. 구글 시트 연결 생성
# 주소는 Secrets의 [connections.gsheets] 섹션에 있는 spreadsheet 항목을 자동으로 읽습니다.
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 데이터 불러오기 함수
def load_data():
    # 인자 없이 호출하여 'str' 변환 에러(UnsupportedSubstrateError)를 원천 차단합니다.
    return conn.read(ttl=0)

try:
    df = load_data()
    # 데이터가 아예 없을 경우를 대비해 컬럼 강제 생성
    if df is None or df.empty:
        df = pd.DataFrame(columns=["subject", "date", "desc", "note"])
except Exception as e:
    st.error(f"시트 연결 중 오류가 발생했습니다.")
    st.info("Secrets에 'spreadsheet' 주소가 정확히 입력되었는지 확인해주세요.")
    st.stop()

# 4. 사이드바: 시험 추가
with st.sidebar:
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용 (예: 중간고사)")
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
            # 저장할 때도 인자 없이 업데이트를 시도합니다.
            conn.update(data=updated_df)
            st.success("성공적으로 저장되었습니다!")
            st.rerun()

# 5. 메인 화면: 일정 목록
st.subheader("📋 전체 시험 일정")

if df.empty:
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
                df = df.drop(idx)
                if 'date_obj' in df.columns:
                    df = df.drop(columns=['date_obj'])
                conn.update(data=df)
                st.rerun()
