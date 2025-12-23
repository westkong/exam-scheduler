import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="개인별 시험 일정 관리", page_icon="📅")
st.title("📅 나만의 시험 일정표")

# 2. 구글 시트 주소 (기존 주소 그대로 사용)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 사용자 식별 (이름 입력)
with st.sidebar:
    st.header("👤 사용자 인증")
    user_id = st.text_input("이름을 입력하세요 (예: 웨스트콩)", key="user_id")
    if not user_id:
        st.warning("이름을 입력해야 일정을 볼 수 있습니다.")
        st.stop()  # 이름 입력 전까지는 아래 코드를 실행하지 않음

# 5. 데이터 불러오기
def load_data():
    try:
        data = conn.read(spreadsheet=SHEET_URL, ttl=0)
        return data
    except:
        return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

all_df = load_data()

# 6. 내 데이터만 필터링
# 'owner' 컬럼이 있는 경우 내 이름과 일치하는 행만 가져옴
if not all_df.empty and "owner" in all_df.columns:
    my_df = all_df[all_df["owner"] == user_id].copy()
else:
    my_df = pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

# 7. 사이드바: 시험 추가
with st.sidebar:
    st.markdown("---")
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용")
        note = st.text_area("메모")
        submit = st.form_submit_button(f"{user_id}님의 일정으로 저장")

        if submit and subject:
            new_row = pd.DataFrame([{
                "owner": user_id,  # 소유자 이름 저장
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            updated_df = pd.concat([all_df, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success(f"저장 완료! 리스트를 확인하세요.")
            st.rerun()

# 8. 메인 화면: 내 일정만 표시
st.subheader(f"📋 {user_id}님의 시험 일정")

if my_df.empty:
    st.info(f"등록된 일정이 없습니다. 사이드바에서 추가해 보세요!")
else:
    my_df['date_obj'] = pd.to_datetime(my_df['date']).dt.date
    my_df = my_df.sort_values(by='date_obj')

    for idx, row in my_df.iterrows():
        today = date.today()
        diff = (row['date_obj'] - today).days
        d_text = f"D-{diff}" if diff > 0 else (":red[D-day]" if diff == 0 else f"D+{abs(diff)}")

        with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
            st.write(f"**내용:** {row['desc']}")
            st.write(f"**메모:** {row['note']}")
            
            # 삭제 기능 (전체 데이터에서 해당 행만 삭제)
            if st.button("삭제", key=f"del_{idx}"):
                # 전체
