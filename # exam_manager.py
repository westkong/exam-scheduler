import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 (DB 연동 완료)")

# 2. 구글 시트 주소
url = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 데이터 불러오기 (에러 방지를 위해 명시적으로 spreadsheet 전달)
def load_data():
    # 데이터가 없을 때를 대비해 빈 데이터프레임 구조를 미리 잡습니다.
    try:
        # 이 부분이 에러 지점이므로, 가장 안전한 방식으로 호출합니다.
        data = conn.read(spreadsheet=url, usecols=[0,1,2,3], ttl=0)
        return data
    except:
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
        submit = st.form_submit_button("저장하기")

        if submit and subject:
            new_row = pd.DataFrame([{
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            # 기존 데이터와 합치기
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # 저장 시에도 주소를 명시적으로 전달
            conn.update(spreadsheet=url, data=updated_df)
            st.success("저장 성공!")
            st.rerun()

# 6. 메인 화면 목록
st.subheader("📋 전체 일정")

if df is None or df.empty:
    st.info("등록된 일정이 없습니다. 사이드바에서 추가해 보세요.")
else:
    # 날짜 정렬
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
                # 삭제 후 업데이트
                df_to_save = df.drop(idx).drop(columns=['date_obj'])
                conn.update(spreadsheet=url, data=df_to_save)
                st.rerun()
