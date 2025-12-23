import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# 페이지 설정
st.set_page_config(page_title="시험 일정 관리 (DB)", page_icon="📅")
st.title("📅 구글 시트 연동 시험 일정 관리")

# 1. 구글 시트 연결 (Secrets에 설정한 정보를 자동으로 가져옵니다)
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 데이터 불러오기 함수
def load_data():
    try:
        # 시트의 데이터를 읽어옵니다
        return conn.read(ttl=0) # ttl=0은 캐시 없이 실시간으로 가져온다는 뜻입니다
    except:
        # 시트가 비어있을 경우 빈 표를 만듭니다
        return pd.DataFrame(columns=["subject", "date", "desc", "note"])

# 데이터 로드
df = load_data()

# 사이드바: 시험 추가
with st.sidebar:
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용 (예: 중간고사)")
        note = st.text_area("메모")
        submit = st.form_submit_button("구글 시트에 저장하기")

        if submit and subject:
            # 새로운 행 데이터 생성
            new_data = pd.DataFrame([{
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }])
            # 기존 데이터에 합치기
            updated_df = pd.concat([df, new_data], ignore_index=True)
            # 구글 시트 업데이트
            conn.update(data=updated_df)
            st.success(f"'{subject}' 일정이 구글 시트에 저장되었습니다!")
            st.rerun()

# 메인 화면: 일정 목록 표시
st.subheader("📋 전체 시험 일정 (실시간)")

if df.empty or len(df) == 0:
    st.info("등록된 시험 일정이 없습니다. 사이드바에서 추가해 주세요.")
else:
    # 날짜순 정렬 (데이터가 있을 때만)
    df['date_obj'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values(by='date_obj')

    for idx, row in df.iterrows():
        today = date.today()
        diff = (row['date_obj'] - today).days
        
        # D-day 계산
        if diff > 0: d_text = f"D-{diff}"
        elif diff == 0: d_text = ":red[D-day]"
        else: d_text = f"D+{abs(diff)}"

        with st.expander(f"{d_text} | {row['subject']} ({row['date']})"):
            st.write(f"**내용:** {row['desc']}")
            st.write(f"**메모:** {row['note']}")
            
            # 삭제 버튼
            if st.button(f"삭제", key=f"del_{idx}"):
                df = df.drop(idx)
                # 정렬용으로 만든 임시 컬럼 삭제 후 저장
                df = df.drop(columns=['date_obj'])
                conn.update(data=df)
                st.success("삭제되었습니다.")
                st.rerun()

st.write("---")
st.caption("이 앱의 데이터는 연결된 구글 스프레드시트에 실시간으로 보관됩니다.")
