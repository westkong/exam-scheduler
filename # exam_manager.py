import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 1. 페이지 설정
st.set_page_config(page_title="개인별 시험 일정 관리", page_icon="📅")
st.title("📅 나만의 시험 일정표")

# 2. 구글 시트 주소 (이미 잘 작동하는 주소입니다)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IsaTPRJ43OgkBlzcwGMXsG_tBElems60wlRtXktkk14/edit?gid=0#gid=0"

# 3. 구글 시트 연결 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 사용자 식별 (이름 입력)
with st.sidebar:
    st.header("👤 사용자 인증")
    user_id = st.text_input("이름을 입력하세요 (예: 웨스트콩)", key="user_id")
    if not user_id:
        st.warning("이름을 입력해야 일정을 볼 수 있습니다.")
        st.stop()  # 이름 입력 전까지는 아래 코드를 실행하지 않음

# 5. 데이터 불러오기 함수
def load_data():
    try:
        data = conn.read(spreadsheet=SHEET_URL, ttl=0)
        # 데이터가 비어있으면 빈 데이터프레임 반환
        if data is None or data.empty:
            return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])
        return data
    except Exception:
        return pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

all_df = load_data()

# 6. 내 데이터만 필터링 (owner 열 기준)
if not all_df.empty and "owner" in all_df.columns:
    my_df = all_df[all_df["owner"] == user_id].copy()
else:
    my_df = pd.DataFrame(columns=["owner", "subject", "date", "desc", "note"])

# 7. 사이드바: 시험 추가 양식
with st.sidebar:
    st.markdown("---")
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용")
        note = st.text_area("메모")
        submit = st.form_submit_button(f"{user_id}님의 일정 저장")

        if submit and subject:
            new_row = pd.DataFrame([{
                "owner": user_id,
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            updated_df = pd.concat([all_df, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success("저장 완료!")
            st.rerun()

# 8. 메인 화면: 내 일정 목록 표시
st.subheader(f"📋 {user_id}님의 시험 일정")

if my_df.empty:
    st.info(f"'{user_id}'님으로 등록된 일정이 없습니다.")
else:
    # 날짜 정렬 처리
    my_df['date_obj'] = pd.to_datetime(my_df['date']).dt.date
    my_df = my_df.sort_values(by='date_obj')

    for idx, row in my_df.iterrows():
        today = date.today()
        diff = (row['date_obj'] - today).days
        
        # D-day 계산 및 색상 표시
        if diff > 0:
            d_text = f"D-{diff}"
        elif diff == 0:
            d_text = ":red[D-day]"
        else:
            d_text = f"D+{abs(diff)}"

        with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
            st.write(f"**상세:** {row['desc']}")
            st.write(f"**메모:** {row['note']}")
            
            # 삭제 버튼 (전체 시트에서 내 데이터만 삭제)
            if st.button("일정 삭제", key=f"del_{idx}"):
                final_df = all_df.drop(idx)
                if 'date_obj' in final_df.columns:
                    final_df = final_df.drop(columns=['date_obj'])
                conn.update(spreadsheet=SHEET_URL, data=final_df)
                st.rerun()
